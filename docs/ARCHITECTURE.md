# Devin 4.0 Architecture

**Last Updated:** 2026-09-24 (Phase B–H refresh)
**Status:** CURRENT — Core runtime, model chain, tool registry, permission gate,
pytest suite, and vision layer all verified this session against live APIs.

## Ground-truth snapshot (this session)

| Fact | Value |
|---|---|
| Python entry | `venv/bin/python main.py` (or `./devin` with `dist/cli.js` absent) |
| TS entry | `./devin` → `node dist/cli.js` (built via `npm run build --legacy-peer-deps`) |
| Model chain (main.py) | Anthropic → Gemini → Hugging Face, first configured wins; auto-fallback across model IDs within each provider |
| Providers actually wired | Anthropic SDK, Gemini REST, HF Router (chat + Qwen2.5-VL vision) |
| Tool registry | 91 functions total in `modules/integrations.py` |
| Schemas exposed to LLM | 63 (main.py `TOOL_SCHEMAS`) |
| Vision path | Anthropic vision → Gemini vision → HF `Qwen/Qwen2.5-VL-*` — verified live against a real screenshot |
| Permission modes | `auto` (default in `.env`), `default` (confirm/refuse dangerous), `plan` (describe only) — all three enforced in the loop, not just flags |
| Pytest | 102 passed, 9 skipped, 0 failed |
| Repos with `HAS[]=True` at runtime | AIA, self-operating-computer, Jarvis (Concept-Bytes), JARVIS-microsoft, gemini-cli SDK, cheetahclaws, HF |
| Repos source-only (deferred integration) | OpenDevin (needs `openhands` SDK), vulnerability-analysis (needs NVIDIA morpheus), shannon, hexstrike-ai, openclaw, Holomat, airgorah, PowerTools, MoltBots, hackability, claude-code-source |
| Repos deliberately source-only (offensive) | Responder, nishang, metasploit-framework |

## Central runtime flow (as executed by `main.py::_run_agentic_loop`)

```
User prompt (one-shot arg, /-command, or REPL line)
        │
        ▼
Build Gemini-shape `contents` from history + current turn
        │
        ▼  _call_gemini_rest (name kept, actually multi-provider now)
        │
        ├─ (1) Anthropic:      _call_anthropic → Claude native tool_use
        │                        (converts contents to Anthropic content blocks,
        │                         assigns synthetic tool_use_ids for matching)
        │
        ├─ (2) Gemini REST:    tries each of _GEMINI_MODELS in order
        │                        (real 2.5/2.0/1.5 IDs, 429/404 fallthrough)
        │
        └─ (3) Hugging Face:   _hf_chat via router.huggingface.co/v1
                               (OpenAI-compat tools + <tool_use> fallback parser)
        │
        ▼  Returns Gemini-shape data → agentic loop:
        │
        │   parse candidates[0].content.parts[] into text_parts + tool_calls
        │   display text via Rich
        │   if no tool_calls & plan-shape text: inject one [[SYSTEM NUDGE]]
        │   else if no tool_calls: break loop, return final_text
        │
        ▼  For each tool_call:
        │
        │   ┌── task_complete → return immediately
        │   ├── PERMISSION_MODE == "plan"    → synthetic [PLANNED …] result
        │   ├── PERMISSION_MODE == "default"
        │   │     + _is_dangerous(name):
        │   │       - TTY: prompt y/N via _confirm_dangerous
        │   │       - non-TTY one-shot: [BLOCKED …] fed back to model
        │   └── otherwise: dispatch_tool(name, args)  → real invocation
        │
        ▼  Append tool result(s) as functionResponse parts to contents
        │
        ▼  Next round (max_rounds = 30)
```

## Permission model (§9 compliance)

Dangerous tools (defined in `main.py::_DANGEROUS_TOOLS`) — 21 tools including
`execute_shell`, `execute_python`, all mouse/keyboard/window/app tools,
`write_file`, `git_command`, `run_nmap_scan`, `port_scan`, `check_ssl_cert`,
`send_telegram_message`, `clipboard_set`, `open_browser` — pass through the
permission gate. `read_file`, `list_files`, `take_screenshot`,
`get_system_info`, etc. skip the gate as read-only. Offensive tools from
Responder / nishang / metasploit are deliberately NOT wired into TOOL_REGISTRY
so they cannot be invoked by the LLM even under `auto` mode; they exist in
`repos/security/` only as source.

## Vision layer (§5 compliance)

`analyze_image(path, question)` (in `modules/integrations.py`) tries in order:
1. **Anthropic Claude vision** (`claude-opus-4-5` → `claude-sonnet-4-5` →
   `claude-3-5-sonnet-20241022`) — best for describing UI/screens.
2. **Gemini vision** (`gemini-2.5-flash` → `gemini-2.0-flash` →
   `gemini-1.5-flash`) — via v1beta REST with `inlineData`.
3. **Hugging Face vision** (`Qwen/Qwen2.5-VL-72B-Instruct` →
   `Qwen/Qwen2.5-VL-7B-Instruct` → Llama 3.2 Vision 90B → 11B) — via
   `router.huggingface.co/v1/chat/completions` with OpenAI-compat
   `image_url` data-URI parts. **Verified live this session** against a real
   `take_screenshot()` output.
4. If none configured, returns a specific "no vision provider available"
   string — the tool doesn't lie about capability.

## Slash-command surface (§15 compliance)

| Command | Python (`main.py`) | TypeScript (`src/cli.ts`) |
|---|---|---|
| `/help` `/clear` `/status` `/tools` `/repos` `/screenshot` `/memory` `/remember` `/shell` `/model` `/exit` | ✓ | ✓ |
| `/plan` (describe, don't run) | ✓ (loop intercepts every tool call with `[PLANNED …]`) | ✓ (planMode flag) |
| `/auto` (auto-approve) | ✓ (sets PERMISSION_MODE) | ✓ |
| `/default` (gate dangerous) | ✓ (interactive y/N or non-TTY refuse) | ✓ (default) |
| `/verbose` | ✓ (toggles DEVIN_DEBUG) | ✓ |
| `/voice` | ✓ (toggles VOICE_MODE) | ✓ |

All twelve Python commands programmatically verified this session. Two
previously-crashing ones (`/memory`, `/remember`) fixed via a legacy-list
migration in `_load_memory()`.

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
