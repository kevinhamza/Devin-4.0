// src/config.ts — Configuration management

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import { Config } from './types.js';

// Load .env from project root
function loadDotenv(dir: string): void {
  const envPath = path.join(dir, '.env');
  if (!fs.existsSync(envPath)) return;
  const lines = fs.readFileSync(envPath, 'utf8').split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const eqIdx = trimmed.indexOf('=');
    if (eqIdx < 0) continue;
    const key = trimmed.slice(0, eqIdx).trim();
    let val = trimmed.slice(eqIdx + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
      val = val.slice(1, -1);
    }
    if (!process.env[key]) process.env[key] = val;
  }
}

// Find project root (directory containing .env or package.json)
function findProjectRoot(): string {
  let dir = process.cwd();
  for (let i = 0; i < 10; i++) {
    if (fs.existsSync(path.join(dir, '.env')) || fs.existsSync(path.join(dir, 'package.json'))) {
      return dir;
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return process.cwd();
}

export const PROJECT_ROOT = findProjectRoot();
loadDotenv(PROJECT_ROOT);

function pickProvider(): Config['provider'] {
  if (process.env.ANTHROPIC_API_KEY) return 'anthropic';
  if (process.env.GEMINI_API_KEY) return 'gemini';
  if (process.env.OPENAI_API_KEY) return 'openai';
  return 'ollama';
}

function pickModel(provider: Config['provider']): string {
  switch (provider) {
    case 'anthropic': return process.env.DEVIN_MODEL || 'claude-sonnet-4-6';
    case 'gemini':    return process.env.DEVIN_MODEL || 'gemini-2.5-flash';
    case 'openai':    return process.env.DEVIN_MODEL || 'gpt-4o';
    default:          return process.env.DEVIN_MODEL || 'llama3.1';
  }
}

export function loadConfig(overrides: Partial<Config> = {}): Config {
  const provider = overrides.provider || pickProvider();
  const model = overrides.model || pickModel(provider);

  return {
    apiKeys: {
      anthropic: process.env.ANTHROPIC_API_KEY,
      gemini: process.env.GEMINI_API_KEY,
      openai: process.env.OPENAI_API_KEY,
      perplexity: process.env.PERPLEXITY_API_KEY,
      telegramBotToken: process.env.TELEGRAM_BOT_TOKEN,
    },
    model,
    provider,
    maxTokens: parseInt(process.env.DEVIN_MAX_TOKENS || '8192', 10),
    enableThinking: process.env.DEVIN_THINKING === 'true',
    thinkingBudget: parseInt(process.env.DEVIN_THINKING_BUDGET || '5000', 10),
    permissionMode: (process.env.DEVIN_PERMISSION_MODE as Config['permissionMode']) || 'auto_approve',
    useVoice: process.env.DEVIN_VOICE === 'true',
    cwd: overrides.cwd || process.cwd(),
    verbose: process.env.DEVIN_VERBOSE === 'true',
    ...overrides,
  };
}

export const DEVIN_DIR = path.join(os.homedir(), '.devin');
export const MEMORY_DB_PATH = path.join(DEVIN_DIR, 'memory.db');
export const HISTORY_PATH = path.join(DEVIN_DIR, 'history.json');
export const CONFIG_PATH = path.join(DEVIN_DIR, 'config.json');

// Ensure ~/.devin directory exists
if (!fs.existsSync(DEVIN_DIR)) {
  fs.mkdirSync(DEVIN_DIR, { recursive: true });
}
