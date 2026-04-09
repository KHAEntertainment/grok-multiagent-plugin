---
name: grok-swarm-setup
description: Bootstrap Grok Swarm for Claude Code, including MCP registration.
argument-hint: None
allowed-tools:
  - Bash
---

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | sort -V | tail -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "Grok Swarm plugin not found."; exit 1; }
bash "$PLUGIN_ROOT/.claude-plugin/setup.sh"
```

After setup succeeds, remind the user that native Grok MCP tools should now appear in Claude and that they can use `/grok-swarm-analyze`, `/grok-swarm-refactor`, `/grok-swarm-code`, and `/grok-swarm-reason`.
