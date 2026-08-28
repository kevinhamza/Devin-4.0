// src/context.ts — Context/system-prompt building (mirrors claude-code/src/context.ts)

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as cp from 'child_process';
import { PROJECT_ROOT } from './config.js';

// Read CLAUDE.md / DEVIN.md if they exist
function getProjectMd(): string {
  const candidates = ['DEVIN.md', 'CLAUDE.md', '.devin/instructions.md'];
  for (const f of candidates) {
    const p = path.join(PROJECT_ROOT, f);
    if (fs.existsSync(p)) {
      return '\n\n---\nProject instructions:\n' + fs.readFileSync(p, 'utf8').slice(0, 5000);
    }
  }
  return '';
}

// Get git status for context
function getGitStatus(): string {
  try {
    const branch = cp.execSync('git branch --show-current 2>/dev/null', { encoding: 'utf8', timeout: 3000 }).trim();
    const status = cp.execSync('git status --short 2>/dev/null', { encoding: 'utf8', timeout: 3000 }).trim();
    if (!branch) return '';
    return `\nGit: branch=${branch}${status ? ', uncommitted changes:\n' + status.slice(0, 500) : ', clean'}`;
  } catch {
    return '';
  }
}

// Build full context for the session
export function buildContext(): string {
  const sysInfo = `System: ${os.platform()} ${os.arch()}, Node ${process.version}`;
  const cwd = `CWD: ${process.cwd()}`;
  const user = `User: ${os.userInfo().username}`;
  const projectMd = getProjectMd();
  const git = getGitStatus();

  return [sysInfo, cwd, user, git, projectMd].filter(Boolean).join('\n');
}

// Build the full system prompt incorporating context
export function buildSystemPrompt(extraInstructions?: string): string {
  const context = buildContext();
  const base = `You are Devin, a highly capable AI engineer and assistant with real, direct control over this computer.

You have access to these capabilities:
- Read/write files, search code, list directories
- Execute shell commands (bash, python, node, etc.)
- Control the mouse and keyboard to interact with any app
- Take screenshots and understand what's on screen
- Browse the web and fetch URLs
- Monitor processes and system resources
- Manage cloud resources (AWS, GCP, Azure)
- Perform authorized security research (pentesting, vulnerability scanning)
- Remember information across sessions with persistent memory
- Delegate bounded sub-tasks to fresh sub-agents
- Send messages via Telegram, Discord, or Slack

Your work style:
- Be concise and direct — no unnecessary preamble
- When asked to do something, do it (show each tool call as you go)
- Show tool calls as they happen: "● tool_name(args)" then "↳ result"
- Ask a short clarifying question when genuinely ambiguous
- Never pretend to have done something you haven't
- Decline unauthorized security testing, but explain why

${context}`;

  return extraInstructions ? base + '\n\n' + extraInstructions : base;
}
