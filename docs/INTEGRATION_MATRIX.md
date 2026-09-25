# Devin-4.0 — Integration Matrix

This document records the integration status of every external repository
coupled to Devin-4.0.

## Integration Status Key

| Symbol | Meaning |
|---|---|
| ✅ | Fully integrated — capabilities exposed through runtime |
| 🔵 | Source preserved — code available, not in TOOLS |
| 🟡 | Partial — some capabilities integrated |
| ❌ | Not yet integrated |

---

## Core AI Repos

| Repo | Status | Integration Notes |
|---|---|---|
| `alishahryar1/free-claude-code` | ✅ | `modules/free_claude_provider.py` — subprocess call, session key, auto-install |
| `kevinhamza/Devin-4.0` | ✅ | This repo — primary runtime |

---

## OS Automation

| Repo / Library | Status | Integration Notes |
|---|---|---|
| pynput | ✅ | Mouse + keyboard in `os_agent.py` and `keyboard_mouse_control.py` |
| xdotool (Linux) | ✅ | Fallback mouse/keyboard/window control in `os_agent.py` |
| pyautogui | 🟡 | Available if installed; pynput preferred |
| mss | ✅ | Screenshot fallback in `os_agent.py` |
| PIL/Pillow | ✅ | Screenshot primary backend |

---

## Browser Automation

| Repo / Library | Status | Integration Notes |
|---|---|---|
| playwright | ✅ | `modules/browser_agent.py` — primary browser backend |
| selenium | ✅ | `modules/browser_agent.py` — fallback browser backend |
| beautifulsoup4 | ✅ | Link extraction in `browser_agent.py` |

---

## AI Providers

| Provider | Status | Integration Notes |
|---|---|---|
| Anthropic (Claude) | ✅ | `ClaudeProvider` in `agent.py`; vision in `os_agent.py` |
| Google Gemini | ✅ | `GeminiProvider` in `agent.py`; vision in `os_agent.py` |
| OpenAI | ✅ | `OpenAIProvider` in `agent.py`; vision in `os_agent.py` |
| HuggingFace | ✅ | `HuggingFaceProvider` + `hf_enhanced_provider.py` (free-tier) |
| Ollama | ✅ | `OllamaProvider` in `agent.py` |

---

## System Monitoring

| Library | Status | Integration Notes |
|---|---|---|
| psutil | ✅ | `system_monitor_enhanced.py` — CPU/mem/disk/net/processes |
| GPUtil | ✅ | `system_monitor_enhanced.py` — GPU monitoring (optional) |

---

## Voice

| Library | Status | Integration Notes |
|---|---|---|
| pyttsx3 | ✅ | TTS primary in `voice_engine.py` |
| gTTS | ✅ | TTS fallback in `voice_engine.py` |
| espeak/festival | ✅ | TTS system fallback (Linux) |
| SpeechRecognition | ✅ | STT in `voice_engine.py` |
| openai-whisper | ✅ | STT primary in `voice_engine.py` |
| pyaudio | ✅ | Audio capture in `voice_engine.py` |

---

## Security Repositories

These repos are **source-preserved** (available in `repos/`) but their
capabilities are **not exposed** through the Devin runtime TOOLS dict.
They may be studied, referenced, or used with explicit user authorization.

| Repo | Status | Notes |
|---|---|---|
| `kevinhamza/Responder` | 🔵 | Network responder — authorized testing only |
| `kevinhamza/nishang` | 🔵 | PowerShell scripts — authorized testing only |
| `kevinhamza/vulnerability-analysis` | 🔵 | Vuln analysis tools — authorized testing only |
| `kevinhamza/airgorah` | 🔵 | WiFi audit tool — authorized testing only |
| `kevinhamza/shannon` | 🔵 | AI pentesting agent — source reference only |

Security policy: these repos require explicit user authorization in the
conversation before any capability is invoked. Unauthorized targeting,
credential theft, persistence, and lateral movement are never permitted.

---

## General Purpose Repos

| Repo | Status | Integration Notes |
|---|---|---|
| `kevinhamza/self-operating-computer` | 🟡 | Vision+mouse patterns referenced in `os_agent.py` |
| `kevinhamza/opendevin.opendevin` | 🟡 | Agent loop patterns referenced in `reasoning_engine.py` |
| `kevinhamza/powertools` | 🟡 | Utility scripts available in `repos/` |
| `kevinhamza/hackability` | 🔵 | Source preserved |
| `kevinhamza/hexstrike-ai` | 🔵 | Source preserved |
| `kevinhamza/gemini-cli` | 🔵 | Source preserved |
| `kevinhamza/devin` | 🟡 | Ancestor — patterns merged into agent.py |
| `kevinhamza/devin-3.0` | 🟡 | Ancestor — patterns merged into agent.py |
| `kevinhamza/openclaw` | 🔵 | Source preserved |
| `kevinhamza/app-aia` | 🔵 | Source preserved |
| `kevinhamza/aia` | 🔵 | Source preserved |
| `kevinhamza/auraview` | 🔵 | Source preserved |
| `kevinhamza/holomat` | 🔵 | Source preserved |
| `kevinhamza/jarvis` | 🔵 | Source preserved |

---

## Tool Count

| Category | Count |
|---|---|
| Total tools in TOOLS dict | 136 |
| OS control tools | 18 |
| Web / HTTP tools | 12 |
| Shell / Python exec tools | 8 |
| Vision tools | 6 |
| Memory tools | 8 |
| File system tools | 14 |
| Browser tools | 10 |
| Voice tools | 4 |
| System monitoring tools | 6 |
| AI provider tools | 10 |
| Other / utility | 40 |
