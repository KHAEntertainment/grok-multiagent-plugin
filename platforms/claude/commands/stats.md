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
/grok-swarm-stats
```

## What it shows

- **Session tokens**: Tokens used in current conversation
- **Total today**: All Grok Swarm usage for today
- **Estimated cost**: Cost based on OpenRouter Grok 4.20 pricing
- **Quota status**: Remaining API quota

## Data Source

## Step 1 — Ensure setup and MCP registration

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | sort -V | tail -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "missing-plugin"; exit 1; }
eval "$(bash "$PLUGIN_ROOT/commands/setup.sh")"
```

## Step 2 — Show stats

```bash
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/cli.py" stats
```

Usage data is stored in `~/.config/grok-swarm/usage.json`.

The Grok Swarm bridge automatically logs each request's token usage for tracking.
