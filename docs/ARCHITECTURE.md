# Devin 4.0 Architecture

**Last Updated:** 2026-09-24
**Status:** CURRENT — Unified agent.py runtime

---

## Overview

Devin 4.0 is a unified, OS-controlling agentic AI CLI. The single entry point is `agent.py`,
invoked via the `./devin` shell script. It provides a Claude Code-style conversational interface
powered by any of three AI providers: Gemini, Claude (Anthropic), or OpenAI.

```
User (CLI)
    │
    ▼
./devin → agent.py (REPL / one-shot)
    │
    ▼
┌─────────────────────────────────────────┐
│         AI PROVIDER LAYER               │
│  GeminiProvider │ ClaudeProvider │      │
│  OpenAIProvider │ (auto-fallback) │     │
└───────────────────┬─────────────────────┘
                    │ tool calls
                    ▼
┌─────────────────────────────────────────┐
│           TOOL REGISTRY (~85 tools)     │
│                                         │
│  reasoning  web  shell  files  vision   │
│  mouse  keyboard  windows  apps         │
│  browser  clipboard  voice  memory      │
│  system  network  data  code  git       │
│  integrations  notes  control           │
└───────────────────┬─────────────────────┘
                    │ dispatch
                    ▼
┌─────────────────────────────────────────┐
│         MODULE INTEGRATION LAYER        │
│                                         │
│  modules/voice.py          (TTS/STT)    │
│  modules/os_automation.py  (OS control) │
│  modules/browser.py        (Selenium)   │
│  modules/persistent_memory.py           │
│  modules/messaging_gateway.py           │
│  modules/integration_hub.py (24 repos)  │
│  modules/system_monitor.py              │
│  modules/cheetahclaws_bridge.py         │
│  + 95 other modules/                    │
└───────────────────┬─────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│           OS / ENVIRONMENT              │
│  filesystem  shell  GUI  browser        │
│  applications  network  clipboard       │
└─────────────────────────────────────────┘
```

## Entry Points

| Command | Description |
|---------|-------------|
| `./devin` | Primary launcher — loads .env, runs agent.py |
| `python3 agent.py` | Direct Python execution |
| `python3 agent.py "task"` | One-shot task mode |
| `python3 agent.py --provider claude "task"` | Specify provider |
| `python3 agent.py --model gemini-2.5-pro` | Specify model |

## Core Components

### agent.py (~3000 lines)
The single unified entry point. Contains:
- **AI Providers**: GeminiProvider, ClaudeProvider, OpenAIProvider
- **Tool functions**: ~85 tools covering all OS capabilities
- **Tool registry**: TOOLS dict with schemas for all providers
- **Agentic loop**: `run_agent()` — observe/plan/act/verify/complete
- **REPL**: `repl()` — interactive conversational interface
- **Module loader**: Graceful loading of all modules/

### modules/ (103 files)
Domain-specific capability modules:
- `voice.py` — TTS (espeak/pyttsx3) + STT (SpeechRecognition/Whisper)
- `os_automation.py` — pyautogui, xdotool, pynput OS control
- `browser.py` — Selenium, Playwright browser automation
- `persistent_memory.py` — SQLite-backed long-term memory
- `messaging_gateway.py` — Telegram, Discord, Slack
- `integration_hub.py` — Bridge to 24 external repos
- `system_monitor.py` — psutil CPU/RAM/disk/network
- `cheetahclaws_bridge.py` — Token tracking, compaction
- `keyboard_mouse_control.py` — Low-level pynput control
- `code_execution.py` — Sandboxed code execution
- `cloud_integration_module.py` — AWS, Azure, GCP
- `ollama_module.py` — Local LLM via Ollama
- `scheduler.py` — Task scheduling
- `encryption_tools.py` — Cryptography utilities

### external/ (24 repos)
Cloned external repositories providing additional capabilities:
- AIA — Advanced Intelligence Architecture
- Devin, Devin-2.0, Devin-3.0 — Earlier versions
- cheetahclaws — Multi-provider streaming agent
- claude-code, claude-code-source — Claude Code reference
- gemini-cli — Gemini CLI reference
- Jarvis, JARVIS-microsoft — Personal assistant patterns
- OpenDevin — Open DevIn reference
- self-operating-computer — Vision-guided clicking
- hackability, vulnerability-analysis — Security tools
- shannon — Additional AI capabilities
- hexstrike-ai — Security assessment
- openclaw — AI assistant patterns
- airgorah — WiFi security
- metasploit-framework, nishang, Responder, PowerTools — Security research
- Holomat — Mixed reality
- moltbots.github.io — Multi-agent patterns

### src/ (TypeScript)
TypeScript source for the original CLI (now superseded by agent.py):
- `src/memory/compaction.ts` — Token estimation, context management
- `src/integrations/gemini_cli_integration.ts` — Gemini API integration

## AI Provider Details

### GeminiProvider
- Models: gemini-3.6-flash (default), gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash, gemini-1.5-flash
- Auth: Traditional `?key=` param (AIzaSy* keys) or `X-goog-api-key` header (AQ.* keys)
- Fallback: Automatic model fallback chain on 404/503
- Retries: 503 (high demand) with 5s×attempt backoff

### ClaudeProvider
- Models: claude-sonnet-4-6 (default), any claude-* model
- Auth: `x-api-key` header + `anthropic-version`
- Retries: 429/529 with 4s×attempt backoff

### OpenAIProvider
- Models: gpt-4o-mini (default), gpt-4o, o3, o4-mini
- Auth: `Authorization: Bearer` header
- Retries: 429 with 4s×attempt backoff

## Agentic Loop

```
task input
    │
    ▼
run_agent(task, provider)
    │
    ├── [conv mode] append to conv_messages (persistent history)
    │
    ▼
while step < max_steps:
    │
    ├── provider.call(messages, system=SYSTEM_PROMPT)
    │   ├── [error] exponential backoff, up to MAX_ERRORS=5
    │   └── [success] text + tool_calls
    │
    ├── print assistant text
    │
    ├── for each tool_call:
    │   ├── _dispatch_tool(name, args)
    │   ├── print tool result
    │   └── append to messages
    │
    ├── [task_complete called] → return result
    ├── [no tool calls] → return text (conv mode)
    └── continue
```

## Security Model

- No API keys in source code — all from .env
- Security modules (vulnerability-analysis, metasploit, etc.) are source-preserved but NOT autonomously invoked
- Destructive operations require explicit user confirmation
- Permission boundaries enforced per tool category
- No credentials stored in memory or logged

## Platform Support

| Feature | Linux | macOS | Windows |
|---------|-------|-------|---------|
| Shell execution | ✓ | ✓ | ✓ |
| File operations | ✓ | ✓ | ✓ |
| Web/HTTP | ✓ | ✓ | ✓ |
| Mouse/keyboard (pyautogui) | ✓ | ✓ | ✓ |
| Mouse/keyboard (xdotool) | ✓ | ✗ | ✗ |
| Screenshot (scrot) | ✓ | ✗ | ✗ |
| Screenshot (pyautogui) | ✓ | ✓ | ✓ |
| Voice TTS (espeak) | ✓ | ✗ | ✗ |
| Voice TTS (say) | ✗ | ✓ | ✗ |
| Browser (Selenium) | ✓ | ✓ | ✓ |
| Clipboard (xclip) | ✓ | ✗ | ✗ |
| Clipboard (pbcopy) | ✗ | ✓ | ✗ |
