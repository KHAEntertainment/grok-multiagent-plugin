---
name: grok-swarm
description: Bootstrap Grok Swarm in Claude Code and show the available Grok-prefixed commands.
argument-hint: [optional-task]
allowed-tools:
  - Bash
---

# Grok Swarm

Use this as the entry point after installing or upgrading the plugin.

## Step 1 — Ensure setup and MCP registration

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | sort -V | tail -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "Grok Swarm plugin not found."; exit 1; }
bash "$PLUGIN_ROOT/.claude-plugin/setup.sh"
```

## Step 2 — Tell the user what to run next

After setup succeeds, tell the user these searchable commands are available:

- `/grok-swarm-setup`
- `/grok-swarm-analyze`
- `/grok-swarm-refactor`
- `/grok-swarm-code`
- `/grok-swarm-reason`
- `/grok-swarm-stats`
- `/grok-swarm-set-key`

Also tell them the native MCP tools should now be available:

- `grok_query`
- `grok_session_start`
- `grok_session_continue`
- `grok_agent`
