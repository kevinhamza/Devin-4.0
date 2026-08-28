# Telemetry & Privacy Analysis

> Based on Claude Code v2.1.88 decompiled source code analysis.

## Overview

Claude Code implements a two-tier analytics pipeline that collects extensive environment and usage metadata. While there is no evidence of keylogging or source code exfiltration, the breadth of collection and inability to fully opt out raises legitimate privacy concerns.

## Data Pipeline Architecture

### First-Party Logging (1P)

- **Endpoint**: `https://api.anthropic.com/api/event_logging/batch`
- **Protocol**: OpenTelemetry with Protocol Buffers
- **Batch size**: Up to 200 events per batch, flushed every 10 seconds
- **Retry**: Quadratic backoff, up to 8 attempts, disk-persisted for durability
- **Storage**: Failed events saved to `~/.claude/telemetry/`

Source: `src/services/analytics/firstPartyEventLoggingExporter.ts`

### Third-Party Logging (Datadog)

- **Endpoint**: `https://http-intake.logs.us5.datadoghq.com/api/v2/logs`
- **Scope**: Limited to 64 pre-approved event types
- **Token**: `pubbbf48e6d78dae54bceaa4acf463299bf`

Source: `src/services/analytics/datadog.ts`

## What Is Collected

### Environment Fingerprint

Every event carries this metadata (`src/services/analytics/metadata.ts:417-452`):

```
- platform, platformRaw, arch, nodeVersion
- terminal type
- installed package managers and runtimes
- CI/CD detection, GitHub Actions metadata
- WSL version, Linux distro, kernel version
- VCS (version control system) type
- Claude Code version and build time
- deployment environment
```

### Process Metrics (`metadata.ts:457-467`)

```
- uptime, rss, heapTotal, heapUsed
- CPU usage and percentage
- memory arrays and external allocations
```

### User Tracking (`metadata.ts:472-496`)

```
- model in use
- session ID, user ID, device ID
- account UUID, organization UUID
- subscription tier (max, pro, enterprise, team)
- repository remote URL hash (SHA256, first 16 chars)
- agent type, team name, parent session ID
```

### Tool Input Logging

Tool inputs are truncated by default:

```
- Strings: truncated at 512 chars, displayed as 128 + ellipsis
- JSON: limited to 4,096 chars
- Arrays: max 20 items
- Nested objects: max 2 levels deep
```

Source: `metadata.ts:236-241`

However, when `OTEL_LOG_TOOL_DETAILS=1` is set, **full tool inputs are logged**.

Source: `metadata.ts:86-88`

### File Extension Tracking

Bash commands involving `rm, mv, cp, touch, mkdir, chmod, chown, cat, head, tail, sort, stat, diff, wc, grep, rg, sed` have their file arguments' extensions extracted and logged.

Source: `metadata.ts:340-412`

## The Opt-Out Problem

The first-party logging pipeline **cannot be disabled** for direct Anthropic API users.

```typescript
// src/services/analytics/firstPartyEventLogger.ts:141-144
export function is1PEventLoggingEnabled(): boolean {
  return !isAnalyticsDisabled()
}
```

`isAnalyticsDisabled()` returns true only for:
- Test environments
- Third-party cloud providers (Bedrock, Vertex)
- Global telemetry opt-out (not exposed in settings UI)

There is **no user-facing setting** to disable first-party event logging.

## GrowthBook A/B Testing

Users are assigned to experiment groups via GrowthBook without explicit consent. The system sends user attributes including:

```
- id, sessionId, deviceID
- platform, organizationUUID, subscriptionType
```

Source: `src/services/analytics/growthbook.ts`

## Key Takeaways

1. **Volume**: Hundreds of events per session are collected
2. **No opt-out**: First-party logging cannot be disabled by direct API users
3. **Persistence**: Failed events are saved to disk and retried aggressively
4. **Third-party sharing**: Data flows to Datadog
5. **Tool detail backdoor**: `OTEL_LOG_TOOL_DETAILS=1` enables full input logging
6. **Repository fingerprinting**: Repo URLs are hashed and sent for server-side correlation
