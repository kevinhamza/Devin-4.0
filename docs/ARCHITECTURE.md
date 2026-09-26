# Devin-4.0 — Architecture

## Overview

Devin-4.0 is a fully autonomous OS-controlling AI agent. It can observe
a real computer screen, reason about what it sees, and operate the
machine through keyboard, mouse, and application automation — exactly
like a human user, but driven by LLM reasoning.

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interfaces                          │
│  REPL (./devin)  │  CLI (python3 agent.py)  │  API (main.py)   │
└─────────────┬───────────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────────┐
│                   Conversation / Reasoning Layer                │
│  conversation_engine.py  │  reasoning_engine.py                 │
│  (streaming chat, slash  │  (ReAct loop, chain-of-thought,      │
│   commands, memory)      │   tool dispatch, 20-step limit)      │
└─────────────┬───────────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────────┐
│                     LLM Provider Layer                          │
│  ClaudeProvider  GeminiProvider  OpenAIProvider                 │
│  HuggingFaceProvider (free-tier, HF_TOKEN)                      │
│  OllamaProvider  FreeClaudeProvider                             │
│  hf_enhanced_provider.py  (streaming, tool calling)             │
│                                                                 │
│  Auto-selection order: Claude → Gemini → OpenAI → HuggingFace  │
│  Override: DEVIN_PROVIDER env var                               │
└─────────────┬───────────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────────┐
│                     OS Abstraction Layer                        │
│  os_agent.py: observe → understand → plan → act → verify       │
│                                                                 │
│  Screenshot  Mouse        Keyboard    Window     Clipboard      │
│  PIL/mss/    pynput/      pynput/     wmctrl/    pyperclip/     │
│  scrot/      xdotool/     xdotool/    xdotool/   xclip/         │
│  screencap/  ctypes(Win)  ctypes(Win) Win32API   pbcopy         │
│  PowerShell  cliclick(Mac)AppleScript             PowerShell    │
└─────────────┬───────────────────────────────────────────────────┘
              │
┌─────────────▼───────────────────────────────────────────────────┐
│                    Capability Modules (modules/)                 │
│                                                                 │
│  system_monitor_enhanced.py  voice_engine.py  browser_agent.py │
│  hf_enhanced_provider.py     free_claude_provider.py            │
│  keyboard_mouse_control.py   hf_provider.py                     │
│  + 96 additional modules loaded via main.py discovery           │
└─────────────────────────────────────────────────────────────────┘
```

## Core Loop (OS Agent)

Every GUI task follows the observe → act → verify pattern:

```
1. OBSERVE  : take screenshot → pass to vision AI → get description
2. UNDERSTAND: parse description → identify target element
3. PLAN     : determine action sequence (click, type, scroll, etc.)
4. ACT      : execute action via pynput/xdotool/ctypes
5. VERIFY   : take new screenshot → confirm action succeeded
6. RETRY    : if verification fails, re-plan (max 3 retries)
```

## Module Dependency Graph

```
agent.py (runtime, 136 tools)
  └── modules/os_agent.py
        └── modules/keyboard_mouse_control.py (pynput)
  └── modules/reasoning_engine.py
        └── providers: anthropic, google-generativeai, openai, requests
  └── modules/conversation_engine.py
        └── modules/reasoning_engine.py
  └── modules/hf_enhanced_provider.py
        └── requests (HF Inference API)
  └── modules/free_claude_provider.py
        └── subprocess (free-claude-code node binary)
  └── modules/system_monitor_enhanced.py
        └── psutil, GPUtil
  └── modules/voice_engine.py
        └── pyttsx3 / gtts / espeak / say
        └── speech_recognition / openai-whisper / pyaudio
  └── modules/browser_agent.py
        └── playwright / selenium
        └── beautifulsoup4
  └── modules/cc_interface.py          [Phase 4]
        └── Claude Code-style terminal UI (banner, spinner, diff display)
  └── modules/voice_control.py         [Phase 4]
        └── TTS: pyttsx3→gTTS→espeak, STT: Whisper→SpeechRecognition
        └── WakeWordDetector, VoiceSession
  └── modules/os_controller.py         [Phase 4]
        └── 19 OS tools: mouse, keyboard, screenshot, clipboard, windows
        └── pyautogui (primary), pynput (fallback), xdotool (Linux)
  └── modules/autonomous_core.py       [Phase 4]
        └── LoopDetector, AutonomousRunner, goal decomposition
  └── modules/screen_vision.py         [Phase 4]
        └── OBSERVE→REASON→ACT→VERIFY GUI automation cycle
        └── run_vision_cycle(), observe(), _execute_action()
        └── OCR element finder (pytesseract), screen_wait_for()
```

## Provider Fallback Chain

```
Request arrives
    │
    ├─ ANTHROPIC_API_KEY set?  → ClaudeProvider (claude-opus-4-5)
    │
    ├─ GEMINI_API_KEY / GOOGLE_API_KEY set? → GeminiProvider (gemini-2.0-flash)
    │
    ├─ OPENAI_API_KEY set? → OpenAIProvider (gpt-4o)
    │
    ├─ HF_TOKEN / HUGGINGFACE_API_KEY set? → HuggingFaceProvider
    │   Free models (in order):
    │     1. Qwen/Qwen2.5-72B-Instruct
    │     2. meta-llama/Meta-Llama-3.1-70B-Instruct
    │     3. mistralai/Mixtral-8x7B-Instruct-v0.1
    │     4. mistralai/Mistral-7B-Instruct-v0.3
    │     5. HuggingFaceH4/zephyr-7b-beta
    │
    └─ No key? → FreeClaudeProvider (free-claude-code via node subprocess)

Override: DEVIN_PROVIDER=claude|gemini|openai|huggingface|ollama|free
```

## Vision Analysis Chain

When a screenshot needs AI vision analysis:

```
Screenshot path
    │
    ├─ GEMINI_API_KEY? → Gemini 2.0 Flash (multimodal)
    ├─ ANTHROPIC_API_KEY? → Claude Opus 4.5 (vision)
    ├─ OPENAI_API_KEY? → GPT-4o (vision)
    └─ HF_TOKEN? → HF Inference API (text description fallback)
```

## Cross-Platform Abstraction

```
Operation         Linux              macOS             Windows
─────────────────────────────────────────────────────────────────
Screenshot        PIL.ImageGrab /    PIL.ImageGrab /   PIL.ImageGrab /
                  mss / scrot /      mss /             mss /
                  gnome-screenshot   screencapture     PowerShell

Mouse click       pynput →           pynput →          pynput →
                  xdotool            cliclick           ctypes/Win32

Keyboard type     pynput →           pynput →          pynput →
                  xdotool            pynput             ctypes

Window list       wmctrl / xdotool   AppleScript        win32gui

Clipboard R/W     pyperclip →        pyperclip →       pyperclip →
                  xclip / xsel       pbcopy/pbpaste     win32clipboard

TTS               espeak / festival  say                System.Speech
```

## Memory Architecture

```
SQLite DB (_DB_PATH = ~/.devin/memory.db)
  ├── messages table: (id, role, content, timestamp, session_id)
  ├── facts table:    (id, key, value, timestamp)
  └── sessions table: (id, created_at, summary)

Session history: ConversationEngine.history (in-memory, last N turns)
Context limit:   max_history_tokens * 4 chars ≈ 32k chars
```

## Module Loading (main.py)

`main.py` uses `importlib` to dynamically discover and import every
`.py` file from 30+ directories, ensuring no capability is missed:

```
SCAN_DIRS = [
  "modules/", "scripts/", "tools/", "AI-APIs/", "cloud/",
  "integrations/", "plugins/", "utils/", "services/",
  "automation/", "analysis/", "communication/", ...
]
```

Each file is imported with `except BaseException` — deliberate, so
pyo3 panics and ImportErrors don't abort the whole startup.

## Phase 4 — Autonomous Enhancement Modules

Added in Phase 4: five modules that transform Devin from a tool-calling
agent into a fully autonomous OS-controlling system.

### screen_vision.py — OBSERVE→REASON→ACT→VERIFY Loop

```
run_vision_cycle(goal, ai_call_fn)
    │
    ├─ OBSERVE  : take_screenshot() → ObservationFrame(path, w, h, description)
    │
    ├─ UNDERSTAND: build_vision_prompt(goal, frame, step, history)
    │              → send to AI provider → get action JSON
    │
    ├─ ACT      : _parse_ai_action_response(ai_response) → ScreenAction
    │              → _execute_action(action) [click/type/key/scroll/wait/done/fail]
    │
    ├─ VERIFY   : time.sleep(step_delay) → next OBSERVE cycle
    │
    └─ COMPLETE : action_type=DONE → VisionCycle(completed=True)
                  action_type=FAIL → VisionCycle(failed=True, reason=...)
                  step > max_steps → VisionCycle(failed=True, reason='timeout')
```

Tool exports registered in TOOLS:
- `screen_observe(save_path?)` — one-shot screenshot + description
- `screen_find_element(description)` — OCR-based element location
- `screen_click_element(description)` — find + click by text
- `screen_wait_for(description, timeout)` — poll until element appears
- `screen_status()` — capability check

### os_controller.py — Full OS Control (19 tools)

All tools registered as `os_*` prefixed entries in TOOLS dict:
`os_mouse_move`, `os_mouse_click`, `os_mouse_double_click`, `os_mouse_right_click`,
`os_mouse_drag`, `os_mouse_scroll`, `os_get_mouse_pos`, `os_keyboard_type`,
`os_keyboard_press`, `os_keyboard_hotkey`, `os_screenshot`, `os_clipboard_get`,
`os_clipboard_set`, `os_get_active_window`, `os_list_windows`, `os_focus_window`,
`os_launch_app`, `os_screen_info`, `os_click_on_text`

### cc_interface.py — Claude Code-style Terminal UI

`banner()`, `Spinner`, `render_markdown()`, `print_tool_call()`,
`print_file_edit()`, `print_diff()`, `confirm_action()`, `print_session_stats()`

### voice_control.py — Voice I/O

TTS: `pyttsx3` → `gTTS` (saves + plays) → `espeak` (subprocess fallback)
STT: `openai-whisper` → `SpeechRecognition` (Google) → manual fallback
`WakeWordDetector` for hands-free activation, `VoiceSession` high-level API

### autonomous_core.py — Planning Orchestrator

`classify_intent()` (code/web/os/file/query), `decompose_goal()` (subtask list),
`LoopDetector` (fingerprint, warn at 3x, inject correction at 5x),
`compact_messages()`, `AutonomousRunner` (full orchestration with retry)

## Security Boundary

```
Tool category    Default behavior
─────────────────────────────────────────
Safe             file, web, memory, math  → auto-execute
Caution          shell, mouse, keyboard   → execute + log output
Authorized only  nmap, sqlmap, burp       → require explicit user
                                            authorization in chat
Never            credential theft,        → refused at tool level
                 unauthorized targeting,
                 persistence, exfiltration
```

## Key Environment Variables

| Variable | Purpose |
|---|---|
| `HF_TOKEN` | HuggingFace free-tier API token |
| `ANTHROPIC_API_KEY` | Claude API key |
| `GEMINI_API_KEY` | Gemini / Google AI API key |
| `OPENAI_API_KEY` | OpenAI API key |
| `OLLAMA_BASE_URL` | Local Ollama endpoint |
| `CLAUDE_SESSION_KEY` | Free Claude session key |
| `DEVIN_PROVIDER` | Force specific provider |
| `DEVIN_MODEL` | Force specific model name |
| `DEVIN_DB_PATH` | SQLite memory DB path |

All credentials are read via `os.environ.get()` only.
No API keys are ever hardcoded in source files.
