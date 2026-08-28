# Devin AGI v4.0.0

Advanced AI assistant with a Claude Code-style interface, full OS control, and 24 integrated external repos. Runs autonomously — no confirmation dialogs.

```
╭──────────────────────────────────────────────────────────────────╮
│   Devin AGI  v4.0.0
│   cwd: /home/kevin/DEVIN2/Devin-4.0
│   model: gemini-3.5-flash   provider: gemini   mode: auto_approve
╰──────────────────────────────────────────────────────────────────╯

✓ Connected to Gemini (gemini-3.5-flash)
✓ Integration hub loaded — 24 repos active

Talk to Devin — ask a question, give a task, or type /help.

❯ open firefox and search for python tutorials

  ● open_application(name="firefox")
  ↳ Launched firefox

  ● analyze_screenshot_gemini(prompt="Where is the address bar?")
  ↳ Address bar is at the top center (x=683, y=50)

  ● mouse_click(x=683, y=50)
  ↳ Clicked at (683, 50)

  ● keyboard_type(text="python tutorials")
  ↳ Typed text

  ● keyboard_press(key="Return")
  ↳ Pressed Return

Searched for "python tutorials" in Firefox.
```

## Features

- **Claude Code-style interface** — streaming `● tool()` / `↳ result` display, ANSI colors, slash commands
- **Full OS control** — autonomous mouse, keyboard, screenshots, window management (xdotool + pyautogui)
- **90+ tools** — file I/O, shell, web search, AI vision, security, cloud, voice, Telegram
- **Autonomous mode** — `auto_approve` by default, executes all tools without prompting
- **Multi-provider AI** — Gemini (free default), Anthropic, OpenAI, DeepSeek, Groq, Ollama
- **24 integrated repos** — live callable modules via integration hub
- **Wayland compatible** — GNOME 49 Wayland screenshot via native PrintScreen shortcut
- **Temporary screenshots** — captures deleted automatically after AI analysis
- **Voice control** — text-to-speech (pyttsx3) + speech-to-text (SpeechRecognition)
- **Persistent memory** — long-term memory across sessions

## Quick Start

```bash
cd /home/kevin/DEVIN2/Devin-4.0

# Activate venv (dependencies already installed)
source venv/bin/activate

# Launch (interactive REPL)
./devin
# or
node dist/cli.js
```

## Usage

```
node dist/cli.js [options] 

Options:
  --print "<text>"    One-shot mode (run task and exit)
  --provider <p>      gemini | anthropic | openai | ollama | groq | deepseek
  --model <name>      Model name override
  --plan              Plan mode (describe without executing)
  --voice             Enable voice input/output
  --web [--port N]    Web UI (default port 3000)
  -v, --verbose       Show raw API responses
```

### Examples

```bash
# Interactive REPL (default)
./devin

# One-shot tasks
node dist/cli.js --print "take a screenshot and describe what's on screen"
node dist/cli.js --print "open firefox and go to github.com"
node dist/cli.js --print "list all python files here and count lines"
node dist/cli.js --print "what's my CPU and RAM usage?"

# Other providers
node dist/cli.js --provider anthropic --model claude-sonnet-4-6
node dist/cli.js --provider groq --model llama-3.1-70b

# Plan before executing
node dist/cli.js --plan "install and configure nginx"
```

### Slash commands

| Command | Description |
|---------|-------------|
| `/help` | Show help |
| `/clear` | Clear history |
| `/status` | System + session info |
| `/tools` | List all 90+ tools |
| `/memory` | Recent memories |
| `/repos` | Integrated repos |
| `/plan` | Switch to plan mode |
| `/auto` | Auto-approve mode |
| `/default` | Default (confirm) mode |
| `/model <name>` | Change model |
| `/verbose` | Toggle verbose |
| `exit` | Quit |

## OS Automation

Devin controls the computer autonomously using xdotool + pyautogui:

```
❯ click the address bar and search for python docs

  ● take_screenshot(path="/tmp/devin_screen_1234.png")
  ↳ Screenshot saved (deleted after analysis)

  ● analyze_screenshot_gemini(prompt="Where is the address bar?")
  ↳ Address bar at top center, approximately x=683, y=50

  ● mouse_click(x=683, y=50)
  ↳ Clicked

  ● keyboard_type(text="docs.python.org")
  ↳ Typed: docs.python.org
```

**Screenshots are temporary** — captured to `/tmp/`, analyzed by Gemini Vision, deleted immediately.

### Mouse
- `mouse_click(x, y, button, double_click)` — left/right/middle, single/double
- `mouse_right_click(x, y)` — context menu
- `mouse_drag(x1, y1, x2, y2)` — drag and drop
- `mouse_scroll(x, y, direction, amount)` — scroll in any direction
- `mouse_move(x, y)` — move without clicking

### Keyboard
- `keyboard_type(text)` — type with realistic timing
- `keyboard_hotkey(keys)` — Ctrl+C, Alt+Tab, Super+D, etc.
- `keyboard_press(key)` — Return, Tab, Escape, F5, Delete, etc.

### Applications & Windows
- `open_application(name)` — launch firefox, terminal, gedit, vlc, etc.
- `run_command_in_terminal(command)` — run and capture output
- `execute_shell(command)` — run shell command (faster, returns output)
- `list_windows()` — all open windows
- `focus_window(name)` — bring window to front

### Screen
- `take_screenshot(path, region)` — capture screen (GNOME Wayland compatible)
- `analyze_screenshot_gemini(prompt)` — capture + analyze with Gemini Vision
- `find_on_screen(image_path)` — template match an image on screen
- `click_image(image_path)` — find and click an image on screen

## Tool Reference

### File & Code
| Tool | Description |
|------|-------------|
| `read_file(path)` | Read with line numbers |
| `write_file(path, content)` | Write/create file |
| `edit_file(path, old, new)` | Replace text in file |
| `delete_file(path)` | Delete file or directory |
| `list_files(path, recursive)` | Directory listing |
| `search_files(pattern, path)` | Grep across files |
| `execute_shell(command)` | Run shell command, get output |
| `execute_python(code)` | Run Python inline |
| `git_command(args)` | Git operations |

### AI & Vision
| Tool | Description |
|------|-------------|
| `analyze_screenshot_gemini(prompt)` | Capture screen + AI analysis (temp file) |
| `analyze_image_gemini(path, prompt)` | Analyze image file with Gemini Vision |
| `gemini_generate(prompt, model)` | Direct Gemini call |

### Voice
| Tool | Description |
|------|-------------|
| `speak(text)` | Text-to-speech (pyttsx3 / espeak) |
| `listen_voice()` | Speech-to-text (mic → text) |

### Web
| Tool | Description |
|------|-------------|
| `web_search(query)` | DuckDuckGo search |
| `web_fetch(url)` | HTTP GET/POST |
| `open_browser(url)` | Open URL in default browser |
| `research(topic)` | Deep multi-source research |

### Integration Hub
| Tool | Description |
|------|-------------|
| `hub_status()` | Status of all 24 integrated repos |
| `hub_dispatch(tool, args)` | Route to any hub module |
| `ai_operate(objective)` | Self-operating-computer (vision automation) |
| `soc_click(description)` | AI vision click by element description |
| `system_metrics_hub()` | CPU/RAM/disk/network/processes |

### Security (authorized use only)
| Tool | Description |
|------|-------------|
| `run_nmap_scan(target)` | Network scan |
| `vulnerability_scan(target)` | CVE analysis |
| `wifi_audit(interface, action)` | WiFi security |
| `osint_lookup(target, type)` | OSINT |
| `xss_test(url, payload)` | XSS testing |

### System
| Tool | Description |
|------|-------------|
| `get_system_info()` | CPU, RAM, disk |
| `list_processes(filter)` | Running processes |
| `kill_process(pid)` | Kill process |
| `volume_control(action, level)` | Audio control |
| `send_telegram(token, chat_id, text)` | Telegram message |

## Integration Hub (24 repos)

All repos are live-callable via `hub_dispatch()` or dedicated tools. No files copied — repos loaded from `external/` via Python path injection.

```bash
node dist/cli.js --print "hub_status"
```

| Repo | Status | Purpose |
|------|--------|---------|
| AIA | ✓ | Voice, automation, ML |
| cheetahclaws | ✓ | Multi-provider streaming |
| Jarvis | ✓ | Voice skills |
| OpenDevin | ✓ | Sandboxed agent |
| self-operating-computer | ✓ | Vision-based automation |
| shannon | ✓ | OSINT, threat intel |
| hexstrike-ai | ✓ | AI pentesting |
| vulnerability-analysis | ✓ | CVE scanning |
| airgorah | ✓ | WiFi audit |
| Responder | ✓ | Network MITM |
| nishang | ✓ | PowerShell toolkit |
| Holomat | ✓ | Spatial computing |
| gemini-cli | ✓ | Gemini CLI patterns |
| Devin v1/v2/v3 | ✓ | Prior versions |
| Telegram | ✓ (needs token) | Bot integration |

## Architecture

```
Devin-4.0/
├── src/                      TypeScript CLI
│   ├── cli.ts                REPL with streaming + retry logic
│   ├── conversation.ts       System prompt + tool rules
│   ├── providers/
│   │   ├── gemini.ts         Gemini provider (stop_reason fix)
│   │   ├── anthropic.ts      Claude provider
│   │   └── multi.ts          11-provider router
│   ├── tools/
│   │   ├── executor.ts       90+ tool implementations
│   │   └── definitions.ts    JSON Schema specs
│   └── config.ts             Default: auto_approve mode
├── modules/
│   ├── os_automation.py      OS control (xdotool + pyautogui)
│   └── integration_hub.py    24-repo live integration hub
├── external/                 24 cloned repos (loaded via sys.path)
├── main.py                   Python orchestration
├── dist/                     Compiled JS (npm run build)
└── .env                      API keys
```

## Configuration

`.env`:
```env
GEMINI_API_KEY="your-key"       # Required (free tier available)
ANTHROPIC_API_KEY="sk-ant-..."  # Optional
OPENAI_API_KEY="sk-..."         # Optional
TELEGRAM_BOT_TOKEN="..."        # Optional (for Telegram bot)
VIRUSTOTAL_API_KEY="..."        # Optional
```

### Providers

| Provider | Free | Recommended models |
|----------|------|--------------------|
| Gemini | Yes | gemini-3.5-flash (default), gemini-3.1-flash-lite |
| Anthropic | No | claude-sonnet-4-6, claude-opus-4-8 |
| OpenAI | No | gpt-4o, gpt-4o-mini |
| DeepSeek | Low cost | deepseek-chat |
| Groq | Free tier | llama-3.1-70b |
| Ollama | Free (local) | llama3, mistral |

## Requirements

```bash
# Python (use venv — already set up)
source venv/bin/activate

# System tools (Kali/Debian)
sudo apt install xdotool

# Node.js 18+
npm install && npm run build

# DISPLAY must be set
export DISPLAY=:0
```

## Troubleshooting

**No response / API error** — Check `.env` has `GEMINI_API_KEY` set.

**Screenshot empty/black** — This is a Wayland issue with mss/X11. Devin uses GNOME's native PrintScreen shortcut (xdotool key Print) which works correctly. Make sure `DISPLAY=:0` is set.

**Screenshot requires click** — Should be fully automatic. The automation presses Print → Return → clicks "Save" button at (683, 710). If screen layout differs, the button position may need updating in `modules/os_automation.py`.

**Mouse/keyboard not working**:
```bash
DISPLAY=:0 xdotool getactivewindow getwindowname
```

**Build errors** — `rm -rf dist && npm run build`

**Voice not working** — `pip install pyttsx3 SpeechRecognition pyaudio`

**Hub tool errors** — Check `node dist/cli.js --print "hub_status"` to see which repos are active.

## License

MIT — Kevin Hamza (kevinhamza) · [GitHub](https://github.com/kevinhamza/Devin-4.0)
