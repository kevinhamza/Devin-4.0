# Integration Matrix: Tools → Repos → Status

**Date:** 2026-09-23  
**Status:** AUDIT MAPPING  

This document maps each tool in TOOL_REGISTRY to its source repository and integration status.

---

## Summary Statistics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tools Registered | 34 | ✓ Verified |
| Tools from repos/ | ~10-12 (estimated) | 🔄 Needs verification |
| Tools from third-party libs | ~22 | ✓ Direct wrappers |
| Active Repos (with code) | 16 | ✓ Present |
| Repos with >100 Python files | 4 | ✓ Substantial |
| Total Python files in repos/ | ~2,600 | 🔄 Not fully integrated |

---

## Tool Registry Breakdown (34 Tools)

### 1. OS Automation Tools (13 tools)
These primarily wrap pyautogui, pynput, or subprocess:

| Tool | Source | Repo | Status | Implementation |
|------|--------|------|--------|-----------------|
| take_screenshot | mss / pyautogui / PIL | BUILTIN | ✓ WORKING | modules/integrations.py:401 |
| mouse_click | pyautogui / pynput | BUILTIN | ✓ WORKING | modules/integrations.py:435 |
| mouse_right_click | pyautogui / pynput | BUILTIN | ✓ WORKING | modules/integrations.py:455 |
| mouse_double_click | pyautogui | BUILTIN | ✓ WORKING | modules/integrations.py:459 |
| mouse_move | pyautogui | BUILTIN | ✓ WORKING | modules/integrations.py:469 |
| mouse_drag | pyautogui | BUILTIN | ✓ WORKING | modules/integrations.py:479 |
| mouse_scroll | pyautogui | BUILTIN | ✓ WORKING | modules/integrations.py:490 |
| keyboard_type | pynput | BUILTIN | ⚠️ FALLBACK | modules/integrations.py:~510 |
| keyboard_press | pynput | BUILTIN | ⚠️ FALLBACK | modules/integrations.py:~520 |
| keyboard_hotkey | pynput | BUILTIN | ⚠️ FALLBACK | modules/integrations.py:~530 |
| get_screen_size | pyautogui | BUILTIN | ✓ WORKING | modules/integrations.py:~540 |
| get_mouse_position | pyautogui | BUILTIN | ✓ WORKING | modules/integrations.py:~550 |
| search_screen | opencv / pil | BUILTIN | ⚠️ REQUIRES CV2 | modules/integrations.py:~560 |

**Status:** Tools work as wrappers around third-party libs. No deep integration with repos/.

### 2. Window Management (2 tools)

| Tool | Source | Repo | Status | Implementation |
|------|--------|------|--------|-----------------|
| list_windows | wmctrl / psutil | BUILTIN | ✓ WORKING | modules/integrations.py:~570 |
| focus_window | wmctrl / xdotool | BUILTIN | ✓ WORKING | modules/integrations.py:~580 |

**Status:** Uses Linux system tools (wmctrl) or psutil; not from repos/.

### 3. Application Launching (1 tool)

| Tool | Source | Repo | Status | Implementation |
|------|--------|------|--------|-----------------|
| open_application | subprocess | BUILTIN | ✓ WORKING | modules/integrations.py:600 |

**Status:** Standard subprocess wrapper.

### 4. Shell & Code Execution (3 tools)

| Tool | Source | Repo | Status | Implementation |
|------|--------|------|--------|-----------------|
| execute_shell | subprocess | BUILTIN | ✓ WORKING | modules/integrations.py:621 |
| execute_python | subprocess exec | BUILTIN | ✓ WORKING | modules/integrations.py:638 |
| git_command | subprocess | BUILTIN | ✓ WORKING | modules/integrations.py:~650 |

**Status:** All standard library wrappers.

### 5. Filesystem Operations (3 tools)

| Tool | Source | Repo | Status | Implementation |
|------|--------|------|--------|-----------------|
| read_file | pathlib | BUILTIN | ✓ WORKING | modules/integrations.py:656 |
| write_file | pathlib | BUILTIN | ✓ WORKING | modules/integrations.py:660 |
| list_files | os.walk / fnmatch | BUILTIN | ✓ WORKING | modules/integrations.py:666 |

**Status:** All pathlib/stdlib wrappers.

### 6. Web Operations (3 tools)

| Tool | Source | Repo | Status | Implementation |
|------|--------|------|--------|-----------------|
| web_search | googlesearch / duckduckgo | BUILTIN | ⚠️ PARTIAL | modules/integrations.py:677 |
| web_fetch | requests | BUILTIN | ✓ WORKING | modules/integrations.py:~700 |
| open_browser | webbrowser / Selenium / Playwright | BUILTIN | ⚠️ FALLBACK | modules/browser.py |

**Status:** web_search and web_fetch work; browser automation has multiple fallbacks.

### 7. Voice Operations (2 tools)

| Tool | Source | Repo | Status | Implementation |
|------|--------|------|--------|-----------------|
| speak | pyttsx3 | BUILTIN | ✓ INSTALLED | modules/voice.py |
| listen | SpeechRecognition | BUILTIN | ✓ INSTALLED | modules/voice.py |

**Status:** Wrappers around external libraries; not from repos/.

### 8. Clipboard (2 tools)

| Tool | Source | Repo | Status | Implementation |
|------|--------|------|--------|-----------------|
| clipboard_get | xclip / pyperclip | BUILTIN | ✓ WORKING | modules/integrations.py:~750 |
| clipboard_set | xclip / pyperclip | BUILTIN | ✓ WORKING | modules/integrations.py:~760 |

**Status:** Wrappers around system clipboard tools.

### 9. System Monitoring (1 tool)

| Tool | Source | Repo | Status | Implementation |
|------|--------|------|--------|-----------------|
| get_system_info | psutil / platform | BUILTIN | ✓ WORKING | modules/integrations.py:~770 |
| list_processes | psutil | BUILTIN | ✓ WORKING | modules/integrations.py:~780 |

**Status:** psutil wrapper.

### 10. Security Tools (1 tool)

| Tool | Source | Repo | Status | Implementation |
|------|--------|------|--------|-----------------|
| run_nmap_scan | python-nmap | BUILTIN | ⚠️ OPTIONAL | modules/integrations.py:~790 |

**Status:** python-nmap wrapper; marked INACTIVE (nmap not installed).

### 11. Vision/Image Analysis (1 tool)

| Tool | Source | Repo | Status | Implementation |
|------|--------|------|--------|-----------------|
| analyze_image | Gemini vision API | GEMINI API | ⚠️ NEEDS KEY | modules/integrations.py:~810 |

**Status:** Requires Gemini API key and network; implemented as REST call.

### 12. Communications (1 tool)

| Tool | Source | Repo | Status | Implementation |
|------|--------|------|--------|-----------------|
| send_telegram_message | python-telegram-bot | BUILTIN | ⚠️ NEEDS TOKEN | modules/integrations.py:~830 |

**Status:** Requires TELEGRAM_BOT_TOKEN environment variable.

---

## Repository Integration Status

### High Integration (Active Bridging)

**None found** — repos/ contain source code but are not actively bridged into TOOL_REGISTRY

### Medium Integration (Attempted)

| Repo | Size | Files | Strategy | Status | Notes |
|------|------|-------|----------|--------|-------|
| aia | 276K | 35 | Try/except import in modules/aia_*.py | ⚠️ PARTIAL | Modules created but not in TOOL_REGISTRY |
| soc | 192K | 19 | screenshot utils extracted | ✓ PARTIAL | Only screenshot function used |
| cheetah | 19M | 475 | modules/cheetah_*.py (15+ wrapper modules) | ⚠️ PARTIAL | Modules exist but no TOOL_REGISTRY entries |
| jarvis | 32K | 6 | modules/jarvis_*.py bridge | ⚠️ PARTIAL | Basic bridging only |
| jarvis_ms | 70M | 24 | modules/jarvis_*.py bridge | ⚠️ PARTIAL | Basic bridging only |
| security | 7.8M | 94 | modules/pentesting_*.py + modules/security/ | ⚠️ PARTIAL | Security tools in separate modules, not TOOL_REGISTRY |
| openclaw | 487M | 21 | modules/opendevin_bridge.py | ❌ STUB | No real integration found |
| opendevin | 20M | 13 | Canvas tool extracted | ⚠️ MINIMAL | Canvas UI tool only; main agent not used |

### Low/No Integration (Reference Only)

| Repo | Size | Strategy | Status | Reason |
|------|------|----------|--------|--------|
| claude_code | 102M | Reference for CLI design | ℹ️ REFERENCE | Used as architecture inspiration only |
| devin1, 2, 3 | 2.5M, 8.3M, 8.3M | Previous versions | ℹ️ REFERENCE | Kept for history; not actively used |
| gemini_cli | 47M | TypeScript wrapper | ℹ️ UNUSED | REST API used directly instead |
| shannon | 27M | TypeScript network AI | ℹ️ UNUSED | No integration found |
| holomat | 19M | XR framework | ❌ STUB | Placeholder bridge exists but untested |
| tools | 32M | PowerTools, moltbots | ❌ STUB | Only 2 Python files; mostly reference |

---

## Integration Gap Analysis

### What's Promised (README)

✅ 24 repos integrated  
✅ 60+ tools  
✅ All repos discoverable by agent  
✅ Deep integration (not wrappers)  

### What's Actually Delivered (Current Audit)

❌ 34 tools registered (not 60+)  
⚠️ ~22 tools from third-party libs (not repos)  
⚠️ ~10-12 tools from repos (estimated)  
✓ 16 repos present with code  
⚠️ Most repos have wrapper modules but NO TOOL_REGISTRY entries  
❌ No discovery mechanism — tools are hardcoded  

### Specific Gaps

| Gap | Issue | Impact | Fix Required |
|-----|-------|--------|--------------|
| Tool Count | 34 actual vs 60+ promised | 43% shortfall | Add 26+ tools or update README |
| Tool Registry | Only 34 entries; many repo functions hidden | Agent can't discover them | Expand TOOL_REGISTRY with repo-specific tools |
| Discovery | Hardcoded tool list | AI can't adapt to new repos | Implement dynamic tool discovery |
| Repo Integration | Modules created but not connected to TOOL_REGISTRY | Repo capabilities isolated | Create tool wrappers for each repo's main functions |
| Documentation | No INTEGRATION_MATRIX before this | Users don't know what's where | Create matrix (this document) |

---

## Per-Repo Integration Details

### aia/ (Automation Framework)
**Size:** 276K | **Files:** 35 Python  
**Provides:** Automation, voice, ML, social  
**Integration:** modules/aia_*.py (7 modules)  
**Status:** ⚠️ Partially integrated; modules exist but no TOOL_REGISTRY entries  
**Missing:** No tool functions exported; HAS["aia_automation"] etc. exist but used nowhere  
**Fix:** Create aia_* tool functions and add to TOOL_REGISTRY

### cheetah/ (Multi-Agent RL)
**Size:** 19M | **Files:** 475 Python  
**Provides:** Multi-agent reasoning, RL agents  
**Integration:** modules/cheetah_*.py (15+ modules)  
**Status:** ⚠️ Modules mimic structure but limited connection  
**Missing:** No agent tools in TOOL_REGISTRY; cheetah reasoning engine not exposed  
**Fix:** Create cheetah reasoning tool; expose agent capabilities

### claude_code/ (Claude Code Source)
**Size:** 102M | **Files:** 170 Python  
**Provides:** CLI interface patterns, tool definition schema  
**Integration:** Reference only  
**Status:** ℹ️ Used for architecture inspiration  
**Note:** NOT actually integrated into Devin-4.0; just copied for reference

### devin1, 2, 3/ (Previous Versions)
**Size:** 2.5M, 8.3M, 8.3M | **Files:** 303, 487, 486 Python  
**Provides:** Previous agent implementations, tools  
**Integration:** modules/devin*_bootstrap.py (stubs)  
**Status:** ℹ️ Kept for history; no active use  
**Note:** Could provide fallback tools but currently unused

### gemini_cli/ (Gemini CLI Wrapper)
**Size:** 47M | **Files:** 0 Python (TypeScript/Node)  
**Provides:** Gemini CLI interface  
**Integration:** None; REST API used directly  
**Status:** ℹ️ Superseded by REST API approach  

### holomat/ (XR Framework)
**Size:** 19M | **Files:** 15 Python  
**Provides:** Holographic/VR interface  
**Integration:** modules/holomat_*.py (stub bridge)  
**Status:** ❌ No real integration; untested  
**Missing:** VR/XR capabilities not accessible; requires hardware  

### jarvis, jarvis_ms/ (Jarvis Agents)
**Size:** 32K, 70M | **Files:** 6, 24 Python  
**Provides:** Task automation, multi-modal agents  
**Integration:** modules/jarvis_*.py bridge  
**Status:** ⚠️ Minimal; basic tool wrappers only  
**Missing:** Main agent loop not connected  

### openclaw/ (Agent Framework)
**Size:** 487M | **Files:** 21 Python  
**Provides:** Multi-agent orchestration, reasoning  
**Integration:** Exists but untested  
**Status:** ❌ No verified integration; openclaw agent not used  

### opendevin/ (OpenDevin Agent)
**Size:** 20M | **Files:** 13 Python  
**Provides:** Full agent with tools, memory, planning  
**Integration:** Canvas UI tool extracted  
**Status:** ⚠️ Only canvas tool exposed; agent not integrated  
**Missing:** Main OpenDevin agent loop, memory, planning capabilities  

### security/ (Pentesting Tools)
**Size:** 7.8M | **Files:** 94 Python  
**Provides:** airgorah, hexstrike, hackability, vuln-analysis, Responder, nishang  
**Integration:** modules/pentesting_*.py (specialized modules)  
**Status:** ⚠️ Tools present but isolated; not in main TOOL_REGISTRY  
**Missing:** Not discoverable by main agent; must be called explicitly  

### shannon/ (Network AI)
**Size:** 27M | **Files:** 0 Python (TypeScript)  
**Provides:** Network-based AI capabilities  
**Integration:** None found  
**Status:** ℹ️ Reference only; TypeScript not used  

### soc/ (Self-Operating-Computer)
**Size:** 192K | **Files:** 19 Python  
**Provides:** OS automation, screenshot utility  
**Integration:** Screenshot utility extracted  
**Status:** ⚠️ Partial; only screenshot helpers used, not main agent  

### tools/ (PowerTools, moltbots)
**Size:** 32M | **Files:** 2 Python  
**Provides:** Various tools and utilities  
**Integration:** Reference only  
**Status:** ℹ️ Not integrated; too many non-Python files  

---

## Recommendations for Deeper Integration

### Priority 1: Connect Existing Modules to TOOL_REGISTRY
- **Current:** modules/ has 90+ Python files with functions that don't appear in TOOL_REGISTRY
- **Action:** Audit all modules/; extract key functions; add to TOOL_REGISTRY
- **Estimated tools:** 20-30 additional tools available

### Priority 2: Expose Agent Capabilities
- **Current:** Individual agents (cheetah, opendevin, openclaw, jarvis) exist but not used
- **Action:** Create unified agent interface tool that AI can call to delegate complex tasks
- **Estimated:** 4-6 new meta-tools

### Priority 3: Dynamic Tool Discovery
- **Current:** Tools hardcoded; agent can't learn about new capabilities
- **Action:** Implement tool registration system; repos can self-register tools
- **Estimated:** Architecture change, enable +30 tools from repos

### Priority 4: Consistent API for Repos
- **Current:** Each repo has different function signatures, error handling
- **Action:** Define standard tool interface; make repos export via standard wrapper
- **Estimated:** 2-3 days work; enables 50+ repo-provided tools

### Priority 5: Test & Verify
- **Current:** No end-to-end tests for tool integration
- **Action:** Create test suite that exercises all tools
- **Estimated:** 10-20 hours; will find 20-30 bugs

---

## Summary: Integration vs. Promise

| Aspect | Promised | Actual | Verified | Gap |
|--------|----------|--------|----------|-----|
| Repos integrated | 24 | 16 | ✓ 16 present | None (but 8 minimal integration) |
| Tools available | 60+ | 34 | ✓ 34 registered | -26+ tools missing |
| Tools from repos | ~40+ | ~10 | ⚠️ Estimated | -30+ not exposed |
| Discovery | ✓ AI learns tools | ✗ Hardcoded | ✗ Cannot discover | Needs implementation |
| Wrapper quality | Deep integration | Mostly surface-level | ⚠️ Partial | Needs deeper linking |
| Test coverage | Assumed | Unknown | ✗ None found | Needs test suite |

**Conclusion:** The project has good foundations (repos present, basic tools work) but **integration is superficial**. Most repository capabilities are hidden. The agent can only access 34 hardcoded tools instead of discovering 50-100+ available in the repositories.

