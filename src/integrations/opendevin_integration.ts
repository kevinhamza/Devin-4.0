// src/integrations/opendevin_integration.ts — OpenDevin agent integration
// OpenDevin is an open-source implementation of Devin-style software agents
// This module bridges Devin-4.0 with OpenDevin's architecture patterns

import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';

const DEVIN_ROOT = path.join(__dirname, '../..');
const OPENDEVIN_DIR = path.join(DEVIN_ROOT, 'external/OpenDevin');

// ── Agent action types (from OpenDevin agent architecture) ────────────────────

export type OpenDevinAction =
  | { type: 'run'; command: string; thought?: string }
  | { type: 'write'; path: string; content: string }
  | { type: 'read'; path: string }
  | { type: 'browse'; url: string }
  | { type: 'think'; thought: string }
  | { type: 'finish'; message: string };

export interface OpenDevinObservation {
  type: 'run_result' | 'file_content' | 'browser_output' | 'error';
  content: string;
  success: boolean;
}

// ── Agent planner (OpenDevin task decomposition pattern) ──────────────────────

export interface AgentPlan {
  goal: string;
  steps: string[];
  currentStep: number;
  completed: boolean;
}

export function createAgentPlan(goal: string, steps: string[]): AgentPlan {
  return { goal, steps, currentStep: 0, completed: false };
}

export function advancePlan(plan: AgentPlan): { step: string; done: boolean } {
  if (plan.currentStep >= plan.steps.length) {
    plan.completed = true;
    return { step: 'All steps complete', done: true };
  }
  const step = plan.steps[plan.currentStep];
  plan.currentStep++;
  plan.completed = plan.currentStep >= plan.steps.length;
  return { step, done: plan.completed };
}

// ── Action executor (OpenDevin CodeActAgent pattern) ─────────────────────────

export async function executeOpenDevinAction(
  action: OpenDevinAction
): Promise<OpenDevinObservation> {
  switch (action.type) {
    case 'run': {
      try {
        const stdout = cp.execSync(action.command, {
          encoding: 'utf8',
          timeout: 30000,
          cwd: DEVIN_ROOT,
        }).trim();
        return { type: 'run_result', content: stdout || '(no output)', success: true };
      } catch (e: unknown) {
        const err = e as { stdout?: string; stderr?: string; message?: string };
        return {
          type: 'run_result',
          content: (err.stdout || '') + (err.stderr || '') || String(err.message || e),
          success: false,
        };
      }
    }
    case 'write': {
      try {
        fs.mkdirSync(path.dirname(action.path), { recursive: true });
        fs.writeFileSync(action.path, action.content, 'utf8');
        return { type: 'run_result', content: `Written: ${action.path}`, success: true };
      } catch (e) {
        return { type: 'error', content: String(e), success: false };
      }
    }
    case 'read': {
      try {
        const content = fs.readFileSync(action.path, 'utf8');
        return { type: 'file_content', content, success: true };
      } catch (e) {
        return { type: 'error', content: String(e), success: false };
      }
    }
    case 'browse': {
      try {
        const result = cp.execSync(
          `curl -sL --max-time 10 "${action.url}" | python3 -c "
import sys, html.parser

class P(html.parser.HTMLParser):
    skip=False
    out=[]
    def handle_starttag(self,t,a):
        self.skip=t in ('script','style')
    def handle_endtag(self,t):
        self.skip=False
    def handle_data(self,d):
        if not self.skip and d.strip():
            self.out.append(d.strip())
p=P()
p.feed(sys.stdin.read())
print(' '.join(p.out)[:3000])
"`,
          { encoding: 'utf8', timeout: 15000 }
        ).trim();
        return { type: 'browser_output', content: result, success: true };
      } catch (e) {
        return { type: 'error', content: String(e).slice(0, 200), success: false };
      }
    }
    case 'think':
      return { type: 'run_result', content: `Thought: ${action.thought}`, success: true };
    case 'finish':
      return { type: 'run_result', content: action.message, success: true };
    default:
      return { type: 'error', content: 'Unknown action type', success: false };
  }
}

// ── Multi-step coding agent (OpenDevin CodeActAgent) ──────────────────────────

export interface CodingTask {
  description: string;
  workdir: string;
  files: Record<string, string>;
}

export async function executeCodingTask(
  task: CodingTask,
  askLLM: (prompt: string) => Promise<string>
): Promise<{ success: boolean; output: string; filesCreated: string[] }> {
  const filesCreated: string[] = [];
  const outputs: string[] = [];
  const workdir = task.workdir || DEVIN_ROOT;

  // Create any seed files
  for (const [filepath, content] of Object.entries(task.files || {})) {
    const fullPath = path.join(workdir, filepath);
    fs.mkdirSync(path.dirname(fullPath), { recursive: true });
    fs.writeFileSync(fullPath, content, 'utf8');
    filesCreated.push(fullPath);
  }

  // Ask LLM to plan
  const plan = await askLLM(
    `You are a software agent. Task: ${task.description}\n\nWorkdir: ${workdir}\n` +
    `Existing files: ${Object.keys(task.files || {}).join(', ')}\n\n` +
    `Respond with a list of bash commands to complete this task, one per line.`
  );

  const commands = plan.split('\n').filter(l => l.trim() && !l.startsWith('#') && !l.startsWith('//'));

  for (const cmd of commands.slice(0, 20)) {
    const obs = await executeOpenDevinAction({ type: 'run', command: cmd });
    outputs.push(`$ ${cmd}\n${obs.content}`);
    if (!obs.success && obs.content.includes('FATAL')) break;
  }

  return {
    success: true,
    output: outputs.join('\n\n'),
    filesCreated,
  };
}

// ── Workspace manager (from OpenDevin workspace patterns) ─────────────────────

export function getWorkspaceFiles(dir = DEVIN_ROOT): string[] {
  try {
    return cp.execSync(
      `find "${dir}" -type f -not -path "*/node_modules/*" -not -path "*/.git/*" -not -path "*/external/*" | head -100`,
      { encoding: 'utf8' }
    ).trim().split('\n').filter(Boolean);
  } catch {
    return [];
  }
}

export function getRepoStructure(dir = DEVIN_ROOT): string {
  try {
    return cp.execSync(
      `find "${dir}" -maxdepth 3 -not -path "*/node_modules/*" -not -path "*/.git/*" | head -80`,
      { encoding: 'utf8' }
    ).trim();
  } catch {
    return '';
  }
}

// ── Sandbox execution (OpenDevin sandbox pattern) ─────────────────────────────

export function runInSandbox(code: string, language: 'python' | 'bash' | 'node'): string {
  const tmpFile = path.join(os.tmpdir(), `devin_sandbox_${Date.now()}`);
  try {
    let cmd: string;
    switch (language) {
      case 'python':
        fs.writeFileSync(tmpFile + '.py', code);
        cmd = `timeout 30 python3 "${tmpFile}.py"`;
        break;
      case 'bash':
        fs.writeFileSync(tmpFile + '.sh', code);
        cmd = `timeout 30 bash "${tmpFile}.sh"`;
        break;
      case 'node':
        fs.writeFileSync(tmpFile + '.js', code);
        cmd = `timeout 30 node "${tmpFile}.js"`;
        break;
    }
    return cp.execSync(cmd, { encoding: 'utf8', timeout: 35000 }).trim();
  } catch (e: unknown) {
    const err = e as { stdout?: string; stderr?: string };
    return (err.stdout || '') + (err.stderr || '') || String(e);
  } finally {
    for (const ext of ['.py', '.sh', '.js']) {
      try { fs.unlinkSync(tmpFile + ext); } catch { /* ignore */ }
    }
  }
}
