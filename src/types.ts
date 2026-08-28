// src/types.ts — Core type definitions for Devin AGI

export type Role = 'user' | 'assistant' | 'system' | 'tool';

export interface Message {
  role: Role;
  content: string;
  name?: string;
  tool_call_id?: string;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface ToolResult {
  tool_call_id: string;
  content: string;
  isError?: boolean;
}

export interface ToolDefinition {
  name: string;
  description: string;
  input_schema: {
    type: 'object';
    properties: Record<string, {
      type: string;
      description: string;
      enum?: string[];
      items?: { type: string };
    }>;
    required?: string[];
  };
}

export interface ThinkingBlock {
  type: 'thinking';
  thinking: string;
}

export interface TextBlock {
  type: 'text';
  text: string;
}

export interface ToolUseBlock {
  type: 'tool_use';
  id: string;
  name: string;
  input: Record<string, unknown>;
}

export type ContentBlock = ThinkingBlock | TextBlock | ToolUseBlock;

export interface ModelResponse {
  id: string;
  model: string;
  role: 'assistant';
  content: ContentBlock[];
  stop_reason: 'end_turn' | 'tool_use' | 'max_tokens' | 'stop_sequence';
  usage: {
    input_tokens: number;
    output_tokens: number;
    cache_read_input_tokens?: number;
    cache_creation_input_tokens?: number;
  };
}

export interface Config {
  apiKeys: {
    anthropic?: string;
    gemini?: string;
    openai?: string;
    perplexity?: string;
    telegramBotToken?: string;
  };
  model: string;
  provider: 'anthropic' | 'gemini' | 'openai' | 'ollama';
  maxTokens: number;
  enableThinking: boolean;
  thinkingBudget: number;
  permissionMode: 'default' | 'auto_approve' | 'plan' | 'bypass';
  useVoice: boolean;
  cwd: string;
  systemPrompt?: string;
  verbose: boolean;
}

export interface Memory {
  id: string;
  content: string;
  embedding?: number[];
  timestamp: number;
  metadata: Record<string, unknown>;
}

export interface SubAgent {
  goal: string;
  history: Message[];
  maxSteps: number;
}

export interface SessionState {
  conversationHistory: Message[];
  currentGoal: string | null;
  activeTools: Set<string>;
  permissionMode: Config['permissionMode'];
  startTime: number;
  tokenCount: { input: number; output: number };
}

export interface OsInfo {
  platform: string;
  arch: string;
  hostname: string;
  username: string;
  homedir: string;
  cwd: string;
  cpus: number;
  memory: { total: number; free: number };
}

export interface FileInfo {
  path: string;
  size: number;
  isDirectory: boolean;
  modified: Date;
}
