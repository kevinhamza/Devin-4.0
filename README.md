# Devin AGI 4.0

**A deeply autonomous AI agent that controls your computer like a real engineer.**

Controls mouse, keyboard, screen, files, shell, browser, and voice — on Linux, macOS, and Windows.
Thinks, plans, acts, and verifies using **213 tools** and **6 AI providers** (including free HuggingFace).
Works headless or with full GUI control. No GUI required for most tasks.

```
  ╭─────────────────────────────────────────────────────────────────────╮
  │ Devin AGI v4.0.0  —  Autonomous OS-Controlling AI                   │
  │ cwd: /home/user/Devin-4.0                                           │
  │ model: Qwen3-235B-A22B  provider: huggingface  mode: auto           │
  │ platform: Linux  gui  ·  tools: 213  ·  modules: 16  ·  memories: 0│
  ╰─────────────────────────────────────────────────────────────────────╯

  ✓ Connected to Huggingface (Qwen3-235B-A22B)
  Free tier  ·  Qwen3-235B · DeepSeek-V3 · Llama3.3 · 1000s more

  Try: open firefox and search for python tutorials

❯ Devin-4.0 open firefox, go to google.com and search python tutorials

● observe_and_plan(goal='open firefox and search python tutorials')
↳ Current screen: desktop. Plan: open_application(firefox) → screenshot → click address bar → type URL → search

● open_and_wait(app_name='firefox', wait_seconds=3)
↳ Opened firefox (pid=63784) | Loaded: YES

● screenshot_and_analyze(prompt='Where is the Firefox address bar? Give exact (x,y) pixel coordinates.')
↳ Address bar visible at approximately (680, 45) — the URL input at top of browser

● mouse_click(x=680, y=45)
↳ Clicked left at (680, 45)

● keyboard_hotkey(keys=['ctrl', 'a'])
↳ OK

● keyboard_type(text='https://www.google.com')
↳ Typed 22 chars

● keyboard_press(key='Return')
↳ Pressed Return

● sleep(seconds=2)

● screenshot_and_analyze(prompt='Is Google loaded? Where is the search box?')
↳ Google homepage visible. Search box at approximately (680, 300).

● mouse_click(x=680, y=300)
↳ Clicked left at (680, 300)

● keyboard_type(text='python tutorials')
↳ Typed 16 chars

● keyboard_press(key='Return')
↳ Pressed Return

● screenshot_and_analyze(prompt='Did python tutorial results appear?')
↳ Yes — showing search results for "python tutorials"

● task_complete(result='Opened Firefox, navigated to Google, searched for python tutorials. Results are displayed.')
↳ TASK_COMPLETE

✓ Task complete

Done. Firefox is showing python tutorial search results.
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Linux / macOS / Windows
- At least one AI provider key (free options available — see below)
- For GUI/mouse/keyboard control on Linux: a running X11 or Wayland display session

### Install

```bash
git clone https://github.com/kevinhamza/Devin-4.0
cd Devin-4.0

# Optional: virtual environment (recommended)
python3 -m venv venv && source venv/bin/activate   # Linux/macOS
# python -m venv venv && venv\Scripts\activate      # Windows

# Install dependencies
pip install -r requirements.txt

# Set up API keys
cp .env.example .env
# Edit .env — add at least one key (HF_TOKEN is free)
```

### Run

```bash
# Interactive REPL (recommended)
./devin

# Same but via Python directly
python3 agent.py

# One-shot task
./devin "write a Python script that monitors CPU usage every 5 seconds"
python3 agent.py "open Firefox and search for AI news"

# Choose a specific AI provider
./devin --provider huggingface "audit the torvalds/linux GitHub repo"
./devin --provider gemini "what's the weather today?"
./devin --provider ollama "explain this code"    # no key needed, requires Ollama

# Choose a specific model
./devin --model Qwen/Qwen3-32B "solve this math problem step by step"
```

---

## Configuration

Copy `.env.example` to `.env` and fill in at least one API key:

```bash
cp .env.example .env
```

### AI Providers (priority order for auto-selection)

| Provider | Key Variable | Free? | Best Model |
|----------|-------------|-------|-----------|
| **HuggingFace** | `HF_TOKEN` | ✅ Free | `Qwen/Qwen3-235B-A22B` (best free 2025) |
| **Google Gemini** | `GEMINI_API_KEY` | ✅ Free tier | `gemini-3.6-flash` |
| **Anthropic Claude** | `ANTHROPIC_API_KEY` | Paid | `claude-sonnet-4-6` |
| **OpenAI** | `OPENAI_API_KEY` | Paid | `gpt-4o-mini` |
| **Free Claude Code** | *(proxy, no key)* | ✅ Free | `claude-sonnet-4-5` |
| **Ollama** | *(none needed)* | ✅ Free | `llama3.2` (local) |

### Fastest Free Setup (HuggingFace)

1. Go to [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)
2. Create a free Read token
3. Add to `.env`:
   ```
   HF_TOKEN=hf_your_token_here
   ```
4. Run: `./devin`

Available free HuggingFace models (all 2025 latest):
- `Qwen/Qwen3-235B-A22B` — best free reasoning model (default)
- `deepseek-ai/DeepSeek-V3-0324` — excellent all-around
- `Qwen/Qwen3-32B` — fast + capable
- `meta-llama/Llama-3.3-70B-Instruct` — great instruction following
- `Qwen/Qwen2.5-Coder-32B-Instruct` — best free code model
- `deepseek-ai/DeepSeek-R1-Distill-Llama-70B` — chain-of-thought reasoning

Switch models with `/model <name>` or set `HF_MODEL=<name>` in `.env`.

### Free Claude Code Proxy (No API Key Required)

[free-claude-code](https://github.com/alishahryar1/free-claude-code) routes Claude API calls to 55+ free providers. Use it as a provider:

```bash
pip install free-claude-code
fcc-server  # start the proxy server
./devin --provider fcc "your task here"
```

Or set `FCC_BASE_URL=http://127.0.0.1:3000` in `.env` and Devin auto-detects it.

---

## What Devin Can Do

### OS Control (Like a Real User)
Devin uses the **observe → reason → act → verify** loop for all GUI tasks:

```
observe_and_plan(goal)          → see what's on screen, make a plan
screenshot_and_analyze(prompt)  → take screenshot + AI analysis + coordinates
mouse_click(x, y)               → click exactly where needed
keyboard_type(text)             → type any text
keyboard_hotkey(['ctrl', 'c'])  → keyboard shortcuts
open_application('firefox')     → launch any app
focus_window('Terminal')        → switch windows
click_by_description('Submit button')  → find + click by description
```

**All OS control tools:**
- **Screenshots**: `screenshot()`, `screenshot_and_analyze()`, `observe_and_plan()`
- **Mouse**: `mouse_click()`, `mouse_double_click()`, `mouse_right_click()`, `mouse_move()`, `mouse_drag()`, `mouse_scroll()`
- **Keyboard**: `keyboard_type()`, `keyboard_press()`, `keyboard_hotkey()`, `type_and_submit()`
- **Windows**: `open_application()`, `focus_window()`, `list_windows()`, `get_screen_size()`
- **Clipboard**: `clipboard_get()`, `clipboard_set()`
- **Helpers**: `click_and_verify()`, `open_and_wait()`, `click_by_description()`

### Shell & Code Execution
```
execute_shell("apt install nmap -y")    → run any shell command
execute_python("print(2+2)")            → run Python code
write_and_run("script.py", code)        → write file + execute
install_and_verify("requests")          → install Python package
git_command("status")                   → run git commands
```

### Web & Browser
```
web_search("latest AI models 2025")     → DuckDuckGo/Bing search
web_fetch("https://example.com")        → fetch URL content
open_url("https://github.com")          → open in default browser
browser_navigate("https://google.com")  → Selenium/Playwright control
browser_get_text()                      → extract page text
browser_click("Submit")                 → click elements by label
browser_screenshot()                    → screenshot the browser
github_repo_audit("torvalds/linux")     → full GitHub repo audit
```

### File & System Management
```
read_file("code.py")                    → read any file
write_file("output.txt", content)       → write files
list_files("/home/user")                → list directory
get_system_info()                       → CPU, memory, disk, OS
list_processes()                        → running processes
platform_info()                         → OS details
```

### Memory & Reasoning
```
remember("my project is at /home/user/proj")  → save facts persistently
recall("project path")                        → search memories
think_and_plan("complex task")                → reason about approach
decompose_task("big task")                    → break into steps
multi_step_workflow(steps_json)               → execute structured plan
batch_execute(tools_json)                     → run tools in parallel
```

### Voice Input
```bash
./devin --voice              # start in voice mode
# In REPL: /voice            # record one voice command
```
Requires: `pip install SpeechRecognition pyaudio`

### Security & Pentesting (Authorized Only)
For authorized environments (HackTheBox, TryHackMe, your own VMs):
```
execute_shell("nmap -sV target")
execute_shell("burpsuite &")           → open Burp Suite
execute_shell("sqlmap -u 'url'")
execute_shell("gobuster dir -u ...")
screenshot_and_analyze("Find open ports in nmap output")
```
Set `AUTHORIZED_SECURITY=1` in `.env` to enable extended security tools.

---

## Slash Commands

```
/help              — This help
/tools [cat]       — List all 213 tools (filter by category)
/status            — Provider, model, API keys, capabilities
/providers         — All providers and their status
/provider <name>   — Switch provider: gemini|claude|openai|huggingface|fcc|ollama
/model <name>      — Switch model (e.g. /model Qwen/Qwen3-32B)
/memory [query]    — Search persistent memory
/remember <fact>   — Save a fact to memory
/forget            — Clear all memories (with confirmation)
/history           — Show conversation history
/save [file]       — Save conversation transcript
/shell <cmd>       — Run shell command directly
/screenshot        — Take screenshot + optional analysis
/voice             — Record voice input → execute as task
/think <task>      — Plan a task step-by-step
/workflow <task>   — Execute as structured multi-step workflow
/pentest <target>  — Authorized pentest assessment
/audit [target]    — System/security audit
/audit_repo <o/n>  — Audit a GitHub repo (e.g. /audit_repo torvalds/linux)
/repos             — List integrated external repositories
/integrations      — Show all module integration status
/os                — OS/platform info
/stats             — Session statistics
/demo              — Quick health check
/compact           — Compress conversation history
/new               — Start fresh conversation
/clear             — Clear screen
/exit              — Exit
```

---

## Architecture

```
User Input (text / voice / one-shot CLI)
         ↓
   Intent Classification
         ↓
   Planning (think_and_plan / decompose_task)
         ↓
   Capability Registry (213 tools, 6 AI providers)
         ↓
   Permission / Safety Layer
         ↓
   Execution Engine
   ┌──────────────────────────────────────────────┐
   │  OS Control      Shell      Browser          │
   │  Mouse/Keyboard  Files      Web Search       │
   │  Screenshots     Git        Cloud Services   │
   │  Voice           Memory     Security Tools   │
   └──────────────────────────────────────────────┘
         ↓
   Observation (screenshot / read output / verify)
         ↓
   Verification (did it work? what changed?)
         ↓
   Recovery (if failed, try different approach)
         ↓
   Completion (task_complete with summary)
```

### Core Agentic Loop
```
THINK   → Reason about goal, tools available, best approach
PLAN    → decompose_task() or think_and_plan() for complex work
OBSERVE → screenshot() or read_file() or get_system_info()
ACT     → Execute with the right tool
VERIFY  → Confirm step worked (screenshot, check output, check file)
RECOVER → If failed: change strategy, different tool, different approach
LOOP    → Repeat until all steps verified complete
DONE    → task_complete("what was done and verified")
```

### GUI Automation Loop
```
Step 1: observe_and_plan("goal")       — analyze screen, make plan
Step 2: open_application("app")        — launch the application
Step 3: screenshot_and_analyze("...")  — find UI elements + coordinates
Step 4: mouse_click(x, y)             — click exactly where needed
Step 5: keyboard_type("text")         — type input
Step 6: keyboard_press("Return")      — submit
Step 7: screenshot_and_analyze("...")  — verify result
Step 8: Continue or recover
```

---

## Integrated Repositories

Devin integrates capabilities from 24 external repositories:

| Repository | Capabilities |
|-----------|-------------|
| AIA | Automation, voice assistant, device control, ML |
| Self-Operating Computer | Screenshot-driven computer control |
| Devin 2.0, 3.0 | Previous Devin generations' capabilities |
| Gemini CLI | Google Gemini integration |
| Claude Code | Anthropic Claude integration |
| CheetahClaws | Browser automation, file operations |
| HexStrike AI | Security assessment tools |
| OpenDevin | Open-source agent capabilities |
| Shannon | Communication tools |
| Jarvis (Microsoft + Concept-Bytes) | Multi-tool orchestration |
| OpenClaw | Web automation |
| Hackability | Security research tools |
| Responder, Nishang | Defensive security (source-preserved, isolated) |
| PowerTools, Airgorah | System utilities |
| MoltBots | Bot automation |
| Holomat | Extended automation |

---

## Cross-Platform Support

| Feature | Linux | macOS | Windows |
|---------|-------|-------|---------|
| Shell execution | ✅ | ✅ | ✅ |
| File management | ✅ | ✅ | ✅ |
| Web search | ✅ | ✅ | ✅ |
| Mouse control | ✅ X11/Wayland | ✅ | ✅ |
| Keyboard control | ✅ | ✅ | ✅ |
| Screenshots | ✅ | ✅ | ✅ |
| App launching | ✅ | ✅ | ✅ |
| Voice I/O | ✅ | ✅ | ✅ |
| Memory (SQLite) | ✅ | ✅ | ✅ |
| Browser (Selenium) | ✅ | ✅ | ✅ |
| Browser (Playwright) | ✅ | ✅ | ✅ |

Linux GUI tools require a running X11/Wayland session (`DISPLAY=:0`).

---

## Testing

```bash
# Core tests (130 tests, no AI required)
python3 agent.py --test

# End-to-end demo (no AI required)
python3 tests/demo_workflow.py

# Full test suite
pytest tests/

# TypeScript build check
npm run build
npm test
```

---

## Security

- **Default**: safe tools (files, web, math, memory) — auto-execute
- **Caution**: shell, mouse, keyboard — execute + show output  
- **Authorized**: security tools (nmap, sqlmap, burpsuite) — require `AUTHORIZED_SECURITY=1` in `.env`
- **Never**: unauthorized targeting, credential theft, persistence, lateral movement

Security repositories (Responder, Nishang) are source-preserved but **not exposed** through the autonomous runtime.

---

## Troubleshooting

**"No API key found"**
→ Add at least one key to `.env`. Easiest free option: `HF_TOKEN` from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

**GUI tools not working on Linux**
→ Make sure X11 is running: `echo $DISPLAY` should show `:0` or `:1`
→ Install: `pip install pyautogui python-xlib`
→ Set `DISPLAY=:0` in `.env` if needed

**Browser tools not working**
→ Install: `pip install selenium playwright`
→ For Playwright: `playwright install chromium`

**Voice not working**  
→ Install: `pip install SpeechRecognition pyaudio`
→ Test microphone access

**HuggingFace rate limits**
→ Free tier has limits; Devin auto-retries with backoff
→ Switch to a smaller/faster model: `/model meta-llama/Meta-Llama-3.1-8B-Instruct`

---

## Environment Variables

See `.env.example` for the complete list. Key variables:

```bash
HF_TOKEN=hf_...                    # HuggingFace token (free)
HF_MODEL=Qwen/Qwen3-235B-A22B     # HuggingFace model override
GEMINI_API_KEY=AI...               # Google Gemini
ANTHROPIC_API_KEY=sk-ant-...       # Anthropic Claude
OPENAI_API_KEY=sk-...              # OpenAI
FCC_BASE_URL=http://127.0.0.1:3000 # Free Claude Code proxy
OLLAMA_BASE_URL=http://localhost:11434 # Ollama local LLM
DISPLAY=:0                         # Linux X11 display
AUTHORIZED_SECURITY=0              # Enable security tools (set to 1 for authorized testing)
TELEGRAM_BOT_TOKEN=                # Remote control via Telegram
VOICE_LANG=en-US                   # Voice recognition language
```

---

## License

MIT — see [LICENSE](LICENSE)

---

*Devin AGI 4.0 — Autonomous OS-Controlling AI Agent*  
*Powered by HuggingFace (free), Google Gemini (free), Anthropic Claude, OpenAI, or Ollama*
