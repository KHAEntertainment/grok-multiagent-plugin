#!/bin/bash
# Setup for Grok Swarm — delegates to PKCE OAuth flow
# The API key NEVER passes through Claude's context window.

set -e

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
CONFIG_DIR="${HOME}/.config/grok-swarm"
CONFIG_FILE="${CONFIG_DIR}/config.json"
VENV_DIR="${PLUGIN_ROOT}/.venv"
REQUIREMENTS_FILE="${PLUGIN_ROOT}/src/requirements.txt"
MCP_SERVER="${PLUGIN_ROOT}/src/mcp/grok_server.py"
OAUTH_SCRIPT="${PLUGIN_ROOT}/src/bridge/oauth_setup.py"
PYTHON_BIN=""
SYSTEM_PYTHON=""
STAMP_FILE="${VENV_DIR}/.grok-swarm-requirements.sha256"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1" >&2; }
error() { echo -e "${RED}[✗]${NC} $1" >&2; }

resolve_system_python() {
    if command -v python3 >/dev/null 2>&1; then
        SYSTEM_PYTHON="$(command -v python3)"
    elif command -v python >/dev/null 2>&1; then
        SYSTEM_PYTHON="$(command -v python)"
    else
        error "Python 3 is required. Install Python 3.8+ and re-run setup."
        exit 1
    fi
}

requirements_hash() {
    "$SYSTEM_PYTHON" - <<'PY' "$REQUIREMENTS_FILE"
import hashlib
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
print(hashlib.sha256(path.read_bytes()).hexdigest())
PY
}

ensure_runtime() {
    resolve_system_python

    if [ ! -f "$REQUIREMENTS_FILE" ]; then
        error "Plugin runtime is incomplete: missing ${REQUIREMENTS_FILE}."
        error "Reinstall the Grok Swarm Claude plugin so the bundled runtime is present."
        exit 1
    fi

    if [ ! -f "$OAUTH_SCRIPT" ] || [ ! -f "$MCP_SERVER" ]; then
        error "Plugin runtime files are missing from ${PLUGIN_ROOT}/src."
        error "Reinstall the Grok Swarm Claude plugin and try again."
        exit 1
    fi

    if [ ! -d "$VENV_DIR" ]; then
        log "Creating plugin-local Python environment..."
        "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
    fi

    PYTHON_BIN="${VENV_DIR}/bin/python3"
    if [ ! -x "$PYTHON_BIN" ]; then
        PYTHON_BIN="${VENV_DIR}/bin/python"
    fi

    if [ ! -x "$PYTHON_BIN" ]; then
        error "Failed to create a usable Python interpreter in ${VENV_DIR}."
        exit 1
    fi

    local wanted_hash=""
    local current_hash=""
    wanted_hash="$(requirements_hash)"
    if [ -f "$STAMP_FILE" ]; then
        current_hash="$(cat "$STAMP_FILE" 2>/dev/null || true)"
    fi

    if [ "$wanted_hash" != "$current_hash" ] || ! "$PYTHON_BIN" -c "import openai" >/dev/null 2>&1; then
        log "Installing Grok Swarm Python dependencies into ${VENV_DIR}..."
        "$PYTHON_BIN" -m pip install --quiet --upgrade pip
        "$PYTHON_BIN" -m pip install --quiet -r "$REQUIREMENTS_FILE"
        printf '%s\n' "$wanted_hash" > "$STAMP_FILE"
    else
        log "Plugin-local Python dependencies already installed"
    fi
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

# Register MCP server for native tool integration
if command -v claude >/dev/null 2>&1; then
    echo
    log "Registering Grok Swarm MCP server..."
    claude mcp remove grok-swarm >/dev/null 2>&1 || true
    if claude mcp add grok-swarm -- "$PYTHON_BIN" "$MCP_SERVER" 2>/dev/null; then
        log "MCP server registered — grok_query, grok_session_start/continue, grok_agent tools available"
    else
        warn "MCP registration failed (non-fatal). Register manually:"
        warn "  claude mcp add grok-swarm -- $PYTHON_BIN $MCP_SERVER"
    fi
else
    warn "Claude CLI not found, skipping MCP registration."
fi

echo
echo "Run '/grok-swarm:analyze Find bugs in this codebase' to get started."
echo "Or use the native MCP tools: grok_query, grok_session_start, grok_session_continue"
