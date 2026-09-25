# Devin AGI 4.0

Devin 4.0 is a fully autonomous OS-controlling AI agent. It operates a
real computer like a human — using mouse, keyboard, and screen vision —
while reasoning with state-of-the-art language models.

## What Devin Can Do

- **See the screen** — takes screenshots, analyzes them with AI vision,
  and describes what it observes
- **Control the mouse and keyboard** — clicks, types, scrolls, drags,
  uses hotkeys on Linux, macOS, and Windows
- **Open and operate applications** — browsers, terminals, editors,
  any GUI app
- **Automate the web** — full browser control via Playwright or Selenium
  with vision-guided element finding
- **Speak and listen** — text-to-speech output, speech-to-text input,
  continuous voice command mode
- **Write and run code** — Python exec with stdout capture, shell
  subprocess with timeout
- **Search the web** — HTTP requests, web scraping, search APIs
- **Manage files** — read, write, move, archive, diff
- **Monitor the system** — CPU, memory, disk, processes, network, GPU
- **Remember things** — persistent SQLite memory, session history,
  named facts
- **Use any LLM** — Claude, Gemini, OpenAI, HuggingFace free-tier,
  Ollama local, free Claude fallback

## Quick Start

```bash
# Clone
git clone https://github.com/kevinhamza/Devin-4.0
cd Devin-4.0

# Install Python deps
pip install -r requirements.txt

# Copy and fill environment variables
cp .env.example .env
# Edit .env — add at minimum HF_TOKEN for free HuggingFace models

# Start the REPL
./devin

# Or run a one-shot task
python3 agent.py "open a browser and search for Python docs"

# Run tests
python3 agent.py --test

# Show loaded capabilities
python3 main.py --caps
```

## AI Provider Setup

Devin automatically selects the best available provider based on
environment variables. Set at least one:

| Provider | Environment Variable | Free? |
|---|---|---|
| HuggingFace | `HF_TOKEN` | Yes (free tier) |
| Claude | `ANTHROPIC_API_KEY` | No |
| Gemini | `GEMINI_API_KEY` | Limited free |
| OpenAI | `OPENAI_API_KEY` | No |
| Ollama | `OLLAMA_BASE_URL` | Yes (local) |
| Free Claude | `CLAUDE_SESSION_KEY` | Yes |

Priority order: Claude → Gemini → OpenAI → HuggingFace → Free Claude

Override with: `DEVIN_PROVIDER=huggingface`

## HuggingFace Free Tier

Set `HF_TOKEN` in your `.env` file to use HuggingFace's free inference
API. Devin will automatically cycle through these free models:

1. `Qwen/Qwen2.5-72B-Instruct` (best quality)
2. `meta-llama/Meta-Llama-3.1-70B-Instruct`
3. `mistralai/Mixtral-8x7B-Instruct-v0.1`
4. `mistralai/Mistral-7B-Instruct-v0.3`
5. `HuggingFaceH4/zephyr-7b-beta` (fallback)

## OS Requirements

| Platform | Status | Notes |
|---|---|---|
| Linux | Full support | Requires display (X11/Wayland) or `_HAS_DISPLAY=false` for headless |
| macOS | Full support | May need accessibility permissions for mouse/keyboard |
| Windows | Full support | PowerShell required for some fallbacks |

## Optional Dependencies

```bash
# Core (highly recommended)
pip install psutil pynput pillow mss pyperclip

# Browser automation
pip install playwright selenium beautifulsoup4
python3 -m playwright install chromium

# Voice
pip install pyttsx3 gtts SpeechRecognition openai-whisper pyaudio

# GPU monitoring
pip install GPUtil

# Vision AI (if using Claude/Gemini/OpenAI for vision)
pip install anthropic google-generativeai openai
```

## Architecture

See `docs/ARCHITECTURE.md` for the full system diagram.

## Directory Structure

```
agent.py          # Runtime (136 tools, 5 AI providers, REPL)
main.py           # Entry point with dynamic module discovery
devin             # Bash launcher
modules/          # 103+ capability modules
tests/            # Test suite (40 core tests)
docs/             # Architecture, compliance, integration docs
src/              # Legacy TypeScript CLI
.env.example      # All supported environment variables
```

## Security

Devin is designed for **authorized use only**. Security tools (nmap,
sqlmap, Responder, nishang) require explicit user authorization in the
conversation. Unauthorized targeting, credential theft, persistence,
and lateral movement are refused at the tool level.

See `docs/INTEGRATION_MATRIX.md` §Security Repositories.

## License

MIT License — see `LICENSE`.
