// src/integrations/jarvis_integration.ts — Jarvis AI assistant integration
// Ported from external/Jarvis/jarvis.py and tools.py
// Provides wake-word detection, TTS, weather, image search, Spotify control

import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

const DEVIN_ROOT = path.join(__dirname, '../..');

// ── Wake-word detection (from Jarvis/jarvis.py) ───────────────────────────────

export interface WakeWordOptions {
  wakeWord?: string;
  timeoutMs?: number;
  sensitivity?: number;
}

export function waitForWakeWord(opts: WakeWordOptions = {}): Promise<boolean> {
  const { wakeWord = 'hey devin', timeoutMs = 30000, sensitivity = 0.6 } = opts;
  return new Promise((resolve) => {
    const code = `
import speech_recognition as sr, sys
r = sr.Recognizer()
r.energy_threshold = 300
m = sr.Microphone()
with m as source:
    r.adjust_for_ambient_noise(source, duration=0.5)
    try:
        audio = r.listen(source, timeout=10, phrase_time_limit=5)
        text = r.recognize_google(audio).lower()
        if "${wakeWord.toLowerCase()}" in text:
            print("DETECTED")
        else:
            print("NOT_DETECTED:" + text)
    except:
        print("TIMEOUT")
`;
    let out = '';
    const child = cp.spawn('python3', ['-c', code]);
    child.stdout.on('data', (d: Buffer) => { out += d.toString(); });
    child.on('close', () => resolve(out.includes('DETECTED')));
    child.on('error', () => resolve(false));
    setTimeout(() => { child.kill(); resolve(false); }, timeoutMs + 5000);
  });
}

// ── TTS from Jarvis (jarvis.py TTS patterns) ──────────────────────────────────

export function jarvisSpeak(text: string): Promise<void> {
  return new Promise((resolve) => {
    const code = `
import pyttsx3
engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('rate', 180)
engine.setProperty('volume', 1.0)
engine.say("""${text.replace(/"""/g, "'''")}""")
engine.runAndWait()
`;
    cp.exec(`python3 -c '${code}'`, { env: { ...process.env, DISPLAY: ':0' } },
      () => resolve());
  });
}

// ── Command dispatcher (from Jarvis/tools.py parse_command) ───────────────────

export interface JarvisCommand {
  intent: string;
  args: string[];
  raw: string;
}

export function parseJarvisCommand(command: string): JarvisCommand {
  const lower = command.toLowerCase().trim();

  if (lower.includes('weather')) {
    const cityMatch = lower.match(/weather\s+(?:in|for|at)?\s*(.+)/);
    return { intent: 'weather', args: [cityMatch?.[1]?.trim() || 'London'], raw: command };
  }
  if (lower.includes('search') || lower.includes('find image')) {
    const query = lower.replace(/search|find image|image/g, '').trim();
    return { intent: 'image_search', args: [query], raw: command };
  }
  if (lower.includes('play music') || lower.includes('play spotify')) {
    return { intent: 'spotify_play', args: [], raw: command };
  }
  if (lower.includes('pause') || lower.includes('stop music')) {
    return { intent: 'spotify_pause', args: [], raw: command };
  }
  if (lower.includes('next') || lower.includes('skip')) {
    return { intent: 'spotify_next', args: [], raw: command };
  }
  if (lower.includes('previous') || lower.includes('back')) {
    return { intent: 'spotify_prev', args: [], raw: command };
  }
  if (lower.includes('volume up')) {
    return { intent: 'volume_up', args: [], raw: command };
  }
  if (lower.includes('volume down')) {
    return { intent: 'volume_down', args: [], raw: command };
  }
  if (lower.includes('time') || lower.includes("what's the time")) {
    return { intent: 'tell_time', args: [], raw: command };
  }
  if (lower.includes('date') || lower.includes("what's today")) {
    return { intent: 'tell_date', args: [], raw: command };
  }
  if (lower.includes('open ')) {
    const app = lower.replace('open ', '').trim();
    return { intent: 'open_app', args: [app], raw: command };
  }
  return { intent: 'unknown', args: [], raw: command };
}

export async function executeJarvisCommand(command: JarvisCommand): Promise<string> {
  switch (command.intent) {
    case 'weather': {
      const city = command.args[0] || 'London';
      try {
        const result = cp.execSync(
          `curl -s "https://wttr.in/${encodeURIComponent(city)}?format=3"`,
          { encoding: 'utf8', timeout: 8000 }
        ).trim();
        return result || `Weather for ${city}: unavailable`;
      } catch {
        return `Could not fetch weather for ${city}`;
      }
    }
    case 'tell_time':
      return `Current time: ${new Date().toLocaleTimeString()}`;
    case 'tell_date':
      return `Today is: ${new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}`;
    case 'volume_up':
      cp.exec('DISPLAY=:0 pactl set-sink-volume @DEFAULT_SINK@ +10%');
      return 'Volume up';
    case 'volume_down':
      cp.exec('DISPLAY=:0 pactl set-sink-volume @DEFAULT_SINK@ -10%');
      return 'Volume down';
    case 'open_app':
      cp.exec(`DISPLAY=:0 ${command.args[0]} &`);
      return `Opening ${command.args[0]}`;
    case 'spotify_play':
      cp.exec('dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Play');
      return 'Playing music';
    case 'spotify_pause':
      cp.exec('dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Pause');
      return 'Music paused';
    case 'spotify_next':
      cp.exec('dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Next');
      return 'Skipped to next track';
    case 'spotify_prev':
      cp.exec('dbus-send --print-reply --dest=org.mpris.MediaPlayer2.spotify /org/mpris/MediaPlayer2 org.mpris.MediaPlayer2.Player.Previous');
      return 'Went to previous track';
    default:
      return `Unknown command: ${command.raw}`;
  }
}

// ── Jarvis conversation loop (from Jarvis/jarvis.py main loop) ────────────────

export interface JarvisLoopOptions {
  wakeWord?: string;
  onResponse?: (text: string) => void;
  maxTurns?: number;
}

export async function runJarvisLoop(
  opts: JarvisLoopOptions,
  handleQuery: (query: string) => Promise<string>
): Promise<void> {
  const { wakeWord = 'hey devin', onResponse, maxTurns = 100 } = opts;
  let turns = 0;

  while (turns < maxTurns) {
    turns++;

    // Wait for wake word
    const detected = await waitForWakeWord({ wakeWord, timeoutMs: 60000 });
    if (!detected) continue;

    await jarvisSpeak("Yes? How can I help?");

    // Listen for command
    const code = `
import speech_recognition as sr
r = sr.Recognizer()
m = sr.Microphone()
with m as source:
    r.adjust_for_ambient_noise(source, duration=0.3)
    audio = r.listen(source, timeout=8, phrase_time_limit=15)
print(r.recognize_google(audio))
`;
    let command = '';
    try {
      command = cp.execSync(`python3 -c '${code}'`, { encoding: 'utf8', timeout: 20000 }).trim();
    } catch {
      await jarvisSpeak("Sorry, I didn't catch that.");
      continue;
    }

    const parsed = parseJarvisCommand(command);
    let response: string;

    if (parsed.intent !== 'unknown') {
      response = await executeJarvisCommand(parsed);
    } else {
      response = await handleQuery(command);
    }

    if (onResponse) onResponse(response);
    await jarvisSpeak(response.slice(0, 500));
  }
}
