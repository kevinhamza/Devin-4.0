# Devin AGI 4.0

An advanced AI agent with **real OS control** — it moves the mouse, types, takes screenshots, runs commands, opens applications, and operates your computer exactly like a human user. Powered by Gemini, Claude, or any LLM with a Claude Code-style terminal interface.

```
╭──────────────────────────────────────────────────────────────────╮
│  Devin AGI  v4.0.0  (Phase B refresh 2026-09-24)
│  cwd: /home/user/project
│  model: gemini-2.5-flash  provider: gemini  mode: auto_approve
╰──────────────────────────────────────────────────────────────────╯
✓ Connected to Gemini (gemini-2.5-flash)

Talk to Devin — ask a question, give a task, or type /help. (exit to quit)

14:22 You
❯ open firefox and search for python tutorials

  ● take_screenshot()
    ↳ /tmp/devin_shot_1234.png (314KB)
  ● open_application(name="firefox")
    ↳ Opened firefox (pid=12345)
  ● analyze_screenshot_gemini(prompt="Where is the address bar? Give pixel coords.")
    ↳ The address bar is at approximately (680, 45)
  ● mouse_click(x=680, y=45)
    ↳ Clicked left at (680, 45)
  ● keyboard_hotkey(keys=["ctrl","a"])
    ↳ OK
  ● keyboard_type(text="https://www.google.com/search?q=python+tutorials")
    ↳ Typed 57 chars
  ● keyboard_press(key="Return")
    ↳ Pressed key: Return
  ● take_screenshot()
    ↳ /tmp/devin_shot_1235.png (280KB)
  ● task_complete(reason="Opened Firefox and searched for python tutorials")
    ↳ ✓ Done

14:22 Devin
Done. Firefox is open showing python tutorial search results.
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for TypeScript CLI)
- Linux/macOS/Windows
- A display server (X11 on Linux, native on macOS/Windows)
- API key for at least one model provider

```bash
# Clone the repository
git clone https://github.com/kevinhamza/Devin-4.0
cd Devin-4.0

# Set your API key (never commit this file)
cp api_keys.yaml.example .env
# Edit .env and add your keys:
echo "GEMINI_API_KEY=your_key_here" > .env
```

### Python CLI (Recommended for first run)

```bash
# Activate the virtual environment
source venv/bin/activate

# Interactive mode
python main.py

# One-shot (non-interactive)
python main.py "open a terminal and run ls -la"

# Voice mode
python main.py --voice

# Smoke test
python main.py --test
```

### TypeScript CLI (Full-featured)

```bash
npm install
npm run build
./devin                              # Interactive mode
./devin "take a screenshot"          # One-shot
./devin --provider anthropic         # Use Claude
./devin --plan                       # Plan mode (describe, don't run)
./devin --auto                       # Auto-approve all actions
./devin --web --port 3000            # Web UI
```

---

## How It Works

Devin follows an **Observe → Understand → Plan → Act → Verify → Continue** loop:

1. **Observe** — Takes a screenshot or runs a shell command to see current state
2. **Understand** — Uses an AI model (Gemini/Claude/GPT) to analyze what it sees
3. **Plan** — Decides the best sequence of actions to complete the task
4. **Act** — Executes: moves mouse, types, clicks, runs commands
5. **Verify** — Takes another screenshot or checks output to confirm success
6. **Continue** — Proceeds to next step or recovers from failure
7. **Complete** — Reports completion only when the task is fully verified

---

## Capabilities

| Capability | Status | Notes |
|------------|--------|-------|
| Mouse control (click, drag, scroll, right-click) | ✓ VERIFIED | pyautogui + xdotool |
| Keyboard control (type, hotkeys, special keys) | ✓ VERIFIED | pyautogui |
| Screenshot capture | ✓ VERIFIED | mss / scrot / PIL |
| AI vision (analyze screenshot) | ✓ VERIFIED | Gemini multimodal |
| Application launching | ✓ VERIFIED | subprocess + xdg-open |
| Window management (list, focus, maximize) | ✓ VERIFIED | xdotool |
| Shell execution (output captured) | ✓ VERIFIED | subprocess |
| GUI terminal execution | ✓ VERIFIED | xterm/gnome-terminal |
| File operations (read, write, edit, delete) | ✓ VERIFIED | native |
| Web search | ✓ VERIFIED | DuckDuckGo API |
| Web fetch (read pages) | ✓ VERIFIED | httpx/requests |
| Browser automation | ✓ VERIFIED | Playwright/Selenium |
| Voice TTS (speak) | ✓ IMPLEMENTED | pyttsx3/gTTS |
| Voice STT (listen) | ✓ IMPLEMENTED | speech_recognition |
| Long-term memory | ✓ VERIFIED | JSON + vector search |
| Clipboard (get/set) | ✓ VERIFIED | pyperclip |
| Git operations | ✓ VERIFIED | subprocess git |
| Python code execution | ✓ VERIFIED | exec + capture |
| System monitoring (CPU, RAM, disk) | ✓ VERIFIED | psutil |
| Network scan (nmap) | ✓ IMPLEMENTED | requires nmap + auth |
| Vulnerability scanning | ✓ IMPLEMENTED | requires auth |
| Cloud integrations (AWS/Azure/GCP) | PARTIALLY | requires credentials |
| Telegram bot control | PARTIALLY | requires bot token |
| Cross-platform (Linux/macOS/Windows) | PARTIALLY | Linux fully tested |
| Multi-model (Gemini/Claude/GPT/Ollama/Hugging Face) | ✓ VERIFIED | auto-fallback across providers, HF live-tested via Qwen 2.5 72B |

---

## Architecture

```
Devin-4.0/
├── main.py                  # Python CLI entry point (Gemini agentic loop)
├── devin                    # Bash launcher (prefers TypeScript CLI)
├── src/                     # TypeScript CLI (primary, full-featured)
│   ├── cli.ts               # Main REPL loop
│   ├── conversation.ts      # System prompt + history management
│   ├── types.ts             # Shared type definitions
│   ├── config.ts            # Config loader (.env + args)
│   ├── providers/           # AI model providers
│   │   ├── anthropic.ts     # Claude (Anthropic)
│   │   ├── gemini.ts        # Gemini (Google)
│   │   ├── openai.ts        # GPT (OpenAI)
│   │   ├── ollama.ts        # Local Ollama models
│   │   └── multi.ts         # Multi-provider router
│   ├── tools/
│   │   ├── definitions.ts   # All 88+ tool schemas
│   │   └── executor.ts      # Tool execution (OS, files, web, security)
│   ├── os/
│   │   ├── automation.ts    # OS automation bridge (TS → Python)
│   │   └── control.ts       # Window/app control
│   ├── ui/
│   │   └── terminal.ts      # Claude Code-style terminal UI
│   ├── memory/              # Persistent memory system
│   ├── agents/              # Research sub-agent
│   ├── security/            # Vulnerability scanner, web scanner
│   ├── voice/               # Voice I/O
│   └── integrations/        # AIA, Jarvis, Gemini CLI, Shannon adapters
├── modules/
│   ├── integrations.py      # Python tool registry (all repos)
│   ├── os_automation.py     # Cross-platform automation backend
│   ├── os_operations/       # Platform-specific (Linux/macOS/Windows)
│   ├── browser.py           # Browser automation
│   ├── voice.py             # TTS/STT
│   └── ...                  # 50+ specialized modules
├── repos/                   # Integrated repo source trees
│   ├── aia/                 # AIA automation + voice + ML
│   ├── soc/                 # self-operating-computer
│   ├── opendevin/           # OpenDevin agent
│   ├── jarvis/              # Jarvis AI assistant
│   ├── cheetah/             # cheetahclaws multi-agent
│   ├── gemini_cli/          # gemini-cli
│   ├── claude_code/         # claude-code
│   ├── shannon/             # Shannon OSINT/network
│   └── security/            # Offensive/defensive security tools
├── external/                # Original git clones (reference)
├── docs/                    # Architecture, compliance, integration docs
├── data/                    # Runtime data (memory, screenshots)
└── venv/                    # Python virtual environment
```

### AI Runtime Flow

```
User Input (text or voice)
        ↓
  Intent Understanding
        ↓
   Tool Selection
        ↓
  Permission Check
        ↓
    Tool Execution
    ├── OS Automation (mouse/keyboard/screenshot)
    ├── Shell/Python execution
    ├── File I/O
    ├── Web search/fetch
    ├── Browser automation
    ├── Voice I/O
    └── Security tools (authorized only)
        ↓
   Result Observation
        ↓
  Verification (screenshot / output check)
        ↓
  Continue / Recover / Complete
```

---

## Slash Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/clear` | Clear conversation history |
| `/status` | CPU, RAM, model, capabilities |
| `/screenshot` | Take and save a screenshot |
| `/memory` | Show stored memories |
| `/remember <fact>` | Save a fact to long-term memory |
| `/tools` | List all available tools (88+) |
| `/repos` | List integrated repositories |
| `/shell <cmd>` | Run a shell command directly |
| `/model [name]` | Show or change AI model |
| `/plan` | Plan mode (describe actions, don't run) |
| `/auto` | Auto-approve all tool calls |
| `/default` | Default mode (confirm dangerous actions) |
| `/voice` | Toggle voice input/output |
| `/verbose` | Toggle verbose debug output |
| `exit` / `quit` | Quit Devin |

---

## Configuration

Create a `.env` file (never commit this):

```env
# Required — at least one of these five
GEMINI_API_KEY=your_gemini_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here   # optional
OPENAI_API_KEY=your_openai_key_here         # optional
HF_TOKEN=your_hf_token_here                 # optional (free tier available)

# Optional
TELEGRAM_BOT_TOKEN=your_bot_token
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
DISPLAY=:0                                  # Linux display (default :0)
```

See `.env.example` for the full list of supported keys.

**Automatic fallback (Python runtime, `main.py`):** if Gemini is unconfigured or
rate-limited, Devin transparently retries the same request against Hugging Face
(`Qwen/Qwen2.5-72B-Instruct`, then Llama 3.1 70B / Mistral 7B / Zephyr 7B). No
code change needed — just set `HF_TOKEN` alongside `GEMINI_API_KEY`.

### Model Selection

```bash
# Use Gemini (default if GEMINI_API_KEY set)
./devin --provider gemini --model gemini-2.5-flash

# Use Claude (requires ANTHROPIC_API_KEY)
./devin --provider anthropic --model claude-opus-5-5

# Use GPT-4 (requires OPENAI_API_KEY)
./devin --provider openai --model gpt-4o

# Use Hugging Face (free-tier — requires HF_TOKEN)
./devin --provider huggingface --model Qwen/Qwen2.5-72B-Instruct

# Use local Ollama
./devin --provider ollama --model llama3.2
```

---

## Security Model

Devin separates capabilities into three tiers:

1. **Safe** — File I/O, web search, memory, conversation (auto-approved)
2. **Caution** — Mouse/keyboard, shell commands, app launching (prompted in default mode)
3. **Dangerous** — Security tools, process kill (requires explicit authorization + `--auto`)

Security tools (nmap, vulnerability scanning, OSINT) require:
- Explicit user authorization in the conversation
- Target must be systems you own or have written permission to test
- Audit logging is maintained at `data/audit.log`

---

## Integrated Repositories

| Repository | Source | Capabilities Used |
|------------|--------|-------------------|
| Hugging Face Inference | huggingface.co/router | Free-tier LLM fallback (Qwen 2.5 72B, Llama 3.1 70B, Mistral, Zephyr) |
| AIA | github.com/kevinhamza/AIA | Automation, voice, ML, social |
| self-operating-computer | github.com/OthersideAI/self-operating-computer | Vision-based computer control |
| OpenDevin | github.com/OpenDevin/OpenDevin | Agent framework, canvas UI |
| cheetahclaws | github.com/OoriData/cheetahclaws | Multi-agent, security analysis |
| Jarvis (Concept-Bytes) | github.com/Concept-Bytes/Jarvis | Voice assistant, tools |
| JARVIS-microsoft | github.com/microsoft/JARVIS | HuggingGPT task planning |
| gemini-cli | github.com/google-gemini/gemini-cli | Gemini CLI patterns |
| claude-code | (source collection) | Agentic loop patterns |
| shannon | (integrated) | OSINT, network intelligence |
| hexstrike-ai | (integrated) | Security tooling |
| Devin-1/2/3 | Earlier versions | Core architecture |

Full details: see `docs/INTEGRATION_MATRIX.md`

---

## Testing

```bash
# Python smoke test
python main.py --test

# TypeScript build test
npm run build

# Run test suite
python -m pytest tests/ -v

# TypeScript tests
npm test
```

Key test areas:
- Import/startup tests
- Tool registry verification
- Shell + Python execution
- File I/O
- Model API connectivity (requires API keys)
- OS automation (requires display)

---

## Known Limitations

- **GUI automation** requires a display server. On headless servers, use `Xvfb` or run in a VNC session.
- **Voice input** requires a microphone and working audio. Uses `speech_recognition` + Google STT.
- **Cloud integrations** (AWS/Azure/GCP) require valid credentials and are not tested without them.
- **Security tools** require the underlying binary (nmap, etc.) to be installed.
- **Screenshot analysis** makes an additional AI API call per screenshot — costs quota.
- **Windows support** is implemented but less tested than Linux.

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run the test suite
5. Submit a PR

See `SECURITY.md` for responsible disclosure.

---

## License

MIT — [@kevinhamza](https://github.com/kevinhamza)
