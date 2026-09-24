# Third-party Licenses and Attribution

**Last Updated:** 2026-09-24 (spec §1 + §23 compliance audit)

Every repository whose source is preserved under `repos/` or `external/` is
listed here with its declared license, upstream URL (from `.gitmodules`
where present), and the path of the LICENSE file inside the tree.

Devin's own source is licensed under MIT (see `LICENSE` at repo root). Devin
does not modify or redistribute upstream repositories in a way that would
strip their license terms — the LICENSE file of each subrepo travels with it.

## Runtime-wired integrations (currently imported by `modules/integrations.py`)

| Subrepo | Path | License | Upstream URL | Notes |
|---|---|---|---|---|
| AIA | `repos/aia/`, `external/AIA/` | *not declared in local tree* | https://github.com/kevinhamza/AIA | User's own repo — MIT per its GitHub metadata. Local checkout is missing a LICENSE file. |
| self-operating-computer | `repos/soc/` | MIT | https://github.com/OthersideAI/self-operating-computer | LICENSE in tree. |
| Jarvis (Concept-Bytes) | `repos/jarvis/` | *not declared in local tree* | https://github.com/Concept-Bytes/Jarvis | LICENSE missing locally; upstream README shows MIT. |
| JARVIS (microsoft/HuggingGPT) | `repos/jarvis_ms/` | MIT | https://github.com/microsoft/JARVIS | LICENSE in tree. |
| gemini-cli | `repos/gemini_cli/` | *not declared in local tree* | https://github.com/google-gemini/gemini-cli | Upstream is Apache-2.0. Local LICENSE missing. |
| cheetahclaws | `repos/cheetah/cheetahclaws/` | Apache-2.0 | https://github.com/SafeRL-Lab/cheetahclaws (per .gitmodules) | LICENSE in tree at `repos/cheetah/LICENSE`. |

## Source-preserved, not runtime-wired

| Subrepo | Path | License | Upstream URL | Reason not wired |
|---|---|---|---|---|
| OpenDevin (OpenHands) | `repos/opendevin/` | MIT (declared in tree) | https://github.com/All-Hands-AI/OpenHands | Canvas tool requires the `openhands` SDK we don't ship. Source preserved. |
| vulnerability-analysis | `repos/security/vuln_analysis/` | Apache-2.0 | https://github.com/kevinhamza/vulnerability-analysis | Needs NVIDIA `morpheus` (GPU-only). Source preserved. |
| shannon | `repos/shannon/` | **AGPL-3.0** | https://github.com/KeygraphHQ/shannon | AGPL is copyleft-strong — deliberately kept out of runtime import path; TS adapters cite patterns only. |
| hexstrike-ai | `repos/security/hexstrike/` | MIT | https://github.com/0x4m4/hexstrike-ai | Source preserved; adapter TBD. |
| airgorah | `repos/security/airgorah/` | MIT | https://github.com/martin-olivier/airgorah | Requires airgorah binary; adapter TBD. |
| openclaw | `repos/openclaw/` | MIT | https://github.com/openclaw/openclaw | Source preserved. |
| Holomat | `repos/holomat/` | *not declared in local tree* | https://github.com/Concept-Bytes/Holomat | LICENSE missing locally. |
| PowerTools | `repos/tools/powertools/` | BSD-3-Clause | https://github.com/kevinhamza/PowerTools | LICENSE in tree. |
| MoltBots | `repos/tools/moltbots/` | MIT | https://github.com/kevinhamza/moltbots.github.io | LICENSE in tree. |
| hackability | `repos/security/hackability/` | *not declared in local tree* | https://github.com/PortSwigger/hackability | LICENSE missing locally. |
| Devin-1 | `repos/devin1/` | GPL (v?) | https://github.com/kevinhamza/Devin | User's own predecessor. |
| Devin-2.0 | `repos/devin2/` | MIT | https://github.com/kevinhamza/Devin-2.0 | User's own. |
| Devin-3.0 | `repos/devin3/` | MIT | https://github.com/kevinhamza/Devin-3.0 | User's own. |

## Deliberately NOT runtime-wired (§9 offensive)

Per spec §9, offensive-security tools are preserved on disk for reference /
authorized use but are NOT connected to the autonomous runtime. The LLM
cannot invoke these through TOOL_SCHEMAS, and their source is not imported by
`modules/integrations.py`.

| Subrepo | Path | License | Upstream URL |
|---|---|---|---|
| Responder | `repos/security/responder/` | GPL (declared in tree) | https://github.com/kevinhamza/Responder |
| nishang | `external/nishang/` (submodule stub) | BSD | https://github.com/samratashok/nishang |
| metasploit-framework | `external/metasploit-framework/` (submodule stub) | BSD-3-Clause | https://github.com/rapid7/metasploit-framework |

## Source-only reference collections

| Subrepo | Path | License | Notes |
|---|---|---|---|
| claude-code | `repos/claude_code/` | **Proprietary** (Anthropic Commercial ToS) | `LICENSE.md` states: "© Anthropic PBC. All rights reserved. Use is subject to Anthropic's Commercial Terms of Service." Devin uses this repo as **reference for terminal-UI patterns only** — no code is directly copied or redistributed. Any patterns retained were reimplemented by hand under Devin's own MIT license. |
| claude-code-source (collection) | `external/claude-code-source/` (submodule stub) | Mixed / see individual files | External research collection. Not imported. |

## Empty submodule stubs

`external/` contains 24 submodule pointers from `.gitmodules`. Only a handful
were ever `git submodule update --init`-ed; the rest are empty directories.
Runtime code (`modules/integrations.py`) prefers `repos/` mirrors when both
exist, so the empty stubs don't affect functionality but should be either
populated or removed from `.gitmodules` in a follow-up cleanup.

## Missing LICENSE files (action items)

The following `repos/` mirrors are missing an in-tree LICENSE file even
though their upstream declares one. Adding a local copy would tighten the
audit trail:

- `repos/aia/` — copy from upstream https://github.com/kevinhamza/AIA/blob/main/LICENSE
- `repos/gemini_cli/` — copy Apache-2.0 from https://github.com/google-gemini/gemini-cli/blob/main/LICENSE
- `repos/holomat/` — check upstream https://github.com/Concept-Bytes/Holomat
- `repos/jarvis/` — check upstream https://github.com/Concept-Bytes/Jarvis
- `repos/security/hackability/` — check upstream https://github.com/PortSwigger/hackability

## Devin's own license

`LICENSE` at repo root — **MIT** © Kevin Hamza. Devin's own code
(everything Devin-authored under `src/`, `modules/`, `main.py`, `devin`,
`docs/`, etc.) is MIT-licensed. Third-party code retains its original
license as listed above; Devin does not sublicense or re-license upstream
sources.
