// src/providers/openai.ts — OpenAI / OpenAI-compatible provider

import OpenAI from 'openai';
import { Message, ToolDefinition, ModelResponse, ContentBlock } from '../types.js';
import { BaseProvider, StreamChunk } from './base.js';

export class OpenAIProvider extends BaseProvider {
  readonly name = 'OpenAI';
  readonly model: string;
  private client: OpenAI;

  constructor(apiKey: string, model = 'gpt-4o', baseURL?: string) {
    super();
    this.model = model;
    this.client = new OpenAI({ apiKey, ...(baseURL ? { baseURL } : {}) });
  }

  private toOpenAIMessages(messages: Message[]): OpenAI.Chat.ChatCompletionMessageParam[] {
    return messages.map(m => {
      if (m.role === 'system') return { role: 'system' as const, content: m.content };
      if (m.role === 'tool') return { role: 'tool' as const, content: m.content, tool_call_id: m.name || 'tool_0' };
      if (m.role === 'assistant') return { role: 'assistant' as const, content: m.content };
      return { role: 'user' as const, content: m.content };
    });
  }

  private toOpenAITools(tools: ToolDefinition[]): OpenAI.Chat.ChatCompletionTool[] {
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
    options: { maxTokens?: number } = {}
  ): Promise<ModelResponse> {
    const response = await this.client.chat.completions.create({
      model: this.model,
      max_tokens: options.maxTokens ?? 8192,
      messages: this.toOpenAIMessages(messages),
      tools: tools.length > 0 ? this.toOpenAITools(tools) : undefined,
      tool_choice: tools.length > 0 ? 'auto' : undefined,
    });

    const choice = response.choices[0];
    const content: ContentBlock[] = [];

    if (choice.message.content) {
      content.push({ type: 'text', text: choice.message.content });
    }
    for (const tc of choice.message.tool_calls ?? []) {
      let input: Record<string, unknown> = {};
      try { input = JSON.parse(tc.function.arguments); } catch { /* ignore */ }
      content.push({ type: 'tool_use', id: tc.id, name: tc.function.name, input });
    }

    return {
      id: response.id,
      model: response.model,
      role: 'assistant',
      content,
      stop_reason: choice.finish_reason === 'tool_calls' ? 'tool_use' :
        choice.finish_reason === 'length' ? 'max_tokens' : 'end_turn',
      usage: {
        input_tokens: response.usage?.prompt_tokens ?? 0,
        output_tokens: response.usage?.completion_tokens ?? 0,
      },
    };
  }

  async stream(
    messages: Message[],
    tools: ToolDefinition[],
    onChunk: (chunk: StreamChunk) => void,
    options: { maxTokens?: number } = {}
  ): Promise<ModelResponse> {
    const stream = await this.client.chat.completions.create({
      model: this.model,
      max_tokens: options.maxTokens ?? 8192,
      messages: this.toOpenAIMessages(messages),
      tools: tools.length > 0 ? this.toOpenAITools(tools) : undefined,
      stream: true,
    });

    let accText = '';
    let stopReason: ModelResponse['stop_reason'] = 'end_turn';
    const toolCallsMap: Record<number, { id: string; name: string; argsJson: string }> = {};

    for await (const chunk of stream) {
      const delta = chunk.choices[0]?.delta;
      if (delta?.content) {
        accText += delta.content;
        onChunk({ type: 'text', content: delta.content });
      }
      for (const tc of delta?.tool_calls ?? []) {
        if (!toolCallsMap[tc.index]) {
          toolCallsMap[tc.index] = { id: tc.id ?? '', name: tc.function?.name ?? '', argsJson: '' };
        }
        toolCallsMap[tc.index].argsJson += tc.function?.arguments ?? '';
      }
      if (chunk.choices[0]?.finish_reason) {
        stopReason = chunk.choices[0].finish_reason === 'tool_calls' ? 'tool_use' : 'end_turn';
      }
    }

    const toolUses = Object.values(toolCallsMap);
    for (const tu of toolUses) {
      let input: Record<string, unknown> = {};
      try { input = JSON.parse(tu.argsJson); } catch { /* ignore */ }
      onChunk({ type: 'tool_use', toolName: tu.name, toolInput: input, toolUseId: tu.id });
    }
    onChunk({ type: 'done' });

    const content: ContentBlock[] = [];
    if (accText) content.push({ type: 'text', text: accText });
    for (const tu of toolUses) {
      let input: Record<string, unknown> = {};
      try { input = JSON.parse(tu.argsJson); } catch { /* ignore */ }
      content.push({ type: 'tool_use', id: tu.id, name: tu.name, input });
    }

    return {
      id: `openai_${Date.now()}`,
      model: this.model,
      role: 'assistant',
      content,
      stop_reason: stopReason,
      usage: { input_tokens: 0, output_tokens: 0 },
    };
  }
}
