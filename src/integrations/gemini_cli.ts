// src/integrations/gemini_cli.ts — Integration with google-gemini/gemini-cli

import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import { PROJECT_ROOT } from '../config.js';

const GEMINI_CLI_DIR = path.join(PROJECT_ROOT, 'external', 'gemini-cli');
const GEMINI_CLI_BIN = path.join(GEMINI_CLI_DIR, 'packages', 'cli', 'bin', 'gemini.js');

export function isGeminiCliAvailable(): boolean {
  return fs.existsSync(GEMINI_CLI_DIR) && (
    fs.existsSync(GEMINI_CLI_BIN) ||
    fs.existsSync(path.join(GEMINI_CLI_DIR, 'dist', 'index.js'))
  );
}

export function runGeminiCli(prompt: string, options: {
  model?: string;
  apiKey?: string;
  timeout?: number;
} = {}): { output: string; error: string; success: boolean } {
  if (!isGeminiCliAvailable()) {
    return { output: '', error: 'gemini-cli not found in external/gemini-cli', success: false };
  }

  const env = {
    ...process.env,
    GEMINI_API_KEY: options.apiKey || process.env.GEMINI_API_KEY || '',
  };

  const args = [prompt];
  if (options.model) args.push('--model', options.model);

  try {
    const result = cp.spawnSync('node', [GEMINI_CLI_BIN, ...args], {
      env,
      timeout: options.timeout || 30000,
      encoding: 'utf8',
      cwd: PROJECT_ROOT,
    });
    return {
      output: result.stdout || '',
      error: result.stderr || '',
      success: result.status === 0,
    };
  } catch (e) {
    return { output: '', error: String(e), success: false };
  }
}
