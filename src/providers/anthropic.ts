// src/providers/anthropic.ts — Anthropic Claude provider

import Anthropic from '@anthropic-ai/sdk';
import { Message, ToolDefinition, ModelResponse, ContentBlock } from '../types.js';
import { BaseProvider, StreamChunk } from './base.js';

export class AnthropicProvider extends BaseProvider {
  readonly name = 'Anthropic';
  readonly model: string;
  private client: Anthropic;

  constructor(apiKey: string, model = 'claude-sonnet-4-6') {
    super();
    this.model = model;
    this.client = new Anthropic({ apiKey });
  }

  private toAnthropicMessages(messages: Message[]): Anthropic.Messages.MessageParam[] {
    return messages
      .filter(m => m.role !== 'system')
      .map(m => ({
        role: m.role as 'user' | 'assistant',
        content: m.content,
      }));
  }

  private getSystemPrompt(messages: Message[], override?: string): string {
    if (override) return override;
    const sys = messages.find(m => m.role === 'system');
    return sys?.content ?? '';
  }

  private toAnthropicTools(tools: ToolDefinition[]): Anthropic.Messages.Tool[] {
    return tools.map(t => ({
      name: t.name,
      description: t.description,
      input_schema: t.input_schema as Anthropic.Messages.Tool['input_schema'],
    }));
  }

  async chat(
    messages: Message[],
    tools: ToolDefinition[],
    options: { maxTokens?: number; enableThinking?: boolean; thinkingBudget?: number; systemPrompt?: string } = {}
  ): Promise<ModelResponse> {
    const params: Anthropic.Messages.MessageCreateParamsNonStreaming = {
      model: this.model,
      max_tokens: options.maxTokens ?? 8192,
      system: this.getSystemPrompt(messages, options.systemPrompt),
      messages: this.toAnthropicMessages(messages),
      tools: tools.length > 0 ? this.toAnthropicTools(tools) : undefined,
    };

    if (options.enableThinking && options.thinkingBudget) {
      (params as unknown as Record<string, unknown>).thinking = {
        type: 'enabled',
        budget_tokens: options.thinkingBudget,
      };
    }

    const response = await this.client.messages.create(params);

    const content: ContentBlock[] = response.content.map(block => {
      const b = block as unknown as Record<string, unknown>;
      if (b.type === 'thinking') {
        return { type: 'thinking' as const, thinking: String(b.thinking || '') };
      } else if (b.type === 'tool_use') {
        return {
          type: 'tool_use' as const,
          id: String(b.id || ''),
          name: String(b.name || ''),
          input: (b.input as Record<string, unknown>) || {},
        };
      } else {
        return { type: 'text' as const, text: String(b.text || '') };
      }
    });

    const usage = response.usage as unknown as Record<string, unknown>;
    return {
      id: response.id,
      model: response.model,
      role: 'assistant',
      content,
      stop_reason: (response.stop_reason || 'end_turn') as ModelResponse['stop_reason'],
      usage: {
        input_tokens: Number(usage.input_tokens || 0),
        output_tokens: Number(usage.output_tokens || 0),
        cache_read_input_tokens: Number(usage.cache_read_input_tokens || 0),
        cache_creation_input_tokens: Number(usage.cache_creation_input_tokens || 0),
      },
    };
  }

  async stream(
    messages: Message[],
    tools: ToolDefinition[],
    onChunk: (chunk: StreamChunk) => void,
    options: { maxTokens?: number; enableThinking?: boolean; thinkingBudget?: number; systemPrompt?: string } = {}
  ): Promise<ModelResponse> {
    const params: Anthropic.Messages.MessageCreateParamsStreaming = {
      model: this.model,
      max_tokens: options.maxTokens ?? 8192,
      system: this.getSystemPrompt(messages, options.systemPrompt),
      messages: this.toAnthropicMessages(messages),
      tools: tools.length > 0 ? this.toAnthropicTools(tools) : undefined,
      stream: true,
    };

    let accText = '';
    let accThinking = '';
    let stopReason: ModelResponse['stop_reason'] = 'end_turn';
    let usage = { input_tokens: 0, output_tokens: 0 };
    let responseId = '';
    let responseModel = this.model;
    const toolUses: Array<{ id: string; name: string; input: Record<string, unknown> }> = [];

    const stream = await this.client.messages.create(params);
    for await (const event of stream as AsyncIterable<Anthropic.Messages.RawMessageStreamEvent>) {
      if (event.type === 'message_start') {
        responseId = event.message.id;
        responseModel = event.message.model;
        usage.input_tokens = event.message.usage.input_tokens;
      } else if (event.type === 'content_block_start') {
        const block = event.content_block;
        if (block.type === 'tool_use') {
          toolUses.push({ id: block.id, name: block.name, input: {} });
        }
      } else if (event.type === 'content_block_delta') {
        const delta = event.delta as unknown as Record<string, unknown>;
        if (delta.type === 'text_delta' && delta.text) {
          accText += String(delta.text);
          onChunk({ type: 'text', content: String(delta.text) });
        } else if (delta.type === 'thinking_delta' && delta.thinking) {
          accThinking += String(delta.thinking);
          onChunk({ type: 'thinking', content: String(delta.thinking) });
        } else if (delta.type === 'input_json_delta') {
          const last = toolUses[toolUses.length - 1];
          if (last) {
            try {
              Object.assign(last.input, JSON.parse(String(delta.partial_json || '{}')));
            } catch { /* partial JSON, ignore */ }
          }
        }
      } else if (event.type === 'message_delta') {
        stopReason = event.delta.stop_reason as ModelResponse['stop_reason'];
        usage.output_tokens = event.usage.output_tokens;
      }
    }

    for (const tu of toolUses) {
      onChunk({ type: 'tool_use', toolName: tu.name, toolInput: tu.input, toolUseId: tu.id });
    }
    onChunk({ type: 'done' });

    const content: ContentBlock[] = [];
    if (accThinking) content.push({ type: 'thinking', thinking: accThinking });
    if (accText) content.push({ type: 'text', text: accText });
    for (const tu of toolUses) {
      content.push({ type: 'tool_use', id: tu.id, name: tu.name, input: tu.input });
    }

    return {
      id: responseId,
      model: responseModel,
      role: 'assistant',
      content,
      stop_reason: stopReason,
      usage,
    };
  }
}
