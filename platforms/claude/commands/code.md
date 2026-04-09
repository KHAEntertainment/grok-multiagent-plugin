---
name: code
description: Generate production-ready code with Grok's multi-agent swarm.
argument-hint: <task> [--output-dir DIR] [--apply]
allowed-tools:
  - Bash
  - Write
  - Glob
---

# Grok Swarm — Code Generation

Generate clean, production-ready code using Grok 4.20 via OpenRouter.

## Usage

```
/grok-swarm:code <task> [--output-dir DIR] [--apply]
```

## Examples

```
/grok-swarm:code Write a FastAPI endpoint for user registration
/grok-swarm:code Add JWT auth middleware to Express --output-dir src/middleware --apply
/grok-swarm:code Create a PostgreSQL migration for the users table
/grok-swarm:code Write unit tests for src/auth.py
```

## Flags

| Flag | Description |
|------|-------------|
| `--apply` | Write generated files to disk (default: dry-run preview) |
| `--output-dir DIR` | Directory for generated files |
| `--thinking high` | Use 16-agent swarm for complex generation |

## Step 1 — Check API key

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | head -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "missing-plugin"; exit 1; }
PYTHON_BIN="$PLUGIN_ROOT/.venv/bin/python3"
[ -x "$PYTHON_BIN" ] || PYTHON_BIN=python3
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/oauth_setup.py" --check >/dev/null 2>&1 && echo key || echo nokey
```

If `nokey`, direct the user to `/grok-swarm:setup` or `/grok-swarm:set-key`.

## Step 2 — Generate code

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | head -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "Grok Swarm plugin not found."; exit 1; }
PYTHON_BIN="$PLUGIN_ROOT/.venv/bin/python3"
[ -x "$PYTHON_BIN" ] || PYTHON_BIN=python3
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/cli.py" code "$ARGUMENTS"
```

## Step 3 — Present results

Show the generated code. If `--apply` was passed, confirm which files were written.
Otherwise ask: "Apply these files?" before writing.
