# Hidden Features & Model Codenames

> Based on Claude Code v2.1.88 decompiled source code analysis.

## Model Codename System

Anthropic uses **animal names** as internal model codenames. These are aggressively protected from leaking into external builds.

### Known Codenames

| Codename | Role | Evidence |
|----------|------|----------|
| **Tengu** (天狗) | Product/telemetry prefix, possibly a model | Used as `tengu_*` prefix for all 250+ analytics events and feature flags |
| **Capybara** | Sonnet-series model, currently at v8 | `capybara-v2-fast[1m]`, prompt patches for v8 behavior issues |
| **Fennec** (耳廓狐) | Predecessor to Opus 4.6 | Migration: `fennec-latest` → `opus` |
| **Numbat** (袋食蚁兽) | Next model launch | Comment: "Remove this section when we launch numbat" |

### Codename Protection

The `undercover` mode explicitly lists protected codenames:

```typescript
// src/utils/undercover.ts:48-49
NEVER include in commit messages or PR descriptions:
- Internal model codenames (animal names like Capybara, Tengu, etc.)
- Unreleased model version numbers (e.g., opus-4-7, sonnet-4-8)
```

The build system uses `scripts/excluded-strings.txt` to scan for leaked codenames. Buddy system species are encoded via `String.fromCharCode()` to avoid triggering the canary:

```typescript
// src/buddy/types.ts:10-13
// One species name collides with a model-codename canary in excluded-strings.txt.
// The check greps build output (not source), so runtime-constructing the value keeps
// the literal out of the bundle while the check stays armed for the actual codename.
```

That colliding species is **capybara** — both a pet species and a model codename.

### Capybara Behavior Issues (v8)

Source code reveals specific behavioral problems with Capybara v8:

1. **Stop sequence false trigger** (~10% rate when `<functions>` at prompt tail)
   - Source: `src/utils/messages.ts:2141`

2. **Empty tool_result causes zero output**
   - Source: `src/utils/toolResultStorage.ts:281`

3. **Over-commenting** — requires dedicated anti-comment prompt patches
   - Source: `src/constants/prompts.ts:204`

4. **High false-claims rate**: v8 has 29-30% FC rate vs v4's 16.7%
   - Source: `src/constants/prompts.ts:237`

5. **Insufficient verification** — requires "thoroughness counterweight"
   - Source: `src/constants/prompts.ts:210`

## Feature Flag Naming Convention

All feature flags use the `tengu_` prefix with **random word pairs** to obscure their purpose:

| Flag | Purpose |
|------|---------|
| `tengu_onyx_plover` | Auto Dream (background memory consolidation) |
| `tengu_coral_fern` | memdir feature |
| `tengu_moth_copse` | Another memdir switch |
| `tengu_herring_clock` | Team memory |
| `tengu_passport_quail` | Path feature |
| `tengu_slate_thimble` | Another memdir switch |
| `tengu_sedge_lantern` | Away Summary |
| `tengu_frond_boric` | Analytics kill switch |
| `tengu_amber_quartz_disabled` | Voice mode kill switch |
| `tengu_amber_flint` | Agent teams |
| `tengu_hive_evidence` | Verification agent |

The random word pattern (adjective/material + nature/object) prevents external observers from inferring feature purpose from flag names alone.

## Internal vs External User Difference

Anthropic employees (`USER_TYPE === 'ant'`) receive significantly better treatment:

### Prompt Differences (`src/constants/prompts.ts`)

| Dimension | External Users | Internal (ant) |
|-----------|---------------|----------------|
| Output style | "Be extra concise" | "Err on the side of more explanation" |
| False-claims mitigation | None | Dedicated Capybara v8 patches |
| Numeric length anchors | None | "≤25 words between tools, ≤100 words final" |
| Verification agent | None | Required for non-trivial changes |
| Comment guidance | Generic | Dedicated anti-over-commenting prompt |
| Proactive correction | None | "If user has misconception, say so" |

### Tool Access

Internal users have access to tools not available externally:
- `REPLTool` — REPL mode
- `SuggestBackgroundPRTool` — background PR suggestions
- `TungstenTool` — performance monitoring panel
- `VerifyPlanExecutionTool` — plan verification
- Agent nesting (agents spawning agents)

## Hidden Commands

| Command | Status | Description |
|---------|--------|-------------|
| `/btw` | Active | Ask side questions without interrupting |
| `/stickers` | Active | Order Claude Code stickers (opens browser) |
| `/thinkback` | Active | 2025 Year in Review |
| `/effort` | Active | Set model effort level |
| `/good-claude` | Stub | Hidden placeholder |
| `/bughunter` | Stub | Hidden placeholder |
