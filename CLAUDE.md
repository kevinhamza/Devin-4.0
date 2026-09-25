# Devin-4.0 — Project Guide for AI Coding Assistants

This file orients AI coding assistants (Claude Code, Cursor, etc.)
working in this repo.

## What Devin is

Devin AGI 4.0 is a single-file Python agent (`agent.py`, ~6,100 lines)
that operates a real computer through 136 tools:

- 5 AI providers: Gemini, Claude, OpenAI, HuggingFace, Ollama
- OS automation: mouse, keyboard, screenshots, windows, apps, clipboard
- Web: search, HTTP, Selenium/Playwright browser
- Shell: subprocess with timeout, Python exec with stdout capture
- Vision: screenshot → AI analysis → coordinates → action
- Memory: SQLite persistent (`_DB_PATH`) + session history
- Integrations: 41 modules loaded from `modules/`, 24 external repos
- REPL + one-shot CLI + slash commands + streaming markdown

The launcher `./devin` always execs `python3 agent.py`. The TypeScript
tree under `src/` is legacy — the shipped experience is Python.

## Structure

```
agent.py                      # THE runtime (edit here)
devin                         # bash launcher (do not add features)
modules/                      # 103 capability modules (import optional)
tests/
  test_core.py                # 40-test suite — RUN AFTER ANY CHANGE
  demo_workflow.py            # 11-step end-to-end demo (no AI required)
docs/
  README_COMPLIANCE.md        # spec compliance status
  INTEGRATION_MATRIX.md       # per-repo integration record
  PHASE_STATUS.md             # phase-by-phase ground-truth report
  ARCHITECTURE.md
src/                          # legacy TypeScript CLI (still type-checks clean)
.env.example                  # ALL supported env vars (copy to .env, fill)
```

## Editing agent.py — non-negotiable rules

1. **Never commit secrets.** No API keys in source, tests, docs, logs,
   or commit messages. `.env` is the ONLY place. `.env.example` uses
   empty values.

2. **Preserve the tool registry contract.** Every entry in `TOOLS` must
   have keys: `fn`, `desc`, `params`, `required`, `category`.
   `test_core.py::t_tools_schema` verifies this.

3. **Preserve the agentic loop.** `run_agent()` contains the smart
   task-mode detection, persistence nudge, anti-loop detection, and
   context-compaction — don't refactor casually.

4. **Cross-platform first.** Use `_IS_LINUX` / `_IS_MAC` / `_IS_WIN`
   / `_HAS_DISPLAY` flags. Never assume Linux or a display.

5. **Graceful degradation.** Every tool must handle missing deps
   with a clear ERROR string, never a crash. Module loading uses
   `except BaseException` — deliberate, so `pyo3` panics don't
   take out the whole program.

6. **Test after every change:**
   ```bash
   python3 agent.py --test         # 40 core tests
   python3 tests/demo_workflow.py  # end-to-end demo, no AI needed
   ```

## Adding a new tool

1. Define `tool_<name>(...) -> str` (always return a string).
2. Register in the `TOOLS` dict with all 5 required keys.
3. Add at least one test in `tests/test_core.py`.
4. Optionally add a REPL shortcut command near the other `elif cmd ==`
   handlers if it deserves one-key access.
5. Bump the tool count in `README.md`, `docs/INTEGRATION_MATRIX.md`,
   `docs/PHASE_STATUS.md`.

## Providers

Each provider class exposes `.call(messages, system) -> (text, calls)`.
`_pick_provider(name, model)` selects one based on env vars.

- `GeminiProvider` — current Google GenAI SDK/API
- `ClaudeProvider` — Anthropic Messages API
- `OpenAIProvider` — OpenAI Chat Completions
- `HuggingFaceProvider` — HF Inference OpenAI-compatible endpoint,
  falls back to ReAct-style `<tool_call>` parsing for text-only models
- `OllamaProvider` — local Ollama at `OLLAMA_BASE_URL`

To add a provider: implement the same `.call()` signature and add to
`_pick_provider()`.

## Security posture

- Default: safe (files, web, memory, math) — auto-execute
- Caution (shell, mouse, keyboard, apps) — execute + show output
- Authorized security tools (nmap, sqlmap) — require explicit user
  authorization in the conversation
- Never: unauthorized targeting, credential theft, persistence,
  lateral movement

Security repos (Responder, nishang) are source-preserved but
**not exposed** through the runtime — see
`docs/INTEGRATION_MATRIX.md` §Security Repositories.

## Commit conventions

- Author: `kevinhamza <kevin.x.hamza@gmail.com>` (set via git config)
- Trailer: Co-Authored-By line for the AI model that helped
- Message: `feat|fix|docs: Phase X — <one line summary>` + body
- Never `--no-verify`, never `--force` to main/master
- Never rewrite history on a shared branch
