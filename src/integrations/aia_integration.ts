// src/integrations/aia_integration.ts — AIA (Artificial Intelligence Agent) integration
// Ported from external/AIA/modules/: automation.py, device_control.py, voice_assistant.py
// Provides task scheduling, OS device control, voice interaction

import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

const DEVIN_ROOT = path.join(__dirname, '../..');
const AIA_DIR = path.join(DEVIN_ROOT, 'external/AIA');

// ── Task Scheduler (from AIA/modules/automation.py) ───────────────────────────

export interface ScheduledTask {
  id: string;
  name: string;
  runAt: Date;
  action: () => void;
  timer?: ReturnType<typeof setTimeout>;
}

const scheduledTasks = new Map<string, ScheduledTask>();

export function scheduleTask(name: string, runAt: Date, action: () => void): string {
  const id = `task_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
  const delayMs = runAt.getTime() - Date.now();
  if (delayMs <= 0) throw new Error('Scheduled time must be in the future.');
  const timer = setTimeout(() => {
    action();
    scheduledTasks.delete(id);
    logTaskExecution(name);
  }, delayMs);
  const task: ScheduledTask = { id, name, runAt, action, timer };
  scheduledTasks.set(id, task);
  return id;
}

export function cancelTask(id: string): boolean {
  const task = scheduledTasks.get(id);
  if (!task) return false;
  if (task.timer) clearTimeout(task.timer);
  scheduledTasks.delete(id);
  return true;
}

export function listScheduledTasks(): { id: string; name: string; runAt: string }[] {
  return [...scheduledTasks.values()].map(t => ({
    id: t.id,
    name: t.name,
    runAt: t.runAt.toISOString(),
  }));
}

function logTaskExecution(taskName: string): void {
  const logDir = path.join(DEVIN_ROOT, 'logs');
  if (!fs.existsSync(logDir)) fs.mkdirSync(logDir, { recursive: true });
  const logFile = path.join(logDir, 'task_execution.log');
  const line = `${new Date().toISOString()} - Executed task: ${taskName}\n`;
  fs.appendFileSync(logFile, line);
}

// ── Action sequence runner (from AIA/modules/automation.py create_task_automation) ──

export async function runActionSequence(
  taskName: string,
  actions: Array<() => Promise<void> | void>
): Promise<void> {
  for (const action of actions) {
    await action();
  }
  logTaskExecution(taskName);
}

// ── Device Control (from AIA/modules/device_control.py) ───────────────────────

function runPyAutogui(code: string): string {
  try {
    return cp.execSync(
      `DISPLAY=:0 python3 -c "${code.replace(/"/g, '\\"')}"`,
      { encoding: 'utf8', timeout: 10000 }
    ).trim();
  } catch (e: unknown) {
    return String((e as Error).message || e).slice(0, 200);
  }
}

export function moveMouse(x: number, y: number): void {
  runPyAutogui(`import pyautogui; pyautogui.moveTo(${x}, ${y})`);
}

export function clickMouse(x: number, y: number): void {
  runPyAutogui(`import pyautogui; pyautogui.click(${x}, ${y})`);
}

export function scrollMouse(direction: 'up' | 'down', amount = 10): void {
  const amt = direction === 'up' ? amount : -amount;
  runPyAutogui(`import pyautogui; pyautogui.scroll(${amt})`);
}

export function takeScreenshot(savePath: string): string {
  runPyAutogui(`import pyautogui; pyautogui.screenshot("${savePath}")`);
  return savePath;
}

export function openApplicationAIA(appName: string): string {
  try {
    cp.execSync(`DISPLAY=:0 ${appName} &`, { timeout: 3000 });
    return `Opened: ${appName}`;
  } catch {
    try {
      cp.execSync(`DISPLAY=:0 xdg-open "${appName}"`, { timeout: 5000 });
      return `Opened via xdg-open: ${appName}`;
    } catch (e) {
      return `Error: ${String(e).slice(0, 100)}`;
    }
  }
}

export function getScreenSize(): { width: number; height: number } {
  const out = runPyAutogui('import pyautogui; s=pyautogui.size(); print(s.width,s.height)');
  const [w, h] = out.split(' ').map(Number);
  return { width: w || 1366, height: h || 768 };
}

export function closeApplicationByName(appName: string): string {
  try {
    cp.execSync(`pkill -f "${appName}"`, { timeout: 5000 });
    return `Closed: ${appName}`;
  } catch {
    return `Process not found or could not be killed: ${appName}`;
  }
}

export function shutdownSystem(): void {
  cp.execSync('sudo shutdown now');
}

export function restartSystem(): void {
  cp.execSync('sudo reboot');
}

export function lockScreen(): string {
  try {
    cp.execSync('DISPLAY=:0 xdg-screensaver lock || DISPLAY=:0 gnome-screensaver-command -l || loginctl lock-session');
    return 'Screen locked';
  } catch (e) {
    return `Lock failed: ${String(e).slice(0, 100)}`;
  }
}

// ── Process management (from AIA device_control: psutil wrappers) ──────────────

export function listProcesses(): string {
  return cp.execSync('ps aux --sort=-%cpu | head -20', { encoding: 'utf8' });
}

export function killProcess(pid: number): string {
  try {
    cp.execSync(`kill -9 ${pid}`);
    return `Killed PID ${pid}`;
  } catch (e) {
    return `Failed to kill PID ${pid}: ${String(e).slice(0, 100)}`;
  }
}

// ── System metrics (from AIA/modules/device_control.py) ──────────────────────

export function getSystemMetrics(): { cpu: string; memory: string; disk: string } {
  try {
    const cpu = cp.execSync("python3 -c \"import psutil; print(psutil.cpu_percent(interval=1))\"",
      { encoding: 'utf8', timeout: 5000 }).trim();
    const mem = cp.execSync("python3 -c \"import psutil; m=psutil.virtual_memory(); print(m.percent)\"",
      { encoding: 'utf8', timeout: 5000 }).trim();
    const disk = cp.execSync("python3 -c \"import psutil; d=psutil.disk_usage('/'); print(d.percent)\"",
      { encoding: 'utf8', timeout: 5000 }).trim();
    return { cpu: cpu + '%', memory: mem + '%', disk: disk + '%' };
  } catch {
    const uptime = cp.execSync('uptime', { encoding: 'utf8' }).trim();
    return { cpu: 'N/A', memory: 'N/A', disk: uptime };
  }
}

// ── Voice interaction (from AIA/modules/voice_assistant.py) ──────────────────

export function speakAIA(text: string, rate = 150): Promise<void> {
  return new Promise((resolve, reject) => {
    const code = `
import pyttsx3, sys
e = pyttsx3.init()
e.setProperty('rate', ${rate})
e.setProperty('volume', 0.9)
e.say(sys.argv[1])
e.runAndWait()
`;
    const child = cp.spawn('python3', ['-c', code, text], {
      env: { ...process.env, DISPLAY: ':0' },
    });
    child.on('close', (code) => code === 0 ? resolve() : reject(new Error(`TTS exited ${code}`)));
    child.on('error', reject);
  });
}

export function listenOnceAIA(timeoutSecs = 10): Promise<string> {
  return new Promise((resolve, reject) => {
    const code = `
import speech_recognition as sr
r = sr.Recognizer()
m = sr.Microphone()
with m as source:
    r.adjust_for_ambient_noise(source, duration=0.5)
    audio = r.listen(source, timeout=${timeoutSecs})
print(r.recognize_google(audio))
`;
    let out = '';
    const child = cp.spawn('python3', ['-c', code], {
      env: { ...process.env, DISPLAY: ':0' },
    });
    child.stdout.on('data', (d: Buffer) => { out += d.toString(); });
    child.on('close', () => resolve(out.trim()));
    child.on('error', reject);
    setTimeout(() => { child.kill(); resolve(out.trim()); }, (timeoutSecs + 3) * 1000);
  });
}

// ── Face detection (from AIA/modules/face_detection.py) ──────────────────────

export function detectFaces(imagePath: string): string {
  const code = `
import cv2, json
img = cv2.imread("${imagePath}")
if img is None:
    print(json.dumps({"faces": 0, "error": "Cannot open image"}))
else:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(gray, 1.1, 4)
    print(json.dumps({"faces": len(faces), "rects": faces.tolist() if len(faces) > 0 else []}))
`;
  try {
    return cp.execSync(`python3 -c '${code}'`, { encoding: 'utf8', timeout: 10000 }).trim();
  } catch (e) {
    return JSON.stringify({ faces: 0, error: String(e).slice(0, 100) });
  }
}

// ── Internet tasks (from AIA/modules/internet_tasks.py patterns) ─────────────

export function fetchWeather(city = 'London'): Promise<string> {
  return new Promise((resolve) => {
    try {
      const result = cp.execSync(
        `python3 -c "import urllib.request, json; r=urllib.request.urlopen('https://wttr.in/${encodeURIComponent(city)}?format=3'); print(r.read().decode())"`,
        { encoding: 'utf8', timeout: 10000 }
      ).trim();
      resolve(result);
    } catch {
      resolve(`Could not fetch weather for ${city}`);
    }
  });
}
