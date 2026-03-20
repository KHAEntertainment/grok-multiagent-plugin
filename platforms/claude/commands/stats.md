---
name: stats
description: Show token usage and cost statistics for Grok Swarm
argument-hint: None
allowed-tools:
  - Bash
---

# Grok Swarm Usage Stats

Shows current session and cumulative token usage for Grok Swarm.

## Usage

```
/grok-swarm:stats
```

## What it shows

- **Session tokens**: Tokens used in current conversation
- **Total today**: All Grok Swarm usage for today
- **Estimated cost**: Cost based on OpenRouter Grok 4.20 pricing
- **Quota status**: Remaining API quota

## Data Source

Usage data is stored in `~/.config/grok-swarm/usage.json`.

The Grok Swarm bridge automatically logs each request's token usage for tracking.
