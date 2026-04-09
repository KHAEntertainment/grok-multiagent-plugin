---
name: analyze
description: Analyze code with Grok's multi-agent swarm. Security audit, bug detection, architecture review.
argument-hint: <task> [file-or-dir...]
allowed-tools:
  - Bash
  - Read
  - Glob
  - Grep
---

# Grok Swarm — Analyze

Runs a multi-agent code analysis using Grok 4.20 via OpenRouter.

## Usage

```
/grok-swarm:analyze <task> [file-or-dir...]
```

## Examples

```
/grok-swarm:analyze Find security vulnerabilities in src/auth/
/grok-swarm:analyze Review this file for bugs
/grok-swarm:analyze Architecture audit of the entire codebase
/grok-swarm:analyze Security audit --thinking high
```

## Step 1 — Check API key

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | head -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "missing-plugin"; exit 1; }
PYTHON_BIN="$PLUGIN_ROOT/.venv/bin/python3"
[ -x "$PYTHON_BIN" ] || PYTHON_BIN=python3
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/oauth_setup.py" --check >/dev/null 2>&1 && echo key || echo nokey
```

If the output is `nokey`, tell the user:
> No API key found. Run `/grok-swarm:setup` to authorize via OAuth (key never enters context), or `/grok-swarm:set-key YOUR_KEY` as a fallback.

Stop here until the key is configured.

## Step 2 — Run analysis

Locate the bridge CLI and run:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | head -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "Grok Swarm plugin not found."; exit 1; }
PYTHON_BIN="$PLUGIN_ROOT/.venv/bin/python3"
[ -x "$PYTHON_BIN" ] || PYTHON_BIN=python3
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/cli.py" analyze "$ARGUMENTS"
```

Where `$ARGUMENTS` is the full argument string passed to this command.

## Step 3 — Present results

Show the analysis output. If files were flagged, list them with the issue and severity.

For `--thinking high` flag, Grok uses a 16-agent swarm for deeper analysis (slower, higher cost).
