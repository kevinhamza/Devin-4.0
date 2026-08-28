// src/providers/gemini.ts — Google Gemini provider (using @google/genai SDK)

import { Message, ToolDefinition, ModelResponse, ContentBlock } from '../types.js';
import { BaseProvider, StreamChunk } from './base.js';

// Dynamic import for google/genai so the whole file doesn't crash if the
// package isn't installed yet.
async function getGenai() {
  try {
    return await import('@google/genai');
  } catch {
    throw new Error("@google/genai not installed. Run: npm install @google/genai");
  }
}

export class GeminiProvider extends BaseProvider {
  readonly name = 'Gemini';
  readonly model: string;
  private apiKey: string;

  private static readonly FALLBACK_MODELS = [
    'gemini-3.5-flash',
    'gemini-3.1-flash-lite',
    'gemini-3.6-flash',
    'gemini-3.7-flash',
    'gemini-flash-latest',
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-pro-latest',
  ];

  constructor(apiKey: string, model = 'gemini-3.6-flash') {
    super();
    this.apiKey = apiKey;
    this.model = model;
  }

  private toGeminiContents(messages: Message[]) {
    // Regex to detect embedded screenshots: __IMG__mime__base64data__ENDIMG__
    const IMG_RE = /__IMG__([\w/]+)__([A-Za-z0-9+/=]+)__ENDIMG__/g;

    return messages
      .filter(m => m.role !== 'system')
      .map(m => {
        const role = m.role === 'assistant' ? 'model' : 'user';
        const text = m.content;

        // Fast path — no embedded image
        if (!text.includes('__IMG__')) {
          return { role, parts: [{ text }] };
        }

        // Build multimodal parts: text fragments + inlineData
        const parts: Array<{ text?: string; inlineData?: { mimeType: string; data: string } }> = [];
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
        if (parts.length === 0) parts.push({ text });

        return { role, parts };
      });
  }

  private toGeminiTools(tools: ToolDefinition[]) {
    return [{
      functionDeclarations: tools.map(t => ({
        name: t.name,
        description: t.description,
        parameters: {
          type: 'OBJECT',
          properties: Object.fromEntries(
            Object.entries(t.input_schema.properties).map(([k, v]) => [
              k,
              { type: v.type.toUpperCase(), description: v.description }
            ])
          ),
          required: t.input_schema.required || [],
        },
      })),
    }];
  }

  async chat(
    messages: Message[],
    tools: ToolDefinition[],
    options: { maxTokens?: number; systemPrompt?: string } = {}
  ): Promise<ModelResponse> {
    const { GoogleGenAI } = await getGenai();
    const genai = new GoogleGenAI({ apiKey: this.apiKey });

    const systemInstruction = options.systemPrompt ||
      messages.find(m => m.role === 'system')?.content;

    const contents = this.toGeminiContents(messages);
    const geminiTools = tools.length > 0 ? this.toGeminiTools(tools) : undefined;

    let lastError: Error | null = null;
    const models = [this.model, ...GeminiProvider.FALLBACK_MODELS.filter(m => m !== this.model)];

    for (const modelId of models) {
      try {
        const response = await genai.models.generateContent({
          model: modelId,
          contents,
          config: {
            maxOutputTokens: options.maxTokens ?? 8192,
            systemInstruction,
            tools: geminiTools as Parameters<typeof genai.models.generateContent>[0]['config'] extends { tools?: infer T } ? T : never,
          },
        });

        const content: ContentBlock[] = [];
        const candidate = response.candidates?.[0];
        if (candidate?.content?.parts) {
          for (const part of candidate.content.parts) {
            if (part.text) {
              content.push({ type: 'text', text: part.text });
            } else if (part.functionCall) {
              content.push({
                type: 'tool_use',
                id: `tool_${Date.now()}`,
                name: part.functionCall.name ?? '',
                input: (part.functionCall.args as Record<string, unknown>) ?? {},
              });
            }
          }
        }

        // tool_use must take priority — Gemini reports finishReason:'STOP' even for function calls
        const stopReason = content.some(b => b.type === 'tool_use') ? 'tool_use' :
          candidate?.finishReason === 'MAX_TOKENS' ? 'max_tokens' : 'end_turn';

        return {
          id: `gemini_${Date.now()}`,
          model: modelId,
          role: 'assistant',
          content,
          stop_reason: stopReason as ModelResponse['stop_reason'],
          usage: {
            input_tokens: response.usageMetadata?.promptTokenCount ?? 0,
            output_tokens: response.usageMetadata?.candidatesTokenCount ?? 0,
          },
        };
      } catch (err) {
        lastError = err instanceof Error ? err : new Error(String(err));
        const msg = lastError.message.toLowerCase();
        // retry on 429 rate-limit, 503, overloaded — try next model
        const shouldTryNext = msg.includes('503') || msg.includes('unavailable') ||
          msg.includes('overloaded') || msg.includes('429') || msg.includes('quota') ||
          msg.includes('rate') || msg.includes('resource_exhausted') ||
          msg.includes('fetch failed') || msg.includes('econnreset') ||
          msg.includes('socket') || msg.includes('network') || msg.includes('enotfound') ||
          msg.includes('etimedout') || msg.includes('connection');
        if (!shouldTryNext) break;
        // brief pause before trying next model
        await new Promise(r => setTimeout(r, 500));
      }
    }

    throw lastError ?? new Error('Gemini: all models exhausted');
  }

  async stream(
    messages: Message[],
    tools: ToolDefinition[],
    onChunk: (chunk: StreamChunk) => void,
    options: { maxTokens?: number; systemPrompt?: string } = {}
  ): Promise<ModelResponse> {
    const { GoogleGenAI } = await getGenai();
    const genai = new GoogleGenAI({ apiKey: this.apiKey });

    const systemInstruction = options.systemPrompt ||
      messages.find(m => m.role === 'system')?.content;
    const contents = this.toGeminiContents(messages);
    const geminiTools = tools.length > 0 ? this.toGeminiTools(tools) : undefined;

    let accText = '';
    const toolUses: Array<{ name: string; input: Record<string, unknown> }> = [];

    const responseStream = await genai.models.generateContentStream({
      model: this.model,
      contents,
      config: {
        maxOutputTokens: options.maxTokens ?? 8192,
        systemInstruction,
        tools: geminiTools as Parameters<typeof genai.models.generateContent>[0]['config'] extends { tools?: infer T } ? T : never,
      },
    });

    for await (const chunk of responseStream) {
      for (const part of chunk.candidates?.[0]?.content?.parts ?? []) {
        if (part.text) {
          accText += part.text;
          onChunk({ type: 'text', content: part.text });
        } else if (part.functionCall) {
          const tu = {
            name: part.functionCall.name ?? '',
            input: (part.functionCall.args as Record<string, unknown>) ?? {},
          };
          toolUses.push(tu);
          onChunk({ type: 'tool_use', toolName: tu.name, toolInput: tu.input, toolUseId: `tool_${Date.now()}` });
        }
      }
    }

    onChunk({ type: 'done' });

    const content: ContentBlock[] = [];
    if (accText) content.push({ type: 'text', text: accText });
    for (const tu of toolUses) {
      content.push({ type: 'tool_use', id: `tool_${Date.now()}`, name: tu.name, input: tu.input });
    }

    return {
      id: `gemini_stream_${Date.now()}`,
      model: this.model,
      role: 'assistant',
      content,
      stop_reason: toolUses.length > 0 ? 'tool_use' : 'end_turn',
      usage: { input_tokens: 0, output_tokens: 0 },
    };
  }
}
