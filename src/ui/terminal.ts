// src/ui/terminal.ts — Claude Code-style terminal renderer

import * as readline from 'readline';
import * as os from 'os';
import * as path from 'path';
import { ContentBlock, ToolUseBlock } from '../types.js';

// Minimal ANSI color helpers (no external deps needed for core colors)
const ESC = '\x1b[';
export const c = {
  reset:    ESC + '0m',
  bold:     ESC + '1m',
  dim:      ESC + '2m',
  italic:   ESC + '3m',
  cyan:     ESC + '36m',
  green:    ESC + '32m',
  yellow:   ESC + '33m',
  red:      ESC + '31m',
  blue:     ESC + '34m',
  magenta:  ESC + '35m',
  white:    ESC + '37m',
  gray:     ESC + '90m',
  brightCyan: ESC + '96m',
  brightGreen: ESC + '92m',
  bgBlack:  ESC + '40m',
};

export function colorize(text: string, ...codes: string[]): string {
  if (!process.stdout.isTTY) return text;
  return codes.join('') + text + c.reset;
}

// ── Banner (matches Claude Code's startup panel) ──────────────────────────
export function printBanner(model: string, provider: string, permMode: string, cwd: string): void {
  const cols = process.stdout.columns || 80;
  const line = '─'.repeat(cols - 2);
  const pad = (s: string) => ' ' + s;

  process.stdout.write('\n');
  process.stdout.write(colorize('╭' + line + '╮\n', c.cyan));
  process.stdout.write(colorize('│', c.cyan) + pad(colorize('  Devin AGI  ', c.bold, c.cyan) + colorize('v4.0.0', c.dim)) + '\n');
  process.stdout.write(colorize('│', c.cyan) + pad(colorize('  cwd: ', c.dim) + colorize(cwd, c.white)) + '\n');
  process.stdout.write(colorize('│', c.cyan) + pad(colorize('  model: ', c.dim) + colorize(model, c.white) + colorize('   provider: ', c.dim) + colorize(provider, c.white) + colorize('   mode: ', c.dim) + colorize(permMode, c.white)) + '\n');
  process.stdout.write(colorize('╰' + line + '╯\n', c.cyan));
  process.stdout.write('\n');
}

// ── Thinking spinner ──────────────────────────────────────────────────────
const SPINNER_FRAMES = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'];

export class Spinner {
  private interval: NodeJS.Timeout | null = null;
  private frame = 0;
  private label: string;

  constructor(label = 'Devin is thinking…') {
    this.label = label;
  }

  start(): void {
    if (!process.stdout.isTTY) return;
    process.stdout.write('\n');
    this.interval = setInterval(() => {
      const f = SPINNER_FRAMES[this.frame % SPINNER_FRAMES.length];
      process.stdout.write('\r' + colorize(f + ' ' + this.label, c.cyan, c.dim));
      this.frame++;
    }, 80);
  }

  stop(): void {
    if (this.interval) {
      clearInterval(this.interval);
      this.interval = null;
      if (process.stdout.isTTY) process.stdout.write('\r\x1b[2K');
    }
  }
}

// ── Markdown renderer (lightweight, no deps) ─────────────────────────────
export function renderMarkdown(text: string): string {
  if (!process.stdout.isTTY) return text;

  let out = text;
  // Code fences
  out = out.replace(/```(\w+)?\n([\s\S]*?)```/g, (_, lang, code) => {
    const header = lang ? colorize(` ${lang} `, c.dim, c.bgBlack) : '';
    const body = code.split('\n').map((l: string) => colorize('│ ', c.dim) + colorize(l, c.white)).join('\n');
    return (header ? header + '\n' : '') + body;
  });
  // Inline code
  out = out.replace(/`([^`]+)`/g, (_, code) => colorize(code, c.brightCyan));
  // Bold
  out = out.replace(/\*\*(.+?)\*\*/g, (_, t) => colorize(t, c.bold));
  // Italic
  out = out.replace(/\*(.+?)\*/g, (_, t) => colorize(t, c.italic));
  // Headers
  out = out.replace(/^### (.+)$/mg, (_, t) => colorize('### ' + t, c.bold, c.cyan));
  out = out.replace(/^## (.+)$/mg, (_, t) => colorize('## ' + t, c.bold, c.cyan));
  out = out.replace(/^# (.+)$/mg, (_, t) => colorize('# ' + t, c.bold, c.brightCyan));
  // Unordered lists
  out = out.replace(/^- (.+)$/mg, (_, t) => colorize('• ', c.gray) + t);
  // Numbered lists
  out = out.replace(/^(\d+)\. (.+)$/mg, (_, n, t) => colorize(n + '. ', c.gray) + t);

  return out;
}

// ── Message display ───────────────────────────────────────────────────────
export function printAssistantMessage(text: string): void {
  process.stdout.write('\n');
  process.stdout.write(colorize('Devin', c.bold, c.brightCyan) + '\n');
  process.stdout.write(renderMarkdown(text) + '\n');
}

export function printThinking(thinking: string): void {
  if (!process.stdout.isTTY) return;
  const lines = thinking.split('\n').slice(0, 5);
  process.stdout.write(colorize('  ∴ ' + lines.join(' ').slice(0, 120) + (thinking.length > 120 ? '…' : ''), c.dim, c.italic) + '\n');
}

export function printToolCall(name: string, args: Record<string, unknown>): void {
  const argsStr = Object.entries(args)
    .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
    .join(', ')
    .slice(0, 100);
  process.stdout.write('\n' + colorize('  ● ', c.dim) + colorize(name, c.cyan) + colorize('(' + argsStr + ')', c.dim) + '\n');
}

export function printToolResult(result: string, isError = false): void {
  const color = isError ? c.red : c.gray;
  const icon = isError ? '  ✗ ' : '  ↳ ';

  // Replace embedded image data with a compact summary
  let display = result.replace(/__IMG__([\w/]+)__([A-Za-z0-9+/=]+)__ENDIMG__/g, (_, mime, data) => {
    const kb = Math.round(data.length * 0.75 / 1024);
    return `[Image: ${kb}KB ${mime}]`;
  });

  const preview = display.trim().slice(0, 300).replace(/\n/g, ' ');
  process.stdout.write(colorize(icon + preview + (display.length > 300 ? '…' : ''), color) + '\n');
}

export function printError(msg: string): void {
  process.stdout.write('\n' + colorize('✗ ' + msg, c.red) + '\n');
}

export function printWarning(msg: string): void {
  process.stdout.write(colorize('⚠ ' + msg, c.yellow) + '\n');
}

export function printInfo(msg: string): void {
  process.stdout.write(colorize('  ' + msg, c.dim) + '\n');
}

export function printSuccess(msg: string): void {
  process.stdout.write(colorize('✓ ' + msg, c.green) + '\n');
}

// ── Dangerous action confirmation ─────────────────────────────────────────
export async function askConfirmation(prompt: string, dangerous = false): Promise<boolean> {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  const label = dangerous
    ? colorize('⚠ Dangerous: ', c.red, c.bold) + prompt + colorize(' (yes/no) ', c.dim)
    : colorize('? ', c.yellow) + prompt + colorize(' (y/n) ', c.dim);

  return new Promise(resolve => {
    rl.question(label, answer => {
      rl.close();
      resolve(['y', 'yes'].includes(answer.trim().toLowerCase()));
    });
  });
}

// ── Prompt line ───────────────────────────────────────────────────────────
export function promptLine(cwd: string): string {
  const short = cwd.replace(os.homedir(), '~');
  return colorize('❯ ', c.bold, c.cyan) + colorize(path.basename(short) + ' ', c.dim);
}

// ── Help text ─────────────────────────────────────────────────────────────
export function printHelp(): void {
  const cmds = [
    ['/help',       'Show this help'],
    ['/clear',      'Clear conversation history'],
    ['/status',     'Show system and session status'],
    ['/plan',       'Switch to plan mode (describe actions, don\'t run)'],
    ['/auto',       'Switch to auto-approve mode'],
    ['/voice',      'Toggle voice input'],
    ['/memory',     'Show recent memories'],
    ['/tools',      'List available tools'],
    ['/subagent X', 'Delegate task X to a fresh sub-agent'],
    ['exit / quit', 'Quit Devin'],
  ];
  process.stdout.write('\n');
  process.stdout.write(colorize('Slash commands:\n', c.bold));
  for (const [cmd, desc] of cmds) {
    process.stdout.write(colorize('  ' + cmd.padEnd(16), c.cyan) + colorize(desc, c.dim) + '\n');
  }
  process.stdout.write('\n');
}
