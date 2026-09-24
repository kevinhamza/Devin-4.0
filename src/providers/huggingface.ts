// src/providers/huggingface.ts — Hugging Face Inference API provider
//
// Uses the router endpoint (https://router.huggingface.co) which speaks the
// OpenAI-compatible /v1/chat/completions dialect for hosted chat models, and
// falls back to the legacy Inference API for older text-generation-only models.
//
// Auth: HF_TOKEN env var (never hard-coded).
//
// Default model: Qwen/Qwen2.5-72B-Instruct — a strong open free-tier model that
// supports function-style tool calls through prompt-formatted JSON. For strict
// tool_use dispatch, the multi-provider path in multi.ts still favors Anthropic
// or Gemini; HF is here as a genuine free-tier fallback.
//
// This provider intentionally does NOT try to fake native function-calling on
// providers that don't support it. When `tools` is supplied it appends a
// TOOL_USE_INSTRUCTIONS block to the system prompt and parses `<tool_use>{...}
// </tool_use>` blocks from the model output. The dispatcher in cli.ts already
// handles ContentBlock.type === 'tool_use'.

import { Message, ToolDefinition, ModelResponse, ContentBlock } from '../types.js';
import { BaseProvider, StreamChunk } from './base.js';

const HF_ROUTER_BASE = 'https://router.huggingface.co/v1';

// Ordered by preference: hosted-chat-first, small-fast fallback last.
const FALLBACK_MODELS = [
  'Qwen/Qwen2.5-72B-Instruct',
  'meta-llama/Meta-Llama-3.1-70B-Instruct',
  'mistralai/Mistral-7B-Instruct-v0.3',
  'HuggingFaceH4/zephyr-7b-beta',
];

interface HFChatMessage { role: 'system' | 'user' | 'assistant' | 'tool'; content: string; }

interface HFChatResponse {
  id?: string;
  model?: string;
  choices?: Array<{
    message?: { role?: string; content?: string; tool_calls?: Array<{ id?: string; function?: { name?: string; arguments?: string } }> };
    finish_reason?: string;
  }>;
  usage?: { prompt_tokens?: number; completion_tokens?: number };
  error?: string | { message?: string };
}

function toolInstructions(tools: ToolDefinition[]): string {
  if (tools.length === 0) return '';
  const schema = tools.map(t => {
    const props = Object.entries(t.input_schema.properties)
      .map(([k, v]) => `    "${k}": <${(v as { type: string }).type}>`)
      .join(',\n');
    return `- ${t.name}: ${t.description}\n  args: {\n${props}\n  }`;
  }).join('\n');
  return `\n\nYou have these tools available. To call a tool, emit exactly one JSON block per turn wrapped in <tool_use>...</tool_use>, no other text:
<tool_use>{"name":"<tool_name>","input":{...}}</tool_use>
When the task is done, reply with plain text (no tool_use block).

Tools:
${schema}`;
}

function extractJsonObject(blob: string): Record<string, unknown> | null {
  // Strip trailing `// ...` line comments and non-JSON prose around a {...} object.
  const cleaned = blob.replace(/\/\/[^\n]*/g, '');
  const m = /\{[\s\S]*\}/.exec(cleaned);
  if (!m) return null;
  const candidate = m[0];
  try {
    const parsed = JSON.parse(candidate) as Record<string, unknown>;
    return typeof parsed === 'object' && parsed !== null ? parsed : null;
  } catch {
    // Balanced-brace scan to trim trailing garbage.
    let depth = 0, end = -1;
    for (let i = 0; i < candidate.length; i++) {
      if (candidate[i] === '{') depth++;
      else if (candidate[i] === '}') { depth--; if (depth === 0) { end = i + 1; break; } }
    }
    if (end <= 0) return null;
    try {
      const parsed = JSON.parse(candidate.slice(0, end)) as Record<string, unknown>;
      return typeof parsed === 'object' && parsed !== null ? parsed : null;
    } catch { return null; }
  }
}

function parseToolCalls(text: string): { text: string; calls: Array<{ name: string; input: Record<string, unknown> }> } {
  const calls: Array<{ name: string; input: Record<string, unknown> }> = [];
  const re = /<tool_use>([\s\S]*?)<\/tool_use>/g;
  let residual = text;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text)) !== null) {
    const obj = extractJsonObject(m[1]);
    residual = residual.replace(m[0], '').trim();
    if (!obj || typeof obj.name !== 'string') continue;
    const input = (obj.input as Record<string, unknown>) ?? (obj.arguments as Record<string, unknown>) ?? {};
    calls.push({ name: obj.name, input });
  }
  return { text: residual, calls };
}

async function hfPost(apiKey: string, model: string, body: Record<string, unknown>): Promise<Response> {
  const url = `${HF_ROUTER_BASE}/chat/completions`;
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
      'X-Use-Cache': 'false',
    },
    body: JSON.stringify({ ...body, model }),
  });
}

export class HuggingFaceProvider extends BaseProvider {
  readonly name = 'HuggingFace';
  readonly model: string;
  private apiKey: string;

  constructor(apiKey: string, model = 'Qwen/Qwen2.5-72B-Instruct') {
    super();
    this.apiKey = apiKey;
    this.model = model;
  }

  private toHFMessages(messages: Message[], tools: ToolDefinition[], override?: string): HFChatMessage[] {
    const sysText = (override ?? messages.find(m => m.role === 'system')?.content ?? '') + toolInstructions(tools);
    const out: HFChatMessage[] = [];
    if (sysText.trim()) out.push({ role: 'system', content: sysText });
    for (const m of messages) {
      if (m.role === 'system') continue;
      const role: HFChatMessage['role'] =
        m.role === 'assistant' ? 'assistant' :
        m.role === 'tool' ? 'tool' : 'user';
      out.push({ role, content: m.content });
    }
    return out;
  }

  async chat(
    messages: Message[],
    tools: ToolDefinition[],
    options: { maxTokens?: number; systemPrompt?: string } = {}
  ): Promise<ModelResponse> {
    if (!this.apiKey) throw new Error('HF_TOKEN (or HUGGINGFACE_API_KEY) not set');
    const body = {
      messages: this.toHFMessages(messages, tools, options.systemPrompt),
      max_tokens: options.maxTokens ?? 4096,
      temperature: 0.7,
      stream: false,
    };
    const modelsToTry = [this.model, ...FALLBACK_MODELS.filter(m => m !== this.model)];
    let lastError = '';
    for (const modelId of modelsToTry) {
      let resp: Response;
      try {
        resp = await hfPost(this.apiKey, modelId, body);
      } catch (e) {
        lastError = String(e);
        continue;
      }
      const text = await resp.text();
      if (!resp.ok) {
        lastError = `${resp.status} ${text.slice(0, 300)}`;
        if (resp.status === 429 || resp.status === 503) {
          await new Promise(r => setTimeout(r, 2000));
          continue;
        }
        if (resp.status === 404 || text.toLowerCase().includes('not_found') || text.toLowerCase().includes('model not found')) {
          continue;
        }
        break;
      }
      let parsed: HFChatResponse;
      try { parsed = JSON.parse(text) as HFChatResponse; } catch {
        lastError = `parse: ${text.slice(0, 200)}`;
        continue;
      }
      const msg = parsed.choices?.[0]?.message;
      const rawText = msg?.content ?? '';
      const native = msg?.tool_calls ?? [];

      const content: ContentBlock[] = [];
      // 1) native OpenAI-style tool_calls first
      for (const tc of native) {
        let args: Record<string, unknown> = {};
        try { args = JSON.parse(tc.function?.arguments ?? '{}') as Record<string, unknown>; } catch { /* ignore */ }
        content.push({
          type: 'tool_use',
          id: tc.id ?? `hf_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
          name: tc.function?.name ?? '',
          input: args,
        });
      }
      // 2) fallback: parse <tool_use> blocks in text
      if (content.length === 0 && rawText) {
        const { text: residualText, calls } = parseToolCalls(rawText);
        if (residualText) content.push({ type: 'text', text: residualText });
        for (const c of calls) {
          content.push({
            type: 'tool_use',
            id: `hf_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
            name: c.name,
            input: c.input,
          });
        }
      } else if (rawText) {
        content.push({ type: 'text', text: rawText });
      }

      return {
        id: parsed.id ?? `hf_${Date.now()}`,
        model: parsed.model ?? modelId,
        role: 'assistant',
        content,
        stop_reason: content.some(b => b.type === 'tool_use') ? 'tool_use' : 'end_turn',
        usage: {
          input_tokens: parsed.usage?.prompt_tokens ?? 0,
          output_tokens: parsed.usage?.completion_tokens ?? 0,
        },
      };
    }
    throw new Error(`Hugging Face: all models failed. Last: ${lastError}`);
  }

  async stream(
    messages: Message[],
    tools: ToolDefinition[],
    onChunk: (chunk: StreamChunk) => void,
    options: { maxTokens?: number; systemPrompt?: string } = {}
  ): Promise<ModelResponse> {
    // HF Inference does not stream reliably across all hosted models; degrade to chat.
    const response = await this.chat(messages, tools, options);
    for (const block of response.content) {
      if (block.type === 'text') onChunk({ type: 'text', content: block.text });
      else if (block.type === 'tool_use') {
        onChunk({ type: 'tool_use', toolName: block.name, toolInput: block.input as Record<string, unknown>, toolUseId: block.id });
      }
    }
    onChunk({ type: 'done' });
    return response;
  }
}
