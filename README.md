# 🦞 Devin AGI

Devin is a large, modular personal-assistant agent: a central LLM-driven "think → act" loop (`main.py`) that can call **195 real, working tools** — file/OS operations, shell and Python execution, network and web-application scanning, threat intelligence (MITRE ATT&CK, VirusTotal, IOC feeds), desktop and browser automation, vision-based screen control, robotics, quantum computing simulation and post-quantum cryptography, differential privacy and PII redaction, digital twins and chaos engineering, a CTF/blue-team training range, GDPR/CCPA/CFAA compliance advisories, crypto-market analysis, and more. It runs entirely on your own machine.

This guide gets you from a fresh clone to a running agent with the fewest surprises. Every step below has been run end-to-end, not just written from the source.

## 🌟 Key Features

- **Runs for free, no credit card:** a Google AI Studio (Gemini) API key has a genuine free tier and is enough to run the *full* assistant — every tool below, real tool-calling, everything. OpenAI, Anthropic, and Perplexity keys are optional extras.
- **Offline mock mode:** no API key at all still gets you a working agent loop against a canned mock model, for development or CI.
- **195 real tools**, not stubs — see [What Devin Can Do](#-what-devin-can-do) below.
- **Full OS control:** mouse, keyboard, screenshots, and a vision-based "look at the screen and operate it" mode.
- **Live visual canvas:** a real-time web dashboard (port 5005) showing Devin's thoughts, logs, and outputs as it works.
- **Persistent memory:** local vector-based long-term memory, so Devin recalls relevant context from past sessions.
- **Safety by default:** every tool that can have a real side effect (deleting files, running shell commands, controlling IoT devices, restoring backups, etc.) is flagged `is_dangerous` and requires your explicit confirmation before it runs, every time.

---

## 🚀 Step-by-Step Setup Guide

### 1. Prerequisites

- **Python 3.10, 3.11, or 3.12** (this is what CI tests against; 3.11 is what this guide was validated on).
- **On Debian/Ubuntu**, install the audio build headers *before* `pip install`, or two packages (`PyAudio`, `simpleaudio`) will fail to build:
  ```bash
  sudo apt-get update && sudo apt-get install -y portaudio19-dev libasound2-dev
  ```
  (macOS: `brew install portaudio`. Windows: these ship as prebuilt wheels, no extra step needed.)

### 2. Clone and Install

```bash
git clone --recurse-submodules https://github.com/kevinhamza/Devin-4.0.git
cd Devin-4.0
# Already cloned without --recurse-submodules? Fetch them now:
# git submodule update --init --recursive

# A virtual environment is strongly recommended -- this repo's own
# code-indexer walks the project directory on startup, and a heavy venv
# created *inside* the repo makes that slower (see Troubleshooting).
python3 -m venv ../devin-venv
source ../devin-venv/bin/activate   # Windows: ..\devin-venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt

# Used by the voice/NLU pipeline
python -m spacy download en_core_web_sm
```

`requirements.txt` also lists an **Extended Capabilities** section (quantum computing, differential privacy, PII redaction, post-quantum crypto, etc.) — those packages are optional. Every tool that needs one degrades gracefully with a clear warning if it's missing, so you can skip them and add only what you actually want later.

Run the pre-flight check to confirm everything installed correctly:
```bash
python bootstrap.py
```
A missing `adb` or `ros2` is expected and fine unless you have Android or ROS 2 hardware — those tools just report unavailable.

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Then edit `.env`. The one decision that matters is **`DEVIN_MODE`**:

- **`DEVIN_MODE=mock`** (the default) — no API key needed at all. Devin runs against a canned offline model. Good for a first look, development, or CI.
- **`DEVIN_MODE=live`** — real reasoning and tool selection. Set **one** of these three (in priority order — Claude wins if more than one is set):
  ```env
  GEMINI_API_KEY="..."      # Recommended: free tier, no billing setup. Get one at https://aistudio.google.com/apikey
  ANTHROPIC_API_KEY="..."
  OPENAI_API_KEY="..."
  ```
  Leave the ones you're not using **blank** (`""`), not the placeholder text — a non-empty placeholder string is still "set" as far as the code is concerned and will be tried first.

Everything else in `.env` (Telegram, VirusTotal, cloud provider credentials, robot serial port) is optional and only unlocks the corresponding tools; leaving it unset just disables that one feature with a log warning, nothing breaks.

### 4. Running Devin

```bash
python main.py            # Text mode -- type your goal when prompted
python main.py --voice    # Voice mode -- speak your goal instead
```

**What happens on startup**, so you're not surprised:
1. Four background servers start (cloud integration, analytics, mobile integration, AI learning — ports 5002/5004/5006/5007). A cloud-integration error with no cloud credentials configured is expected and harmless.
2. Devin indexes its own source code for the code-retrieval tool. This takes a few seconds.
3. You're prompted for your goal.

### 5. Accessing the Live Canvas

Once running, open `http://localhost:5005` to watch Devin's live log/status feed.

---

## 🛠️ Usage Examples

- *"List the files in the current directory."*
- *"Look up MITRE ATT&CK technique T1059.003 and summarize the recommended mitigations."*
- *"Scan example.com's attack surface for open ports and subdomains."* *(you'll be asked to confirm — this is a real scan)*
- *"Hash this string with SHA-256, then encrypt it."*
- *"Open Chrome, go to a URL, and check if the page loaded."*
- *"Move my mouse to the top-left corner and take a screenshot."*

---

## 🧰 What Devin Can Do

Run this to see the live, current tool list at any time (grouped by facade, with descriptions):
```bash
python -c "from modules.tool_executor import ToolExecutor; te = ToolExecutor(); [print(f'{n}: {t[\"description\"]}') for n, t in te.tools.items()]"
```

Roughly, by category:

| Category | Examples |
|---|---|
| Files & shell | list/read/write files, execute shell/Python (sandboxed via Docker if available) |
| Desktop & web automation | mouse/keyboard/screenshot, vision-based screen operation, browser navigation & scraping |
| Security | port/web scanning, MITRE ATT&CK & VirusTotal lookups, IOC feeds, a CTF training range with blue-team SOC playbooks and threat hunting |
| Quantum & crypto | Qiskit circuit simulation, post-quantum key exchange/signing, symmetric/asymmetric crypto, hashing |
| Privacy & compliance | differential privacy, PII detection/redaction, GDPR/CCPA/CFAA advisories (informational, not legal advice) |
| Reality & IoT | web/dark-web crawling (Tor-gated, authorized-OSINT use only), geocoding, local IoT device control |
| Resilience | digital twins, latency/network-partition chaos testing, filesystem snapshots & backup/restore, process watchdogs |
| Ops & monitoring | CPU/memory monitoring, license/feature-flag checks, ML drift & fairness metrics, Prometheus metrics |
| Communication | Telegram messaging, email (IMAP/SMTP), social media search, robotics control |

Every tool that writes to disk, executes code, controls a real device, or touches an external system asks for your confirmation before running (`is_dangerous=True`) — you'll see exactly what it's about to do first.

**Deliberately not included:** a malware-execution sandbox, cyber_range's red-team/ransomware-simulation content, and anything under `hardware/battlefield/` — these stay out of the live, autonomous tool registry regardless of how they're framed in the source.

---

## 🧪 Running Tests

```bash
pytest tests/
```
(Note the custom file pattern in `pytest.ini` — some test modules use a `*_tests.py` suffix instead of pytest's default, which is already configured for you.)

---

## 🏗️ Architecture

- `main.py` — entry point; orchestrates the background servers and the think-act loop.
- `modules/tool_executor.py` — the central tool registry and dispatcher; auto-discovers and registers every facade below.
- `modules/all_ais_modules.py` — the `AIAgent`, unifying Claude/OpenAI/Gemini/mock providers behind one interface.
- `modules/*_tools.py` — the extended-capability facades (threat intel, quantum, privacy, resilience, reality/XR, cyber range, plugins, ethics/legal, platform ops).
- `modules/canvas_server.py` — the live visual web dashboard.
- `ai_core/cognitive_arch/` — working memory and persistent long-term (vector) memory.
- `singularity/goal_system/` — the ethical-constraint checks and utility-function scoring every plan passes through before execution.
- `security/security_dashboard.py` — rule-based detection of dangerous commands.
- `external/` — the complete, unmodified source of every external tool this project integrates, vendored as git submodules (pinned at a fixed commit each). See below.

---

## 🔗 External Repos (`external/`)

These are separate, independently-maintained projects vendored as git submodules (full source, not cherry-picked files) so the complete history and every module of each is available to read, audit, or build from inside this repo:

| Submodule | Upstream | How Devin uses it |
|---|---|---|
| `external/claude-code` | [anthropics/claude-code](https://github.com/anthropics/claude-code) | Shelled out to via `delegate_to_claude_code` (needs `npm install -g @anthropic-ai/claude-code`) |
| `external/gemini-cli` | [google-gemini/gemini-cli](https://github.com/google-gemini/gemini-cli) | Shelled out to via `delegate_to_gemini_cli` (needs `npm install -g @google/gemini-cli`) |
| `external/openclaw` | [openclaw/openclaw](https://github.com/openclaw/openclaw) | Shelled out to via `run_openclaw_command` (needs its own `pnpm install` + build) |
| `external/shannon` | [KeygraphHQ/shannon](https://github.com/KeygraphHQ/shannon) | Shelled out to via `run_shannon_pentest` (needs Docker + `npx @keygraph/shannon`) |
| `external/airgorah` | [martin-olivier/airgorah](https://github.com/martin-olivier/airgorah) | Rust/GTK4 GUI, can't run headlessly; Devin instead drives the aircrack-ng suite it wraps directly via `run_aircrack_suite_command` |
| `external/metasploit-framework` | [rapid7/metasploit-framework](https://github.com/rapid7/metasploit-framework) | Reference source; Devin talks to a running `msfrpcd` via `pymetasploit3` (`run_full_pentest_scan`'s exploitation path) rather than invoking the Ruby CLI directly |
| `external/PowerTools` | [kevinhamza/PowerTools](https://github.com/kevinhamza/PowerTools) | PowerShell toolkit; run via `execute_shell` on Windows/pwsh targets |
| `external/Responder` | [kevinhamza/Responder](https://github.com/kevinhamza/Responder) | LLMNR/NBT-NS/mDNS poisoner; run via `execute_shell` (requires root and an authorized network) |
| `external/nishang` | [kevinhamza/nishang](https://github.com/kevinhamza/nishang) | PowerShell offensive scripts; run via `execute_shell` on Windows/pwsh targets |
| `external/hackability` | [PortSwigger/hackability](https://github.com/PortSwigger/hackability) | Burp Suite extension source; reference/manual use inside Burp, not invoked by Devin directly |
| `external/AIA` | [kevinhamza/AIA](https://github.com/kevinhamza/AIA) | Reference copy; individual modules (social media APIs, device control, face recognition) are ported natively into `modules/*` rather than imported from here, since AIA's own agent loop duplicates what `main.py`/`tool_executor.py` already do |
| `external/vulnerability-analysis` | [kevinhamza/vulnerability-analysis](https://github.com/kevinhamza/vulnerability-analysis) | Reference copy of the user's Docker-based scanning pipeline |
| `external/moltbots.github.io` | [kevinhamza/moltbots.github.io](https://github.com/kevinhamza/moltbots.github.io) | Static site; reference only |
| `external/Devin` | [kevinhamza/Devin](https://github.com/kevinhamza/Devin) | Reference copy of the original v1 project. Its own README opens with "THIS IS THE FAIL PROJECT" -- every feature in its list (voice control, PC control, system monitoring, cloud management, threat detection, mobile sync, analytics, utility tools, conversational AI, cross-platform support) is already implemented more completely in Devin-4.0 |
| `external/Devin-2.0` | [kevinhamza/Devin-2.0](https://github.com/kevinhamza/Devin-2.0) | Reference copy; this is the actual base Devin-4.0 was originally seeded from, so its working subsystems already live in `modules/` |
| `external/Devin-3.0` | [kevinhamza/Devin-3.0](https://github.com/kevinhamza/Devin-3.0) | Reference copy; audited for unique subsystems, which were ported natively into `modules/` |

**Note on `self-operating-computer` and `hexstrike-ai`:** these two are *not* in `external/` -- they're vendored as plain, fully-tracked directories at the repo root (`self-operating-computer/`, `hexstrike-ai/`), not submodules, because Devin actually runs their Python source directly/via subprocess rather than treating them as reference-only. Both were diffed file-for-file against fresh upstream clones to confirm completeness (each was missing its `LICENSE`; `hexstrike-ai` was also missing three asset images -- since fixed).

**Why submodules and not a subprocess-only integration:** for actively-maintained external tools with their own runtime (Node, Ruby, Rust, PowerShell), Python can't execute their code directly either way — a submodule vendors the *complete, exact* source into this repo (satisfying "the whole repo, not just a module") without duplicating its git history into Devin-4.0's own, while the actual invocation still goes through each project's own documented entry point (installed CLI, `npx`, `msfrpcd`, `pwsh`), exactly as that project intends to be run.

**Why some repos aren't vendored:** `OpenDevin` (the `AI-App/OpenDevin.OpenDevin` mirror) is a stale snapshot from April 2024 predating its rename to OpenHands, with no packaged CLI entrypoint and an agent-loop architecture already superseded by this project's own `tool_executor.py`/autonomous-reasoning stack — not vendored. `Holomat` (both `Concept-Bytes/Holomat` and `itachity/Holomat`) is a physical hologram-table/hand-tracking hardware project (camera-rig calibration) with no portable module for a general OS-controlling assistant. `microsoft/JARVIS` (HuggingGPT) and the simple `Concept-Bytes/Jarvis`/`itachity` voice-assistant scripts largely duplicate capability Devin already has (see `modules/robotics/voice_assistant.py`, `modules/user_interaction_module.py`) or would need a much larger dedicated integration effort (HuggingGPT's model-orchestration research codebase); `modules/ollama_module.py` ports the one genuinely new idea from `itachity/Holomat`'s `assist_local.py` -- a fully local, zero-cost LLM fallback -- as a proper `AIAgent` provider instead.

To fetch/update all vendored submodules at once:
```bash
git submodule update --init --recursive
```

---

## 🔧 Troubleshooting

- **`pip install` fails building PyAudio/simpleaudio** — install the system audio headers from step 1 first (`portaudio19-dev libasound2-dev` on Debian/Ubuntu).
- **Startup is slow / seems to hang after "Building code index..."** — this is normal and takes a few seconds; if it's taking much longer, check that you didn't create your virtual environment *inside* the repo directory (it gets walked and indexed along with your source).
- **"Could not load embedding model... 403 Forbidden. Using placeholder embeddings."** — expected in a network-restricted/offline environment; long-term memory and semantic code search fall back to keyword-only search and still work, just less precisely.
- **`gemini-flash-latest` intermittently returns `503 UNAVAILABLE`** — Devin automatically retries against alternate model aliases; you shouldn't need to do anything, but if it persists Google's status page will confirm an outage.
- **Desktop/browser automation tools report "no X connection"** — expected on a headless server/container; they need a real display (X11/Wayland/macOS/Windows desktop session).
- **`adb`/`ros2` missing** — expected unless you have Android or ROS 2 hardware connected; those tools just report unavailable and everything else still works.
- **First run is noticeably slower than later ones** — the threat-intelligence tools download and cache the ~35MB MITRE ATT&CK dataset to `intel_cache/` on first use; subsequent runs read from that cache in under a second.

---
**Author:** Kevin Devin / KevinHamza
**License:** MIT
