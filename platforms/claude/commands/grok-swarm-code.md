---
name: grok-swarm-code
description: Generate code with Grok's multi-agent swarm. Searchable Grok-prefixed command.
argument-hint: <task> [--output-dir DIR] [--apply]
allowed-tools:
  - Bash
  - Write
  - Glob
---

## Step 1 — Ensure setup and MCP registration

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | sort -V | tail -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "missing-plugin"; exit 1; }
eval "$(bash "$PLUGIN_ROOT/commands/setup.sh")"
```

## Step 2 — Generate code

```bash
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/cli.py" code "$ARGUMENTS"
```

If files were written, summarize them. Otherwise show the generated output and the next apply step.
