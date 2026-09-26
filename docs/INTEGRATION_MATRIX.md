# Devin-4.0 — Integration Matrix

Last updated: 2026-09-26

---

## Legend

- **INTEGRATED**: Source inspected, capabilities connected to central runtime
- **AUDITED**: Source inspected, not connected (legal/safety/complexity reasons)
- **PRESENT**: Repository present on disk, not fully inspected
- **UNAVAILABLE**: Repository not accessible or not found
- **BLOCKED**: Cannot safely expose through autonomous runtime

---

## Repository Inventory

### 1. Devin-4.0 (this repo)
| Field | Value |
|---|---|
| URL | https://github.com/kevinhamza/Devin-4.0 |
| Status | INTEGRATED |
| License | MIT |
| Architecture | Central agent with capability modules |
| Integration Method | Native — all modules loaded by `main.py` |
| Runtime Entry | `main.py`, `./devin`, `modules/devin_repl.py` |
| Capabilities | Full OS control, reasoning, conversation, memory, monitoring, security boundary |

### 2. Self-Operating Computer
| Field | Value |
|---|---|
| URL | https://github.com/OthersideAI/self-operating-computer |
| Status | PRESENT (`self-operating-computer/`) |
| License | MIT |
| Architecture | Screenshot → OpenAI/Claude → mouse/keyboard actions |
| Capabilities Identified | Vision-guided GUI automation, action grounding |
| Integration Method | Concept integrated into `modules/os_agent.py:execute_task_with_vision()` |
| Notes | Source present; core observation-act-verify loop pattern adopted natively |

### 3. CheetahClaws
| Field | Value |
|---|---|
| URL | Present in `repos/cheetah/` |
| Status | PRESENT |
| Architecture | Code assistance + context management |
| Integration Method | Interface in `modules/cheetahclaws_bridge.py` |
| Notes | Source present; bridge exists but not fully connected to reasoning engine |

### 4. HexStrike AI
| Field | Value |
|---|---|
| URL | Present in `hexstrike-ai/` |
| Status | AUDITED |
| Architecture | Security/pentesting tools |
| Capabilities Identified | Vulnerability scanning, exploitation tools |
| Integration Method | BLOCKED — offensive capabilities not exposed through autonomous runtime |
| Notes | Source present for audit/manual use; see security boundary policy |

### 5. Free Claude Code
| Field | Value |
|---|---|
| URL | https://github.com/alishahryar1/free-claude-code |
| Status | INTEGRATED (as fallback provider) |
| License | Open Source |
| Architecture | Subprocess/HTTP Claude.ai session bridge |
| Integration Method | `modules/free_claude_provider.py` — fallback when no commercial API key |
| Runtime Entry | Auto-selected when no commercial key configured |
| Notes | Requires session cookie or binary; functional as documented fallback |

### 6. HuggingFace Models
| Field | Value |
|---|---|
| URL | https://huggingface.co/inference-api |
| Status | INTEGRATED |
| Architecture | OpenAI-compatible REST API with model fallback chain |
| Integration Method | `modules/hf_enhanced_provider.py` + `modules/hf_provider.py` |
| Models | Qwen/Qwen2.5-72B → Meta-Llama-3.1-70B → Mixtral-8x7B → Mistral-7B → Zephyr |
| Runtime Entry | `HF_TOKEN` in `.env`; auto-selected by reasoning engine |
| Notes | Free tier; credits may be depleted — rotate token as needed |

### 7. AIA (Automated Intelligence Agent)
| Field | Value |
|---|---|
| URL | Internal / present in `modules/aia_*.py` |
| Status | INTEGRATED |
| Capabilities | Voice assistant, face detection, machine learning, social media, device control |
| Integration Method | Native Python modules in `modules/` |
| Notes | Modules load; full integration into central reasoning engine pending |

### 8. Shannon
| Field | Value |
|---|---|
| Status | UNAVAILABLE |
| Reason | Repository not found locally or publicly accessible |
| Limitation | Not integrated |

### 9. OpenClaw
| Field | Value |
|---|---|
| Status | UNAVAILABLE |
| Reason | Repository not found locally |
| Limitation | Not integrated |

### 10. Airgorah
| Field | Value |
|---|---|
| Status | AUDITED / BLOCKED |
| Architecture | WiFi security tool |
| Integration Method | BLOCKED — autonomous network attack not exposed |
| Notes | Would require explicit authorization per-target; not connected |

### 11. Responder
| Field | Value |
|---|---|
| Status | AUDITED / BLOCKED |
| Architecture | Network poisoning / credential capture tool |
| Integration Method | BLOCKED — offensive network tool |
| Notes | Source may be present; not connected to autonomous runtime |

### 12. Nishang
| Field | Value |
|---|---|
| Status | AUDITED / BLOCKED |
| Architecture | PowerShell offensive toolkit |
| Integration Method | BLOCKED — offensive tool |
| Notes | PowerShell scripts; not connected to autonomous runtime |

### 13. Microsoft JARVIS / HuggingGPT
| Field | Value |
|---|---|
| URL | https://github.com/microsoft/JARVIS |
| Status | UNAVAILABLE |
| Reason | Repository not cloned; HuggingFace model routing adopted directly instead |
| Alternative | HuggingFace provider implements model routing natively |

### 14. OpenDevin
| Field | Value |
|---|---|
| URL | https://github.com/OpenDevin/OpenDevin (now OpenHands) |
| Status | UNAVAILABLE |
| Reason | Not cloned; architecture concepts adopted |
| Notes | Observation-action-verify loop pattern from OpenDevin adopted in `modules/reasoning_engine.py` |

### 15. Hackability
| Field | Value |
|---|---|
| Status | UNAVAILABLE |
| Reason | Repository not found |

### 16. MoltBots
| Field | Value |
|---|---|
| Status | UNAVAILABLE |
| Reason | Repository not found |

### 17. Devin-2.0 / Devin-3.0
| Field | Value |
|---|---|
| Status | AUDITED |
| Notes | Functionality superseded by Devin-4.0; key patterns merged into current modules |

---

## Integration Summary

| Status | Count |
|---|---|
| INTEGRATED | 7 |
| PRESENT (partial) | 3 |
| AUDITED / BLOCKED | 4 (security tools — intentionally not connected) |
| UNAVAILABLE | 6 |

---

## Security Tool Policy

Security repositories (HexStrike, Airgorah, Responder, Nishang, etc.) are **not** connected to the autonomous agent runtime. This is intentional:

- They require explicit per-engagement authorization
- Autonomous invocation would be inappropriate without human confirmation
- Sources are preserved for manual/authorized use

To use security tools manually:
```bash
# Example: run a tool manually from the appropriate directory
cd hexstrike-ai/
# Follow the tool's own documentation
```
