# Devin AGI 4.0

An autonomous OS-controlling AI agent. Controls the computer like a human: moves the mouse, types, takes screenshots, runs commands, launches applications, browses the web, and reasons about what it sees. Powered by Gemini, Claude, OpenAI, HuggingFace, or Ollama.

```
  Devin AGI  v4.0.0
  ──────────────────────────────────────────────────────
  ✓ Connected to Gemini (gemini/gemini-3.6-flash)
  cwd:      /home/user/Devin-4.0
  platform: Linux  display
  tools:    103  ·  16/16 modules  ·  12 memories
  ──────────────────────────────────────────────────────

  Try: open firefox and search for python tutorials

❯ Devin-4.0 open firefox, go to google.com, search python tutorials

● think(thought='Plan: open_and_wait(firefox), screenshot_and_analyze for address bar, click+type URL, search')
↳ ready

● open_and_wait(app_name='firefox', wait_seconds=3)
↳ Opened firefox (pid=18234) | Loaded: YES

● screenshot_and_analyze(prompt='Where is the address bar? Give exact (x,y) pixel coordinates.')
↳ Address bar is at approximately (680, 45) — the URL input field at the top

● mouse_click(x=680, y=45)
↳ Clicked left at (680, 45)

● keyboard_hotkey(keys=['ctrl', 'a'])
↳ OK

● keyboard_type(text='https://www.google.com')
↳ Typed 22 chars

● keyboard_press(key='Return')
↳ Pressed key: Return

● sleep(seconds=2)
↳ waited 2s

● screenshot_and_analyze(prompt='Is Google loaded? Where is the search box?')
↳ Google homepage visible. Search box at (680, 300).

● mouse_click(x=680, y=300)
↳ Clicked left at (680, 300)

● keyboard_type(text='python tutorials')
↳ Typed 16 chars

● keyboard_press(key='Return')
↳ Pressed key: Return

● screenshot_and_analyze(prompt='Did python tutorials search results appear?')
↳ Yes — showing 10 results for "python tutorials"

● task_complete(result='Opened Firefox, navigated to Google, searched python tutorials. Results visible.')
↳ TASK_COMPLETE: Done. Firefox is open on python tutorial results.

✓ Task complete

Done. Firefox is showing python tutorial search results.
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Linux / macOS / Windows
- At least one AI provider key (see below)
- For GUI control on Linux: a running X11/Wayland display session

```bash
git clone https://github.com/kevinhamza/Devin-4.0
cd Devin-4.0

# Optional but recommended — virtual environment
python3 -m venv venv && source venv/bin/activate   # Linux/macOS
# python -m venv venv && venv\Scripts\activate      # Windows

# Install Python dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env and add at least one key (see Configuration below)
```

### Run

```bash
# Interactive REPL (recommended)
./devin

# One-shot task
./devin "create a Python script that monitors CPU usage"

# Specify provider
./devin --provider huggingface "open calculator and compute 42*7"
./devin --provider claude      "summarise all .py files in this folder"
./devin --provider gemini      "take a screenshot and describe the desktop"

# Specify model
./devin --model gemini-2.5-pro "write a detailed tech analysis"
./devin --model meta-llama/Meta-Llama-3.1-70B-Instruct "explain this code"
```

---

## Configuration

Create a `.env` file (never commit it — it is in `.gitignore`):

```env
# At least ONE of these is required:
GEMINI_API_KEY=your_gemini_key_here         # https://aistudio.google.com/app/apikey (free)
ANTHROPIC_API_KEY=your_anthropic_key_here   # https://console.anthropic.com/
OPENAI_API_KEY=your_openai_key_here         # https://platform.openai.com/api-keys
HF_TOKEN=your_huggingface_token_here        # https://huggingface.co/settings/tokens (free)

# Optional
DISPLAY=:0                  # Linux X11 display (for GUI tools)
OLLAMA_BASE_URL=http://localhost:11434  # local Ollama server
TELEGRAM_BOT_TOKEN=         # remote control via Telegram
AWS_ACCESS_KEY_ID=          # cloud integrations
AWS_SECRET_ACCESS_KEY=
```

See `.env.example` for the full list.

---

## AI Providers

| Provider | Key env var | Free? | Default model | Fallback |
|---|---|---|---|---|
| `gemini` | `GEMINI_API_KEY` | ✓ free | gemini-3.6-flash | → 2.5-flash → 2.5-pro → 2.0-flash |
| `claude` | `ANTHROPIC_API_KEY` | paid | claude-sonnet-4-6 | — |
| `openai` | `OPENAI_API_KEY` | paid | gpt-4o-mini | — |
| `huggingface` | `HF_TOKEN` | ✓ free | Qwen2.5-72B-Instruct | → Llama-3.3-70B → DeepSeek-R1 |
| `ollama` | none | ✓ local | llama3.2 | — |

Switch providers at runtime with `/provider <name>` or `--provider <name>`.

```bash
./devin --provider huggingface --model Qwen/Qwen2.5-72B-Instruct "task here"
```

---

## Architecture

```
User (CLI / voice)
       │
       ▼
 agent.py — REPL / one-shot
       │
       ▼
┌──────────────────────────────────────────┐
│  AI PROVIDER LAYER                       │
│  GeminiProvider │ ClaudeProvider │        │
│  OpenAIProvider │ HuggingFaceProvider │  │
│  OllamaProvider                          │
└────────────────┬─────────────────────────┘
                 │  tool calls (135 tools)
                 ▼
┌──────────────────────────────────────────┐
│  TOOL REGISTRY  (135 tools)              │
│  reasoning  web  shell  files  vision    │
│  mouse  keyboard  windows  apps          │
│  browser  clipboard  voice  memory       │
│  system  network  code  git  notes       │
│  integrations  control                   │
└────────────────┬─────────────────────────┘
                 │  dispatch
                 ▼
┌──────────────────────────────────────────┐
│  MODULE INTEGRATION LAYER               │
│  modules/voice.py          (TTS/STT)     │
│  modules/os_automation.py  (OS control)  │
│  modules/browser.py        (Selenium)    │
│  modules/persistent_memory.py            │
│  modules/messaging_gateway.py            │
│  modules/integration_hub.py (24 repos)   │
│  modules/system_monitor.py               │
│  + 96 other modules/                     │
└────────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────┐
│  OS / ENVIRONMENT                        │
│  filesystem  shell  GUI  browser         │
│  applications  network  clipboard        │
└──────────────────────────────────────────┘
```

### Agentic Loop

Every task follows:

```
OBSERVE → UNDERSTAND → PLAN → ACT → VERIFY → CONTINUE / RECOVER / COMPLETE
```

1. **OBSERVE** — `observe_and_plan(goal)` takes a screenshot and analyzes the screen with AI to understand current state before acting
2. **UNDERSTAND** — AI vision identifies what is on screen, what is in focus, what to do first
3. **PLAN** — `think_and_plan(task)` produces a numbered step-by-step execution plan
4. **ACT** — execute: mouse click, keyboard type, shell command, browser navigation, etc.
5. **VERIFY** — take screenshot again, check command output, confirm result
6. **LOOP** — continue to next step or recover from failure
7. **COMPLETE** — call `task_complete` only when outcome is verified

**Smart task vs conversation detection** (`_is_task_mode`): action-verb queries (open, run, search, install…) engage the full agentic loop with persistence. Questions get answered directly without unnecessary tool calls.

**Persistence**: when the AI responds without tool calls mid-task, Devin automatically injects a "continue executing" nudge (up to 3×) before accepting the response as complete.

The agent never gives up. Errors are information. If one approach fails, it switches strategy.

---

## Capabilities

### OS Automation

| Capability | Linux | macOS | Windows | Notes |
|---|---|---|---|---|
| Mouse move/click/drag/scroll | ✓ | ✓ | ✓ | pyautogui + xdotool |
| Keyboard type/press/hotkey | ✓ | ✓ | ✓ | pyautogui |
| Screenshot | ✓ | ✓ | ✓ | mss/pyautogui/scrot |
| AI screenshot analysis | ✓ | ✓ | ✓ | Gemini multimodal |
| Application launch/close | ✓ | ✓ | ✓ | subprocess |
| Window list/focus/resize | ✓ | partial | partial | wmctrl/xdotool |
| Clipboard get/set | ✓ | ✓ | ✓ | xclip/pbcopy/clip |
| Desktop notification | ✓ | ✓ | ✓ | notify-send/osascript/PS |

### Web & Browser

| Capability | Status |
|---|---|
| Web search | ✓ DuckDuckGo API |
| Web fetch / scrape | ✓ urllib + HTML strip |
| Browser automation | ✓ Selenium + Playwright (modules/browser.py) |
| Browser screenshot | ✓ |
| JS execution | ✓ |
| HTTP requests (any) | ✓ |

### Shell & Files

| Capability | Status |
|---|---|
| Shell command execution | ✓ subprocess, timeout, capture |
| Python code execution | ✓ exec() with stdout capture |
| File read/write/edit/delete | ✓ |
| Directory operations | ✓ |
| Script execution (.py/.sh/.js/.ps1/.bat) | ✓ auto-detected |
| Package installation (pip/apt/brew/choco) | ✓ |
| Git operations | ✓ |

### Voice

| Capability | Status | Notes |
|---|---|---|
| Text-to-speech | ✓ IMPLEMENTED | espeak / pyttsx3 / say (macOS) — requires install |
| Speech-to-text | ✓ IMPLEMENTED | SpeechRecognition / Whisper — requires install + mic |
| Voice loop | ✓ | /voice command enters listen→execute→speak loop |

### Memory

| Capability | Status |
|---|---|
| Persistent memory (SQLite) | ✓ `.devin_memory.db` |
| Save / recall facts | ✓ `/remember`, `/memory` |
| Session history | ✓ `conv_messages` list |
| Delete all memories | ✓ `/forget` |

### Monitoring

| Metric | Status |
|---|---|
| CPU / RAM / disk | ✓ psutil |
| Process list | ✓ |
| Network info | ✓ ip/ifconfig/ipconfig |
| Internet connectivity | ✓ ping test |

---

## Tools (135)

```
/tools               — list all tools
/tools vision        — list tools in category
```

135 tools total across all categories. Categories:
- **reasoning**: think
- **web**: web_search, web_fetch, open_browser, http_request, parse_json
- **shell**: execute_shell, execute_python, list_processes, kill_process, sleep, run_script, install_package
- **files**: read_file, write_file, edit_file, delete_file, list_files, create_directory, search_files
- **git**: git_command, git_advanced
- **vision**: screenshot, analyze_screenshot, analyze_image, find_on_screen, wait_for_window, wait_and_click, scroll_to_element
- **mouse**: mouse_move, mouse_click, mouse_double_click, mouse_right_click, mouse_drag, mouse_scroll, get_mouse_position
- **keyboard**: keyboard_type, keyboard_press, keyboard_hotkey, click_and_type, type_text_at, press_key_at
- **windows**: get_screen_size, list_windows, focus_window, maximize_window, minimize_window, alt_tab, get_active_window, resize_window, move_window
- **apps**: open_application, open_terminal, close_application, send_notification
- **browser**: browser_start, browser_navigate, browser_click, browser_type, browser_get_text, browser_screenshot, browser_execute_js, browser_close
- **clipboard**: clipboard_get, clipboard_set, select_all_copy
- **voice**: speak, listen
- **memory**: remember, recall
- **system**: get_system_info, get_system_metrics, network_info, context_info
- **code**: analyze_code
- **integrations**: devin_module, list_integrations, run_devin_module, discover_modules
- **notes**: take_note
- **control**: task_complete, ask_user, wait_and_verify
- **power**: write_and_run, install_and_verify, git_clone_and_explore, search_and_open, screen_to_clipboard
- **email**: send_email
- **data**: analyze_data
- **scheduling**: schedule_task

---

## Slash Commands

| Command | Description |
|---|---|
| `/help` | Show this help |
| `/tools [category]` | List tools, optionally filtered by category |
| `/status` | Provider, keys, platform, display, modules |
| `/providers` | All providers with key status |
| `/provider <name>` | Switch provider (gemini\|claude\|openai\|huggingface\|ollama) |
| `/model <name>` | Switch model |
| `/memory [query]` | Show memories, optionally filtered |
| `/remember <fact>` | Save a fact |
| `/forget` | Clear all memories (with confirmation) |
| `/history` | Show conversation history |
| `/shell <cmd>` | Run shell command directly |
| `/screenshot` | Take screenshot, optionally analyze with AI |
| `/voice` | Listen for voice then run as task |
| `/repos` | List external repos |
| `/integrations` | Module integration status |
| `/compact` | Compress conversation history to save context window |
| `/debug` | Show context size, provider, diagnostics |
| `/audit [target]` | Run a system or security audit |
| `/think <task>` | Plan a task step-by-step (shows plan, asks to execute) |
| `/workflow <task>` | Execute as a structured multi-step workflow |
| `/pentest <target>` | Run authorized penetration test on target |
| `/lab [setup]` | Show/setup security lab environment and tools |
| `/os` | Show OS, platform, display, and tool availability |
| `/run <cmd>` | Run a shell command directly (alias for /shell) |
| `/new` | Start fresh conversation |
| `/clear` | Clear screen |
| `/exit` / `/quit` | Exit |

---

## Integrated Repositories (24)

All repositories are in `external/`. Capabilities are accessible via `run_devin_module` and `discover_modules`.

| Repository | Source | Capabilities |
|---|---|---|
| AIA | github.com/kevinhamza/AIA | Voice, ML, social media |
| self-operating-computer | github.com/OthersideAI/self-operating-computer | Vision-guided clicking |
| OpenDevin | github.com/OpenDevin/OpenDevin | Agent framework |
| cheetahclaws | github.com/OoriData/cheetahclaws | Multi-agent, context management |
| Jarvis (Concept-Bytes) | github.com/Concept-Bytes/Jarvis | Voice assistant |
| JARVIS-microsoft | github.com/microsoft/JARVIS | HuggingGPT task planning |
| gemini-cli | github.com/google-gemini/gemini-cli | Gemini CLI patterns |
| claude-code | (reference) | Agentic loop patterns |
| shannon | (integrated) | OSINT, network |
| hexstrike-ai | (integrated) | Security tooling |
| openclaw | (integrated) | AI assistant |
| airgorah | (integrated) | WiFi security (authorized use only) |
| vulnerability-analysis | (integrated) | Security research |
| metasploit-framework | (reference) | Penetration testing framework |
| nishang | (reference) | PowerShell security |
| Responder | (reference) | Network analysis |
| PowerTools | (reference) | Security tooling |
| hackability | (reference) | Security analysis |
| Holomat | (reference) | Mixed reality |
| moltbots.github.io | (reference) | Multi-agent patterns |
| Devin / Devin-2.0 / Devin-3.0 | (earlier versions) | Architecture history |

Full details: `docs/INTEGRATION_MATRIX.md`

---

## Security

Devin separates capabilities into tiers:

| Tier | Examples | Behavior |
|---|---|---|
| Safe | file I/O, web search, memory, conversation | auto-execute |
| Caution | shell commands, app launch, mouse/keyboard | execute with output shown |
| Authorized Security | nmap, sqlmap, security tools | explicit authorization required |
| Blocked | attacking unauthorized systems | **never autonomously** |

Security tools require:
- Explicit user authorization in the conversation
- Target must be systems you own or have written permission to test
- Authorized lab environments (HackTheBox, TryHackMe, DVWA, own machines) are fine
- No autonomous credential theft, persistence, or lateral movement

---

## Modules (103)

The `modules/` directory contains 103 Python capability modules. Key ones:

| Module | Capability |
|---|---|
| `voice.py` | TTS (espeak/pyttsx3) + STT (SpeechRecognition/Whisper) |
| `os_automation.py` | pyautogui, xdotool, pynput |
| `browser.py` | Selenium + Playwright |
| `persistent_memory.py` | SQLite long-term memory |
| `messaging_gateway.py` | Telegram, Discord, Slack |
| `integration_hub.py` | Bridge to 24 external repos |
| `system_monitor.py` | psutil CPU/RAM/disk/network |
| `cheetahclaws_bridge.py` | Token tracking, compaction |
| `code_execution.py` | Sandboxed code execution |
| `cloud_integration_module.py` | AWS, Azure, GCP |
| `ollama_module.py` | Local LLM via Ollama |
| `scheduler.py` | Task scheduling |
| `encryption_tools.py` | Cryptography |

Use `run_devin_module` to call any function from any module:
```
Devin, use run_devin_module to call the voice module's speak function with "hello world"
```

---

## Platform Support

| Feature | Linux | macOS | Windows |
|---|---|---|---|
| Shell execution | ✓ | ✓ | ✓ |
| File operations | ✓ | ✓ | ✓ |
| Web / HTTP | ✓ | ✓ | ✓ |
| Mouse / keyboard (pyautogui) | ✓ | ✓ | ✓ |
| Mouse / keyboard (xdotool) | ✓ | ✗ | ✗ |
| Screenshot (mss/pyautogui) | ✓ | ✓ | ✓ |
| Screenshot (scrot) | ✓ | ✗ | ✗ |
| Window management (wmctrl) | ✓ | ✗ | ✗ |
| Voice TTS (espeak) | ✓ | ✗ | ✗ |
| Voice TTS (say) | ✗ | ✓ | ✗ |
| Browser (Selenium) | ✓ | ✓ | ✓ |
| Clipboard (xclip) | ✓ | ✗ | ✗ |
| Clipboard (pbcopy/clip) | ✗ | ✓ | ✓ |
| Desktop notifications | ✓ | ✓ | ✓ |
| Package install (apt) | ✓ | ✗ | ✗ |
| Package install (brew) | ✗ | ✓ | ✗ |
| Package install (choco) | ✗ | ✗ | ✓ |

---

## Testing

```bash
# Core test suite (38 tests, no API key required)
python3 tests/test_core.py

# Syntax check only
python3 -m py_compile agent.py && echo "OK"

# One-shot smoke test (requires API key)
./devin "what is 2+2"

# Full workflow test (requires display + API key)
./devin "take a screenshot and describe what you see"

# HuggingFace free-tier end-to-end
HF_TOKEN=your_token ./devin --provider huggingface "list files in this directory"
```

Test categories and status:
- **Syntax / import**: AUTOMATED VERIFIED (38 tests pass, `tests/test_core.py`)
- **Tool registry (135 tools)**: AUTOMATED VERIFIED
- **Shell/file/code execution**: AUTOMATED VERIFIED
- **Memory (SQLite)**: AUTOMATED VERIFIED
- **Provider/model selection**: AUTOMATED VERIFIED
- **Task mode detection**: AUTOMATED VERIFIED
- **Context management**: AUTOMATED VERIFIED
- **Model API connectivity**: BLOCKED BY EXTERNAL ENVIRONMENT (requires valid API key)
- **GUI / mouse / keyboard**: MANUAL VERIFICATION REQUIRED (requires display)
- **Voice STT/TTS**: MANUAL VERIFICATION REQUIRED (requires audio hardware)
- **Browser automation**: MANUAL VERIFICATION REQUIRED (requires display + browser)

---

## Troubleshooting

**No provider available**
```
Add at least one key to .env:
  GEMINI_API_KEY=...   (free at aistudio.google.com)
  HF_TOKEN=...         (free at huggingface.co/settings/tokens)
```

**GUI tools return "No display"**
```bash
# On a headless server, use Xvfb:
Xvfb :1 -screen 0 1920x1080x24 &
export DISPLAY=:1
./devin "take a screenshot"
```

**pyautogui not working on macOS**
```
macOS requires Accessibility permission:
System Settings → Privacy & Security → Accessibility → add Terminal/Python
```

**pyautogui not working on Windows**
```
Run as administrator, or install via: pip install pyautogui
```

**Gemini rate limit**
Devin automatically retries with fallback models (2.5-flash → 2.5-pro → 2.0-flash).

**HuggingFace model loading (503)**
Devin retries with increasing delays — free tier models cold-start in ~20s.

---

## Docs

- `docs/ARCHITECTURE.md` — System architecture and component map
- `docs/INTEGRATION_MATRIX.md` — All 24 external repos, integration status
- `docs/README_COMPLIANCE.md` — Requirements compliance checklist
- `.env.example` — All supported environment variables
