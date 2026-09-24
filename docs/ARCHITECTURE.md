# Devin 4.0 Architecture

**Last Updated:** 2026-09-24  
**Status:** CURRENT — Phase B+ (Core Runtime + OS Automation complete)

---

## Overview

Devin 4.0 is a multi-provider AI agent with real OS control, built on:
- **TypeScript CLI** (`src/`) — primary, full-featured, multi-provider
- **Python CLI** (`main.py`) — secondary, Gemini-native agentic loop
- **Python backend** (`modules/`) — OS automation, integrations, tool registry

### Entry Points

| Entry | Command | When to use |
|-------|---------|-------------|
| `./devin` | Bash launcher | Preferred — tries TS first, falls back to Python |
| `python main.py` | Python CLI | Direct Python mode, useful without Node.js |
| `npm start` | TS dev mode | Development |
| `node dist/cli.js` | TS production | After `npm run build` |

---

## Runtime Architecture

```
User Input (terminal or voice)
        │
        ▼
┌───────────────────────────────────────────┐
│          Entry Point                       │
│  TypeScript CLI (src/cli.ts)              │
│  or Python CLI (main.py)                  │
└─────────────────┬─────────────────────────┘
                  │
                  ▼
┌───────────────────────────────────────────┐
│          AI Provider Layer                 │
│  ┌─────────┐ ┌─────────┐ ┌────────────┐  │
│  │ Gemini  │ │ Claude  │ │ OpenAI/etc │  │
│  │(primary)│ │(fallback│ │ (fallback) │  │
│  └─────────┘ └─────────┘ └────────────┘  │
│  Auto-fallback on rate limit / error       │
└─────────────────┬─────────────────────────┘
                  │
                  ▼
┌───────────────────────────────────────────┐
│        Conversation + System Prompt        │
│  OBSERVE → UNDERSTAND → PLAN → ACT →      │
│  VERIFY → CONTINUE → COMPLETE             │
└─────────────────┬─────────────────────────┘
                  │ tool calls
                  ▼
┌───────────────────────────────────────────┐
│         Capability Registry (88+ tools)    │
│                                           │
│  OS Automation    │  Files & Code         │
│  Screenshot/Vision│  Web Search/Fetch     │
│  Mouse/Keyboard   │  Memory               │
│  Windows/Apps     │  Voice I/O            │
│  Shell/Python     │  Security             │
│  Browser          │  Cloud/Messaging      │
└─────────────────┬─────────────────────────┘
                  │
                  ▼
┌───────────────────────────────────────────┐
│     OS Automation Backend                  │
│  modules/os_automation.py                 │
│  pyautogui + xdotool + mss + PIL          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │  Linux   │ │  macOS   │ │ Windows  │ │
│  │ (tested) │ │ (impl'd) │ │ (impl'd) │ │
│  └──────────┘ └──────────┘ └──────────┘ │
└───────────────────────────────────────────┘
```

---

## Component Details

### src/cli.ts — TypeScript Main Loop
- Interactive REPL with slash commands
- One-shot mode (`./devin "task"`)
- Web UI mode (`./devin --web`)
- Streaming output with spinner
- Loop detection (prevents infinite tool loops)
- History compaction (handles long conversations)

### src/conversation.ts — System Prompt + Context
- Rich system prompt with OBSERVE-ACT-VERIFY loop
- Full tool reference with examples
- OS detection and integration listing
- History management + compaction
- Context builder for provider APIs

### src/providers/ — AI Model Providers
- `anthropic.ts` — Claude (streaming, tool use, thinking)
- `gemini.ts` — Gemini (REST, function calling, vision)
- `openai.ts` — GPT-4/etc (streaming, function calling)
- `ollama.ts` — Local models via Ollama
- `multi.ts` — DeepSeek, Groq, Mistral, etc.
- Auto-fallback on rate limit / unavailability

### src/tools/executor.ts — Tool Execution
- 88+ tools across all categories
- OS automation via Python subprocess bridge
- File I/O with security checks
- Shell execution with timeout
- Web search (DuckDuckGo) + HTTP fetch
- Browser automation (Playwright)
- AI vision (inline image embedding for Gemini)
- Security tools with authorization checks

### src/os/automation.ts — OS Automation Bridge
- TypeScript → Python subprocess (`modules/os_automation.py`)
- Cross-platform: Linux/macOS/Windows
- Actions: screenshot, mouse, keyboard, windows, apps
- Result parsing: JSON protocol

### modules/os_automation.py — OS Automation Backend
- pyautogui (primary): mouse, keyboard, screenshot
- xdotool (Linux): window management, keyboard
- mss (screenshot): fast multi-screen capture
- PIL/Pillow: image processing
- Platform detection and routing

### modules/integrations.py — Python Tool Registry
- Loads all 22+ integrated repos via sys.path manipulation
- Graceful fallback if any repo fails to load
- HAS[] dict tracks what's actually available
- Unified TOOL_REGISTRY exposed to main.py

---

## Data Flow: Screenshot → Vision → Action

```
1. take_screenshot()
   → modules/os_automation.py: screenshot action
   → mss/pyautogui captures screen
   → saves to /tmp/devin_shot_<timestamp>.png
   → returns file path

2. analyze_screenshot_gemini(prompt)
   → executor.ts: automate('screenshot', {path: tmpFile})
   → reads screenshot bytes
   → base64 encodes
   → returns __IMG__image/png__<base64>__ENDIMG__\nTask: <prompt>

3. Provider receives result with embedded image
   → gemini.ts: makeParts() splits text + inline image
   → Gemini API analyzes image inline (no extra API call)
   → Returns text description + coordinates

4. AI uses coordinates
   → mouse_click(x, y)
   → automation backend moves and clicks
   → returns OK

5. take_screenshot() again → verify
```

---

## Memory System

- **Local JSON** (`data/memory.json`): simple fact storage
- **Vector search** (`LocalMemory` in `src/memory/`): semantic recall
- **Session compaction**: old history summarized when > 200 messages
- Memories auto-recalled at conversation start

---

## Security Boundaries

| Tier | Tools | Default Mode |
|------|-------|-------------|
| Safe | read_file, web_search, recall, speak | Auto-approved |
| Caution | mouse_click, keyboard_type, execute_shell, write_file | Prompted |
| Dangerous | security tools, kill_process, delete_file | Requires --auto or explicit yes |

---

## External Repository Integration

22+ repos integrated via three mechanisms:

1. **Native Python** — source in `repos/*/` added to sys.path, imported directly
2. **TypeScript adapters** — `src/integrations/` wraps TS/JS repos
3. **Subprocess bridge** — shell-called for CLI tools (nmap, etc.)

See `docs/INTEGRATION_MATRIX.md` for per-repo details.

---

## Platform Support

| Platform | Mouse | Keyboard | Screenshot | Window Mgmt | Status |
|----------|-------|----------|------------|-------------|--------|
| Linux (X11) | ✓ pyautogui + xdotool | ✓ pyautogui + xdotool | ✓ mss | ✓ xdotool | TESTED |
| Linux (Wayland) | ✓ via XWayland | ✓ via XWayland | ✓ mss | PARTIAL | PARTIAL |
| macOS | ✓ pyautogui | ✓ pyautogui | ✓ mss | ✓ osascript | IMPLEMENTED |
| Windows | ✓ pyautogui | ✓ pyautogui | ✓ mss | ✓ win32gui | IMPLEMENTED |
