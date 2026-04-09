---
name: reason
description: Multi-perspective reasoning with Grok's swarm. Compare approaches, evaluate trade-offs, get architectural guidance.
argument-hint: <question-or-task>
allowed-tools:
  - Bash
---

# Grok Swarm — Reason

Multi-perspective collaborative reasoning using Grok 4.20's multi-agent swarm.

## Usage

```
/grok-swarm-reason <question-or-task>
```

## Examples

```
/grok-swarm-reason Compare microservices vs monolith for this project
/grok-swarm-reason What's the best database schema for a multi-tenant SaaS?
/grok-swarm-reason Should we use GraphQL or REST for this API?
/grok-swarm-reason Evaluate the trade-offs of our current auth approach
```

## Step 1 — Ensure setup and MCP registration

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | sort -V | tail -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "missing-plugin"; exit 1; }
eval "$(bash "$PLUGIN_ROOT/commands/setup.sh")"
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/oauth_setup.py" --check >/dev/null 2>&1 && echo ready || echo setup_failed
```

If setup fails, explain the error and recommend running `/grok-swarm-setup`.

## Step 2 — Run reasoning

```bash
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/cli.py" reason "$ARGUMENTS"
```

## Step 3 — Present results

Present the multi-agent consensus and highlight where agents disagreed — divergent perspectives are often the most valuable part of reason mode.
