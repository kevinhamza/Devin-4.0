# Devin 4.0 Architecture

**Last Updated:** 2026-09-23  
**Status:** CURRENT STATE AUDIT

## Overview

Devin 4.0 is a multi-provider AI assistant with real OS control, built on Python (backend) + TypeScript (CLI).

### Entry Points
- **Python:** `python main.py [task]` or `./devin [task]` (shell wrapper)
- **TypeScript:** `npm run build && ./devin_ts [task]` (not primary)

### Core Architecture
```
User Input
  ↓ main.py
  ↓ Gemini API (REST) or Claude/OpenAI
  ↓ AI generates tool calls
  ↓ TOOL_REGISTRY executes tools
  ↓ Results returned to AI
  ↓ Loop continues until task_complete()
```

## Key Components

### 1. main.py (~900 lines)
**Purpose:** Entry point, Claude Code-style TUI, agentic loop  
**Key Functions:**
- CLI argument parsing (task, --voice, --test, etc.)
- Conversation history management
- Model selection and retry logic
- Tool registry import from modules.integrations
- Rich library for colored output

**Flow:**
1. Load .env for API keys
2. Import integrations.py (bootstraps all repos)
3. Enter REPL or run one-shot task
4. For each user message:
   - Add to conversation history
   - Call Gemini REST API with tool definitions
   - Parse response, check stop_reason
   - If tool_use: execute tools, add results, repeat
   - If end_turn: return response to user

### 2. modules/integrations.py (TOOL_REGISTRY)
**Purpose:** Unified tool API for all 24 repos  
**Key Components:**

- **sys.path bootstrap:** Adds repos/, external/, modules/ so all imports work
- **Capability flags (HAS[]):** Track which repos successfully loaded
  - aia_automation, aia_internet, aia_device, aia_voice, aia_face, aia_ml
  - soc (self-operating-computer)
  - jarvis, cheetah, opendevin, vuln_analysis
  - And ~15-20 others
  
- **Core tools (37 registered):**
  - **OS:** take_screenshot, mouse_*, keyboard_*, get_screen_size, list_windows, focus_window, open_application
  - **Shell:** execute_shell, execute_python, git_command
  - **Files:** read_file, write_file, list_files
  - **Web:** web_search, web_fetch, open_browser
  - **Voice:** speak, listen
  - **Clipboard:** clipboard_get, clipboard_set
  - **System:** get_system_info, list_processes
  - **Security:** run_nmap_scan
  - **Vision:** analyze_image
  - **Comms:** send_telegram_message

### 3. modules/os_automation.py
**Purpose:** Cross-platform OS interaction via xdotool (Linux), pyautogui (fallback)  
**Key Functions:**
- **Mouse:** click, right_click, double_click, move, drag, scroll, get_position
- **Keyboard:** type, press (Return, Tab, etc.), hotkey (Ctrl+C)
- **Screenshot:** mss (primary) → xdotool key Print (Wayland fallback)
- **Shell:** subprocess.run() with shell=True and output capture
- **Window:** wmctrl or ps-based window listing and focus
- **Files:** pathlib Path operations
- **Applications:** subprocess to launch with `which`

### 4. modules/voice.py
**Purpose:** TTS + STT voice control  
**Dependencies:** pyttsx3, SpeechRecognition, PyAudio  
**Key Functions:**
- `speak(text)` → pyttsx3 engine
- `listen()` → Google Speech Recognition API via SpeechRecognition

### 5. Gemini Integration
**API:** REST POST to generativelanguage.googleapis.com/v1/beta/models/{model}/generateContent  
**Models (in order of fallback):**
1. gemini-3.6-flash (primary, ~10-15s/call)
2. gemini-3.5-flash (fallback)
3. gemini-3.1-flash-lite (fast, ~2s)
4. gemini-flash-latest
5. gemini-1.5-flash (legacy)

**Request Format:**
- messages array with role (user/assistant) and content
- tools array defining available functions
- Receive response with stop_reason and tool_use blocks

**Response Handling:**
- Check stop_reason: 'tool_use' or 'end_turn' (not 'STOP')
- Parse tool_use blocks to extract tool name and arguments
- Execute from TOOL_REGISTRY
- Add tool_result to messages
- Loop until end_turn

## Integrated Repositories (16 active in repos/)

| Repo | Purpose | Type | Status |
|------|---------|------|--------|
| aia | Automation framework | Python | Bridged via modules |
| cheetah | Multi-agent RL | Python | Partially integrated |
| claude_code | Claude Code source | TypeScript | Reference copy |
| devin1, 2, 3 | Previous versions | Python | Reference/fallback |
| gemini_cli | Gemini CLI | TypeScript | Not used (REST API used instead) |
| holomat | XR framework | Python | Bridged |
| jarvis_ms | HuggingGPT | Python | Bridged |
| jarvis | Concept-Bytes Jarvis | Python | Bridged |
| openclaw | Agent framework | Python | Partially integrated |
| opendevin | OpenDevin agent | Python | Canvas tool extracted |
| security | Pentesting tools | Mixed | Via pentesting_tools/ modules |
| shannon | Network AI | TypeScript | Not actively used |
| soc | Self-operating-computer | Python | Integrated (screenshot utils) |
| tools | PowerTools, moltbots | Mixed | Reference only |

## Tool Registry (37 tools)

Defined in `modules/integrations.py` at line 902. Each tool has:
- Name (string key)
- Function reference (callable)
- Called by AI via: `{"name": "tool_name", "args": {...}}`

## Perception-Action Cycle

```
Loop:
  1. take_screenshot() → PNG file
  2. Show to user / add to context (if vision task)
  3. AI analyzes screenshot
  4. AI generates tool_use calls:
     - mouse_click(x, y)
     - keyboard_type(text)
     - read_file(path)
     - etc.
  5. Execute tools in sequence
  6. Capture tool results
  7. Add results to conversation
  8. AI generates next action
  9. Repeat (or return if task_complete)
```

Typical cycle time: ~15-20 seconds (mostly Gemini API latency)

## Configuration & Deployment

### .env (Required)
```env
GEMINI_API_KEY=your_key_here
```

### .env (Optional)
```env
ANTHROPIC_API_KEY=...
OPENAI_API_KEY=...
TELEGRAM_BOT_TOKEN=...
```

### Launch Modes
- **Interactive REPL:** `python main.py` (or `./devin`)
- **One-shot:** `python main.py "do something"`
- **Voice mode:** `python main.py --voice`
- **Test mode:** `python main.py --test`

### TypeScript Build
```bash
npm install
npm run build
dist/cli.js "task" # or use ./devin (wrapper script)
```

## Dependencies

**Python:** requests, rich, pydantic, python-dotenv, mss, pyautogui, pyttsx3, SpeechRecognition, PyAudio, PIL, opencv-python, selenium, playwright, paramiko, pycryptodome, nmap, and 100+ more

**System:**
- xdotool (mouse/keyboard on Linux)
- wmctrl (window management on Linux)
- xclip (clipboard on Linux)
- nmap (security scanning)

**Node.js:** typescript, ts-node, prettier, eslint (dev only)

## Known Limitations

1. **Wayland Screenshot:** Requires xdotool Print key workaround; mss fails on Wayland
2. **No Permission System:** All tools available to AI; no access control
3. **shell=True Security:** execute_shell() allows command injection if AI inputs untrusted data
4. **Rate Limiting:** Gemini free tier ~10-15s per request
5. **No Persistent Memory:** Between sessions, only conversation history in REPL
6. **Cross-platform Untested:** Only Linux (Kali) verified; macOS/Windows have conditional code but untested

## Previous Session Fixes (Opus 5 session)

1. Fixed screenshot black on Wayland → xdotool Print workaround
2. Fixed run_command_in_terminal output → captures actual stdout
3. Fixed confirmation dialogs → auto_approve mode
4. Fixed stop_reason detection → checks tool_use blocks first before checking finishReason
5. Fixed stream() early exit → condition changed from OR to AND

## Next Steps for Audit

1. Verify all 37 tools work end-to-end
2. Test tool count accuracy (claim: 60+, actual: 37)
3. Map exact tool origins (which repo provides which tool)
4. Verify all 16 repos actually integrated
5. Create INTEGRATION_MATRIX.md
6. Run comprehensive test suite
7. Document missing features (persistent memory, permission system, tests)
