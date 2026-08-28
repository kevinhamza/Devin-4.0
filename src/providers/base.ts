// src/providers/base.ts — Abstract base provider

import { Message, ToolDefinition, ModelResponse } from '../types.js';

export interface StreamChunk {
  type: 'thinking' | 'text' | 'tool_use' | 'done';
  content?: string;
  toolName?: string;
  toolInput?: Record<string, unknown>;
  toolUseId?: string;
}

export abstract class BaseProvider {
  abstract readonly name: string;
  abstract readonly model: string;

  abstract chat(
    messages: Message[],
    tools: ToolDefinition[],
    options?: {
      maxTokens?: number;
      enableThinking?: boolean;
      thinkingBudget?: number;
      systemPrompt?: string;
    }
  ): Promise<ModelResponse>;

  abstract stream(
    messages: Message[],
    tools: ToolDefinition[],
    onChunk: (chunk: StreamChunk) => void,
    options?: {
      maxTokens?: number;
      enableThinking?: boolean;
      thinkingBudget?: number;
      systemPrompt?: string;
    }
  ): Promise<ModelResponse>;

  protected isConfigured(): boolean {
    return true;
  }
}
