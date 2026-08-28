// src/integrations/self_operating_computer.ts — Integration with self-operating-computer

import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import { PROJECT_ROOT } from '../config.js';

const SOC_DIR = path.join(PROJECT_ROOT, 'self-operating-computer');

export function isSocAvailable(): boolean {
  return fs.existsSync(path.join(SOC_DIR, 'operate'));
}

export function operateComputer(objective: string, options: {
  model?: string;
  apiKey?: string;
  timeout?: number;
} = {}): { output: string; error: string; success: boolean } {
  const venvPython = path.join(PROJECT_ROOT, 'venv', 'bin', 'python3');
  const python = fs.existsSync(venvPython) ? venvPython : 'python3';

  const env: Record<string, string> = {
    ...Object.fromEntries(
      Object.entries(process.env).filter(([, v]) => v !== undefined) as [string, string][]
    ),
    GEMINI_API_KEY: options.apiKey || process.env.GEMINI_API_KEY || '',
    OPENAI_API_KEY: process.env.OPENAI_API_KEY || '',
    ANTHROPIC_API_KEY: process.env.ANTHROPIC_API_KEY || '',
  };

  try {
    const result = cp.spawnSync(
      python,
      ['-m', 'operate', '-p', options.model || 'gemini', '--action', objective],
      {
        env,
        timeout: options.timeout || 60000,
        encoding: 'utf8',
        cwd: SOC_DIR,
      }
    );
    return {
      output: result.stdout || '',
      error: result.stderr || '',
      success: result.status === 0,
    };
  } catch (e) {
    return { output: '', error: String(e), success: false };
  }
}
