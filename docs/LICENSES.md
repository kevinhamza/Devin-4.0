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

## LICENSE fetch pass (2026-09-24)

Ran `curl` against upstream `raw.githubusercontent.com` and GitHub's
`/license` API for the 5 mirrors that were missing a local LICENSE file:

- ✓ `repos/aia/LICENSE` — fetched from upstream (MIT).
- ✓ `repos/gemini_cli/LICENSE` — fetched from upstream (Apache-2.0).
- ⚠ `repos/holomat/` — upstream `Concept-Bytes/Holomat` exists but has
  **no LICENSE file** at any conventional path, and GitHub's license
  detector returns null. Treat as *unlicensed source, all rights reserved
  by author*; Devin only references it for XR/holographic-UI patterns —
  no code redistribution.
- ⚠ `repos/jarvis/` — upstream `Concept-Bytes/Jarvis` — same as above:
  no LICENSE file upstream. Devin only imports specific tool functions
  via its adapter; treated as "pattern reference, do not redistribute".
- ⚠ `repos/security/hackability/` — upstream `PortSwigger/hackability`
  — no LICENSE file upstream. Devin does not directly invoke this repo
  at runtime; kept as security-research reference only.

The three ⚠ entries are documented rather than deleted so a future
maintainer knows the provenance situation without re-doing the audit.
If PortSwigger / Concept-Bytes later publish a LICENSE, rerun the same
`curl raw.githubusercontent.com/<slug>/main/LICENSE` command to fold it
in.

## Devin's own license

`LICENSE` at repo root — **MIT** © Kevin Hamza. Devin's own code
(everything Devin-authored under `src/`, `modules/`, `main.py`, `devin`,
`docs/`, etc.) is MIT-licensed. Third-party code retains its original
license as listed above; Devin does not sublicense or re-license upstream
sources.
