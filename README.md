THIS HAS MANY BUGS RIGHT NOW AND I AM LOOKING FOR CONTRIBUTORS # Devin AGI 4.0

An advanced AI assistant with **real OS control** — it moves the mouse, types, takes screenshots, runs commands, and operates software exactly like a human user. Powered by Gemini with a Claude Code-style terminal interface.

```
╭──────────────────────────────────────────────────────────────────╮
│  Devin AGI  v4.0.0  ·  24 repos integrated  ·  Linux
│  model: gemini-2.5-flash  ·  tools: 37  ·  voice: off
╰──────────────────────────────────────────────────────────────────╯

10:42 You
> open firefox and search for python tutorials

  ● take_screenshot()
    ↳ /tmp/devin_1234.png
  ● open_application(name='firefox')
    ↳ OK
  ● mouse_click(x=680, y=45)
    ↳ OK
  ● keyboard_type(text='https://google.com/search?q=python+tutorials')
    ↳ OK
  ● keyboard_press(key='Return')
    ↳ OK
  ● task_complete(reason='Opened Firefox and searched for python tutorials')
    ↳ ✓ Done

10:42 Devin
Done. Firefox is open with python tutorial results.
```

---

## Quick Start

```bash
# Clone
git clone https://github.com/kevinhamza/Devin-4.0
cd Devin-4.0

# Set your API key
echo "GEMINI_API_KEY=your_key_here" > .env

# Activate venv
source venv/bin/activate

# Run
python main.py
```

**One-shot mode:**
```bash
python main.py "open a terminal and run ls -la"
```

**Voice mode:**
```bash
python main.py --voice
```

**Smoke test:**
```bash
python main.py --test
```

---

## Features

| Feature | Status |
|---------|--------|
| Full mouse control — click, drag, scroll, right-click | ✓ |
| Full keyboard control — type, hotkeys, special keys | ✓ |
| Screenshot + vision — see the screen, analyze with AI | ✓ |
| Window management — list, focus, maximize windows | ✓ |
| Shell execution — run any command, capture output | ✓ |
| File operations — read, write, list, search files | ✓ |
| Web search + fetch — search web and read pages | ✓ |
| Voice I/O — TTS + STT voice control | ✓ |
| Long-term memory — remember facts across sessions | ✓ |
| Security tools — nmap, vulnerability scanning | ✓ |
| Clipboard — get/set clipboard contents | ✓ |
| Cross-platform — Linux, macOS, Windows | ✓ |
| Claude Code-style TUI — Rich markdown, spinners, color | ✓ |
| Multi-model fallback — Gemini 2.5 → 2.0 → 1.5 | ✓ |

---

## Architecture

```
Devin-4.0/
├── main.py                  # Entry point — Claude Code TUI + agentic loop
├── modules/
│   ├── integrations.py      # Unified API for all 24 repos (60+ tools)
│   ├── os_automation.py     # Cross-platform mouse/keyboard/screenshot
│   ├── engine.py            # DevinEngine class
│   ├── browser.py           # Selenium → Playwright → webbrowser
│   ├── voice.py             # TTS + STT voice thread
│   └── repo_tools.py        # TOOL_REGISTRY for all repos
├── repos/                   # Full source of all integrated repos
│   ├── aia/                 # AIA — automation, voice, ML, social (Python)
│   ├── devin1/              # Original Devin (Python)
│   ├── devin2/              # Devin-2.0 (Python)
│   ├── devin3/              # Devin-3.0 (Python)
│   ├── soc/                 # self-operating-computer (Python)
│   ├── opendevin/           # OpenDevin agent (Python)
│   ├── jarvis/              # Jarvis Concept-Bytes (Python)
│   ├── jarvis_ms/           # Microsoft JARVIS / HuggingGPT (Python)
│   ├── cheetah/             # cheetahclaws multi-agent RL (Python)
│   ├── gemini_cli/          # gemini-cli (TypeScript)
│   ├── claude_code/         # claude-code source (TypeScript)
│   ├── openclaw/            # openclaw agent framework
│   ├── holomat/             # Holomat XR (Python)
│   ├── shannon/             # Shannon network AI (TypeScript)
│   ├── security/            # airgorah, hexstrike, hackability,
│   │                        #   vuln-analysis, Responder, nishang
│   └── tools/               # PowerTools, moltbots
├── external/                # Original git clones (reference)
├── src/                     # TypeScript CLI (npm run dev)
└── venv/                    # Python virtual environment
```

---

## Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/clear` | Clear conversation history |
| `/status` | CPU, RAM, active model, capabilities |
| `/tools` | List all available tools |
| `/repos` | List all integrated repositories |
| `/voice` | Toggle voice mode |
| `/screenshot` | Take a screenshot |
| `/memory` | Show long-term memories |
| `/remember <fact>` | Save a fact to memory |
| `/shell <cmd>` | Run a shell command |
| `/model` | Show active AI model |
| `/exit` | Quit |

---

## Configuration

`.env` (never commit):
```env
GEMINI_API_KEY=your_gemini_key
ANTHROPIC_API_KEY=your_anthropic_key   # optional
OPENAI_API_KEY=your_openai_key         # optional
TELEGRAM_BOT_TOKEN=your_bot_token      # optional
```

---

## TypeScript CLI

```bash
npm install && npm run build
./devin "your task here"
```

---

## License

MIT — [@kevinhamza](https://github.com/kevinhamza)
