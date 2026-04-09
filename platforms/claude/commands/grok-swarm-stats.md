---
name: grok-swarm-stats
description: Show token usage and cost statistics for Grok Swarm.
argument-hint: None
allowed-tools:
  - Bash
---

## Step 1 — Ensure setup and MCP registration

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | sort -V | tail -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "missing-plugin"; exit 1; }
eval "$(bash "$PLUGIN_ROOT/commands/setup.sh")"
```

## Step 2 — Show usage stats

```bash
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/cli.py" stats
```
