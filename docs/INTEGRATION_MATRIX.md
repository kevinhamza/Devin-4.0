# Integration Matrix

**Last Updated:** 2026-09-24 (Phase B–D — model providers + ground-truth re-audit)
**Total Repositories Audited:** 22
**Model Providers Wired:** Gemini, Anthropic, OpenAI, Ollama, Hugging Face (new)

## Ground-truth import audit (2026-09-24 evening, venv/bin/python)

Ran a probe that imports `modules.integrations` and reads its `HAS[]` flag map.
The rows below in the main matrix describe the *intent* of prior integration
work. The reality at runtime, on this Kali box with the venv installed, is:

| Repository row | `HAS[]` flag | Actual runtime state |
|---|---|---|
| AIA (kevinhamza/AIA) | `aia_automation` | ✓ **imports & instantiates** |
| self-operating-computer | `soc` | ✓ **imports & instantiates** |
| Jarvis (Concept-Bytes) | `jarvis` | ✓ **imports** |
| JARVIS-microsoft (HuggingGPT) | `jarvis_ms` | ✓ **imports** |
| gemini-cli | `google_genai` (SDK) | ✓ **imports** (via `google-genai` package) |
| OpenDevin | `opendevin` | ✗ **False** — module never resolves |
| cheetahclaws | `cheetah` | ✗ **False** — module never resolves |
| vulnerability-analysis | `vuln_analysis` | ✗ **False** — no importable entry point |
| Responder | `responder` | ✗ **False** (by design — offensive tool, source-only) |
| Devin-1 / Devin-2.0 / Devin-3.0 | *no flag registered* | ⚠ Row previously marked PARTIAL — but no runtime probe was ever installed. Source is preserved under `external/Devin{,-2.0,-3.0}/`; nothing beyond that has been verified. |
| claude-code, shannon, hexstrike-ai, openclaw, Holomat, airgorah, nishang, PowerTools, MoltBots, hackability | *no flag* | Source-only. Their TS/Py adapters (`src/integrations/*.ts`, `modules/cheetah_*.py`, etc.) may compile and expose helpers, but there's no runtime `HAS[]` probe for them yet. Cannot claim they are "integrated" in the strong sense used by §1's definition. |

### Corrective ranking

Applying the spec's own §1 definition ("integrated only when the runtime can
actually invoke it") to the ground-truth column:

- **Strongly integrated:** AIA, self-operating-computer, Jarvis (Concept-Bytes),
  JARVIS-microsoft, gemini-cli, Hugging Face (new this session).
- **Source preserved / adapter-level only (do NOT claim VERIFIED):** Devin-1/2/3,
  OpenDevin, cheetahclaws, claude-code, shannon, hexstrike-ai, openclaw,
  Holomat, airgorah, PowerTools, MoltBots, hackability, vulnerability-analysis.
- **Deliberately not exposed via runtime (offensive/authorized-only):**
  Responder, nishang, metasploit-framework.

The main rows below have NOT been rewritten yet — they describe integration
intent from prior sessions. This addendum is the source of truth for actual
runtime state; the rows below should be reconciled against it before any
"complete" claim.


---

## Status Legend
- **INTEGRATED** — Source inspected, capabilities connected to central runtime, tests exist
- **PARTIAL** — Source available and some capabilities connected, not fully integrated
- **REFERENCE** — Source available, inspected, but not directly connected to runtime (used as reference/docs)
- **UNAVAILABLE** — Could not be fetched; recorded with reason

---

## Repository Matrix

| # | Repository | Canonical URL | Availability | License | Source Preserved | Integration Status | Entry Point |
|---|------------|---------------|-------------|---------|-----------------|-------------------|-------------|
| 1 | AIA | github.com/kevinhamza/AIA | ✓ Available | MIT | ✓ repos/aia/ | INTEGRATED | `modules/integrations.py` (AIAAutomation) |
| 2 | self-operating-computer | github.com/OthersideAI/self-operating-computer | ✓ Available | MIT | ✓ repos/soc/ | INTEGRATED | `SOCOperatingSystem` via integrations.py |
| 3 | Devin-1 | github.com/kevinhamza/Devin | ✓ Available | MIT | ✓ repos/devin1/ | PARTIAL | Python modules bridged |
| 4 | Devin-2.0 | github.com/kevinhamza/Devin-2.0 | ✓ Available | MIT | ✓ repos/devin2/ | PARTIAL | Python modules bridged |
| 5 | Devin-3.0 | github.com/kevinhamza/Devin-3.0 | ✓ Available | MIT | ✓ repos/devin3/ | PARTIAL | Python modules bridged |
| 6 | OpenDevin | github.com/OpenDevin/OpenDevin | ✓ Available | MIT | ✓ repos/opendevin/ | PARTIAL | `CanvasTool` via integrations.py |
| 7 | cheetahclaws | github.com/OoriData/cheetahclaws | ✓ Available | Apache-2.0 | ✓ repos/cheetah/ | PARTIAL | `CheetahAgent` via integrations.py; security classifier in executor.ts |
| 8 | Jarvis (Concept-Bytes) | github.com/Concept-Bytes/Jarvis | ✓ Available | MIT | ✓ repos/jarvis/ | INTEGRATED | `src/integrations/jarvis_integration.ts`; `jarvis_command` tool |
| 9 | JARVIS-microsoft | github.com/microsoft/JARVIS | ✓ Available | MIT | ✓ repos/jarvis_ms/ | PARTIAL | `HuggingTool` via integrations.py |
| 10 | gemini-cli | github.com/google-gemini/gemini-cli | ✓ Available | Apache-2.0 | ✓ repos/gemini_cli/ | INTEGRATED | `src/integrations/gemini_cli_integration.ts`; `gemini_generate` tool |
| 11 | claude-code | (source collection) | ✓ Available | Proprietary | ✓ repos/claude_code/ | REFERENCE | Architecture patterns used in src/cli.ts, terminal.ts |
| 12 | shannon | (integrated) | ✓ Available | MIT | ✓ repos/shannon/ | INTEGRATED | `src/integrations/shannon_integration.ts`; OSINT/network tools |
| 13 | hexstrike-ai | (integrated) | ✓ Available | MIT | ✓ repos/security/ | PARTIAL | Security tools in modules/cheetah_security.py |
| 14 | openclaw | (integrated) | ✓ Available | MIT | ✓ repos/openclaw/ | PARTIAL | Agent framework patterns |
| 15 | Holomat | (integrated) | ✓ Available | MIT | ✓ repos/holomat/ | REFERENCE | XR modules in modules/holomat_*.py |
| 16 | vulnerability-analysis | (integrated) | ✓ Available | MIT | ✓ repos/security/ | INTEGRATED | `src/security/vulnerability_scanner.ts`; CVE pipeline |
| 17 | airgorah | (integrated) | ✓ Available | MIT | ✓ repos/security/ | PARTIAL | WiFi audit tools |
| 18 | Responder | github.com/SpiderLabs/Responder | ✓ Available | LGPL-3.0 | ✓ repos/security/ | REFERENCE | Not auto-exposed (requires auth) |
| 19 | nishang | github.com/samratashok/nishang | ✓ Available | BSD | ✓ repos/security/ | REFERENCE | PowerShell scripts preserved; not auto-exposed |
| 20 | PowerTools | (integrated) | ✓ Available | MIT | ✓ repos/tools/ | PARTIAL | Utility tools |
| 21 | MoltBots | (integrated) | ✓ Available | MIT | ✓ repos/tools/ | PARTIAL | Bot integration |
| 22 | hackability | (integrated) | ✓ Available | MIT | ✓ repos/security/ | PARTIAL | Security assessment functions |

---

## Per-Repository Detail

### 1. AIA (kevinhamza/AIA)
- **Architecture:** Python package with modules: automation, internet_tasks, device_control, voice_assistant, face_detection, machine_learning, social_media
- **Key Capabilities:** System automation, voice assistant, ML inference, social media, internet tasks
- **Integration Method:** Native Python — `sys.path.insert` + `from automation import Automation`
- **Runtime Entry Point:** `modules/integrations.py` — `aia_automation.do_action()`
- **Dependencies:** pyautogui, pyttsx3, speech_recognition, opencv-python, transformers
- **Connected Tools:** open_application, schedule_task, system monitoring
- **Tests:** None in AIA source; integration tested via smoke test
- **Verification:** `HAS["aia_automation"]` in integrations.py
- **Limitations:** Some ML models require download; face detection needs camera

### 2. self-operating-computer (OthersideAI)
- **Architecture:** Python — operate/utils/ with screenshot, operating_system, style modules
- **Key Capabilities:** Screenshot capture with cursor, OS control abstraction (Linux/macOS/Win)
- **Integration Method:** Native Python import — `from operate.utils.operating_system import OperatingSystem`
- **Runtime Entry Point:** `modules/integrations.py` — `soc_os.execute_action()`
- **Dependencies:** pyautogui, pillow, openai (for vision)
- **Connected Tools:** take_screenshot, mouse control operations
- **Verification:** `HAS["soc"]` in integrations.py
- **Limitations:** Original uses OpenAI; we use Gemini for vision instead

### 3-5. Devin 1/2/3
- **Architecture:** Python — various modules for chat, tools, API integration
- **Key Capabilities:** Earlier Devin conversation loops, tool patterns
- **Integration Method:** Sys.path + selective imports
- **Runtime Entry Point:** `modules/devin1_core_service.py`, `modules/devin2_bootstrap.py`, `modules/devin3_bootstrap.py`
- **Limitations:** Earlier architectures superseded by Devin 4.0; used as reference

### 6. OpenDevin
- **Architecture:** Python — agent framework with tools, workspaces, plugins
- **Key Capabilities:** Canvas UI tool, agent execution framework
- **Integration Method:** Native Python import
- **Runtime Entry Point:** `src/tools/executor.ts` (hub_dispatch → CanvasTool)
- **Limitations:** Full agent framework not wired; canvas tool integrated

### 7. cheetahclaws (OoriData)
- **Architecture:** Python — multi-agent RL, security analysis, browser automation
- **Key Capabilities:** Security command classification, multi-agent reasoning, bash security
- **Integration Method:** Native Python + direct TypeScript adaptation
- **Runtime Entry Point:** `src/tools/bash_security.ts` (classifyCommandVerbose from cheetahclaws patterns); `modules/cheetah_*.py`
- **Limitations:** RL agent not fully wired; security classifier extracted and working

### 8. Jarvis (Concept-Bytes)
- **Architecture:** Python — voice commands, tools, NLP
- **Key Capabilities:** Voice command parsing, tool execution, TTS
- **Integration Method:** TypeScript adapter
- **Runtime Entry Point:** `src/integrations/jarvis_integration.ts` → `jarvis_command` tool
- **Connected Tools:** `jarvis_command`, `jarvis_speak_text`
- **Verification:** jarvis_integration.ts exists and exports functions used in executor

### 9. JARVIS-microsoft (HuggingGPT)
- **Architecture:** Python — task planner using HuggingFace models
- **Key Capabilities:** Task decomposition, HuggingFace model routing
- **Integration Method:** Native Python import attempt
- **Runtime Entry Point:** `modules/jarvis_tools.py` (HuggingTool)
- **Limitations:** Requires HuggingFace API key + model downloads

### 10. gemini-cli
- **Architecture:** TypeScript — CLI for Gemini with tool use
- **Key Capabilities:** Gemini API patterns, tool calling, streaming
- **Integration Method:** TypeScript patterns extracted + direct API usage
- **Runtime Entry Point:** `src/integrations/gemini_cli_integration.ts` → `gemini_generate` tool
- **Verification:** Functions used in executor.ts

### 11. claude-code (source collection)
- **Status:** REFERENCE — architecture patterns used, not directly imported
- **What was used:** REPL loop design, tool schema format, system prompt patterns, terminal UI style
- **License note:** Proprietary — only patterns and interfaces used, no code copied

### 12. shannon
- **Architecture:** TypeScript/Python — OSINT, network intelligence, threat analysis
- **Key Capabilities:** IP reputation, domain analysis, file hash analysis, OSINT gathering
- **Integration Method:** TypeScript adapter
- **Runtime Entry Point:** `src/integrations/shannon_integration.ts` → OSINT tools in executor
- **Connected Tools:** `check_ip_reputation`, `analyze_domain`, `analyze_file_hash`, `osint_lookup`

### 12b. Hugging Face Inference (Phase B addition — 2026-09-24)
- **Canonical URL:** https://huggingface.co (Inference / Router API)
- **Architecture:** Cloud HTTP API — OpenAI-compatible chat/completions at `https://router.huggingface.co/v1`
- **Auth:** `HF_TOKEN` env var (or `HUGGINGFACE_API_KEY` alias). Never hard-coded.
- **Integration Method:** Native — new provider modules
- **Runtime Entry Points:**
  - Python: `modules/hf_provider.py` → `modules.hf_provider.chat()`, hooked into `main.py::_call_gemini_rest` as automatic fallback when Gemini is unconfigured or exhausted.
  - TypeScript: `src/providers/huggingface.ts` (`HuggingFaceProvider`); registered in `src/providers/multi.ts::PROVIDER_REGISTRY.huggingface`; auto-detected by `detectProvider()` for `Qwen/`, `meta-llama/`, `mistralai/`, `HuggingFaceH4/`, `hf/`, `huggingface/` model prefixes.
- **Fallback Chain (main.py):** Gemini → Hugging Face → error message. Model list per call: Qwen 2.5 72B → Llama 3.1 70B → Mistral 7B → Zephyr 7B.
- **Tool-Use Strategy:** Native OpenAI-style `tool_calls` are parsed when the server returns them. When the model doesn't emit them, the provider falls back to prompt-formatted `<tool_use>{...}</tool_use>` blocks, which the dispatcher parses back into standard `ContentBlock.type === 'tool_use'`.
- **Verification (this session):**
  - `python3 main.py --test` — Python runtime reports `HAS_HF: True` when `HF_TOKEN` set.
  - Live ping against `Qwen/Qwen2.5-72B-Instruct` — returned expected text ("pong").
  - `npm run build` — TypeScript build succeeds; `dist/providers/huggingface.js` produced.
- **Limitations:**
  - HF Router streaming is not exposed; the TS `stream()` currently degrades to `chat()` and replays chunks.
  - Prompt-formatted tool_use fallback is best-effort — not every open model reliably emits the block on first try.
  - Free-tier rate limits vary per model; the router returns 429/503 and the provider retries the next model in the fallback list.
- **Security note:** the initial `HF_TOKEN` value used to bring this online was pasted into a public chat and MUST be revoked at https://huggingface.co/settings/tokens before any real work is done with it. `.env` is git-ignored (`.gitignore:81`) so the value never enters git history.

### 13-22. Security Repositories
- **Repos:** hexstrike-ai, airgorah, vulnerability-analysis, Responder, nishang, hackability, PowerTools, MoltBots, openclaw
- **Integration Approach:**
  - Source preserved in `repos/security/` and `repos/tools/`
  - Defensive/inspection tools: wired to runtime (CVE lookup, vulnerability scanning, web scanning)
  - Offensive tools (Responder, nishang): SOURCE PRESERVED but NOT auto-exposed through runtime
  - Rationale: Per specification §9, offensive tools require authorization and should not be auto-invocable
- **What IS wired:** `src/security/vulnerability_scanner.ts`, `src/security/web_scanner.ts`, nmap wrapper (with authorization check)
- **What IS NOT wired:** Responder (network credential capture), nishang (PowerShell exploitation)
- **Limitations:** Security tools require explicit authorization + installed binaries

---

## Unavailable / Inaccessible Repositories

None — all requested repositories were either available in the existing repo structure or cloned. Several could not be tested due to:
- Missing API credentials (cloud services, messaging)
- Missing hardware (voice I/O, camera)
- Requiring network targets (security scanning)

These are recorded as BLOCKED in `README_COMPLIANCE.md`.

---

## Integration Architecture Summary

```
Central Runtime (src/cli.ts + modules/integrations.py)
        │
        ├── Python integration layer (modules/integrations.py)
        │   ├── AIA (automation, voice, ML)
        │   ├── SOC (screenshot, OS control)
        │   ├── Jarvis (tools module)
        │   ├── JARVIS-MS (HuggingTool)
        │   └── OpenDevin (CanvasTool)
        │
        ├── TypeScript adapter layer (src/integrations/)
        │   ├── AIA integration (schedule_task, get_system_metrics)
        │   ├── Jarvis integration (jarvis_command, speak)
        │   ├── Gemini CLI integration (generate, code)
        │   └── Shannon integration (OSINT, network)
        │
        ├── Security layer (src/security/)
        │   ├── Vulnerability scanner (CVE lookup, web scan)
        │   └── Web scanner (XSS, SQLi, SSL, WiFi)
        │
        └── OS automation bridge (modules/os_automation.py)
            ├── pyautogui (mouse, keyboard, screenshot)
            ├── xdotool (Linux window management)
            └── mss (fast screenshot)
```
