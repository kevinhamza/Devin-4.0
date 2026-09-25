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
