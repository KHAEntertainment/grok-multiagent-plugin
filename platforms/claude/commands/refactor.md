---
name: refactor
description: Refactor code with Grok's multi-agent swarm. Improves quality while preserving behavior.
argument-hint: <task> [file-or-dir...] [--apply] [--output-dir DIR]
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Grok Swarm — Refactor

Runs multi-agent refactoring using Grok 4.20 via OpenRouter.

## Usage

```
/grok-swarm-refactor <task> [file-or-dir...] [--apply] [--output-dir DIR]
```

## Examples

```
/grok-swarm-refactor Convert callbacks to async/await in src/
/grok-swarm-refactor Improve error handling in api/ --apply
/grok-swarm-refactor Extract shared utilities --output-dir src/shared --apply
/grok-swarm-refactor Convert to async --use-morph --apply
```

## Flags

| Flag | Description |
|------|-------------|
| `--apply` | Write refactored files to disk (default: dry-run preview) |
| `--output-dir DIR` | Directory to write output files |
| `--use-morph` | Use Morph LLM MCP for partial file edits |
| `--thinking high` | Use 16-agent swarm for deeper reasoning |

## Step 1 — Ensure setup and MCP registration

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | sort -V | tail -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "missing-plugin"; exit 1; }
eval "$(bash "$PLUGIN_ROOT/commands/setup.sh")"
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/oauth_setup.py" --check >/dev/null 2>&1 && echo ready || echo setup_failed
```

If setup fails, explain the error and recommend running `/grok-swarm-setup`.

## Step 2 — Run refactor

```bash
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/cli.py" refactor "$ARGUMENTS"
```

## Step 3 — Present results

If `--apply` was passed, list the files written to disk.
Otherwise show the proposed changes as a preview and ask if the user wants to apply them.
