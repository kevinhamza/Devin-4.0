// src/voice/index.ts — Voice input/output for Devin AGI
// Speech-to-text via speech_recognition (Google), TTS via pyttsx3
// Adapted from AIA/modules/voice_assistant.py patterns

import * as cp from 'child_process';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';

const DEVIN_ROOT = path.join(__dirname, '../..');
const VENV_PYTHON = path.join(DEVIN_ROOT, 'venv/bin/python3');
const PYTHON = fs.existsSync(VENV_PYTHON) ? VENV_PYTHON : 'python3';

function runPy(code: string, timeout = 30000): string {
  const tmp = path.join(os.tmpdir(), `devin_voice_${Date.now()}.py`);
  fs.writeFileSync(tmp, code);
  try {
    return cp.execSync(`"${PYTHON}" "${tmp}"`, { timeout, encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'], env: { ...process.env, PYTHONUNBUFFERED: '1' }
    }).trim();
  } catch (e: unknown) {
    const ex = e as { stdout?: string; stderr?: string };
    return [ex.stdout, ex.stderr].filter(Boolean).join('\n').trim();
  } finally {
    try { fs.unlinkSync(tmp); } catch { /* ignore */ }
  }
}

// ── Text-to-speech ────────────────────────────────────────────────────────────

export function speak(text: string, rate = 165, voice?: string): string {
  const code = `
import pyttsx3, sys
engine = pyttsx3.init()
engine.setProperty('rate', ${rate})
engine.setProperty('volume', 0.9)
${voice ? `voices = engine.getProperty('voices')
for v in voices:
    if '${voice}'.lower() in v.name.lower():
        engine.setProperty('voice', v.id)
        break` : ''}
engine.say("""${text.replace(/"/g, '\\"').replace(/\\/g, '\\\\')}""")
engine.runAndWait()
print("OK")
`;
  return runPy(code, 20000);
}

export function listVoices(): string {
  return runPy(`
import pyttsx3
engine = pyttsx3.init()
for v in engine.getProperty('voices'):
    print(f"{v.name} | {v.id} | {v.languages}")
`, 10000);
}

// ── Speech-to-text ────────────────────────────────────────────────────────────

export function listenOnce(timeoutSeconds = 8): string {
  return runPy(`
import speech_recognition as sr
r = sr.Recognizer()
r.energy_threshold = 300
r.dynamic_energy_threshold = True
try:
    with sr.Microphone() as src:
        r.adjust_for_ambient_noise(src, duration=0.5)
        print("Listening...", flush=True)
        audio = r.listen(src, timeout=${timeoutSeconds}, phrase_time_limit=15)
    text = r.recognize_google(audio)
    print(text)
except sr.WaitTimeoutError:
    print("TIMEOUT")
except sr.UnknownValueError:
    print("UNCLEAR")
except Exception as e:
    print(f"ERROR:{e}")
`, (timeoutSeconds + 5) * 1000);
}

export function listenLoop(onTranscript: (text: string) => void, stopSignal: { stop: boolean }): void {
  const code = `
import speech_recognition as sr, sys, time
r = sr.Recognizer()
r.energy_threshold = 300
r.dynamic_energy_threshold = True
print("READY", flush=True)
while True:
    try:
        with sr.Microphone() as src:
            r.adjust_for_ambient_noise(src, duration=0.3)
            audio = r.listen(src, timeout=5, phrase_time_limit=15)
        text = r.recognize_google(audio)
        print(f"TRANSCRIPT:{text}", flush=True)
    except sr.WaitTimeoutError:
        print("IDLE", flush=True)
    except sr.UnknownValueError:
        print("UNCLEAR", flush=True)
    except Exception as e:
        print(f"ERROR:{e}", flush=True)
        time.sleep(1)
`;
  const tmp = path.join(os.tmpdir(), 'devin_listen.py');
  fs.writeFileSync(tmp, code);
  const child = cp.spawn(PYTHON, [tmp], {
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, PYTHONUNBUFFERED: '1' },
  });

  child.stdout?.on('data', (data: Buffer) => {
    for (const line of data.toString().split('\n')) {
      if (line.startsWith('TRANSCRIPT:')) {
        onTranscript(line.slice('TRANSCRIPT:'.length).trim());
      }
    }
  });

  const interval = setInterval(() => {
    if (stopSignal.stop) {
      child.kill();
      clearInterval(interval);
      try { fs.unlinkSync(tmp); } catch { /* ignore */ }
    }
  }, 500);
}

// ── Wake-word detection ────────────────────────────────────────────────────────

export function waitForWakeWord(wakeWord = 'hey devin', timeoutMs = 60000): string {
  return runPy(`
import speech_recognition as sr, sys
r = sr.Recognizer()
wake = "${wakeWord}".lower()
import time; start = time.time()
while time.time() - start < ${timeoutMs / 1000}:
    try:
        with sr.Microphone() as src:
            r.adjust_for_ambient_noise(src, duration=0.2)
            audio = r.listen(src, timeout=3, phrase_time_limit=5)
        text = r.recognize_google(audio).lower()
        if wake in text:
            print("WAKE_WORD_DETECTED")
            sys.exit(0)
    except: pass
print("TIMEOUT")
`, timeoutMs + 5000);
}
