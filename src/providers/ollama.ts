// src/providers/ollama.ts — Local Ollama provider (no API key needed)

import * as http from 'http';
import { Message, ToolDefinition, ModelResponse, ContentBlock } from '../types.js';
import { BaseProvider, StreamChunk } from './base.js';

async function ollamaRequest(
  endpoint: string,
  body: Record<string, unknown>,
  host = 'localhost',
  port = 11434
): Promise<Record<string, unknown>> {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req = http.request({ host, port, path: endpoint, method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) }
    }, res => {
      let body = '';
      res.on('data', chunk => body += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(body)); }
        catch { reject(new Error(`Invalid JSON: ${body.slice(0, 100)}`)); }
      });
    });
    req.on('error', reject);
    req.setTimeout(60000, () => { req.destroy(); reject(new Error('Ollama timeout')); });
    req.write(data);
    req.end();
  });
}

export class OllamaProvider extends BaseProvider {
  readonly name = 'Ollama';
  readonly model: string;
  private host: string;
  private port: number;

  constructor(model = 'llama3.1', host = 'localhost', port = 11434) {
    super();
    this.model = model;
    this.host = host;
    this.port = port;
  }

  private buildMessages(messages: Message[], systemPrompt?: string): Array<{ role: string; content: string }> {
    const result: Array<{ role: string; content: string }> = [];
    if (systemPrompt) result.push({ role: 'system', content: systemPrompt });
    for (const m of messages) {
      if (m.role === 'system') result.push({ role: 'system', content: m.content });
      else if (m.role === 'user') result.push({ role: 'user', content: m.content });
      else if (m.role === 'assistant') result.push({ role: 'assistant', content: m.content });
      else result.push({ role: 'user', content: `[Tool result: ${m.content}]` });
    }
    return result;
  }

  async chat(
    messages: Message[],
    tools: ToolDefinition[],
    options: { maxTokens?: number; systemPrompt?: string } = {}
  ): Promise<ModelResponse> {
    const built = this.buildMessages(messages.filter(m => m.role !== 'system'), options.systemPrompt ||
      messages.find(m => m.role === 'system')?.content);

    const response = await ollamaRequest('/api/chat', {
      model: this.model,
      messages: built,
      stream: false,
      options: { num_predict: options.maxTokens ?? 4096 },
    }, this.host, this.port) as { message?: { content?: string }; prompt_eval_count?: number; eval_count?: number };

    const text = response.message?.content || '';
    const content: ContentBlock[] = [{ type: 'text', text }];

    // Simple tool detection: look for JSON tool call patterns in the response
    const toolCallMatch = text.match(/```json\s*(\{[^`]+\})\s*```/);
    if (toolCallMatch && tools.length > 0) {
      try {
        const parsed = JSON.parse(toolCallMatch[1]);
        if (parsed.tool && parsed.parameters) {
          content.push({
            type: 'tool_use',
            id: `ollama_tool_${Date.now()}`,
            name: parsed.tool,
            input: parsed.parameters,
          });
        }
      } catch { /* not a tool call */ }
    }

    return {
      id: `ollama_${Date.now()}`,
      model: this.model,
      role: 'assistant',
      content,
      stop_reason: content.some(b => b.type === 'tool_use') ? 'tool_use' : 'end_turn',
      usage: {
        input_tokens: response.prompt_eval_count ?? 0,
        output_tokens: response.eval_count ?? 0,
      },
    };
  }

  async stream(
    messages: Message[],
    tools: ToolDefinition[],
    onChunk: (chunk: StreamChunk) => void,
    options: { maxTokens?: number; systemPrompt?: string } = {}
  ): Promise<ModelResponse> {
    // Ollama streaming via line-delimited JSON
    const built = this.buildMessages(messages.filter(m => m.role !== 'system'), options.systemPrompt);

    return new Promise((resolve, reject) => {
      const body = JSON.stringify({
        model: this.model,
        messages: built,
        stream: true,
        options: { num_predict: options.maxTokens ?? 4096 },
      });

      let accText = '';
      const req = http.request({
        host: this.host, port: this.port, path: '/api/chat', method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
      }, res => {
        res.on('data', (chunk: Buffer) => {
          const lines = chunk.toString().split('\n').filter(Boolean);
          for (const line of lines) {
            try {
              const parsed = JSON.parse(line) as { message?: { content?: string }; done?: boolean };
              if (parsed.message?.content) {
                accText += parsed.message.content;
                onChunk({ type: 'text', content: parsed.message.content });
              }
            } catch { /* partial JSON */ }
          }
        });
        res.on('end', () => {
          onChunk({ type: 'done' });
          resolve({
            id: `ollama_stream_${Date.now()}`,
            model: this.model,
            role: 'assistant',
            content: [{ type: 'text', text: accText }],
            stop_reason: 'end_turn',
            usage: { input_tokens: 0, output_tokens: 0 },
          });
        });
        res.on('error', reject);
      });
      req.on('error', reject);
      req.write(body);
      req.end();
    });
  }
}
