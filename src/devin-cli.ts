#!/usr/bin/env node
/**
 * Devin AGI 4.0 — TypeScript CLI Wrapper
 *
 * Provides a Node.js entry point that spawns the Python Devin agent.
 * Uses Gemini / Claude / OpenAI / HuggingFace via env vars in .env.
 * Never hardcodes API keys.
 */

import { spawn, execSync } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as readline from 'readline';

const ROOT = path.resolve(__dirname, '..');
const ENV_FILE = path.join(ROOT, '.env');
const MAIN_PY = path.join(ROOT, 'main.py');
const AGENT_PY = path.join(ROOT, 'agent.py');

// Load .env into process.env
if (fs.existsSync(ENV_FILE)) {
  for (const line of fs.readFileSync(ENV_FILE, 'utf-8').split('\n')) {
    const l = line.trim();
    if (!l || l.startsWith('#') || !l.includes('=')) continue;
    const [key, ...rest] = l.split('=');
    const val = rest.join('=').replace(/^"|"$|^'|'$/g, '');
    if (!(key.trim() in process.env)) {
      process.env[key.trim()] = val.trim();
    }
  }
}

const VERSION = '4.0.0';

function printBanner(): void {
  const w = process.stdout.columns || 80;
  const line = '─'.repeat(w - 4);
  console.log(`\n  \x1b[36;1m╭${line}╮`);
  console.log(`  │\x1b[1;37m  Devin AGI v${VERSION} — TypeScript CLI  \x1b[36;1m`);
  console.log(`  ╰${line}╯\x1b[0m\n`);
}

function getPython(): string {
  for (const cmd of ['python3', 'python']) {
    try {
      execSync(`${cmd} --version`, { stdio: 'ignore' });
      return cmd;
    } catch {
      // continue
    }
  }
  throw new Error('Python 3 not found. Install it first.');
}

function spawnDevin(args: string[]): void {
  const python = getPython();
  const script = fs.existsSync(MAIN_PY) ? MAIN_PY : AGENT_PY;
  const child = spawn(python, [script, ...args], {
    stdio: 'inherit',
    env: process.env,
    cwd: ROOT,
  });
  child.on('exit', (code) => process.exit(code ?? 0));
}

function printHelp(): void {
  console.log(`
  Devin AGI v${VERSION} — Autonomous OS-Controlling AI

  Usage:
    devin [command] [options]

  Commands:
    (no args)          Start interactive REPL (Claude Code-style)
    "<prompt>"         One-shot prompt, then exit
    test               Run core test suite
    status             Show module load status
    caps               Show capability summary
    setup              Install Python dependencies
    version            Show version

  Options:
    --provider <p>     Force AI provider: gemini | claude | openai | hf
    --voice            Start in voice command mode
    --classic          Use classic agent.py REPL
    --no-agent         Load modules only, skip REPL

  Environment (set in .env):
    GEMINI_API_KEY     Google Gemini API key
    ANTHROPIC_API_KEY  Anthropic Claude API key
    OPENAI_API_KEY     OpenAI API key
    HF_TOKEN           HuggingFace token
    DEVIN_PROVIDER     Default provider override
  `);
}

function setup(): void {
  const python = getPython();
  const reqFile = path.join(ROOT, 'requirements.txt');
  if (!fs.existsSync(reqFile)) {
    console.error('requirements.txt not found.');
    process.exit(1);
  }
  console.log('\x1b[36mInstalling Python dependencies…\x1b[0m');
  const child = spawn(python, ['-m', 'pip', 'install', '-r', reqFile], {
    stdio: 'inherit',
    cwd: ROOT,
  });
  child.on('exit', (code) => {
    if (code === 0) console.log('\x1b[32m✓ Setup complete.\x1b[0m');
    process.exit(code ?? 1);
  });
}

// ── Main ────────────────────────────────────────────────────────────────────────
printBanner();

const argv = process.argv.slice(2);

if (argv.length === 0) {
  spawnDevin([]);
} else if (argv[0] === 'test') {
  spawnDevin(['--test']);
} else if (argv[0] === 'status') {
  spawnDevin(['--status']);
} else if (argv[0] === 'caps') {
  spawnDevin(['--caps']);
} else if (argv[0] === 'setup') {
  setup();
} else if (argv[0] === 'version') {
  console.log(`  Devin AGI v${VERSION}`);
} else if (argv[0] === '--help' || argv[0] === '-h' || argv[0] === 'help') {
  printHelp();
} else if (argv[0] === '--classic') {
  process.env.DEVIN_USE_CLASSIC_REPL = '1';
  spawnDevin(argv.slice(1));
} else {
  spawnDevin(argv);
}
