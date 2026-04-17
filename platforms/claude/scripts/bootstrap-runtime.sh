#!/bin/bash
# Bootstrap the plugin-local Python runtime and print the interpreter path.

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
VENV_DIR="${PLUGIN_ROOT}/.venv"
REQUIREMENTS_FILE="${PLUGIN_ROOT}/src/requirements.txt"
OAUTH_SCRIPT="${PLUGIN_ROOT}/src/bridge/oauth_setup.py"
MCP_SERVER="${PLUGIN_ROOT}/src/mcp/grok_server.py"
STAMP_FILE="${VENV_DIR}/.grok-swarm-requirements.sha256"
SYSTEM_PYTHON=""
PYTHON_BIN=""

log() { printf '%s\n' "$*" >&2; }

resolve_system_python() {
    if command -v python3 >/dev/null 2>&1; then
        SYSTEM_PYTHON="$(command -v python3)"
    elif command -v python >/dev/null 2>&1; then
        SYSTEM_PYTHON="$(command -v python)"
    else
        log "ERROR: Python 3 is required. Install Python 3.8+ and re-run /grok-swarm-setup."
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

if [ ! -f "$REQUIREMENTS_FILE" ]; then
    log "ERROR: Plugin runtime is incomplete: missing ${REQUIREMENTS_FILE}."
    log "Reinstall the Grok Swarm Claude plugin so the bundled runtime is present."
    exit 1
fi

if [ ! -f "$OAUTH_SCRIPT" ] || [ ! -f "$MCP_SERVER" ]; then
    log "ERROR: Plugin runtime files are missing from ${PLUGIN_ROOT}/src."
    log "Reinstall the Grok Swarm Claude plugin and try again."
    exit 1
fi

resolve_system_python

if [ ! -d "$VENV_DIR" ]; then
    log "Creating Grok Swarm plugin-local Python environment..."
    "$SYSTEM_PYTHON" -m venv "$VENV_DIR"
fi

PYTHON_BIN="${VENV_DIR}/bin/python3"
if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN="${VENV_DIR}/bin/python"
fi

if [ ! -x "$PYTHON_BIN" ]; then
    log "ERROR: Failed to create a usable Python interpreter in ${VENV_DIR}."
    exit 1
fi

wanted_hash="$(requirements_hash)"
current_hash=""
if [ -f "$STAMP_FILE" ]; then
    current_hash="$(cat "$STAMP_FILE" 2>/dev/null || true)"
fi

if [ "$wanted_hash" != "$current_hash" ] || ! "$PYTHON_BIN" -c "import openai" >/dev/null 2>&1; then
    log "Installing Grok Swarm Python dependencies into ${VENV_DIR}..."
    "$PYTHON_BIN" -m pip install --quiet --upgrade pip
    "$PYTHON_BIN" -m pip install --quiet -r "$REQUIREMENTS_FILE"
    printf '%s\n' "$wanted_hash" > "$STAMP_FILE"
fi

printf '%s\n' "$PYTHON_BIN"
