#!/usr/bin/env node
// src/cli.ts — Devin AGI  (Claude Code-compatible interface)
// Streaming, multi-provider, full OS control, 87+ tools, all repos integrated.

import * as readline from 'readline';
import * as os from 'os';
import * as path from 'path';
import * as fs from 'fs';
import { parseArgs } from 'util';

import { Config, Message, ToolUseBlock } from './types.js';
import { loadConfig, PROJECT_ROOT } from './config.js';
import { ALL_TOOLS } from './tools/definitions.js';
import { executeTool, DANGEROUS_TOOLS as DANGEROUS_SET } from './tools/executor.js';
import {
  printBanner, printAssistantMessage, printThinking, printToolCall,
  printToolResult, printError, printWarning, printInfo, printSuccess,
  printHelp, promptLine, askConfirmation, Spinner, c, colorize,
  renderMarkdown,
} from './ui/terminal.js';
import {
  getSystemPrompt, compactHistory, buildContext,
} from './conversation.js';
import { LocalMemory } from './memory/index.js';
import { BaseProvider, StreamChunk } from './providers/base.js';

// ── Provider factory ──────────────────────────────────────────────────────────
async function buildProvider(config: Config): Promise<BaseProvider> {
  // Try providers in priority order based on available keys
  if (config.provider === 'anthropic' || (!config.provider && config.apiKeys.anthropic)) {
    const { AnthropicProvider } = await import('./providers/anthropic.js');
    return new AnthropicProvider(config.apiKeys.anthropic!, config.model);
  }
  if (config.provider === 'gemini' || (!config.provider && config.apiKeys.gemini)) {
    const { GeminiProvider } = await import('./providers/gemini.js');
    return new GeminiProvider(config.apiKeys.gemini!, config.model);
  }
  if (config.provider === 'openai' || (!config.provider && config.apiKeys.openai)) {
    const { OpenAIProvider } = await import('./providers/openai.js');
    return new OpenAIProvider(config.apiKeys.openai!, config.model);
  }
  // Try multi-provider (deepseek, groq, mistral, ollama, etc.)
  const { buildMultiProvider } = await import('./providers/multi.js');
  const mp = buildMultiProvider(config.model, '');
  if (mp) return mp;
  // Hard fallback to Gemini free tier
  const { GeminiProvider } = await import('./providers/gemini.js');
  const key = process.env.GEMINI_API_KEY || config.apiKeys.gemini || '';
  printWarning('No primary API key found — using Gemini free tier.');
  return new GeminiProvider(key, 'gemini-2.0-flash');
}

// ── Streaming conversation loop ───────────────────────────────────────────────
async function runConversation(
  provider: BaseProvider,
  history: Message[],
  memory: LocalMemory,
  config: Config,
  spinner: Spinner,
  onComplete?: (reply: string) => void
): Promise<void> {
  const MAX_STEPS = 30;
  let steps = 0;
  const recentSigs: string[] = [];
  let fullReply = '';

  while (steps < MAX_STEPS) {
    steps++;
    spinner.start();

    // Collect streaming output
    let streamText = '';
    const streamToolUses: Array<{ id: string; name: string; input: Record<string, unknown> }> = [];
    let streamDone = false;

    let response;
    const callOptions = {
      maxTokens: config.maxTokens,
      enableThinking: config.enableThinking,
      thinkingBudget: config.thinkingBudget,
      systemPrompt: getSystemPrompt(),
    };
    const MAX_RETRIES = 4;
    let lastCallError: unknown;
    let gotResponse = false;
    for (let attempt = 0; attempt < MAX_RETRIES && !gotResponse; attempt++) {
      if (attempt > 0) {
        spinner.stop();
        const delay = 2000 * attempt;
        if (config.verbose) printInfo(`Retry ${attempt}/${MAX_RETRIES - 1} in ${delay / 1000}s…`);
        await new Promise(r => setTimeout(r, delay));
        spinner.start();
      }
      try {
        response = await provider.stream(
          buildContext(history),
          ALL_TOOLS,
          (chunk: StreamChunk) => {
            if (chunk.type === 'text' && chunk.content) {
              if (!streamDone) {
                spinner.stop();
                streamDone = true;
                process.stdout.write('\n' + colorize('Devin', c.bold, c.brightCyan) + '\n');
              }
              process.stdout.write(renderMarkdown(chunk.content));
              streamText += chunk.content;
              fullReply += chunk.content;
            }
          },
          callOptions
        );
        gotResponse = true;
      } catch (e: unknown) {
        lastCallError = e;
        spinner.stop();
        // Fall back to non-streaming chat()
        try {
          response = await provider.chat(buildContext(history), ALL_TOOLS, callOptions);
          streamDone = false;
          gotResponse = true;
        } catch (e2: unknown) {
          lastCallError = e2;
          const msg = String(e2).toLowerCase();
          const isTransient = msg.includes('fetch failed') || msg.includes('econnreset') ||
            msg.includes('socket') || msg.includes('network') || msg.includes('etimedout') ||
            msg.includes('503') || msg.includes('429') || msg.includes('rate') ||
            msg.includes('quota') || msg.includes('unavailable');
          if (!isTransient) break; // non-retriable — give up immediately
        }
      }
    }
    if (!gotResponse || !response) {
      spinner.stop();
      printError(`Provider error: ${lastCallError}`);
      return;
    }

    spinner.stop();

    // Extract content from response
    let textContent = streamText;
    const toolUses: ToolUseBlock[] = [];

    for (const block of response.content) {
      if (block.type === 'thinking') {
        printThinking(block.thinking);
      } else if (block.type === 'text' && !streamText) {
        // Only print if we didn't stream it already
        textContent += block.text;
      } else if (block.type === 'tool_use') {
        toolUses.push(block);
      }
    }

    // Print text if it wasn't streamed
    if (textContent && !streamText) {
      printAssistantMessage(textContent);
    } else if (streamText) {
      // Already streamed — just add a newline
      process.stdout.write('\n');
    }

    // Build assistant history entry — do NOT include [Tool: ...] text, it confuses Gemini
    // into mimicking that format as plain text instead of using real function calls.
    const assistantContent = textContent || (toolUses.length > 0 ? '(acting)' : '');
    if (assistantContent) {
      history.push({ role: 'assistant', content: assistantContent });
    }

    // Detect when Gemini outputs "[Tool: name({args})]" as plain text instead of a real call.
    // Parse and re-execute those as actual tool uses so the task continues.
    if (toolUses.length === 0 && textContent) {
      const TEXT_TOOL_RE = /\[Tool:\s*(\w+)\s*\((\{.*?\}|)\)\]/g;
      let m: RegExpExecArray | null;
      const recovered: ToolUseBlock[] = [];
      while ((m = TEXT_TOOL_RE.exec(textContent)) !== null) {
        const tName = m[1];
        let tInput: Record<string, unknown> = {};
        try { tInput = JSON.parse(m[2] || '{}'); } catch { /* empty args */ }
        recovered.push({ type: 'tool_use', id: `rec_${Date.now()}`, name: tName, input: tInput });
      }
      if (recovered.length > 0) {
        // Execute recovered tool calls and continue the loop
        for (const tu of recovered) {
          printToolCall(tu.name, tu.input as Record<string, unknown>);
          const result = await executeTool(tu.name, tu.input as Record<string, unknown>, config);
          printToolResult(result.content, result.isError);
          history.push({ role: 'tool', content: result.content, name: tu.id });
        }
        continue; // Re-enter loop so model can act on results
      }
    }

    // task_complete → done
    const taskComplete = toolUses.find(tu => tu.name === 'task_complete');
    if (toolUses.length === 0 && response.stop_reason !== 'tool_use') {
      const finalText = taskComplete
        ? String((taskComplete.input as Record<string, unknown>).reason || '')
        : textContent;
      if (taskComplete && finalText && !streamText.includes(finalText)) {
        printAssistantMessage(finalText);
      }
      if (taskComplete) {
        const lastUserMsg = [...history].reverse().find(m => m.role === 'user');
        memory.add(
          `User: ${lastUserMsg?.content || ''}\nDevin: ${finalText}`,
          ['conversation']
        );
      }
      onComplete?.(fullReply);
      return;
    }
    if (taskComplete) {
      const finalText = String((taskComplete.input as Record<string, unknown>).reason || '');
      if (finalText && !streamText.includes(finalText)) printAssistantMessage(finalText);
      onComplete?.(fullReply);
      return;
    }

    // Execute tool calls
    for (const toolUse of toolUses) {
      const { name, input, id } = toolUse;
      const sig = `${name}:${JSON.stringify(input)}`;

      // Loop detection
      recentSigs.push(sig);
      if (recentSigs.length >= 3 && new Set(recentSigs.slice(-3)).size === 1) {
        printWarning(`Loop detected: repeating ${name} without progress. Pausing.`);
        return;
      }

      printToolCall(name, input as Record<string, unknown>);

      // Plan mode
      if (config.permissionMode === 'plan') {
        printInfo(`[PLAN] ${name} — described but not executed.`);
        history.push({ role: 'tool', content: '(plan mode, not executed)', name: id });
        continue;
      }

      // Confirmation for dangerous tools
      if (DANGEROUS_SET.has(name) && config.permissionMode === 'default') {
        const ok = await askConfirmation(`Run ${colorize(name, c.cyan)}?`, true);
        if (!ok) {
          printInfo('Skipped.');
          history.push({ role: 'tool', content: 'User declined.', name: id });
          continue;
        }
      }

      // Execute
      const result = await executeTool(name, input as Record<string, unknown>, config);
      printToolResult(result.content, result.isError);

      history.push({ role: 'tool', content: result.content, name: id });
    }

    // Compact history if it gets too long
    if (history.length > 200) {
      history.splice(0, history.length, ...compactHistory(history));
    }
  }

  printWarning('Reached step limit. Pausing — what would you like to do next?');
}

// ── Slash command handler ─────────────────────────────────────────────────────
function handleSlashCommand(
  input: string,
  config: Config,
  history: Message[],
  memory: LocalMemory
): boolean {
  const cmd = input.trim().toLowerCase();
  const parts = input.trim().split(/\s+/);
  const sub = parts[1] || '';

  switch (cmd) {
    case '/help':
      printHelp();
      return true;

    case '/clear':
      history.splice(0, history.length);
      printSuccess('Conversation cleared.');
      return true;

    case '/status': {
      const memFree = Math.round(os.freemem() / 1024 / 1024);
      const memTotal = Math.round(os.totalmem() / 1024 / 1024);
      const uptime = Math.round(os.uptime() / 60);
      printInfo('Session status:');
      printInfo(`  Provider: ${config.provider}  Model: ${config.model}`);
      printInfo(`  Permission: ${config.permissionMode}  Voice: ${config.useVoice ? 'on' : 'off'}`);
      printInfo(`  History: ${history.length} messages  Memory: ${memory.all().length} entries`);
      printInfo(`  OS: ${os.platform()} ${os.arch()}  CPU: ${os.cpus().length}×${os.cpus()[0]?.speed || '?'}MHz`);
      printInfo(`  RAM: ${memFree}MB free / ${memTotal}MB total  Uptime: ${uptime}min`);
      printInfo(`  Project: ${PROJECT_ROOT}`);
      return true;
    }

    case '/plan':
      config.permissionMode = 'plan';
      printSuccess('Plan mode — actions described but not executed.');
      return true;

    case '/auto':
      config.permissionMode = 'auto_approve';
      printSuccess('Auto-approve mode — dangerous actions run without confirmation.');
      return true;

    case '/default':
      config.permissionMode = 'default';
      printSuccess('Default mode — confirmation required for dangerous actions.');
      return true;

    case '/memory': {
      const recent = memory.recent(15);
      if (recent.length === 0) {
        printInfo('No memories yet.');
      } else {
        printInfo(`Recent memories (${recent.length}):`);
        for (const m of recent) {
          const ts = new Date(m.timestamp).toLocaleString();
          printInfo(`  [${ts}] ${m.content.slice(0, 120)}`);
        }
      }
      return true;
    }

    case '/tools': {
      printInfo(`Available tools (${ALL_TOOLS.length}):`);
      for (const t of ALL_TOOLS) {
        const dangerous = DANGEROUS_SET.has(t.name) ? colorize(' ⚠', c.yellow) : '';
        printInfo(`  ${colorize(t.name.padEnd(30), c.cyan)}${dangerous} ${t.description.slice(0, 55)}`);
      }
      return true;
    }

    case '/repos': {
      const extDir = path.join(PROJECT_ROOT, 'external');
      if (!fs.existsSync(extDir)) { printInfo('No external repos found.'); return true; }
      const repos = fs.readdirSync(extDir).filter(d => fs.statSync(path.join(extDir, d)).isDirectory());
      printInfo(`External repos (${repos.length}):`);
      for (const r of repos) {
        printInfo(`  ${colorize(r, c.cyan)}`);
      }
      const intDir = path.join(PROJECT_ROOT, 'integrated');
      if (fs.existsSync(intDir)) {
        let total = 0;
        for (const type of fs.readdirSync(intDir)) {
          const td = path.join(intDir, type);
          if (fs.statSync(td).isDirectory()) {
            for (const _repo of fs.readdirSync(td)) total++;
          }
        }
        printInfo(`Integrated source files from all repos: in integrated/`);
      }
      return true;
    }

    case '/model':
      if (sub) {
        config.model = sub;
        printSuccess(`Model set to ${sub}. Takes effect on next conversation start.`);
      } else {
        printInfo(`Current model: ${config.model}`);
      }
      return true;

    case '/verbose':
      config.verbose = !config.verbose;
      printSuccess(`Verbose ${config.verbose ? 'on' : 'off'}.`);
      return true;

    default:
      // /subagent <task>
      if (parts[0] === '/subagent' && parts.length > 1) {
        const task = parts.slice(1).join(' ');
        history.push({ role: 'user', content: `[SUBAGENT TASK] ${task}` });
        return false; // Let main loop handle it
      }
      return false;
  }
}

// ── Main entry point ──────────────────────────────────────────────────────────
async function main(): Promise<void> {
  let args: ReturnType<typeof parseArgs>['values'] & { _positionals?: string[] };
  try {
    const parsed = parseArgs({
      options: {
        help:        { type: 'boolean', short: 'h' },
        model:       { type: 'string',  short: 'm' },
        provider:    { type: 'string',  short: 'p' },
        plan:        { type: 'boolean' },
        auto:        { type: 'boolean' },
        voice:       { type: 'boolean' },
        verbose:     { type: 'boolean', short: 'v' },
        version:     { type: 'boolean', short: 'V' },
        print:       { type: 'string' },
        prompt:      { type: 'string' },
        web:         { type: 'boolean' },
        port:        { type: 'string' },
        dangerously: { type: 'boolean' },
      },
      allowPositionals: true,
    });
    args = { ...parsed.values, _positionals: parsed.positionals };
  } catch {
    args = {};
  }

  if (args.help) {
    process.stdout.write([
      '',
      colorize('  Devin AGI v4.0.0', c.bold, c.cyan) + '  ' + colorize('AI assistant with OS control', c.dim),
      '',
      '  Usage: devin [options] [prompt]',
      '',
      '  Options:',
      '    -h, --help              Show this help',
      '    -V, --version           Show version',
      '    -m, --model <name>      Model to use (e.g. gemini-2.5-flash)',
      '    -p, --provider <p>      Provider: anthropic | gemini | openai | ollama',
      '    --plan                  Plan mode (describe actions, don\'t run)',
      '    --auto                  Auto-approve all tool calls',
      '    --dangerously           Alias for --auto (no confirmation)',
      '    --voice                 Enable voice input',
      '    -v, --verbose           Verbose output (show tool classification)',
      '    --print <text>          Run one prompt non-interactively and exit',
      '    --prompt <text>         Same as --print',
      '    --web [--port <N>]      Start web UI (default port 3000)',
      '',
      '  Slash commands (inside REPL):',
      '    /help   /clear   /status   /tools   /memory   /repos',
      '    /plan   /auto    /default  /model <name>  /verbose',
      '',
      '  Examples:',
      '    devin                              # Interactive mode',
      '    devin "open firefox"               # One-shot via positional',
      '    devin --print "take a screenshot"  # Non-interactive',
      '    devin --provider anthropic --plan  # Plan mode with Claude',
      '    devin --web --port 8080            # Web UI',
      '',
    ].join('\n') + '\n');
    process.exit(0);
  }

  if (args.version) {
    process.stdout.write('Devin AGI v4.0.0\n');
    process.exit(0);
  }

  // Web UI mode
  if (args.web) {
    const port = args.port ? parseInt(String(args.port)) : 3000;
    const config = loadConfig({});
    const provider = await buildProvider(config);
    const memory = new LocalMemory();
    const history: Message[] = [];
    const spinner = new Spinner();

    printBanner(provider.model, provider.name, config.permissionMode, process.cwd());
    printSuccess(`Connected to ${provider.name} (${provider.model})`);

    try {
      const { startWebServer, setConversationHandler } = await import('./server.js');
      setConversationHandler(async (message: string) => {
        history.push({ role: 'user', content: message });
        let lastReply = '';
        await runConversation(provider, history, memory, config, spinner, (r) => { lastReply = r; });
        return { response: lastReply || 'Done.', toolCalls: [] };
      });
      await startWebServer(port);
      printSuccess(`Web UI → http://localhost:${port}`);
      await new Promise(() => {}); // keep alive
    } catch (e) {
      printError(`Web server error: ${e}`);
      process.exit(1);
    }
    return;
  }

  // Build config from args
  const overrides: Partial<Config> = {};
  if (args.model) overrides.model = String(args.model);
  if (args.provider) overrides.provider = args.provider as Config['provider'];
  if (args.plan) overrides.permissionMode = 'plan';
  if (args.auto || args.dangerously) overrides.permissionMode = 'auto_approve';
  if (args.voice) overrides.useVoice = true;
  if (args.verbose) overrides.verbose = true;
  const config = loadConfig(overrides);

  printBanner(config.model, config.provider, config.permissionMode, config.cwd);

  const memory = new LocalMemory();
  const spinner = new Spinner();

  let provider: BaseProvider;
  try {
    provider = await buildProvider(config);
    printSuccess(`Connected to ${provider.name} (${provider.model})`);
  } catch (e) {
    printError(`Failed to initialize AI provider: ${e}`);
    printInfo('Set GEMINI_API_KEY, ANTHROPIC_API_KEY, or OPENAI_API_KEY in .env');
    process.exit(1);
    return;
  }

  const history: Message[] = [];

  // Non-interactive (one-shot) mode: --print / --prompt / positional
  const oneShot = args.print || args.prompt || (args._positionals && args._positionals.length > 0
    ? args._positionals.join(' ') : undefined);
  if (oneShot) {
    history.push({ role: 'user', content: String(oneShot) });
    await runConversation(provider, history, memory, config, spinner);
    process.exit(0);
    return;
  }

  // Interactive REPL
  process.stdout.write(colorize(
    '\nTalk to Devin — ask a question, give a task, or type /help. (exit to quit)\n',
    c.dim
  ));

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    terminal: true,
    historySize: 1000,
    prompt: '',
  });

  rl.on('SIGINT', () => {
    process.stdout.write('\n' + colorize('(Ctrl+C again to exit, or type "exit")\n', c.dim));
  });

  const askLine = (): Promise<string> => new Promise(resolve => {
    process.stdout.write('\n' + promptLine(config.cwd));
    rl.once('line', line => resolve(line.trim()));
  });

  while (true) {
    let input: string;
    try {
      input = await askLine();
    } catch {
      break;
    }

    if (!input) continue;
    if (['exit', 'quit', 'bye', ':q', 'q'].includes(input.toLowerCase())) {
      printInfo('Goodbye.');
      break;
    }

    if (input.startsWith('/')) {
      if (!handleSlashCommand(input, config, history, memory)) {
        if (!input.startsWith('/subagent')) {
          printWarning(`Unknown command: ${input}. Type /help.`);
          continue;
        }
      } else {
        continue;
      }
    }

    // Recall relevant memories
    const recalled = memory.search(input, 3);
    if (recalled.length > 0) {
      const mem = recalled.map(m => `- ${m.content.slice(0, 100)}`).join('\n');
      history.push({ role: 'system', content: `Recalled memories:\n${mem}` });
    }

    history.push({ role: 'user', content: input });
    await runConversation(provider, history, memory, config, spinner);
  }

  rl.close();
  process.exit(0);
}

main().catch(e => {
  process.stderr.write(`\nFatal error: ${e instanceof Error ? e.stack || e.message : String(e)}\n`);
  process.exit(1);
});
