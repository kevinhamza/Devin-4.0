# Future Roadmap — What the Source Code Reveals

> Based on Claude Code v2.1.88 decompiled source code analysis.

## 1. Next Model: Numbat

The most concrete evidence of the next model launch:

```typescript
// src/constants/prompts.ts:402
// @[MODEL LAUNCH]: Remove this section when we launch numbat.
```

**Numbat** (袋食蚁兽) is the codename for an upcoming model. The comment indicates the output efficiency section will be revised when Numbat launches, suggesting it may have better native output control.

### Future Version Numbers

```typescript
// src/utils/undercover.ts:49
- Unreleased model version numbers (e.g., opus-4-7, sonnet-4-8)
```

**Opus 4.7** and **Sonnet 4.8** are in development.

### Codename Evolution Chain

```
Fennec (耳廓狐) → Opus 4.6 → [Numbat?]
Capybara (水豚) → Sonnet v8 → [?]
Tengu (天狗) → telemetry/product prefix
```

The Fennec-to-Opus migration is documented:

```typescript
// src/migrations/migrateFennecToOpus.ts:7-11
// fennec-latest → opus
// fennec-latest[1m] → opus[1m]
// fennec-fast-latest → opus[1m] + fast mode
```

### MODEL LAUNCH Checklist

The codebase contains 20+ `@[MODEL LAUNCH]` markers listing everything to update:

- Default model names (`FRONTIER_MODEL_NAME`)
- Model family IDs
- Knowledge cutoff dates
- Pricing tables
- Context window configurations
- Thinking mode support flags
- Display name mappings
- Migration scripts

## 2. KAIROS — Autonomous Agent Mode

The largest unreleased feature, KAIROS transforms Claude Code from a reactive assistant into a proactive autonomous agent.

### System Prompt (excerpts)

```
// src/constants/prompts.ts:860-913

You are running autonomously.
You will receive <tick> prompts that keep you alive between turns.
If you have nothing useful to do, call SleepTool.
Bias toward action — read files, make changes, commit without asking.

## Terminal focus
- Unfocused: The user is away. Lean heavily into autonomous action.
- Focused: The user is watching. Be more collaborative.
```

### Associated Tools

| Tool | Feature Flag | Purpose |
|------|-------------|---------|
| SleepTool | KAIROS / PROACTIVE | Control pacing between autonomous actions |
| SendUserFileTool | KAIROS | Proactively send files to users |
| PushNotificationTool | KAIROS / KAIROS_PUSH_NOTIFICATION | Push notifications to user devices |
| SubscribePRTool | KAIROS_GITHUB_WEBHOOKS | Subscribe to GitHub PR webhook events |
| BriefTool | KAIROS_BRIEF | Proactive status updates |

### Behavior

- Operates on `<tick>` heartbeat prompts
- Adjusts autonomy based on terminal focus state
- Can commit, push, and make decisions independently
- Sends proactive notifications and status updates
- Monitors GitHub PRs for changes

## 3. Voice Mode

Push-to-talk voice input is fully implemented but gated behind `VOICE_MODE` feature flag.

```typescript
// src/voice/voiceModeEnabled.ts
// Connects to Anthropic's voice_stream WebSocket endpoint
// Uses conversation_engine backed models for speech-to-text
// Hold-to-talk: hold keybinding to record, release to submit
```

- OAuth-only (no API key / Bedrock / Vertex support)
- Uses mTLS for WebSocket connections
- Killswitch: `tengu_amber_quartz_disabled`

## 4. Unreleased Tools

Tools found in source but not yet enabled for external users:

| Tool | Feature Flag | Description |
|------|-------------|-------------|
| **WebBrowserTool** | `WEB_BROWSER_TOOL` | Built-in browser automation (codename: bagel) |
| **TerminalCaptureTool** | `TERMINAL_PANEL` | Terminal panel capture and monitoring |
| **WorkflowTool** | `WORKFLOW_SCRIPTS` | Execute predefined workflow scripts |
| **MonitorTool** | `MONITOR_TOOL` | System/process monitoring |
| **SnipTool** | `HISTORY_SNIP` | Conversation history snipping/truncation |
| **ListPeersTool** | `UDS_INBOX` | Unix domain socket peer discovery |
| **RemoteTriggerTool** | `AGENT_TRIGGERS_REMOTE` | Remote agent triggering |
| **TungstenTool** | ant-only | Internal performance monitoring panel |
| **VerifyPlanExecutionTool** | VERIFY_PLAN env | Plan execution verification |
| **OverflowTestTool** | `OVERFLOW_TEST_TOOL` | Context overflow testing |
| **SubscribePRTool** | `KAIROS_GITHUB_WEBHOOKS` | GitHub PR webhook subscriptions |

## 5. Coordinator Mode

Multi-agent coordination system:

```typescript
// src/coordinator/coordinatorMode.ts
// Feature flag: COORDINATOR_MODE
```

Enables coordinated task execution across multiple agents with shared state and messaging.

## 6. Buddy System (Virtual Pets)

The complete pet companion system is implemented but not yet launched:

- **18 species**: duck, goose, blob, cat, dragon, octopus, owl, penguin, turtle, snail, ghost, axolotl, capybara, cactus, robot, rabbit, mushroom, chonk
- **5 rarity tiers**: Common (60%), Uncommon (25%), Rare (10%), Epic (4%), Legendary (1%)
- **7 hats**: crown, tophat, propeller, halo, wizard, beanie, tinyduck
- **5 stats**: DEBUGGING, PATIENCE, CHAOS, WISDOM, SNARK
- **1% shiny chance**: Sparkle variant of any species
- **Deterministic generation**: Based on hash of user ID

Source: `src/buddy/`

## 7. Dream Task

Background memory consolidation subagent:

```
// src/tasks/DreamTask/
// Auto-dreaming feature that works in the background
// Controlled by 'tengu_onyx_plover' feature flag
```

Enables the AI to autonomously process and consolidate memories during idle time.

## Summary: The Three Directions

1. **New Models**: Numbat (next), Opus 4.7, Sonnet 4.8 in development
2. **Autonomous Agent**: KAIROS mode — unattended operation, proactive actions, push notifications
3. **Multi-modal**: Voice input ready, browser tool waiting, workflow automation coming

Claude Code is evolving from a **coding assistant** into an **always-on autonomous development agent**.
