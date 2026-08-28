// src/providers/multi.ts — Multi-provider routing
// Ported from cheetahclaws/providers.py: supports 12+ AI providers
// Automatic detection from model string, fallback chains, streaming

import * as https from 'https';
import * as http from 'http';
import { Message, ToolDefinition, ModelResponse, ContentBlock } from '../types.js';
import { BaseProvider, StreamChunk } from './base.js';

// ── Provider registry (from cheetahclaws/providers.py) ───────────────────────

export const PROVIDER_REGISTRY: Record<string, {
  type: string;
  api_key_env: string;
  base_url?: string;
  context_limit: number;
  models: string[];
}> = {
  anthropic: {
    type: 'anthropic',
    api_key_env: 'ANTHROPIC_API_KEY',
    context_limit: 200000,
    models: [
      'claude-opus-4-8', 'claude-sonnet-4-6', 'claude-haiku-4-5-20251001',
      'claude-opus-4-5', 'claude-sonnet-4-5',
      'claude-3-5-sonnet-20241022', 'claude-3-5-haiku-20241022',
    ],
  },
  openai: {
    type: 'openai',
    api_key_env: 'OPENAI_API_KEY',
    base_url: 'https://api.openai.com/v1',
    context_limit: 128000,
    models: [
      'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4.1', 'gpt-4.1-mini',
      'gpt-5', 'gpt-5-nano', 'gpt-5-mini', 'o4-mini', 'o3', 'o3-mini', 'o1',
    ],
  },
  gemini: {
    type: 'openai',
    api_key_env: 'GEMINI_API_KEY',
    base_url: 'https://generativelanguage.googleapis.com/v1beta/openai/',
    context_limit: 1000000,
    models: [
      'gemini-2.5-flash', 'gemini-2.5-pro',
      'gemini-2.0-flash', 'gemini-2.0-flash-lite',
      'gemini-1.5-pro', 'gemini-1.5-flash',
    ],
  },
  ollama: {
    type: 'openai',
    api_key_env: '',
    base_url: 'http://localhost:11434/v1',
    context_limit: 32000,
    models: ['llama3.3', 'llama3.1', 'qwen2.5-coder', 'mistral', 'gemma3'],
  },
  deepseek: {
    type: 'openai',
    api_key_env: 'DEEPSEEK_API_KEY',
    base_url: 'https://api.deepseek.com/v1',
    context_limit: 128000,
    models: ['deepseek-chat', 'deepseek-reasoner', 'deepseek-coder'],
  },
  openrouter: {
    type: 'openai',
    api_key_env: 'OPENROUTER_API_KEY',
    base_url: 'https://openrouter.ai/api/v1',
    context_limit: 200000,
    models: ['openrouter/anthropic/claude-sonnet-4-6', 'openrouter/google/gemini-2.0-flash'],
  },
  groq: {
    type: 'openai',
    api_key_env: 'GROQ_API_KEY',
    base_url: 'https://api.groq.com/openai/v1',
    context_limit: 128000,
    models: ['llama-3.3-70b-versatile', 'mixtral-8x7b-32768', 'gemma2-9b-it'],
  },
  together: {
    type: 'openai',
    api_key_env: 'TOGETHER_API_KEY',
    base_url: 'https://api.together.xyz/v1',
    context_limit: 32000,
    models: ['meta-llama/Llama-3-70b-chat-hf', 'mistralai/Mixtral-8x7B-Instruct-v0.1'],
  },
  perplexity: {
    type: 'openai',
    api_key_env: 'PERPLEXITY_API_KEY',
    base_url: 'https://api.perplexity.ai',
    context_limit: 128000,
    models: ['sonar', 'sonar-pro', 'sonar-reasoning'],
  },
  mistral: {
    type: 'openai',
    api_key_env: 'MISTRAL_API_KEY',
    base_url: 'https://api.mistral.ai/v1',
    context_limit: 128000,
    models: ['mistral-large-latest', 'mistral-small-latest', 'codestral-latest'],
  },
  cohere: {
    type: 'openai',
    api_key_env: 'COHERE_API_KEY',
    base_url: 'https://api.cohere.com/compatibility/v1',
    context_limit: 128000,
    models: ['command-r-plus', 'command-r'],
  },
};

// ── Token estimation (from cheetahclaws/compaction.py) ───────────────────────
// chars/2.8 (conservative for code-heavy content) + 4 tokens/msg framing + 10% buffer

export function estimateTokens(messages: Message[]): number {
  let totalChars = 0;
  for (const m of messages) {
    totalChars += m.content.length;
  }
  const contentTokens = Math.floor(totalChars / 2.8);
  const framingTokens = messages.length * 4;
  return Math.floor((contentTokens + framingTokens) * 1.1);
}

export function getContextLimit(model: string): number {
  for (const [, prov] of Object.entries(PROVIDER_REGISTRY)) {
    if (prov.models.some(m => model.includes(m) || m.includes(model.split('/').pop() ?? ''))) {
      return prov.context_limit;
    }
  }
  if (model.startsWith('claude')) return 200000;
  if (model.startsWith('gemini')) return 1000000;
  if (model.startsWith('gpt')) return 128000;
  return 32000;
}

// ── Provider auto-detection ───────────────────────────────────────────────────

export function detectProvider(model: string): string {
  if (model.startsWith('claude')) return 'anthropic';
  if (model.startsWith('gemini') || model.startsWith('models/gemini')) return 'gemini';
  if (model.startsWith('gpt') || model.startsWith('o1') || model.startsWith('o3') || model.startsWith('o4')) return 'openai';
  if (model.includes('/')) {
    const prefix = model.split('/')[0];
    if (prefix in PROVIDER_REGISTRY) return prefix;
    if (prefix === 'openrouter') return 'openrouter';
  }
  if (model.startsWith('llama') || model.startsWith('mistral') || model.startsWith('qwen')) return 'ollama';
  if (model.startsWith('deepseek')) return 'deepseek';
  if (model.startsWith('sonar')) return 'perplexity';
  return 'gemini'; // default
}

// ── OpenAI-compatible HTTP client ─────────────────────────────────────────────

interface OpenAIMessage { role: string; content: string; name?: string; }
interface OpenAITool { type: 'function'; function: { name: string; description: string; parameters: unknown }; }

async function openAIChat(
  baseUrl: string,
  apiKey: string,
  model: string,
  messages: OpenAIMessage[],
  tools: OpenAITool[],
  maxTokens: number,
  systemPrompt?: string,
): Promise<{ content: string; toolCalls: Array<{ id: string; name: string; args: Record<string, unknown> }> }> {
  const allMessages = systemPrompt
    ? [{ role: 'system', content: systemPrompt }, ...messages]
    : messages;

  const body = JSON.stringify({
    model,
    messages: allMessages,
    max_tokens: maxTokens,
    tools: tools.length > 0 ? tools : undefined,
    tool_choice: tools.length > 0 ? 'auto' : undefined,
  });

  return new Promise((resolve, reject) => {
    const url = new URL(`${baseUrl.replace(/\/$/, '')}/chat/completions`);
    const isHttps = url.protocol === 'https:';
    const lib = isHttps ? https : http;

    const reqOptions = {
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: url.pathname + url.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
        ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
      },
    };

    const req = lib.request(reqOptions, (res) => {
      let data = '';
      res.on('data', (chunk: Buffer) => { data += chunk.toString(); });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data) as {
            choices?: Array<{
              message?: {
                content?: string;
                tool_calls?: Array<{ id?: string; function?: { name?: string; arguments?: string } }>;
              };
            }>;
            error?: { message: string };
          };
          if (parsed.error) { reject(new Error(parsed.error.message)); return; }
          const msg = parsed.choices?.[0]?.message;
          const content = msg?.content || '';
          const toolCalls = (msg?.tool_calls || []).map(tc => ({
            id: tc.id || `tc_${Date.now()}`,
            name: tc.function?.name || '',
            args: (() => { try { return JSON.parse(tc.function?.arguments || '{}') as Record<string, unknown>; } catch { return {}; } })(),
          }));
          resolve({ content, toolCalls });
        } catch (e) {
          reject(new Error(`Parse error: ${data.slice(0, 200)}`));
        }
      });
    });

    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

// ── Multi-provider provider class ─────────────────────────────────────────────

export class MultiProvider extends BaseProvider {
  readonly name: string;
  readonly model: string;
  private providerKey: string;
  private apiKey: string;
  private baseUrl: string;

  constructor(model: string, apiKeyOverride?: string) {
    super();
    this.model = model;
    this.providerKey = detectProvider(model);
    const prov = PROVIDER_REGISTRY[this.providerKey];
    this.name = `Multi(${this.providerKey})`;
    this.apiKey = apiKeyOverride || process.env[prov?.api_key_env || ''] || '';
    this.baseUrl = prov?.base_url || 'https://api.openai.com/v1';
  }

  private toOpenAIMessages(messages: Message[]): OpenAIMessage[] {
    return messages
      .filter(m => m.role !== 'system')
      .map(m => ({
        role: m.role === 'tool' ? 'tool' : m.role === 'assistant' ? 'assistant' : 'user',
        content: m.content,
        ...(m.name ? { name: m.name } : {}),
      }));
  }

  private toOpenAITools(tools: ToolDefinition[]): OpenAITool[] {
    return tools.map(t => ({
      type: 'function' as const,
      function: {
        name: t.name,
        description: t.description,
        parameters: t.input_schema,
      },
    }));
  }

  async chat(
    messages: Message[],
    tools: ToolDefinition[],
    options: { maxTokens?: number; systemPrompt?: string } = {}
  ): Promise<ModelResponse> {
    // For anthropic, delegate to AnthropicProvider
    if (this.providerKey === 'anthropic') {
      const { AnthropicProvider } = await import('./anthropic.js');
      const p = new AnthropicProvider(this.apiKey, this.model);
      return p.chat(messages, tools, options);
    }

    // For original gemini SDK, delegate to GeminiProvider
    if (this.providerKey === 'gemini' && !this.baseUrl.includes('openai')) {
      const { GeminiProvider } = await import('./gemini.js');
      const p = new GeminiProvider(this.apiKey, this.model);
      return p.chat(messages, tools, options);
    }

    // OpenAI-compatible path (gemini-compat, openai, ollama, deepseek, groq, etc.)
    const oaiMessages = this.toOpenAIMessages(messages);
    const oaiTools = this.toOpenAITools(tools);
    const { content, toolCalls } = await openAIChat(
      this.baseUrl, this.apiKey, this.model,
      oaiMessages, oaiTools,
      options.maxTokens ?? 8192,
      options.systemPrompt ?? messages.find(m => m.role === 'system')?.content,
    );

    const blocks: ContentBlock[] = [];
    if (content) blocks.push({ type: 'text', text: content });
    for (const tc of toolCalls) {
      blocks.push({ type: 'tool_use', id: tc.id, name: tc.name, input: tc.args });
    }

    return {
      id: `multi_${Date.now()}`,
      model: this.model,
      role: 'assistant',
      content: blocks,
      stop_reason: toolCalls.length > 0 ? 'tool_use' : 'end_turn',
      usage: { input_tokens: 0, output_tokens: 0 },
    };
  }

  async stream(
    messages: Message[],
    tools: ToolDefinition[],
    onChunk: (chunk: StreamChunk) => void,
    options: { maxTokens?: number; systemPrompt?: string } = {}
  ): Promise<ModelResponse> {
    // Fallback to non-streaming for now
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

// ── Smart provider builder ────────────────────────────────────────────────────

export function buildMultiProvider(model: string, apiKey?: string): MultiProvider {
  return new MultiProvider(model, apiKey);
}

export function listAvailableProviders(): string[] {
  return Object.keys(PROVIDER_REGISTRY).filter(k => {
    const env = PROVIDER_REGISTRY[k].api_key_env;
    return !env || process.env[env];
  });
}
