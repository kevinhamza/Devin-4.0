// src/commands.ts — Claude Code-style slash command registry for Devin
// All /commands available in the REPL, mirroring Claude Code's structure.

import * as os from 'os';
import * as path from 'path';
import * as fs from 'fs';
import { Message, Config } from './types.js';
import { LocalMemory } from './memory/index.js';
import { ALL_TOOLS } from './tools/definitions.js';
import {
  printAssistantMessage, printInfo, printSuccess, printWarning, printError,
  printHelp, colorize, c,
} from './ui/terminal.js';
import { getSystemInfo, getDiskUsage, getNetworkInterfaces } from './os/control.js';
import { compactHistory } from './conversation.js';

export interface CommandContext {
  history: Message[];
  memory: LocalMemory;
  config: Config;
  sessionStart: number;
  tokenCount: { input: number; output: number };
}

export interface Command {
  name: string;
  aliases?: string[];
  description: string;
  handler: (args: string, ctx: CommandContext) => void | Promise<void>;
}

export const COMMANDS: Command[] = [
  {
    name: 'help',
    description: 'Show all available commands',
    handler: () => { printHelp(); },
  },
  {
    name: 'clear',
    description: 'Clear conversation history',
    handler: (_, ctx) => {
      ctx.history.splice(0, ctx.history.length);
      printSuccess('Conversation history cleared.');
    },
  },
  {
    name: 'compact',
    description: 'Summarize old history to save context',
    handler: (_, ctx) => {
      const before = ctx.history.length;
      const compacted = compactHistory(ctx.history, 40);
      ctx.history.splice(0, ctx.history.length, ...compacted);
      printSuccess(`Compacted ${before} → ${ctx.history.length} messages.`);
    },
  },
  {
    name: 'status',
    aliases: ['info'],
    description: 'Show session and system status',
    handler: (_, ctx) => {
      const sysInfo = getSystemInfo();
      const disk = getDiskUsage('/');
      const elapsed = Math.floor((Date.now() - ctx.sessionStart) / 1000);
      const mins = Math.floor(elapsed / 60);
      const secs = elapsed % 60;
      process.stdout.write('\n');
      printInfo(`${colorize('Session', c.bold)}`);
      printInfo(`  Duration:   ${mins}m ${secs}s`);
      printInfo(`  Messages:   ${ctx.history.length}`);
      printInfo(`  Tokens:     in=${ctx.tokenCount.input} out=${ctx.tokenCount.output}`);
      printInfo(`  Memories:   ${ctx.memory.all().length}`);
      process.stdout.write('\n');
      printInfo(`${colorize('System', c.bold)}`);
      printInfo(`  OS:         ${sysInfo.platform} ${sysInfo.arch}`);
      printInfo(`  Hostname:   ${sysInfo.hostname}`);
      printInfo(`  User:       ${sysInfo.user}`);
      printInfo(`  CPU:        ${sysInfo.cpuCount}× ${sysInfo.cpuModel.slice(0, 40)}`);
      printInfo(`  Memory:     ${sysInfo.freeMemMb}MB free / ${sysInfo.totalMemMb}MB total`);
      printInfo(`  Disk:       ${disk.percent}% used (${Math.round(disk.free / 1e9)}GB free)`);
      printInfo(`  Uptime:     ${Math.floor(sysInfo.uptime / 3600)}h`);
      process.stdout.write('\n');
      printInfo(`${colorize('Devin', c.bold)}`);
      printInfo(`  Provider:   ${ctx.config.provider}`);
      printInfo(`  Model:      ${ctx.config.model}`);
      printInfo(`  Mode:       ${ctx.config.permissionMode}`);
      printInfo(`  CWD:        ${ctx.config.cwd}`);
      process.stdout.write('\n');
    },
  },
  {
    name: 'plan',
    description: 'Switch to plan mode (describe actions without running)',
    handler: (_, ctx) => {
      ctx.config.permissionMode = 'plan';
      printSuccess('Plan mode: actions will be described but not executed.');
    },
  },
  {
    name: 'auto',
    description: 'Switch to auto-approve mode (no confirmation prompts)',
    handler: (_, ctx) => {
      ctx.config.permissionMode = 'auto_approve';
      printSuccess('Auto-approve mode: dangerous tools run without confirmation.');
    },
  },
  {
    name: 'default',
    description: 'Switch to default mode (confirm dangerous tools)',
    handler: (_, ctx) => {
      ctx.config.permissionMode = 'default';
      printSuccess('Default mode: will ask before running dangerous tools.');
    },
  },
  {
    name: 'memory',
    aliases: ['mem'],
    description: 'Show or search memory. Usage: /memory [query]',
    handler: (args, ctx) => {
      if (args.trim()) {
        const results = ctx.memory.search(args.trim(), 10);
        if (results.length === 0) {
          printInfo('No memories found matching that query.');
        } else {
          printInfo(`Found ${results.length} memories:`);
          for (const m of results) {
            const ts = new Date(m.timestamp).toLocaleString();
            printInfo(`  [${ts}] ${m.content.slice(0, 120)}`);
          }
        }
      } else {
        const recent = ctx.memory.recent(10);
        if (recent.length === 0) {
          printInfo('No memories stored yet.');
        } else {
          printInfo(`Recent memories (${ctx.memory.all().length} total):`);
          for (const m of recent) {
            const ts = new Date(m.timestamp).toLocaleString();
            printInfo(`  [${ts}] ${m.content.slice(0, 100)}`);
          }
        }
      }
    },
  },
  {
    name: 'tools',
    description: 'List all available tools',
    handler: () => {
      printInfo(`Available tools (${ALL_TOOLS.length} total):`);
      for (const t of ALL_TOOLS) {
        process.stdout.write(
          '  ' + colorize(t.name.padEnd(30), c.cyan) +
          colorize(t.description.slice(0, 55), c.dim) + '\n'
        );
      }
    },
  },
  {
    name: 'cost',
    description: 'Show estimated token usage for this session',
    handler: (_, ctx) => {
      const { input, output } = ctx.tokenCount;
      // Rough cost estimate for Claude Sonnet
      const inputCost = (input / 1000000) * 3.0;
      const outputCost = (output / 1000000) * 15.0;
      printInfo(`Token usage: ${input.toLocaleString()} in / ${output.toLocaleString()} out`);
      printInfo(`Estimated cost (Sonnet): ~$${(inputCost + outputCost).toFixed(4)}`);
    },
  },
  {
    name: 'history',
    description: 'Show recent conversation history',
    handler: (args, ctx) => {
      const n = parseInt(args.trim() || '10', 10);
      const recent = ctx.history.slice(-n * 2);
      for (const m of recent) {
        if (m.role === 'system') continue;
        const role = m.role === 'user' ? colorize('You', c.cyan) : colorize('Devin', c.brightCyan);
        process.stdout.write(`\n${role}: ${m.content.slice(0, 200)}\n`);
      }
    },
  },
  {
    name: 'config',
    description: 'Show or set configuration. Usage: /config [key=value]',
    handler: (args, ctx) => {
      if (!args.trim()) {
        printInfo('Current configuration:');
        for (const [k, v] of Object.entries(ctx.config)) {
          if (typeof v === 'object') continue;
          printInfo(`  ${k.padEnd(20)} ${String(v)}`);
        }
      } else {
        const [key, val] = args.trim().split('=', 2);
        if (key && val) {
          (ctx.config as unknown as Record<string, unknown>)[key.trim()] = val.trim();
          printSuccess(`Set ${key.trim()} = ${val.trim()}`);
        }
      }
    },
  },
  {
    name: 'doctor',
    description: 'Check system dependencies and configuration',
    handler: async () => {
      const checks: Array<{ label: string; check: () => boolean | Promise<boolean> }> = [
        { label: 'Python 3', check: () => { try { const { execSync } = require('child_process'); execSync('python3 --version'); return true; } catch { return false; } } },
        { label: 'Node.js 18+', check: () => parseInt(process.version.slice(1)) >= 18 },
        { label: 'GEMINI_API_KEY', check: () => !!process.env.GEMINI_API_KEY },
        { label: 'ANTHROPIC_API_KEY', check: () => !!process.env.ANTHROPIC_API_KEY },
        { label: 'pyautogui', check: () => { try { const { execSync } = require('child_process'); execSync('python3 -c "import pyautogui"'); return true; } catch { return false; } } },
        { label: 'nmap', check: () => { try { const { execSync } = require('child_process'); execSync('which nmap'); return true; } catch { return false; } } },
        { label: 'venv', check: () => fs.existsSync(path.join(process.cwd(), 'venv')) },
        { label: 'rich', check: () => { try { const { execSync } = require('child_process'); execSync('python3 -c "import rich"'); return true; } catch { return false; } } },
      ];

      printInfo('System check:');
      for (const { label, check } of checks) {
        const ok = await check();
        process.stdout.write(
          '  ' + (ok ? colorize('✓', c.green) : colorize('✗', c.red)) +
          ' ' + label.padEnd(25) + (ok ? colorize('ok', c.dim) : colorize('missing', c.yellow)) + '\n'
        );
      }
    },
  },
  {
    name: 'repos',
    description: 'List all integrated external repositories',
    handler: () => {
      const extDir = path.join(process.cwd(), 'external');
      if (!fs.existsSync(extDir)) { printWarning('external/ not found'); return; }
      const repos = fs.readdirSync(extDir).filter(r => fs.statSync(path.join(extDir, r)).isDirectory());
      printInfo(`Integrated repositories (${repos.length}):`);
      for (const r of repos) {
        const hasContent = fs.readdirSync(path.join(extDir, r)).length > 0;
        process.stdout.write(
          '  ' + colorize(r.padEnd(30), c.cyan) +
          (hasContent ? colorize('ready', c.green) : colorize('empty', c.yellow)) + '\n'
        );
      }
    },
  },
  {
    name: 'voice',
    description: 'Toggle voice input mode',
    handler: (_, ctx) => {
      ctx.config.useVoice = !ctx.config.useVoice;
      printSuccess(`Voice input ${ctx.config.useVoice ? 'enabled' : 'disabled'}.`);
    },
  },
  {
    name: 'cd',
    description: 'Change working directory. Usage: /cd <path>',
    handler: (args) => {
      const dir = args.trim() || os.homedir();
      try {
        process.chdir(dir);
        printSuccess(`Changed directory to ${process.cwd()}`);
      } catch (e) {
        printError(`Cannot change to ${dir}: ${e}`);
      }
    },
  },
  {
    name: 'screenshot',
    description: 'Take a screenshot of the current screen',
    handler: async () => {
      const outPath = path.join(os.tmpdir(), `devin_ss_${Date.now()}.png`);
      const { execSync } = await import('child_process');
      try {
        execSync(`import -window root "${outPath}" 2>/dev/null || scrot "${outPath}" 2>/dev/null || python3 -c "import pyautogui; pyautogui.screenshot('${outPath}')"`, { timeout: 10000 });
        printSuccess(`Screenshot saved to ${outPath}`);
      } catch (e) {
        printError(`Screenshot failed: ${e}`);
      }
    },
  },
];

export function handleCommand(input: string, ctx: CommandContext): boolean {
  const parts = input.trim().slice(1).split(/\s+(.+)?/, 2);
  const cmdName = parts[0]?.toLowerCase() || '';
  const args = parts[1] || '';

  const cmd = COMMANDS.find(c => c.name === cmdName || c.aliases?.includes(cmdName));
  if (!cmd) return false;

  Promise.resolve(cmd.handler(args, ctx)).catch(e => printError(String(e)));
  return true;
}
