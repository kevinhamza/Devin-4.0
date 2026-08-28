// src/os/automation.ts — Real-user OS automation layer
// Delegates to modules/os_automation.py which uses pyautogui + xdotool + pynput
// Provides full mouse/keyboard/window/screenshot control like a real human user.

import * as cp from 'child_process';
import * as path from 'path';
import * as os from 'os';
import * as fs from 'fs';

const DEVIN_ROOT = path.join(__dirname, '../..');
const AUTOMATION_SCRIPT = path.join(DEVIN_ROOT, 'modules/os_automation.py');
// Use venv Python if available, otherwise system Python
const VENV_PY_UNIX = path.join(DEVIN_ROOT, 'venv/bin/python3');
const VENV_PY_WIN  = path.join(DEVIN_ROOT, 'venv/Scripts/python.exe');
const IS_WINDOWS   = process.platform === 'win32';

export type AutomationResult = { ok: boolean; result?: unknown; error?: string };

// ── Core dispatcher ──────────────────────────────────────────────────────────

export function runAutomation(action: string, args: Record<string, unknown> = {}, timeout = 15000): AutomationResult {
  const payload = JSON.stringify({ action, args });

  // Resolve Python interpreter: prefer venv, fall back to system Python
  let python: string;
  if (IS_WINDOWS) {
    python = fs.existsSync(VENV_PY_WIN) ? VENV_PY_WIN : 'python';
  } else {
    python = fs.existsSync(VENV_PY_UNIX) ? VENV_PY_UNIX : 'python3';
  }

  // Build command — on Linux ensure DISPLAY is set for any X11 sub-tools
  const escapedPayload = payload.replace(/'/g, "'\\''");
  const cmd = IS_WINDOWS
    ? `"${python}" "${AUTOMATION_SCRIPT}" "${payload.replace(/"/g, '\\"')}"`
    : `"${python}" "${AUTOMATION_SCRIPT}" '${escapedPayload}'`;

  const env: NodeJS.ProcessEnv = { ...process.env };
  if (process.platform === 'linux' && !env['DISPLAY']) {
    env['DISPLAY'] = ':0';
  }

  try {
    const out = cp.execSync(cmd, { timeout, encoding: 'utf8', stdio: ['pipe', 'pipe', 'pipe'], env });
    return JSON.parse(out.trim()) as AutomationResult;
  } catch (e: unknown) {
    const err = e as { stdout?: string; stderr?: string; message?: string };
    const raw = [err.stdout, err.stderr].filter(Boolean).join('\n').trim();
    try {
      return JSON.parse(raw) as AutomationResult;
    } catch {
      return { ok: false, error: err.message || String(e) };
    }
  }
}

function auto(action: string, args: Record<string, unknown> = {}, timeout = 15000): string {
  const r = runAutomation(action, args, timeout);
  if (!r.ok) return `Error: ${r.error}`;
  return String(r.result ?? 'OK');
}

// ── Screenshot ───────────────────────────────────────────────────────────────

export function takeScreenshot(savePath?: string, region?: [number, number, number, number]): string {
  const args: Record<string, unknown> = {};
  if (savePath) args.path = savePath;
  if (region) args.region = region;
  return auto('screenshot', args, 10000);
}

export function takeScreenshotBase64(): string {
  return auto('screenshot_b64', {}, 10000);
}

// ── Mouse ────────────────────────────────────────────────────────────────────

export function mouseMove(x: number, y: number, duration = 0.2): string {
  return auto('mouse_move', { x, y, duration });
}

export function mouseClick(x: number, y: number, button: 'left' | 'right' | 'middle' = 'left', double = false): string {
  return auto('mouse_click', { x, y, button, double });
}

export function mouseRightClick(x: number, y: number): string {
  return auto('mouse_right_click', { x, y });
}

export function mouseDrag(x1: number, y1: number, x2: number, y2: number, duration = 0.5): string {
  return auto('mouse_drag', { x1, y1, x2, y2, duration });
}

export function mouseScroll(x: number, y: number, direction: 'up' | 'down' = 'down', amount = 3): string {
  return auto('mouse_scroll', { x, y, direction, amount });
}

export function getMousePosition(): string {
  return auto('mouse_position');
}

// ── Keyboard ─────────────────────────────────────────────────────────────────

export function keyboardType(text: string, humanLike = true, interval = 0.03): string {
  return auto('type', { text, human_like: humanLike, interval });
}

export function keyboardHotkey(...keys: string[]): string {
  return auto('hotkey', { keys });
}

export function keyboardPress(key: string): string {
  return auto('press', { key });
}

// ── Applications ──────────────────────────────────────────────────────────────

export function openApplication(name: string, args?: string): string {
  return auto('open_app', { name, args }, 10000);
}

export function openUrl(url: string): string {
  return auto('open_url', { url }, 10000);
}

export function openFile(filePath: string): string {
  return auto('open_file', { path: filePath }, 10000);
}

export function openTerminal(): string {
  return auto('open_terminal', {}, 5000);
}

export function closeApplication(name: string): string {
  return auto('close_app', { name });
}

// ── Windows ───────────────────────────────────────────────────────────────────

export function listWindows(): string {
  return auto('list_windows');
}

export function focusWindow(name: string): string {
  return auto('focus_window', { name });
}

export function getActiveWindow(): string {
  return auto('active_window');
}

export function maximizeWindow(name?: string): string {
  return auto('maximize', name ? { name } : {});
}

export function minimizeWindow(): string {
  return auto('minimize');
}

export function altTab(times = 1): string {
  return auto('alt_tab', { times });
}

export function closeCurrentWindow(): string {
  return auto('close_window');
}

export function getScreenSize(): string {
  return auto('screen_size');
}

// ── Clipboard ─────────────────────────────────────────────────────────────────

export function clipboardGet(): string {
  return auto('clipboard_get');
}

export function clipboardSet(text: string): string {
  return auto('clipboard_set', { text });
}

export function copySelected(): string {
  return auto('copy');
}

export function paste(): string {
  return auto('paste');
}

// ── Composite real-user actions ───────────────────────────────────────────────

export function clickAndType(x: number, y: number, text: string, clearFirst = true): string {
  return auto('click_and_type', { x, y, text, clear: clearFirst });
}

export function searchAndOpenApp(name: string): string {
  return auto('search_open', { name }, 8000);
}

export function showDesktop(): string {
  return auto('show_desktop');
}

export function runCommandInTerminal(command: string): string {
  return auto('run_in_terminal', { command }, 10000);
}

export function findOnScreen(imagePath: string, confidence = 0.8): string {
  return auto('find_on_screen', { image: imagePath, confidence });
}

export function clickImage(imagePath: string, confidence = 0.8, double = false): string {
  return auto('click_image', { image: imagePath, confidence, double });
}

export function waitForImage(imagePath: string, timeout = 10): string {
  return auto('wait_for_image', { image: imagePath, timeout }, timeout * 1000 + 2000);
}

export function browserAutomate(url: string, actions?: unknown[]): string {
  return auto('browser_auto', { url, actions }, 30000);
}

export function openFileManager(dirPath?: string): string {
  return auto('open_file_manager', dirPath ? { path: dirPath } : {}, 8000);
}

export function volumeUp(steps = 5): string {
  return auto('volume_up', { steps });
}

export function volumeDown(steps = 5): string {
  return auto('volume_down', { steps });
}

export function volumeMute(): string {
  return auto('volume_mute');
}
