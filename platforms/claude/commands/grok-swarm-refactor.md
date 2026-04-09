---
name: grok-swarm-refactor
description: Refactor code with Grok's multi-agent swarm. Searchable Grok-prefixed command.
argument-hint: <task> [file-or-dir...] [--apply] [--output-dir DIR]
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

## Step 1 — Ensure setup and MCP registration

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | sort -V | tail -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "missing-plugin"; exit 1; }
eval "$(bash "$PLUGIN_ROOT/commands/setup.sh")"
```

## Step 2 — Run refactor

```bash
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/cli.py" refactor "$ARGUMENTS"
```

If `--apply` was used, summarize the files written. Otherwise present the preview and next apply step.
