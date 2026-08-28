// src/integrations/gemini_cli_integration.ts — Gemini CLI integration
// Ported from external/gemini-cli/ architecture + @google/genai SDK
// Provides multi-modal Gemini API calls: text, vision, code, function calling

import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as https from 'https';

const DEVIN_ROOT = path.join(__dirname, '../..');
const GEMINI_API_KEY = process.env.GEMINI_API_KEY || '';

// ── API endpoint builder ──────────────────────────────────────────────────────

const GEMINI_BASE = 'https://generativelanguage.googleapis.com/v1beta';

export type GeminiModel =
  | 'gemini-3.5-flash'
  | 'gemini-3.6-flash'
  | 'gemini-3.7-flash'
  | 'gemini-3.1-flash-lite'
  | 'gemini-3.1-pro-preview'
  | 'gemini-flash-latest'
  | 'gemini-1.5-flash'
  | 'gemini-1.5-pro'
  | 'gemini-1.0-pro'
  | string;

export interface GeminiPart {
  text?: string;
  inlineData?: { mimeType: string; data: string };
  fileData?: { mimeType: string; fileUri: string };
}

export interface GeminiContent {
  role: 'user' | 'model';
  parts: GeminiPart[];
}

export interface GeminiConfig {
  temperature?: number;
  topP?: number;
  topK?: number;
  maxOutputTokens?: number;
  stopSequences?: string[];
}

export interface GeminiResponse {
  text: string;
  finishReason: string;
  promptTokens: number;
  outputTokens: number;
  model: string;
}

// ── Core API call ──────────────────────────────────────────────────────────────

function geminiRequest(
  model: string,
  contents: GeminiContent[],
  config: GeminiConfig = {},
  apiKey: string = GEMINI_API_KEY
): Promise<GeminiResponse> {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify({
      contents,
      generationConfig: {
        temperature: config.temperature ?? 0.7,
        topP: config.topP ?? 0.9,
        topK: config.topK ?? 40,
        maxOutputTokens: config.maxOutputTokens ?? 8192,
        ...(config.stopSequences ? { stopSequences: config.stopSequences } : {}),
      },
    });

    const url = new URL(`${GEMINI_BASE}/models/${model}:generateContent?key=${apiKey}`);
    const opts: https.RequestOptions = {
      hostname: url.hostname,
      path: url.pathname + url.search,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
    };

    const req = https.request(opts, (res) => {
      let data = '';
      res.on('data', (chunk: Buffer) => { data += chunk.toString(); });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          if (parsed.error) {
            reject(new Error(`Gemini API error: ${parsed.error.message}`));
            return;
          }
          const candidate = parsed.candidates?.[0];
          const text = candidate?.content?.parts?.map((p: GeminiPart) => p.text || '').join('') || '';
          const usage = parsed.usageMetadata || {};
          resolve({
            text,
            finishReason: candidate?.finishReason || 'STOP',
            promptTokens: usage.promptTokenCount || 0,
            outputTokens: usage.candidatesTokenCount || 0,
            model,
          });
        } catch (e) {
          reject(new Error(`JSON parse error: ${String(e)}`));
        }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

// ── Simple text generation ────────────────────────────────────────────────────

export async function generateText(
  prompt: string,
  model: GeminiModel = 'gemini-3.5-flash',
  config: GeminiConfig = {}
): Promise<string> {
  const contents: GeminiContent[] = [
    { role: 'user', parts: [{ text: prompt }] }
  ];
  const result = await geminiRequest(model, contents, config);
  return result.text;
}

// ── Multi-turn chat (from gemini-cli patterns) ─────────────────────────────────

export class GeminiChat {
  private history: GeminiContent[] = [];
  private model: GeminiModel;
  private config: GeminiConfig;

  constructor(model: GeminiModel = 'gemini-3.5-flash', config: GeminiConfig = {}) {
    this.model = model;
    this.config = config;
  }

  async sendMessage(text: string): Promise<string> {
    this.history.push({ role: 'user', parts: [{ text }] });
    const result = await geminiRequest(this.model, this.history, this.config);
    this.history.push({ role: 'model', parts: [{ text: result.text }] });
    return result.text;
  }

  reset(): void {
    this.history = [];
  }

  getHistory(): GeminiContent[] {
    return [...this.history];
  }
}

// ── Vision / multi-modal (from gemini-cli multimodal patterns) ─────────────────

// Models tried in order for vision — dedicated image models have separate quota buckets
const VISION_MODELS: GeminiModel[] = [
  'gemini-3.1-flash-image',      // dedicated image model, separate quota
  'gemini-3.5-flash-lite',       // lighter quota than 3.5-flash
  'gemini-3.5-flash',            // primary
  'gemini-3.1-flash-lite',       // fastest fallback
  'gemini-flash-lite-latest',    // alias for latest lite
];

export async function analyzeImage(
  imagePath: string,
  prompt = 'Describe this image in detail.',
  model?: GeminiModel
): Promise<string> {
  if (!fs.existsSync(imagePath)) {
    throw new Error(`Screenshot file not found: ${imagePath}`);
  }
  const imageBuffer = fs.readFileSync(imagePath);
  if (imageBuffer.length < 500) {
    throw new Error(`Screenshot file is too small (${imageBuffer.length} bytes) — likely empty or corrupt`);
  }
  const base64 = imageBuffer.toString('base64');
  const ext = path.extname(imagePath).toLowerCase().slice(1);
  const mimeTypes: Record<string, string> = {
    jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png',
    gif: 'image/gif', webp: 'image/webp', bmp: 'image/bmp',
  };
  const mimeType = mimeTypes[ext] || 'image/png';

  const contents: GeminiContent[] = [{
    role: 'user',
    parts: [
      { inlineData: { mimeType, data: base64 } },
      { text: prompt },
    ],
  }];

  const modelsToTry = model ? [model] : VISION_MODELS;
  let lastError = '';

  for (const m of modelsToTry) {
    // Retry up to 3 times per model (rate limit retry)
    for (let attempt = 0; attempt < 3; attempt++) {
      try {
        const result = await geminiRequest(m, contents, { maxOutputTokens: 2048 });
        if (result.text && result.text.trim().length > 0) {
          return result.text;
        }
      } catch (e: unknown) {
        const msg = String((e as Error).message || e);
        lastError = msg;
        const isRateLimit = msg.includes('429') || msg.toLowerCase().includes('quota') || msg.toLowerCase().includes('rate');
        if (isRateLimit) {
          // Extract retry delay from error if present, otherwise use backoff
          const retryMatch = msg.match(/retry in ([\d.]+)s/i);
          const delaySec = retryMatch ? parseFloat(retryMatch[1]) + 0.5 : (attempt + 1) * 3;
          await new Promise(r => setTimeout(r, delaySec * 1000));
          continue;
        }
        break; // non-rate-limit error — try next model
      }
    }
  }

  throw new Error(`Vision analysis failed across all models. Last error: ${lastError}`);
}

export async function analyzeScreenshot(
  screenshotPath: string,
  task: string
): Promise<string> {
  return analyzeImage(screenshotPath,
    `You are analyzing a live screenshot from a computer screen.\n` +
    `Task: ${task}\n\n` +
    `Describe EXACTLY what you see: all visible windows, applications, text content, buttons, ` +
    `menu items, dialogs, terminal output, browser URLs, and any other UI elements. ` +
    `Be specific with positions (top-left, center, bottom-right) and exact text. ` +
    `If there is terminal output, quote it verbatim.`
  );
}

// ── Code generation (gemini-cli code mode) ───────────────────────────────────

export async function generateCode(
  description: string,
  language: string,
  context?: string,
  model: GeminiModel = 'gemini-3.5-flash'
): Promise<string> {
  const prompt = [
    `Write ${language} code for: ${description}`,
    context ? `\nContext:\n${context}` : '',
    '\nProvide only the code without explanation. Use best practices.',
  ].join('');

  const result = await generateText(prompt, model, { temperature: 0.3 });
  // Extract code block if present
  const codeMatch = result.match(/```(?:\w+)?\n([\s\S]+?)```/);
  return codeMatch ? codeMatch[1].trim() : result.trim();
}

// ── Function calling (from gemini-cli tool-use pattern) ───────────────────────

export interface GeminiFunctionDeclaration {
  name: string;
  description: string;
  parameters: {
    type: string;
    properties: Record<string, { type: string; description: string }>;
    required?: string[];
  };
}

export interface GeminiFunctionCall {
  name: string;
  args: Record<string, unknown>;
}

export async function callWithFunctions(
  prompt: string,
  functions: GeminiFunctionDeclaration[],
  model: GeminiModel = 'gemini-3.5-flash'
): Promise<{ text: string; functionCalls: GeminiFunctionCall[] }> {
  const body = JSON.stringify({
    contents: [{ role: 'user', parts: [{ text: prompt }] }],
    tools: [{ functionDeclarations: functions }],
  });

  return new Promise((resolve, reject) => {
    const url = new URL(`${GEMINI_BASE}/models/${model}:generateContent?key=${GEMINI_API_KEY}`);
    const opts: https.RequestOptions = {
      hostname: url.hostname,
      path: url.pathname + url.search,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
    };

    const req = https.request(opts, (res) => {
      let data = '';
      res.on('data', (c: Buffer) => { data += c.toString(); });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          const candidate = parsed.candidates?.[0];
          const parts = candidate?.content?.parts || [];
          const text = parts.filter((p: GeminiPart) => p.text).map((p: GeminiPart) => p.text).join('');
          const functionCalls = parts
            .filter((p: Record<string, unknown>) => p.functionCall)
            .map((p: Record<string, { name: string; args: Record<string, unknown> }>) => ({
              name: p.functionCall.name,
              args: p.functionCall.args,
            }));
          resolve({ text, functionCalls });
        } catch (e) {
          reject(e);
        }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}

// ── Model listing (gemini-cli list models) ────────────────────────────────────

export async function listGeminiModels(): Promise<string[]> {
  return new Promise((resolve) => {
    const url = new URL(`${GEMINI_BASE}/models?key=${GEMINI_API_KEY}`);
    const opts: https.RequestOptions = {
      hostname: url.hostname,
      path: url.pathname + url.search,
      method: 'GET',
    };
    const req = https.request(opts, (res) => {
      let data = '';
      res.on('data', (c: Buffer) => { data += c.toString(); });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          const models = (parsed.models || []).map((m: { name: string }) => m.name.replace('models/', ''));
          resolve(models);
        } catch {
          resolve(['gemini-3.5-flash', 'gemini-3.1-pro-preview', 'gemini-3.5-flash', 'gemini-1.5-flash']);
        }
      });
    });
    req.on('error', () => resolve([]));
    req.end();
  });
}

// ── Embedding generation ──────────────────────────────────────────────────────

export async function generateEmbedding(
  text: string,
  model = 'text-embedding-004'
): Promise<number[]> {
  const body = JSON.stringify({ model: `models/${model}`, content: { parts: [{ text }] } });
  return new Promise((resolve, reject) => {
    const url = new URL(`${GEMINI_BASE}/models/${model}:embedContent?key=${GEMINI_API_KEY}`);
    const opts: https.RequestOptions = {
      hostname: url.hostname,
      path: url.pathname + url.search,
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) },
    };
    const req = https.request(opts, (res) => {
      let data = '';
      res.on('data', (c: Buffer) => { data += c.toString(); });
      res.on('end', () => {
        try {
          const parsed = JSON.parse(data);
          resolve(parsed.embedding?.values || []);
        } catch (e) { reject(e); }
      });
    });
    req.on('error', reject);
    req.write(body);
    req.end();
  });
}
