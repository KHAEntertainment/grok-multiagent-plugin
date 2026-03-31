#!/bin/bash
# Setup for Grok Swarm — delegates to PKCE OAuth flow
# The API key NEVER passes through Claude's context window.

set -e

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
CONFIG_DIR="${HOME}/.config/grok-swarm"
CONFIG_FILE="${CONFIG_DIR}/config.json"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1" >&2; }
error() { echo -e "${RED}[✗]${NC} $1" >&2; }

echo "=========================================="
echo "  Grok Swarm Setup"
echo "=========================================="
echo

# Check for existing key in config.json or env
if [ -f "$CONFIG_FILE" ]; then
    key=$(python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('api_key',''))" 2>/dev/null || echo "")
    if [ -n "$key" ]; then
        log "Found existing API key in $CONFIG_FILE"
        exit 0
    fi
fi

env_key="${OPENROUTER_API_KEY:-${XAI_API_KEY:-}}"
if [ -n "$env_key" ]; then
    log "Found API key in environment variable"
    exit 0
fi

# No key found — launch OAuth flow
OAUTH_SCRIPT="${PLUGIN_ROOT}/src/bridge/oauth_setup.py"
if [ ! -f "$OAUTH_SCRIPT" ]; then
    # Try relative to installed location
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    OAUTH_SCRIPT="${SCRIPT_DIR}/../src/bridge/oauth_setup.py"
fi

if [ -f "$OAUTH_SCRIPT" ]; then
    log "Launching OAuth setup — your API key will never touch the LLM context"
    echo
    if python3 "$OAUTH_SCRIPT"; then
        log "Setup complete!"
        echo
        echo "Run '/grok-swarm:analyze Find bugs in this codebase' to get started."
    else
        error "OAuth setup failed. Set OPENROUTER_API_KEY env var as a fallback."
        exit 1
    fi
else
    error "OAuth setup script not found."
    echo
    echo "Set your API key manually:"
    echo "  export OPENROUTER_API_KEY='your-key-here'"
    echo "  Get a key at: https://openrouter.ai/keys"
    exit 1
fi
