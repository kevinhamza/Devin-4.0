# Undercover Mode Analysis

> Based on Claude Code v2.1.88 decompiled source code analysis.

## What Is Undercover Mode?

Undercover mode is a safety system for Anthropic employees contributing to public/open-source repositories. When active, it strips all AI attribution and instructs the model to present its contributions as if written by a human developer.

Source: `src/utils/undercover.ts`

## Activation Logic

```typescript
// src/utils/undercover.ts:28-37
export function isUndercover(): boolean {
  if (process.env.USER_TYPE === 'ant') {
    if (isEnvTruthy(process.env.CLAUDE_CODE_UNDERCOVER)) return true
    // Auto: active unless positively confirmed internal repo
    return getRepoClassCached() !== 'internal'
  }
  return false
}
```

Key properties:
- **Internal only**: Only active for Anthropic employees (`USER_TYPE === 'ant'`)
- **Default ON**: Active in all repos except those on the internal allowlist
- **No force-off**: "There is NO force-OFF. This guards against model codename leaks"
- **External builds**: Dead-code-eliminated by the bundler; never executes

## The Prompt Given to the Model

```typescript
// src/utils/undercover.ts:39-69
export function getUndercoverInstructions(): string {
  return `## UNDERCOVER MODE — CRITICAL

You are operating UNDERCOVER in a PUBLIC/OPEN-SOURCE repository. Your commit
messages, PR titles, and PR bodies MUST NOT contain ANY Anthropic-internal
information. Do not blow your cover.

NEVER include in commit messages or PR descriptions:
- Internal model codenames (animal names like Capybara, Tengu, etc.)
- Unreleased model version numbers (e.g., opus-4-7, sonnet-4-8)
- Internal repo or project names (e.g., claude-cli-internal, anthropics/…)
- Internal tooling, Slack channels, or short links (e.g., go/cc, #claude-code-…)
- The phrase "Claude Code" or any mention that you are an AI
- Any hint of what model or version you are
- Co-Authored-By lines or any other attribution

Write commit messages as a human developer would — describe only what the code
change does.

GOOD:
- "Fix race condition in file watcher initialization"
- "Add support for custom key bindings"

BAD (never write these):
- "Fix bug found while testing with Claude Capybara"
- "1-shotted by claude-opus-4-6"
- "Generated with Claude Code"
- "Co-Authored-By: Claude Opus 4.6 <…>"`
}
```

## Attribution System

The attribution system (`src/utils/attribution.ts`, `src/utils/commitAttribution.ts`) complements undercover mode:

```typescript
// src/utils/attribution.ts:70-72
// @[MODEL LAUNCH]: Update the hardcoded fallback model name below
// (guards against codename leaks).
// For external repos, fall back to "Claude Opus 4.6" for unrecognized models.
```

```typescript
// src/utils/model/model.ts:386-392
function maskModelCodename(baseName: string): string {
  // e.g. capybara-v2-fast → cap*****-v2-fast
  const [codename = '', ...rest] = baseName.split('-')
  const masked = codename.slice(0, 3) + '*'.repeat(Math.max(0, codename.length - 3))
  return [masked, ...rest].join('-')
}
```

## Implications

### For Open Source

When Anthropic employees use Claude Code to contribute to open-source projects:
1. Code is written by AI but commits appear human-authored
2. No "Co-Authored-By: Claude" attribution
3. No "Generated with Claude Code" markers
4. Project maintainers and community cannot identify AI-generated contributions
5. This potentially violates open-source transparency norms regarding AI contributions

### For Anthropic's Protection

The primary stated purpose is preventing accidental leaks of:
- Internal model codenames (competitive intelligence)
- Unreleased version numbers (market timing)
- Internal infrastructure details (security)

### Ethical Considerations

The phrase "Do not blow your cover" frames the AI as an undercover agent. The intentional concealment of AI authorship in public code contributions raises questions about:
- Transparency in open-source communities
- Compliance with project contribution guidelines
- The line between trade secret protection and deception
