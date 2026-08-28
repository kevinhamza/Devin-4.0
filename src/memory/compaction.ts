// src/memory/compaction.ts — Conversation compaction and token management
// Ported from cheetahclaws/compaction.py: token estimation, context limits,
// two-layer compression for long conversations

import { Message } from '../types.js';

// ── Token estimation (from cheetahclaws/compaction.py) ───────────────────────
// chars/2.8 conservative for code-heavy content + 4 tokens/msg framing + 10% buffer

export function estimateTokens(messages: Message[]): number {
  let totalChars = 0;
  for (const m of messages) {
    totalChars += m.content.length;
    if (m.name) totalChars += m.name.length;
  }
  const contentTokens = Math.floor(totalChars / 2.8);
  const framingTokens = messages.length * 4;
  return Math.floor((contentTokens + framingTokens) * 1.1);
}

// ── Context limits by model ───────────────────────────────────────────────────

const CONTEXT_LIMITS: Record<string, number> = {
  'claude-opus-4-8': 200000,
  'claude-sonnet-4-6': 200000,
  'claude-haiku-4-5-20251001': 200000,
  'claude-3-5-sonnet-20241022': 200000,
  'gemini-3.6-flash': 1000000,
  'gemini-2.5-pro': 1000000,
  'gemini-2.0-flash': 1000000,
  'gemini-1.5-pro': 1000000,
  'gemini-1.5-flash': 1000000,
  'gpt-4o': 128000,
  'gpt-4-turbo': 128000,
  'gpt-4.1': 128000,
  'o3': 200000,
  'o4-mini': 200000,
};

export function getContextLimit(model: string): number {
  // Exact match
  if (model in CONTEXT_LIMITS) return CONTEXT_LIMITS[model];
  // Prefix match
  for (const [k, v] of Object.entries(CONTEXT_LIMITS)) {
    if (model.startsWith(k) || k.startsWith(model)) return v;
  }
  if (model.startsWith('claude')) return 200000;
  if (model.startsWith('gemini')) return 1000000;
  if (model.startsWith('gpt')) return 128000;
  return 32000;
}

// ── Compaction threshold ──────────────────────────────────────────────────────
// Trigger compaction when tokens reach 80% of context limit

export function shouldCompact(messages: Message[], model: string, threshold = 0.8): boolean {
  const limit = getContextLimit(model);
  const tokens = estimateTokens(messages);
  return tokens > limit * threshold;
}

// ── Message sanitization ──────────────────────────────────────────────────────
// From cheetahclaws/compaction.py: sanitize_history

export function sanitizeHistory(messages: Message[]): Message[] {
  return messages.filter(m => {
    if (!m.content.trim()) return false;
    if (m.content.length > 50000) {
      // Truncate very long messages (tool results, file contents)
      return true;
    }
    return true;
  }).map(m => {
    if (m.content.length > 50000) {
      return {
        ...m,
        content: m.content.slice(0, 25000) + '\n\n[...truncated for context...]',
      };
    }
    return m;
  });
}

// ── Two-layer compaction ──────────────────────────────────────────────────────
// Layer 1: Keep recent N messages intact
// Layer 2: Summarize old messages into a [Summary] block

export function compactMessages(messages: Message[], keepTail = 40, maxSummaryChars = 4000): Message[] {
  if (messages.length <= keepTail) return messages;

  const old = messages.slice(0, -keepTail);
  const recent = messages.slice(-keepTail);

  // Build summary of old messages
  const summaryParts: string[] = [];
  let summaryChars = 0;

  for (const m of old) {
    if (m.role === 'system') continue; // Skip system messages in summary
    const prefix = m.role === 'assistant' ? 'Devin' : m.role === 'user' ? 'User' : 'Tool';
    const snippet = m.content.slice(0, 200).replace(/\n+/g, ' ');
    const line = `${prefix}: ${snippet}`;
    if (summaryChars + line.length > maxSummaryChars) break;
    summaryParts.push(line);
    summaryChars += line.length;
  }

  const summary: Message = {
    role: 'system',
    content: `[Conversation summary — earlier context]\n${summaryParts.join('\n')}\n[End summary]`,
  };

  return [summary, ...recent];
}

// ── Smart compaction with token budget ───────────────────────────────────────

export function maybeCompact(
  messages: Message[],
  model: string,
  reserveTokens = 4000
): { messages: Message[]; compacted: boolean; tokensBefore: number; tokensAfter: number } {
  const tokensBefore = estimateTokens(messages);
  const limit = getContextLimit(model);

  if (tokensBefore + reserveTokens < limit * 0.8) {
    return { messages, compacted: false, tokensBefore, tokensAfter: tokensBefore };
  }

  // Determine how many recent messages to keep based on token budget
  const budget = Math.floor(limit * 0.6); // target 60% full after compaction
  let keepTail = 20;

  // Binary search for optimal keepTail
  for (let k = 10; k <= messages.length; k += 10) {
    const trial = compactMessages(messages, k);
    if (estimateTokens(trial) <= budget) keepTail = k;
    else break;
  }

  const compacted = sanitizeHistory(compactMessages(messages, keepTail));
  const tokensAfter = estimateTokens(compacted);

  return { messages: compacted, compacted: true, tokensBefore, tokensAfter };
}

// ── Conversation statistics ───────────────────────────────────────────────────

export interface ConversationStats {
  messageCount: number;
  estimatedTokens: number;
  contextLimit: number;
  usagePercent: number;
  shouldCompact: boolean;
  userMessages: number;
  assistantMessages: number;
  toolMessages: number;
}

export function getConversationStats(messages: Message[], model: string): ConversationStats {
  const estimatedTokens = estimateTokens(messages);
  const contextLimit = getContextLimit(model);
  const usagePercent = Math.round((estimatedTokens / contextLimit) * 100);
  const compact = shouldCompact(messages, model);

  return {
    messageCount: messages.length,
    estimatedTokens,
    contextLimit,
    usagePercent,
    shouldCompact: compact,
    userMessages: messages.filter(m => m.role === 'user').length,
    assistantMessages: messages.filter(m => m.role === 'assistant').length,
    toolMessages: messages.filter(m => m.role === 'tool').length,
  };
}
