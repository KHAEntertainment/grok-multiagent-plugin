#!/bin/bash
# Helper for Grok Swarm Claude commands.
# Ensures the plugin-local runtime exists and Grok MCP is registered.

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
SETUP_SCRIPT="${PLUGIN_ROOT}/.claude-plugin/setup.sh"
PYTHON_BIN="${PLUGIN_ROOT}/.venv/bin/python3"
NEEDS_SETUP=0

log() { printf '%s\n' "$*" >&2; }

if [ ! -d "$PLUGIN_ROOT" ]; then
    log "ERROR: Grok Swarm plugin root not found."
    exit 1
fi

if [ ! -f "$SETUP_SCRIPT" ]; then
    log "ERROR: Grok Swarm setup script not found at ${SETUP_SCRIPT}."
    exit 1
fi

if [ ! -x "$PYTHON_BIN" ]; then
    NEEDS_SETUP=1
fi

if [ "$NEEDS_SETUP" -eq 0 ] && ! "$PYTHON_BIN" -c "import openai" >/dev/null 2>&1; then
    NEEDS_SETUP=1
fi

if command -v claude >/dev/null 2>&1; then
    if ! claude mcp list 2>/dev/null | grep -q '^grok-swarm:'; then
        NEEDS_SETUP=1
    fi
fi

if [ "$NEEDS_SETUP" -eq 1 ]; then
    log "Grok Swarm runtime or MCP registration missing; running setup..."
    bash "$SETUP_SCRIPT" >&2
fi

if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

printf 'PLUGIN_ROOT=%q\n' "$PLUGIN_ROOT"
printf 'PYTHON_BIN=%q\n' "$PYTHON_BIN"
