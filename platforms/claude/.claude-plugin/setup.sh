#!/bin/bash
# Setup for Grok Swarm — delegates to PKCE OAuth flow
# The API key NEVER passes through Claude's context window.

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
CONFIG_DIR="${HOME}/.config/grok-swarm"
CONFIG_FILE="${CONFIG_DIR}/config.json"
OAUTH_SCRIPT="${PLUGIN_ROOT}/src/bridge/oauth_setup.py"
BOOTSTRAP_SCRIPT="${PLUGIN_ROOT}/scripts/bootstrap-runtime.sh"
PYTHON_BIN=""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1" >&2; }
error() { echo -e "${RED}[✗]${NC} $1" >&2; }

ensure_runtime() {
    if [ ! -f "$BOOTSTRAP_SCRIPT" ]; then
        error "Plugin runtime is incomplete: missing ${BOOTSTRAP_SCRIPT}."
        error "Reinstall the Grok Swarm Claude plugin and try again."
        exit 1
    fi

    PYTHON_BIN="$("$BOOTSTRAP_SCRIPT")"
    if [ ! -x "$PYTHON_BIN" ]; then
        error "Bootstrap did not return a usable Python interpreter."
        exit 1
    fi
    log "Plugin-local Python runtime ready at ${PYTHON_BIN}"
}

echo "=========================================="
echo "  Grok Swarm Setup"
echo "=========================================="
echo

ensure_runtime

# Check for existing key in config.json or env
HAVE_KEY=0
if [ -f "$CONFIG_FILE" ]; then
    key=$("$PYTHON_BIN" -c "import json; print(json.load(open('$CONFIG_FILE')).get('api_key',''))" 2>/dev/null || echo "")
    if [ -n "$key" ]; then
        log "Found existing API key in $CONFIG_FILE"
        HAVE_KEY=1
    fi
fi

env_key="${OPENROUTER_API_KEY:-${XAI_API_KEY:-}}"
if [ -n "$env_key" ]; then
    log "Found API key in environment variable"
    HAVE_KEY=1
fi

if [ "$HAVE_KEY" -eq 0 ]; then
    log "Launching OAuth setup — your API key will never touch the LLM context"
    echo
    if "$PYTHON_BIN" "$OAUTH_SCRIPT"; then
        log "Setup complete!"
    else
        error "OAuth setup failed. Set OPENROUTER_API_KEY env var as a fallback."
        exit 1
    fi
fi

# Claude Code starts plugin MCP servers automatically from .mcp.json.
# Remove the legacy manual entry created by older setup flows when the plugin
# scoped server is visible, otherwise users see duplicate Grok MCP servers.
if command -v claude >/dev/null 2>&1; then
    echo
    if claude mcp list 2>/dev/null | grep -q '^plugin:grok-swarm:grok-swarm:'; then
        claude mcp remove grok-swarm >/dev/null 2>&1 || true
        log "Plugin MCP server is managed by Claude Code"
    else
        warn "Plugin MCP server is not visible yet. Restart Claude Code or re-enable the plugin if MCP tools do not appear."
    fi
else
    warn "Claude CLI not found; plugin MCP will be managed by Claude Code when available."
fi

echo
echo "Run '/grok-swarm' or '/grok-swarm-analyze Find bugs in this codebase' to get started."
echo "Other searchable commands: /grok-swarm-refactor, /grok-swarm-code, /grok-swarm-reason, /grok-swarm-stats, /grok-swarm-set-key"
echo "Native MCP tools: grok_query, grok_session_start, grok_session_continue, grok_agent"
