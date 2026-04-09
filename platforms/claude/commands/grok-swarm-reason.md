---
name: grok-swarm-reason
description: Multi-perspective reasoning with Grok's swarm. Searchable Grok-prefixed command.
argument-hint: <question-or-task>
allowed-tools:
  - Bash
---

## Step 1 — Ensure setup and MCP registration

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | sort -V | tail -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "missing-plugin"; exit 1; }
eval "$(bash "$PLUGIN_ROOT/commands/setup.sh")"
```

## Step 2 — Run reasoning

```bash
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/cli.py" reason "$ARGUMENTS"
```

Present the conclusion and the main trade-offs Grok surfaced.
