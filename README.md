<div align="center">

<h1>🤖 Devin 4.0</h1>
<h3>The most capable open-source autonomous AI agent — fully controls your OS, works with zero API keys</h3>

[![CI](https://github.com/kevinhamza/Devin-4.0/actions/workflows/devin-ci.yml/badge.svg)](https://github.com/kevinhamza/Devin-4.0/actions/workflows/devin-ci.yml)
[![Security Scan](https://github.com/kevinhamza/Devin-4.0/actions/workflows/security-scan.yml/badge.svg)](https://github.com/kevinhamza/Devin-4.0/actions/workflows/security-scan.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Stars](https://img.shields.io/github/stars/kevinhamza/Devin-4.0?style=social)](https://github.com/kevinhamza/Devin-4.0/stargazers)

<br/>

> **Works completely free — no API key required.**  
> Uses HuggingFace free tier or free-claude-code proxy automatically when no paid key is set.

</div>

---

## ⚡ Install

### pip install

```bash
pip install devin
devin          # done — interactive REPL starts
```

> _Once published to PyPI. Until then use the git URL:_
> ```bash
> pip install git+https://github.com/kevinhamza/Devin-4.0
> devin
> ```

### curl one-liner

```bash
curl -fsSL https://github.com/kevinhamza/Devin-4.0/raw/main/scripts/install.sh | sh
devin
```

Both methods install the `devin` command globally — no `cd`, no virtual-env activation needed.

---

## ⚡ Quick Start (manual clone)

### 1 — Clone & install

```bash
git clone https://github.com/kevinhamza/Devin-4.0
cd Devin-4.0
pip install -r requirements.txt
```

### 2 — Add an API key (optional — works without one)

```bash
cp .env.example .env
# Then open .env and paste at least one key, e.g.:
#   HF_TOKEN=hf_...          ← free at huggingface.co/settings/tokens
#   GEMINI_API_KEY=...        ← free tier at aistudio.google.com
#   ANTHROPIC_API_KEY=...     ← paid, best quality
```

### 3 — Run

```bash
# Interactive REPL (recommended)
python3 agent.py

# Or use the shell launcher (same thing, picks Python automatically)
chmod +x devin
./devin

# One-shot task — no REPL
python3 agent.py "open a browser and go to github.com"

# Headless / server (no display)
_HAS_DISPLAY=false python3 agent.py "scrape the top 10 Hacker News headlines"
```

> **Zero-key mode:** if no key is set, Devin falls back to the HuggingFace free tier automatically.

---

## 🧠 What Makes Devin Different

| Feature | Devin 4.0 | AutoGPT | Open Interpreter | Devin (commercial) |
|---|:---:|:---:|:---:|:---:|
| **Zero API key needed** | ✅ | ❌ | ❌ | ❌ |
| **Full OS mouse/keyboard control** | ✅ | ❌ | Partial | ✅ |
| **Screen vision (AI sees your screen)** | ✅ | ❌ | ❌ | ✅ |
| **Voice input + output** | ✅ | ❌ | ❌ | ❌ |
| **213 built-in tools** | ✅ | ~30 | ~20 | Unknown |
| **5 AI providers + auto-fallback** | ✅ | 1–2 | 1–2 | 1 |
| **110+ capability modules** | ✅ | ❌ | ❌ | ❌ |
| **Local LLM support (Ollama)** | ✅ | Partial | ✅ | ❌ |
| **Open source** | ✅ | ✅ | ✅ | ❌ |
| **Price** | **Free** | API cost | API cost | $500/mo |

---

## 🎯 What Devin Can Do

### 👁️ See & Understand
- Takes screenshots and analyzes them with AI vision
- Reads any UI element, window, dialog, or terminal output
- Identifies positions, text, and state of everything on screen

### 🖱️ Control Your Computer
- Clicks, types, scrolls, drags — full mouse + keyboard control
- Works on Linux (X11/Wayland), macOS, and Windows
- Opens and operates any GUI application

### 🌐 Automate the Web
- Full browser control via Playwright and Selenium
- Vision-guided element finding — no selectors needed
- Scrapes, fills forms, logs in, navigates complex SPAs

### 🗣️ Speak & Listen
- Text-to-speech (pyttsx3, gTTS, ElevenLabs)
- Speech-to-text via Whisper and SpeechRecognition
- Continuous voice command mode

### 💻 Write & Execute Code
- Python execution with live stdout capture
- Shell subprocess with timeout and safety checks
- Iterates until the code actually works

### 📁 Manage Everything
- Files: read, write, move, archive, diff, search
- Processes: list, kill, monitor, spawn
- Network: HTTP requests, scraping, API calls
- Databases: SQLite, query, CRUD

### 🔐 Security & Pentesting (Authorized Use)
- nmap, sqlmap, Metasploit integration
- Network analysis, vulnerability scanning
- Requires explicit authorization — refuses unauthorized use

---

## 🤖 AI Providers

Devin automatically picks the best available provider. Set any one key — or none.

| Priority | Provider | Variable | Free? | Best Model |
|:---:|---|---|:---:|---|
| 1 | **Anthropic Claude** | `ANTHROPIC_API_KEY` | No | claude-sonnet-5 |
| 2 | **Google Gemini** | `GEMINI_API_KEY` | Limited | gemini-2.5-flash |
| 3 | **OpenAI GPT** | `OPENAI_API_KEY` | No | gpt-4o |
| 4 | **HuggingFace** | `HF_TOKEN` | ✅ Yes | Qwen2.5-72B |
| 5 | **Ollama (local)** | `OLLAMA_BASE_URL` | ✅ Yes | llama3.1 |
| 6 | **Free Claude proxy** | `CLAUDE_SESSION_KEY` | ✅ Yes | claude-sonnet |

**Override:** `DEVIN_PROVIDER=huggingface python3 agent.py`

### Zero-Key Setup (Completely Free)

```bash
# Option A: HuggingFace free tier
HF_TOKEN=your_free_token  # get at huggingface.co/settings/tokens

# Option B: Free Claude proxy (no account needed)
# Install: curl -fsSL https://github.com/Alishahryar1/free-claude-code/raw/main/scripts/install.sh | sh
# Run in background: fcc-server
CLAUDE_SESSION_KEY=your_session_cookie

# Option C: Local Ollama (fully offline)
OLLAMA_BASE_URL=http://localhost:11434
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      agent.py                           │
│              11,776 lines · 213 tools                   │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ AI Core  │  │ OS Layer │  │  Tools   │             │
│  │ 5 provs  │  │mouse/kbd │  │ 213 fns  │             │
│  │ fallback │  │ vision   │  │ REPL loop│             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
          ↕ graceful import (fails silently)
┌─────────────────────────────────────────────────────────┐
│                   modules/  (110+ files)                │
│                                                         │
│  browser     │ voice        │ os_agent    │ security    │
│  reasoning   │ web_scrape   │ analytics   │ automation  │
│  memory      │ social_media │ robotics    │ cloud       │
│  Gemini      │ OpenAI       │ HuggingFace │ Claude      │
│  + 70 more capability modules…                          │
└─────────────────────────────────────────────────────────┘
          ↕
┌─────────────────────────────────────────────────────────┐
│            src/  — TypeScript CLI (optional)            │
│   providers · memory · tools · voice · agents · ui     │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Project Structure

```
Devin-4.0/
├── agent.py           # Core runtime — 11,776 lines, 213 tools, 5 AI providers
├── main.py            # Entry point with dynamic module discovery
├── devin              # Shell launcher (chmod +x devin && ./devin)
├── modules/           # 110+ plug-in capability modules
│   ├── browser.py          # Playwright/Selenium browser control
│   ├── browser_agent.py    # Vision-guided autonomous browsing
│   ├── os_agent.py         # Full OS control (mouse, keyboard, screen)
│   ├── voice_engine.py     # Speech I/O
│   ├── reasoning_engine.py # Chain-of-thought planning
│   ├── free_claude_provider.py  # Zero-key Claude fallback
│   └── ...  (100+ more)
├── src/               # TypeScript CLI (optional alternative interface)
│   ├── providers/     # Claude · Gemini · OpenAI · HuggingFace · Ollama
│   ├── tools/         # Tool definitions and executors
│   ├── memory/        # SQLite conversation memory
│   └── ui/            # Terminal UI components
├── tests/             # 130 tests
├── .env.example       # All supported environment variables
└── requirements.txt   # Python dependencies
```

---

## 🖥️ Platform Support

| Platform | Status | Notes |
|---|:---:|---|
| **Linux** | ✅ Full | X11/Wayland or headless with `_HAS_DISPLAY=false` |
| **macOS** | ✅ Full | May need accessibility permissions |
| **Windows** | ✅ Full | PowerShell required for some features |

---

## 🛠️ Advanced Usage

```bash
# One-shot task
python3 agent.py "take a screenshot, describe what's on screen, and open a browser"

# Run the test suite
python3 agent.py --test

# Show all loaded capabilities
python3 main.py --caps

# Use a specific provider
DEVIN_PROVIDER=gemini python3 agent.py

# Headless (no display, e.g. CI/server)
_HAS_DISPLAY=false python3 agent.py "write and run a Python web scraper"

# TypeScript CLI (alternative interface)
npm install && npm run dev
```

### Useful `.env` Options

```bash
DEVIN_MODEL=claude-sonnet-5        # override model name
DEVIN_MAX_TOKENS=8192              # token limit per response
DEVIN_THINKING=true                # enable chain-of-thought reasoning
DEVIN_PERMISSION_MODE=auto_approve # auto-approve all tool calls
DEVIN_VOICE=true                   # enable voice I/O
DEVIN_VERBOSE=true                 # verbose logging
```

---

## 🔐 Security

Devin is built for **authorized use only**:

- Security and pentesting tools require explicit authorization in the conversation
- Unauthorized targeting, credential theft, persistence, and lateral movement are refused at the tool level
- API keys are never hard-coded — always loaded from `.env`
- `.env` is in `.gitignore` and must never be committed

---

## 🤝 Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Add your changes (a new module goes in `modules/`, register its tools in `agent.py`)
4. Run tests: `python3 agent.py --test`
5. Open a PR

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full system design.

---

## 📄 License

MIT — free for personal and commercial use. See [`LICENSE`](LICENSE).

---

<div align="center">

**If Devin helped you — give it a ⭐ and share it.**  
[GitHub Issues](https://github.com/kevinhamza/Devin-4.0/issues) · [Discussions](https://github.com/kevinhamza/Devin-4.0/discussions)

</div>
