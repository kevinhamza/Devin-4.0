// src/providers/gemini.ts — Google Gemini provider (REST + SDK)
// Uses native fetch() against the v1beta REST endpoint as the primary path
// because the @google/genai TypeScript SDK has had version-specific issues
// sending API keys in the correct format. Curl confirms the REST endpoint works.

import { Message, ToolDefinition, ModelResponse, ContentBlock } from '../types.js';
import { BaseProvider, StreamChunk } from './base.js';

const GEMINI_BASE = 'https://generativelanguage.googleapis.com/v1beta/models';

// Models to try in order. gemini-3.6-flash confirmed working via REST test.
const FALLBACK_MODELS = [
  'gemini-3.6-flash',
  'gemini-3.5-flash',
  'gemini-2.5-flash',
  'gemini-2.5-pro',
  'gemini-2.0-flash',
  'gemini-1.5-pro',
  'gemini-1.5-flash',
];

type GeminiPart = { text?: string; inlineData?: { mimeType: string; data: string } };
type GeminiContent = { role: 'user' | 'model'; parts: GeminiPart[] };

function makeParts(text: string): GeminiPart[] {
  const IMG_RE = /__IMG__([\w/]+)__([A-Za-z0-9+/=]+)__ENDIMG__/g;
  if (!text.includes('__IMG__')) return [{ text: text || ' ' }];
  const parts: GeminiPart[] = [];
  let cursor = 0;
  IMG_RE.lastIndex = 0;
  let match: RegExpExecArray | null;
  while ((match = IMG_RE.exec(text)) !== null) {
    const before = text.slice(cursor, match.index).trim();
    if (before) parts.push({ text: before });
    parts.push({ inlineData: { mimeType: match[1], data: match[2] } });
    cursor = match.index + match[0].length;
  }
  const after = text.slice(cursor).trim();
  if (after) parts.push({ text: after });
  if (parts.length === 0) parts.push({ text: text || ' ' });
  return parts;
}

function toGeminiContents(messages: Message[]): GeminiContent[] {
  const raw: GeminiContent[] = messages
    .filter(m => m.role !== 'system')
    .map(m => ({
      role: m.role === 'assistant' ? 'model' as const : 'user' as const,
      parts: makeParts(m.content),
    }));

  // Gemini requires strict user↔model alternation.
  // When the model makes only tool calls (no text), no assistant message is pushed
  // to history (cli.ts), so consecutive user-role messages appear. Insert a neutral
  // model turn between them so Gemini doesn't reject the conversation.
  const fixed: GeminiContent[] = [];
  for (const msg of raw) {
    const prev = fixed[fixed.length - 1];
    if (prev && prev.role === msg.role) {
      if (msg.role === 'user') {
        fixed.push({ role: 'model', parts: [{ text: ' ' }] });
      } else {
        prev.parts.push(...msg.parts);
        continue;
      }
    }
    fixed.push(msg);
  }
  if (fixed.length > 0 && fixed[0].role === 'model') {
    fixed.unshift({ role: 'user', parts: [{ text: ' ' }] });
  }
  return fixed;
}

function toGeminiTools(tools: ToolDefinition[]) {
  return [{
    functionDeclarations: tools.map(t => ({
      name: t.name,
      description: t.description,
      parameters: {
        type: 'OBJECT',
        properties: Object.fromEntries(
          Object.entries(t.input_schema.properties).map(([k, v]) => [
            k,
            { type: (v.type as string).toUpperCase(), description: v.description }
          ])
        ),
        required: t.input_schema.required || [],
      },
    })),
  }];
}

// Parse a Gemini REST response into our ModelResponse format
function parseResponse(data: Record<string, unknown>, modelId: string): ModelResponse {
  const content: ContentBlock[] = [];
  const candidates = data.candidates as Array<Record<string, unknown>> | undefined;
  const candidate = candidates?.[0];
  const parts = (candidate?.content as Record<string, unknown>)?.parts as Array<Record<string, unknown>> | undefined;

  for (const part of parts ?? []) {
    if (part.text) {
      content.push({ type: 'text', text: part.text as string });
    } else if (part.functionCall) {
      const fc = part.functionCall as Record<string, unknown>;
      content.push({
        type: 'tool_use',
        id: `tool_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
        name: (fc.name as string) ?? '',
        input: (fc.args as Record<string, unknown>) ?? {},
      });
    }
  }

  const stopReason = content.some(b => b.type === 'tool_use') ? 'tool_use' :
    (candidate?.finishReason === 'MAX_TOKENS' ? 'max_tokens' : 'end_turn');

  const usage = data.usageMetadata as Record<string, number> | undefined;
  return {
    id: `gemini_${Date.now()}`,
    model: modelId,
    role: 'assistant',
    content,
    stop_reason: stopReason as ModelResponse['stop_reason'],
    usage: {
      input_tokens: usage?.promptTokenCount ?? 0,
      output_tokens: usage?.candidatesTokenCount ?? 0,
    },
  };
}

async function geminiPost(
  apiKey: string,
  modelId: string,
  body: Record<string, unknown>,
  stream = false
): Promise<Response> {
  // Python SDK confirmed working format:
  // - Key goes in x-goog-api-key header (NOT query param)
  // - x-goog-api-client header required for the API to accept the key
  // - URL has NO ?key= query parameter
  const url = stream
    ? `${GEMINI_BASE}/${modelId}:streamGenerateContent?alt=sse`
    : `${GEMINI_BASE}/${modelId}:generateContent`;
  return fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-goog-api-key': apiKey,
      'x-goog-api-client': 'google-genai-sdk/2.19.0 gl-node/24',
    },
    body: JSON.stringify(body),
  });
}

function isRetryable(status: number, text: string): boolean {
  return status === 429 || status === 503 || status === 502 || status === 408 ||
    text.includes('rate') || text.includes('quota') || text.includes('overloaded') ||
    text.includes('unavailable') || text.includes('resource_exhausted');
}

function isModelError(status: number, text: string): boolean {
  return status === 404 || text.includes('not found') || text.includes('not_found') ||
    text.includes('no longer available') || text.includes('deprecated');
}

function retryDelayMs(respText: string, defaultMs = 2000): number {
  // Parse "Please retry in X.XXs" from Gemini 429 response.
  // Cap at 5s so we fail fast — callers show a clear rate-limit message
  // instead of hanging for a full minute.
  const match = respText.match(/retry in (\d+(?:\.\d+)?)s/i);
  if (match) return Math.min(Math.ceil(parseFloat(match[1])) * 1000, 5000);
  return defaultMs;
}

function isRateLimit(status: number, text: string): boolean {
  return status === 429 || text.includes('resource_exhausted') || text.includes('quota exceeded');
}

export class GeminiProvider extends BaseProvider {
  readonly name = 'Gemini';
  readonly model: string;
  private apiKey: string;

  constructor(apiKey: string, model = 'gemini-3.6-flash') {
    super();
    this.apiKey = apiKey;
    this.model = model;
  }

  private buildBody(
    messages: Message[],
    tools: ToolDefinition[],
    options: { maxTokens?: number; systemPrompt?: string }
  ): Record<string, unknown> {
    const systemText = options.systemPrompt || messages.find(m => m.role === 'system')?.content;
    const body: Record<string, unknown> = {
      contents: toGeminiContents(messages),
      generationConfig: { maxOutputTokens: options.maxTokens ?? 8192 },
    };
    if (systemText) {
      body.system_instruction = { parts: [{ text: systemText }] };
    }
    if (tools.length > 0) {
      body.tools = toGeminiTools(tools);
    }
    return body;
  }

  async chat(
    messages: Message[],
    tools: ToolDefinition[],
    options: { maxTokens?: number; systemPrompt?: string } = {}
  ): Promise<ModelResponse> {
    const body = this.buildBody(messages, tools, options);
    const models = [this.model, ...FALLBACK_MODELS.filter(m => m !== this.model)];
    let lastError = '';

    for (const modelId of models) {
      let resp: Response;
      try {
        resp = await geminiPost(this.apiKey, modelId, body);
      } catch (e) {
        lastError = String(e);
        continue;
      }

      const text = await resp.text();
      if (resp.ok) {
        return parseResponse(JSON.parse(text), modelId);
      }

      lastError = `${resp.status} ${text.slice(0, 300)}`;
      // Fail fast on rate limit — show clear message instead of spinning for 60s
      if (isRateLimit(resp.status, text.toLowerCase())) {
        const match = text.match(/retry in (\d+(?:\.\d+)?)s/i);
        const retryIn = match ? `${Math.ceil(parseFloat(match[1]))}s` : '~60s';
        throw new Error(`Rate limit (free tier quota). Retry in ${retryIn}.`);
      }
      if (isRetryable(resp.status, text.toLowerCase())) {
        await new Promise(r => setTimeout(r, 2000));
        continue;
      }
      if (isModelError(resp.status, text.toLowerCase())) continue;
      break; // non-retriable auth/format error
    }

    throw new Error(`Gemini: all models failed. Last error: ${lastError}`);
  }

  async stream(
    messages: Message[],
    tools: ToolDefinition[],
    onChunk: (chunk: StreamChunk) => void,
    options: { maxTokens?: number; systemPrompt?: string } = {}
  ): Promise<ModelResponse> {
    const body = this.buildBody(messages, tools, options);
    const models = [this.model, ...FALLBACK_MODELS.filter(m => m !== this.model)];
    let lastError = '';

    for (const modelId of models) {
      let resp: Response;
      try {
        resp = await geminiPost(this.apiKey, modelId, body, true);
      } catch (e) {
        lastError = String(e);
        continue;
      }

      if (!resp.ok) {
        const text = await resp.text();
        lastError = `${resp.status} ${text.slice(0, 300)}`;
        if (isRateLimit(resp.status, text.toLowerCase())) {
          const match = text.match(/retry in (\d+(?:\.\d+)?)s/i);
          const retryIn = match ? `${Math.ceil(parseFloat(match[1]))}s` : '~60s';
          throw new Error(`Rate limit (free tier quota). Retry in ${retryIn}.`);
        }
        if (isRetryable(resp.status, text.toLowerCase())) {
          await new Promise(r => setTimeout(r, 2000));
          continue;
        }
        if (isModelError(resp.status, text.toLowerCase())) continue;
        break;
      }

      // Stream SSE response
      const accText = { v: '' };
      const toolUses: Array<{ name: string; input: Record<string, unknown> }> = [];
      const decoder = new TextDecoder();

      try {
        const reader = resp.body!.getReader();
        let buf = '';
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const lines = buf.split('\n');
          buf = lines.pop() ?? '';
          for (const line of lines) {
            if (!line.startsWith('data: ')) continue;
            const payload = line.slice(6).trim();
            if (!payload || payload === '[DONE]') continue;
            let chunk: Record<string, unknown>;
            try { chunk = JSON.parse(payload); } catch { continue; }
            const parts = ((chunk.candidates as Array<Record<string,unknown>>)?.[0]?.content as Record<string,unknown>)?.parts as Array<Record<string,unknown>> | undefined;
            for (const part of parts ?? []) {
              if (part.text) {
                const t = part.text as string;
                accText.v += t;
                onChunk({ type: 'text', content: t });
              } else if (part.functionCall) {
                const fc = part.functionCall as Record<string, unknown>;
                const tu = {
                  name: (fc.name as string) ?? '',
                  input: (fc.args as Record<string, unknown>) ?? {},
                };
                toolUses.push(tu);
                onChunk({
                  type: 'tool_use',
                  toolName: tu.name,
                  toolInput: tu.input,
                  toolUseId: `tool_${Date.now()}`,
                });
              }
            }
          }
        }
      } catch (e) {
        // If streaming fails partway, fall back to non-streaming
        onChunk({ type: 'done' });
        return this.chat(messages, tools, options);
      }

      onChunk({ type: 'done' });
      const content: ContentBlock[] = [];
      if (accText.v) content.push({ type: 'text', text: accText.v });
      for (const tu of toolUses) {
        content.push({
          type: 'tool_use',
          id: `tool_${Date.now()}_${Math.random().toString(36).slice(2,6)}`,
          name: tu.name,
          input: tu.input,
        });
      }
      return {
        id: `gemini_stream_${Date.now()}`,
        model: modelId,
        role: 'assistant',
        content,
        stop_reason: toolUses.length > 0 ? 'tool_use' : 'end_turn',
        usage: { input_tokens: 0, output_tokens: 0 },
      };
    }

    throw new Error(`Gemini: all models failed during stream. Last: ${lastError}`);
  }
}
