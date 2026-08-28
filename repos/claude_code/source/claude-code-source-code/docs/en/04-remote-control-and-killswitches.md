# Remote Control & Killswitches

> Based on Claude Code v2.1.88 decompiled source code analysis.

## Overview

Claude Code implements multiple remote control mechanisms that allow Anthropic (and enterprise administrators) to modify behavior without explicit user consent.

## 1. Remote Managed Settings

### Architecture

Every eligible session fetches settings from:
```
GET /api/claude_code/settings
```

Source: `src/services/remoteManagedSettings/index.ts:105-107`

### Polling Behavior

```typescript
// src/services/remoteManagedSettings/index.ts:52-54
const SETTINGS_TIMEOUT_MS = 10000
const DEFAULT_MAX_RETRIES = 5
const POLLING_INTERVAL_MS = 60 * 60 * 1000 // 1 hour
```

Settings are polled every hour, with up to 5 retries on failure.

### Eligibility

- Console users (API key): All eligible
- OAuth users: Only Enterprise/C4E and Team subscribers

### Accept-or-Die Dialog

When remote settings contain "dangerous" changes, a blocking dialog is shown:

```typescript
// src/services/remoteManagedSettings/securityCheck.tsx:67-73
export function handleSecurityCheckResult(result: SecurityCheckResult): boolean {
  if (result === 'rejected') {
    gracefulShutdownSync(1)  // Exit with code 1
    return false
  }
  return true
}
```

Users who reject remote settings have the application **forcefully terminated**. The only options are: accept the remote settings, or Claude Code exits.

### Graceful Degradation

If the remote server is unreachable, cached settings from disk are used:

```typescript
// src/services/remoteManagedSettings/index.ts:433-436
if (cachedSettings) {
  logForDebugging('Remote settings: Using stale cache after fetch failure')
  setSessionCache(cachedSettings)
  return cachedSettings
}
```

Once remote settings have been applied, they persist even when the server is down.

## 2. Feature Flag Killswitches

Multiple features can be remotely disabled via GrowthBook feature flags:

### Bypass Permissions Killswitch

```typescript
// src/utils/permissions/bypassPermissionsKillswitch.ts
// Checks a Statsig gate to disable bypass permissions
```

Can disable permission bypass capabilities without user consent.

### Auto Mode Circuit Breaker

```typescript
// src/utils/permissions/autoModeState.ts
// autoModeCircuitBroken state prevents re-entry to auto mode
```

Auto mode can be remotely disabled.

### Fast Mode Killswitch

```typescript
// src/utils/fastMode.ts
// Fetches from /api/claude_code_penguin_mode
// Can permanently disable fast mode for a user
```

### Analytics Sink Killswitch

```typescript
// src/services/analytics/sinkKillswitch.ts:4
const SINK_KILLSWITCH_CONFIG_NAME = 'tengu_frond_boric'
```

Can remotely stop all analytics output.

### Agent Teams Killswitch

```typescript
// src/utils/agentSwarmsEnabled.ts
// Requires both env var AND GrowthBook gate 'tengu_amber_flint'
```

### Voice Mode Killswitch

```typescript
// src/voice/voiceModeEnabled.ts:21
// 'tengu_amber_quartz_disabled' — emergency off for voice mode
```

## 3. Model Override System

Anthropic can remotely override which model internal employees use:

```typescript
// src/utils/model/antModels.ts:32-33
// @[MODEL LAUNCH]: Update tengu_ant_model_override with new ant-only models
// @[MODEL LAUNCH]: Add the codename to scripts/excluded-strings.txt
```

The `tengu_ant_model_override` GrowthBook flag can:
- Set a default model
- Set default effort level
- Append to the system prompt
- Define custom model aliases

## 4. Penguin Mode

Fast mode status is fetched from a dedicated endpoint:

```typescript
// src/utils/fastMode.ts
// GET /api/claude_code_penguin_mode
// If API indicates disabled, permanently disabled for user
```

Multiple feature flags control fast mode availability:
- `tengu_penguins_off`
- `tengu_marble_sandcastle`

## Summary

| Mechanism | Scope | User Consent |
|-----------|-------|-------------|
| Remote managed settings | Enterprise/Team | Accept or exit |
| GrowthBook feature flags | All users | None |
| Killswitches | All users | None |
| Model override | Internal (ant) | None |
| Fast mode control | All users | None |

The remote control infrastructure is extensive and operates largely without user visibility or consent. Enterprise administrators can enforce policies that users cannot override, and Anthropic can remotely change behavior for any user through feature flags.
