// src/tools/executor.ts — Tool executor for Devin AGI
// Real OS control via pyautogui + xdotool backend (modules/os_automation.py)

import * as fs from 'fs';
import * as path from 'path';
import * as os from 'os';
import * as cp from 'child_process';
import { Config } from '../types.js';
import { httpFetch, duckDuckGoSearch, formatSearchResults } from './web_tool.js';
import { classifyCommandVerbose } from './bash_security.js';
import { runResearch, formatResearchBrief } from '../agents/research.js';
import { readFile, writeFile, editFile, statFile, listDirectory, globFiles, grepFiles, findFiles } from './file_tool.js';
import { lookupCVE, searchCVEByKeyword, scanWebApp, generateVulnReport } from '../security/vulnerability_scanner.js';
import { scanPaths, testXSS, testSQLi, checkSSL, scanWiFiNetworks } from '../security/web_scanner.js';
import { scheduleTask, listScheduledTasks, cancelTask, getSystemMetrics, fetchWeather } from '../integrations/aia_integration.js';
import { parseJarvisCommand, executeJarvisCommand, jarvisSpeak } from '../integrations/jarvis_integration.js';
import { generateText, generateCode, listGeminiModels } from '../integrations/gemini_cli_integration.js';
import { checkIPReputation, analyzeDomain, analyzeFileHash, gatherOSINT } from '../integrations/shannon_integration.js';

export type ToolResult = { content: string; isError: boolean };
type ToolFn = (args: Record<string, unknown>, config: Config) => Promise<ToolResult>;

export const DANGEROUS_TOOLS = new Set([
  'execute_shell', 'delete_file', 'write_file', 'edit_file', 'kill_process',
  'mouse_click', 'mouse_right_click', 'mouse_drag', 'keyboard_type', 'keyboard_hotkey',
  'keyboard_press', 'click_and_type', 'operate_computer', 'browser_automate',
  'run_command_in_terminal', 'search_and_open_app', 'open_application', 'close_application',
  'run_nmap_scan', 'vulnerability_scan', 'run_metasploit', 'run_hexstrike',
  'run_cloud_command', 'close_current_window',
]);

const DEVIN_ROOT = path.join(__dirname, '../..');
const AUTOMATION_SCRIPT = path.join(DEVIN_ROOT, 'modules/os_automation.py');
const VENV_PYTHON = path.join(DEVIN_ROOT, 'venv/bin/python3');
const PYTHON = fs.existsSync(VENV_PYTHON) ? VENV_PYTHON : 'python3';

function ok(content: string): ToolResult { return { content, isError: false }; }
function err(content: string): ToolResult { return { content, isError: true }; }

// ── OS Automation bridge ──────────────────────────────────────────────────────

function automate(action: string, args: Record<string, unknown> = {}, timeout = 15000): ToolResult {
  const payload = JSON.stringify({ action, args }).replace(/'/g, "'\\''");
  try {
    const out = cp.execSync(
      `DISPLAY=:0 "${PYTHON}" "${AUTOMATION_SCRIPT}" '${payload}'`,
      { timeout, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'] }
    ).trim();
    const parsed = JSON.parse(out) as { ok: boolean; result?: unknown; error?: string };
    if (parsed.ok) return ok(String(parsed.result ?? 'OK'));
    return err(String(parsed.error ?? 'Unknown error'));
  } catch (e: unknown) {
    const ex = e as { stdout?: string; stderr?: string; message?: string };
    const raw = [ex.stdout, ex.stderr].filter(Boolean).join('\n').trim();
    try {
      const p = JSON.parse(raw) as { ok: boolean; error?: string; result?: unknown };
      return p.ok ? ok(String(p.result ?? 'OK')) : err(String(p.error ?? raw));
    } catch {
      return err(ex.message || String(e));
    }
  }
}

// ── Shell execution ───────────────────────────────────────────────────────────

function runShell(cmd: string, cwd?: string, timeout = 30000): ToolResult {
  try {
    const out = cp.execSync(cmd, {
      cwd: cwd || process.cwd(),
      timeout,
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
    });
    return ok(out || '(no output)');
  } catch (e: unknown) {
    const ex = e as { stdout?: string; stderr?: string; message?: string };
    return err([ex.stdout, ex.stderr, ex.message].filter(Boolean).join('\n') || String(e));
  }
}

function runPython(code: string, cwd?: string): ToolResult {
  const tmpFile = path.join(os.tmpdir(), `devin_py_${Date.now()}.py`);
  fs.writeFileSync(tmpFile, code);
  try {
    return runShell(`"${PYTHON}" "${tmpFile}"`, cwd);
  } finally {
    try { fs.unlinkSync(tmpFile); } catch { /* ignore */ }
  }
}

// ── Tool registry ─────────────────────────────────────────────────────────────

const tools: Record<string, ToolFn> = {

  // ── File System ─────────────────────────────────────────────────────────────
  async read_file({ path: filePath, offset, limit }) {
    const p = path.resolve(String(filePath));
    if (!fs.existsSync(p)) return err(`File not found: ${p}`);
    const raw = fs.readFileSync(p, 'utf8');
    const lines = raw.split('\n');
    const start = offset ? Number(offset) - 1 : 0;
    const end = limit ? start + Number(limit) : lines.length;
    const selected = lines.slice(start, end);
    return ok(selected.map((l, i) => `${start + i + 1}\t${l}`).join('\n'));
  },

  async write_file({ path: filePath, content }) {
    const p = path.resolve(String(filePath));
    fs.mkdirSync(path.dirname(p), { recursive: true });
    fs.writeFileSync(p, String(content), 'utf8');
    return ok(`Written ${Buffer.byteLength(String(content))} bytes to ${p}`);
  },

  async edit_file({ path: filePath, old_string, new_string, replace_all }) {
    const p = path.resolve(String(filePath));
    if (!fs.existsSync(p)) return err(`File not found: ${p}`);
    const content = fs.readFileSync(p, 'utf8');
    const oldStr = String(old_string);
    if (!content.includes(oldStr)) return err(`old_string not found in ${p}`);
    const updated = replace_all === 'true'
      ? content.split(oldStr).join(String(new_string))
      : content.replace(oldStr, String(new_string));
    fs.writeFileSync(p, updated, 'utf8');
    return ok(`Edited ${p}`);
  },

  async list_files({ path: dirPath, recursive, pattern }) {
    const p = path.resolve(String(dirPath || '.'));
    if (!fs.existsSync(p)) return err(`Directory not found: ${p}`);
    const pat = pattern ? String(pattern).replace(/\*/g, '') : '';
    function listDir(dir: string, prefix = ''): string[] {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      const results: string[] = [];
      for (const e of entries) {
        const rel = prefix + e.name;
        if (pat && !e.name.endsWith(pat) && !e.isDirectory()) continue;
        results.push(e.isDirectory() ? `${rel}/` : rel);
        if (e.isDirectory() && recursive === 'true') {
          results.push(...listDir(path.join(dir, e.name), rel + '/'));
        }
      }
      return results;
    }
    return ok(listDir(p).join('\n') || '(empty)');
  },

  async delete_file({ path: filePath }) {
    const p = path.resolve(String(filePath));
    if (!fs.existsSync(p)) return err(`Not found: ${p}`);
    const stat = fs.statSync(p);
    if (stat.isDirectory()) fs.rmSync(p, { recursive: true });
    else fs.unlinkSync(p);
    return ok(`Deleted ${p}`);
  },

  async create_directory({ path: dirPath }) {
    const p = path.resolve(String(dirPath));
    fs.mkdirSync(p, { recursive: true });
    return ok(`Created directory: ${p}`);
  },

  async search_files({ pattern, path: searchPath, file_pattern, case_sensitive }) {
    const dir = String(searchPath || '.');
    const pat = String(pattern);
    const ci = case_sensitive === 'false' ? '-i' : '';
    const inc = file_pattern ? `--include="${file_pattern}"` : '';
    return runShell(`grep -rn ${ci} ${inc} "${pat.replace(/"/g, '\\"')}" "${dir}" 2>/dev/null | head -100`);
  },

  // ── Shell / Process ─────────────────────────────────────────────────────────
  async execute_shell({ command, cwd, timeout, background }, config) {
    const cmd = String(command);

    // Security classification (from cheetahclaws/tools/security.py)
    if (config.verbose) {
      const { classification, summary } = classifyCommandVerbose(cmd);
      process.stderr.write(`[bash-security] ${classification}: ${summary}\n`);
    }

    if (background === 'true') {
      const child = cp.spawn('sh', ['-c', cmd], {
        cwd: String(cwd || process.cwd()),
        detached: true, stdio: 'ignore',
      });
      child.unref();
      return ok(`Started in background with PID: ${child.pid}`);
    }
    return runShell(cmd, cwd ? String(cwd) : undefined, timeout ? Number(timeout) : 30000);
  },

  async execute_python({ code, cwd }) {
    return runPython(String(code), cwd ? String(cwd) : undefined);
  },

  async kill_process({ pid, signal }) {
    try {
      process.kill(Number(pid), (signal as NodeJS.Signals) || 'SIGTERM');
      return ok(`Sent ${signal || 'SIGTERM'} to PID ${pid}`);
    } catch (e) {
      return err(`Failed: ${e}`);
    }
  },

  // ── Web ──────────────────────────────────────────────────────────────────────
  async web_fetch({ url, method, headers, body }) {
    try {
      const hdrs = headers ? JSON.parse(String(headers)) as Record<string, string> : {};
      const result = await httpFetch(String(url), {
        method: String(method || 'GET'),
        headers: hdrs,
        body: body ? String(body) : undefined,
      });
      return ok(`HTTP ${result.status} — ${result.contentType}\n\n${result.text.slice(0, 10000)}`);
    } catch (e) {
      return err(`Fetch failed: ${e}`);
    }
  },

  async web_search({ query, num_results }) {
    const n = Number(num_results || 8);
    try {
      const results = await duckDuckGoSearch(String(query), n);
      return ok(formatSearchResults(results));
    } catch (e) {
      // Fallback: Python googlesearch
      const q = String(query).replace(/"/g, '\\"');
      return runPython(`
try:
    from googlesearch import search
    results = list(search("${q}", num_results=${n}, advanced=True))
    for r in results:
        print(f"{r.title}\\n{r.url}\\n{r.description}\\n---")
except Exception as e:
    print(f"Search error: {e}")
`);
    }
  },

  async research({ topic, limit, fetch_content }) {
    try {
      const brief = await runResearch({
        topic: String(topic),
        limit: limit ? Number(limit) : 8,
        fetchContent: fetch_content === 'true',
      });
      return ok(formatResearchBrief(brief));
    } catch (e) {
      return err(`Research failed: ${e}`);
    }
  },

  async open_browser({ url }) {
    return automate('open_url', { url }, 8000);
  },

  // ── Screenshot ──────────────────────────────────────────────────────────────
  async take_screenshot({ path: savePath, region }) {
    const args: Record<string, unknown> = {};
    if (savePath) args.path = String(savePath);
    if (region) {
      const parts = String(region).split(',').map(Number);
      if (parts.length === 4) args.region = parts;
    }
    return automate('screenshot', args, 10000);
  },

  // ── Real Mouse ──────────────────────────────────────────────────────────────
  async mouse_click({ x, y, button, double_click }) {
    return automate('mouse_click', {
      x: Number(x), y: Number(y),
      button: String(button || 'left'),
      double: double_click === 'true',
    });
  },

  async mouse_right_click({ x, y }) {
    return automate('mouse_right_click', { x: Number(x), y: Number(y) });
  },

  async mouse_move({ x, y }) {
    return automate('mouse_move', { x: Number(x), y: Number(y) });
  },

  async mouse_drag({ x1, y1, x2, y2, duration }) {
    return automate('mouse_drag', {
      x1: Number(x1), y1: Number(y1),
      x2: Number(x2), y2: Number(y2),
      duration: duration ? Number(duration) : 0.5,
    });
  },

  async mouse_scroll({ x, y, direction, amount }) {
    return automate('mouse_scroll', {
      x: Number(x), y: Number(y),
      direction: String(direction || 'down'),
      amount: Number(amount || 3),
    });
  },

  async get_mouse_position() {
    return automate('mouse_position', {});
  },

  // ── Real Keyboard ───────────────────────────────────────────────────────────
  async keyboard_type({ text, human_like }) {
    return automate('type', {
      text: String(text),
      human_like: human_like !== 'false',
    });
  },

  async keyboard_hotkey({ keys }) {
    const keyList = String(keys).split(',').map(k => k.trim());
    return automate('hotkey', { keys: keyList });
  },

  async keyboard_press({ key }) {
    return automate('press', { key: String(key) });
  },

  // ── Applications ────────────────────────────────────────────────────────────
  async open_application({ name, args }) {
    return automate('open_app', { name: String(name), args: args ? String(args) : undefined }, 10000);
  },

  async close_application({ name }) {
    return automate('close_app', { name: String(name) });
  },

  async open_terminal() {
    return automate('open_terminal', {}, 6000);
  },

  async run_command_in_terminal({ command }) {
    return automate('run_in_terminal', { command: String(command) }, 12000);
  },

  async search_and_open_app({ name }) {
    return automate('search_open', { name: String(name) }, 10000);
  },

  async open_file_manager({ path: dirPath }) {
    return automate('open_file_manager', dirPath ? { path: String(dirPath) } : {}, 8000);
  },

  // ── Window Management ────────────────────────────────────────────────────────
  async list_windows() {
    return automate('list_windows', {});
  },

  async focus_window({ name }) {
    return automate('focus_window', { name: String(name) });
  },

  async get_active_window() {
    return automate('active_window', {});
  },

  async maximize_window({ name }) {
    return automate('maximize', name ? { name: String(name) } : {});
  },

  async minimize_window() {
    return automate('minimize', {});
  },

  async alt_tab({ times }) {
    return automate('alt_tab', { times: Number(times || 1) });
  },

  async close_current_window() {
    return automate('close_window', {});
  },

  async get_screen_size() {
    return automate('screen_size', {});
  },

  async show_desktop() {
    return automate('show_desktop', {});
  },

  // ── Smart actions ────────────────────────────────────────────────────────────
  async click_and_type({ x, y, text, clear_first }) {
    return automate('click_and_type', {
      x: Number(x), y: Number(y),
      text: String(text),
      clear: clear_first !== 'false',
    });
  },

  async find_on_screen({ image, confidence }) {
    return automate('find_on_screen', {
      image: String(image),
      confidence: confidence ? Number(confidence) : 0.8,
    });
  },

  async click_image({ image, confidence, double_click }) {
    return automate('click_image', {
      image: String(image),
      confidence: confidence ? Number(confidence) : 0.8,
      double: double_click === 'true',
    });
  },

  // ── Clipboard ────────────────────────────────────────────────────────────────
  async clipboard_read() {
    return automate('clipboard_get', {});
  },

  async clipboard_write({ text }) {
    return automate('clipboard_set', { text: String(text) });
  },

  // ── System Info ──────────────────────────────────────────────────────────────
  async get_system_info({ include }) {
    // Use Python psutil layer — works on all platforms
    const pyInfo = automate('system_info', {}, 10000);
    const nodeParts = [
      `Platform: ${os.platform()} ${os.arch()}`,
      `Hostname: ${os.hostname()}`,
      `Uptime: ${Math.floor(os.uptime() / 3600)}h`,
      `CPUs: ${os.cpus().length}`,
      `Free RAM: ${Math.round(os.freemem() / 1024 / 1024)}MB / ${Math.round(os.totalmem() / 1024 / 1024)}MB`,
    ].join('\n');
    const pyStr = pyInfo.isError ? '' : '\n' + String(pyInfo.content);
    return ok(nodeParts + pyStr);
  },

  async list_processes({ filter, sort_by }) {
    const result = automate('processes', { top: 30 }, 10000);
    if (!result.isError && filter) {
      const lines = String(result.content).split('\n')
        .filter(l => l.toLowerCase().includes(String(filter).toLowerCase()));
      return ok(lines.join('\n') || 'No matching processes');
    }
    return result;
  },

  async screenshot_all_monitors() {
    return automate('screenshot_all', {}, 30000);
  },

  async set_volume({ level }) {
    return automate('volume_set', { level: Number(level) });
  },

  // ── Memory ───────────────────────────────────────────────────────────────────
  async remember({ content, tags }) {
    const c = String(content).replace(/"/g, '\\"');
    const t = tags ? String(tags) : '';
    return runPython(`
import sys; sys.path.insert(0, '${DEVIN_ROOT}')
from dotenv import load_dotenv; load_dotenv()
try:
    from ai_core.cognitive_arch.long_term_memory import LongTermMemory
    ltm = LongTermMemory()
    ltm.add_memory("${c}", metadata={"type": "manual", "tags": "${t}"})
    print("Remembered.")
except Exception as e:
    import json, os, time
    p = os.path.expanduser('~/.devin/memory.json')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    mems = json.load(open(p)) if os.path.exists(p) else []
    mems.append({"content": "${c}", "tags": "${t}", "timestamp": time.time()})
    json.dump(mems, open(p,'w'))
    print("Remembered (local).")
`);
  },

  async recall({ query, top_k }) {
    const q = String(query).replace(/"/g, '\\"');
    const k = Number(top_k || 5);
    return runPython(`
import sys; sys.path.insert(0, '${DEVIN_ROOT}')
from dotenv import load_dotenv; load_dotenv()
try:
    from ai_core.cognitive_arch.long_term_memory import LongTermMemory
    ltm = LongTermMemory()
    mems = ltm.retrieve_relevant_memories("${q}", top_k=${k})
    for m in mems: print(m.get('metadata', {}).get('content_preview', str(m)))
except Exception as e:
    import json, os
    p = os.path.expanduser('~/.devin/memory.json')
    if not os.path.exists(p): print("No memories."); exit()
    mems = json.load(open(p))
    q_lower = "${q}".lower()
    found = [m for m in mems if q_lower in m.get('content','').lower()]
    for m in found[:${k}]: print(m.get('content','')[:200])
    if not found: print("No relevant memories found.")
`);
  },

  // ── High-level OS operate ────────────────────────────────────────────────────
  async operate_computer({ objective, model }) {
    const m = String(model || 'gemini');
    const o = String(objective).replace(/"/g, '\\"');
    // First take a screenshot for context
    const shot = automate('screenshot', {}, 8000);
    // Then try self-operating-computer
    const result = runShell(
      `cd "${DEVIN_ROOT}" && source venv/bin/activate && python -m operate -p "${m}" --action "${o}" 2>&1`,
      undefined, 60000
    );
    if (!result.isError) return result;
    return ok(`Screenshot taken: ${shot.content}\nObjective: ${o}\n(Manual intervention may be needed)`);
  },

  // ── Browser automation ───────────────────────────────────────────────────────
  async browser_automate({ url, actions }) {
    const acts = actions ? JSON.parse(String(actions)) as unknown[] : [];
    return automate('browser_auto', { url: String(url), actions: acts }, 30000);
  },

  // ── Voice ─────────────────────────────────────────────────────────────────────
  async speak({ text, rate }) {
    return automate('speak', { text: String(text), rate: Number(rate || 180) }, 20000);
  },

  async listen_voice({ timeout, language }) {
    return automate('listen', {
      timeout: Number(timeout || 8),
      phrase_limit: 15,
      language: String(language || 'en-US'),
    }, 30000);
  },

  // ── Volume ───────────────────────────────────────────────────────────────────
  async volume_control({ action, steps, level }) {
    const a = String(action || 'up');
    const n = Number(steps || 5);
    if (a === 'mute') return automate('volume_mute', {});
    if (a === 'set' && level !== undefined) return automate('volume_set', { level: Number(level) });
    if (a === 'down') return automate('volume_down', { steps: n });
    return automate('volume_up', { steps: n });
  },

  // ── Sub-agent ─────────────────────────────────────────────────────────────────
  async delegate_subtask({ goal }) {
    return ok(`Sub-task queued: ${goal}`);
  },

  // ── Task complete ─────────────────────────────────────────────────────────────
  async task_complete({ reason }) {
    return ok(String(reason));
  },

  // ── Pentesting ───────────────────────────────────────────────────────────────
  async run_nmap_scan({ target, flags, authorized }) {
    if (authorized !== 'yes') return err('Authorization required. Set authorized="yes" only for systems you own or have explicit permission to scan.');
    return runShell(`nmap ${flags || '-sV'} "${target}" 2>&1`, undefined, 120000);
  },

  async run_hexstrike({ command, target }) {
    const hexDir = path.join(DEVIN_ROOT, 'hexstrike-ai');
    if (!fs.existsSync(hexDir)) return err('hexstrike-ai not found in project root');
    return runShell(`cd "${DEVIN_ROOT}" && source venv/bin/activate && python hexstrike-ai/hexstrike_server.py --command "${command}" ${target ? `--target "${target}"` : ''} 2>&1`, undefined, 60000);
  },

  async vulnerability_scan({ target, scan_type, authorized }) {
    if (authorized !== 'yes') return err('Authorization required.');
    return runShell(`cd "${DEVIN_ROOT}" && source venv/bin/activate && python -c "
from modules.pentesting_tools.vulnerability_scanner import VulnerabilityScanner
import json
s = VulnerabilityScanner()
print(json.dumps(s.scan('${target}', '${scan_type || 'network'}'), default=str))
" 2>&1`, undefined, 120000);
  },

  async run_metasploit({ module, options, authorized }) {
    if (authorized !== 'yes') return err('Authorization required.');
    return runShell(`msfconsole -x "use ${module}; ${options || ''}; run; exit" 2>&1`, undefined, 120000);
  },

  // ── Cloud ─────────────────────────────────────────────────────────────────────
  async list_aws_resources({ resource_type, region }) {
    return runShell(`aws ${resource_type} describe-${resource_type}s --region ${region || 'us-east-1'} --output json 2>&1`, undefined, 30000);
  },

  async run_cloud_command({ provider, command }) {
    return runShell(`${provider} ${command} 2>&1`, undefined, 60000);
  },

  // ── File tools (from claude-code-source GlobTool/GrepTool + cheetahclaws) ────
  async read_file_lines({ path: filePath, start_line, end_line }) {
    try {
      const result = readFile(String(filePath), Number(start_line) || 1, end_line ? Number(end_line) : undefined);
      return ok(result.content);
    } catch (e) { return err(String(e)); }
  },

  async glob_search({ pattern, directory, max_results }) {
    const result = globFiles(String(pattern), directory ? String(directory) : undefined, Number(max_results) || 100);
    const lines = result.files.map((f, i) => `${i + 1}. ${f}`);
    if (result.truncated) lines.push(`(truncated — showing first ${result.files.length} of more)`);
    return ok(lines.join('\n') || 'No files found');
  },

  async grep_search({ pattern, path: searchPath, glob, case_insensitive, max_results }) {
    const result = grepFiles(
      String(pattern),
      searchPath ? String(searchPath) : undefined,
      { glob: glob ? String(glob) : undefined, caseInsensitive: Boolean(case_insensitive), maxResults: Number(max_results) || 250 }
    );
    const lines = result.matches.map(m => `${m.file}:${m.line}: ${m.content}`);
    return ok(lines.join('\n') || 'No matches found');
  },

  async find_files({ directory, name, extension, max_depth }) {
    const files = findFiles(String(directory || '.'), {
      name: name ? String(name) : undefined,
      extension: extension ? String(extension) : undefined,
      maxDepth: max_depth ? Number(max_depth) : 5,
    });
    return ok(files.join('\n') || 'No files found');
  },

  async stat_file({ path: filePath }) {
    try {
      const s = statFile(String(filePath));
      return ok(JSON.stringify(s, null, 2));
    } catch (e) { return err(String(e)); }
  },

  async list_directory({ path: dirPath, recursive }) {
    try {
      const entries = listDirectory(String(dirPath), Boolean(recursive), 3);
      return ok(entries.map(e => `${e.type === 'directory' ? 'd' : '-'} ${e.name}`).join('\n'));
    } catch (e) { return err(String(e)); }
  },

  // ── CVE / Security tools ──────────────────────────────────────────────────────
  async lookup_cve({ cve_id }) {
    const result = await lookupCVE(String(cve_id));
    if (!result) return err(`CVE not found: ${cve_id}`);
    return ok(`${result.cve_id} [${result.severity}] CVSS:${result.cvss_score}\n${result.description}\nPublished: ${result.published}`);
  },

  async search_cves({ keyword, max_results }) {
    const results = await searchCVEByKeyword(String(keyword), Number(max_results) || 10);
    if (results.length === 0) return ok('No CVEs found for that keyword.');
    return ok(results.map(r => `${r.cve_id} [${r.severity}/${r.cvss_score}] ${r.description.slice(0, 120)}`).join('\n'));
  },

  async scan_web_security({ url, authorized }) {
    if (authorized !== 'yes') return err('Authorization required. Set authorized="yes" for systems you own.');
    const findings = await scanWebApp(String(url), true);
    const report = generateVulnReport(findings, String(url), 'Web Security Scan');
    return ok(report);
  },

  async scan_paths({ url, authorized, custom_paths }) {
    if (authorized !== 'yes') return err('Authorization required.');
    const customPaths = custom_paths ? String(custom_paths).split(',').map(s => s.trim()) : undefined;
    const results = await scanPaths(String(url), true, customPaths);
    if (results.length === 0) return ok('No accessible paths found.');
    return ok(results.map(r => `[${r.status}] ${r.url}${r.title ? ` — ${r.title}` : ''}`).join('\n'));
  },

  async test_xss({ url, param, authorized }) {
    if (authorized !== 'yes') return err('Authorization required.');
    const result = await testXSS(String(url), String(param), true);
    return ok(result.vulnerable
      ? `VULNERABLE to XSS!\nPayload: ${result.payload}\nEvidence: ${result.evidence}`
      : 'Not vulnerable to XSS (tested common payloads)');
  },

  async test_sqli({ url, param, authorized }) {
    if (authorized !== 'yes') return err('Authorization required.');
    const result = await testSQLi(String(url), String(param), true);
    return ok(result.vulnerable
      ? `VULNERABLE to SQL injection!\nType: ${result.type}\nEvidence: ${result.evidence}`
      : 'Not vulnerable to SQLi (tested common payloads)');
  },

  async check_ssl({ host, port }) {
    const result = checkSSL(String(host), Number(port) || 443);
    return ok(`SSL/TLS for ${result.host}:${Number(port) || 443}
Valid: ${result.valid}
Subject: ${result.subject}
Issuer: ${result.issuer}
Expires: ${result.validTo} (${result.daysRemaining} days)
Warnings: ${result.warnings.join(', ') || 'none'}`);
  },

  async scan_wifi({ authorized }) {
    if (authorized !== 'yes') return err('Authorization required.');
    const networks = scanWiFiNetworks(true);
    if (networks.length === 0) return ok('No WiFi networks found (may need root or nmcli).');
    return ok(networks.map(n => `${n.ssid} | ${n.bssid} | ch${n.channel} | ${n.signal}% | ${n.encryption}`).join('\n'));
  },

  // ── Threat intelligence ───────────────────────────────────────────────────────
  async check_ip_reputation({ ip }) {
    const result = await checkIPReputation(String(ip));
    return ok(`IP: ${result.indicator}\nMalicious: ${result.isMalicious}\nReputation score: ${result.reputation}\nFindings: ${result.findings.join(', ')}`);
  },

  async analyze_domain({ domain }) {
    const result = await analyzeDomain(String(domain));
    return ok(`Domain: ${result.indicator}\nMalicious: ${result.isMalicious}\nFindings:\n${result.findings.join('\n')}`);
  },

  async check_file_hash({ hash, type }) {
    const result = await analyzeFileHash(String(hash), (type as 'md5' | 'sha1' | 'sha256') || 'sha256');
    return ok(`Hash: ${result.indicator}\nMalicious: ${result.isMalicious}\nFindings: ${result.findings.join(', ')}`);
  },

  async osint_gather({ target, type }) {
    const result = await gatherOSINT(String(target), (type as 'person' | 'company' | 'domain' | 'username') || 'domain');
    const lines = result.findings.map(f => `[${f.source}] ${f.data}`);
    return ok(`OSINT: ${result.target} (${result.type})\n${lines.join('\n') || 'No findings'}`);
  },

  // ── System metrics & task scheduler (from AIA) ────────────────────────────────
  async system_metrics(_args) {
    const metrics = getSystemMetrics();
    return ok(`CPU: ${metrics.cpu}\nMemory: ${metrics.memory}\nDisk: ${metrics.disk}`);
  },

  async get_weather({ city }) {
    const result = await fetchWeather(String(city || 'London'));
    return ok(result);
  },

  async schedule_task_runner({ name, delay_minutes, command }) {
    const runAt = new Date(Date.now() + Number(delay_minutes) * 60 * 1000);
    const id = scheduleTask(String(name), runAt, () => {
      cp.exec(String(command));
    });
    return ok(`Task scheduled: ${id}\nName: ${name}\nRuns at: ${runAt.toLocaleString()}\nCommand: ${command}`);
  },

  async list_scheduled_tasks(_args) {
    const tasks = listScheduledTasks();
    if (tasks.length === 0) return ok('No scheduled tasks.');
    return ok(tasks.map(t => `${t.id}: ${t.name} @ ${t.runAt}`).join('\n'));
  },

  // ── AI vision (Gemini) ────────────────────────────────────────────────────────
  async analyze_image_gemini({ image_path, prompt, keep_file }) {
    const p = String(image_path);
    if (!fs.existsSync(p)) return err(`Image file not found: ${p}`);

    const imageBuffer = fs.readFileSync(p);
    if (keep_file !== 'true' && p.startsWith('/tmp/')) {
      try { fs.unlinkSync(p); } catch { /* ignore */ }
    }
    if (imageBuffer.length < 100) return err(`Image file is empty: ${p}`);

    const ext = path.extname(p).toLowerCase().slice(1);
    const mimeMap: Record<string, string> = { jpg: 'image/jpeg', jpeg: 'image/jpeg', png: 'image/png', gif: 'image/gif', webp: 'image/webp' };
    const mime = mimeMap[ext] || 'image/png';
    const base64 = imageBuffer.toString('base64');
    const task = String(prompt || 'Describe this image in detail.');

    return ok(`__IMG__${mime}__${base64}__ENDIMG__\nTask: ${task}`);
  },

  async analyze_screenshot_gemini({ prompt }) {
    const screenshotPath = `/tmp/devin_screen_${Date.now()}.png`;
    const shotResult = automate('screenshot', { path: screenshotPath }, 20000);
    if (shotResult.isError) {
      return err(`Screenshot capture failed: ${shotResult.content}`);
    }
    if (!fs.existsSync(screenshotPath)) {
      return err(`Screenshot file not written to ${screenshotPath}. Capture may have failed silently.`);
    }

    const imageBuffer = fs.readFileSync(screenshotPath);
    try { fs.unlinkSync(screenshotPath); } catch { /* ignore */ }

    if (imageBuffer.length < 500) {
      return err(`Screenshot is empty (${imageBuffer.length} bytes) — Wayland capture may have failed.`);
    }

    const base64 = imageBuffer.toString('base64');
    const task = String(prompt || 'What do you see on screen? Describe ALL visible windows, applications, text content, buttons, terminal output, URLs, and UI elements with their positions.');

    // Embed inline — Gemini will analyze it in the same API call (no extra quota)
    return ok(`__IMG__image/png__${base64}__ENDIMG__\nTask: ${task}`);
  },

  async generate_code_gemini({ description, language, context }) {
    const code = await generateCode(String(description), String(language || 'python'), context ? String(context) : undefined);
    return ok(code);
  },

  async jarvis_speak_text({ text }) {
    await jarvisSpeak(String(text));
    return ok(`Spoken: "${String(text).slice(0, 80)}"`);
  },

  async jarvis_command({ command }) {
    const parsed = parseJarvisCommand(String(command));
    const result = await executeJarvisCommand(parsed);
    return ok(result);
  },

  // ── Integration Hub — routes to any of the 24 integrated repos ───────────────
  async hub_dispatch({ tool, args: hubArgs }) {
    const payload = JSON.stringify({ action: 'hub_dispatch', args: { tool: String(tool), args: hubArgs || {} } });
    return runPython(`
import sys, json
sys.path.insert(0, '${DEVIN_ROOT}/modules')
from integration_hub import get_hub
hub = get_hub()
result = hub.dispatch(${JSON.stringify(String(tool))}, ${JSON.stringify(hubArgs || {})})
print(result)
`);
  },

  async hub_status() {
    return runPython(`
import sys
sys.path.insert(0, '${DEVIN_ROOT}/modules')
from integration_hub import get_hub
print(get_hub().status())
`);
  },

  async soc_click({ description }) {
    return runPython(`
import sys
sys.path.insert(0, '${DEVIN_ROOT}/modules')
from integration_hub import get_hub
hub = get_hub()
result = hub.soc.ai_click_element(${JSON.stringify(String(description))})
print(result)
`);
  },

  async system_metrics_hub() {
    return runPython(`
import sys
sys.path.insert(0, '${DEVIN_ROOT}/modules')
from integration_hub import get_hub
hub = get_hub()
metrics = hub.monitor.get_metrics()
print(hub.monitor.format_metrics(metrics))
`);
  },

  async ai_operate({ objective, model }) {
    return runPython(`
import sys
sys.path.insert(0, '${DEVIN_ROOT}/modules')
from integration_hub import get_hub
hub = get_hub()
results = hub.soc.operate(${JSON.stringify(String(objective))}, ${JSON.stringify(String(model || 'gemini'))})
for r in results: print(r)
`, undefined);
  },
};

export async function executeTool(
  name: string,
  args: Record<string, unknown>,
  config: Config
): Promise<ToolResult> {
  const fn = tools[name];
  if (!fn) return err(`Unknown tool: ${name}`);
  try {
    return await fn(args, config);
  } catch (e) {
    return err(`Tool ${name} threw: ${e}`);
  }
}
