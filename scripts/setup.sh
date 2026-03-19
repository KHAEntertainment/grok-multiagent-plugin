#!/bin/bash
# setup.sh — First-time setup for Grok Swarm
# Handles API key configuration for Claude Code (no built-in secret management)

set -e

CONFIG_DIR="${HOME}/.config/grok-swarm"
CONFIG_FILE="${CONFIG_DIR}/config.json"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1" >&2; }

echo "=========================================="
echo "  Grok Swarm Setup"
echo "=========================================="
echo

# Check for existing key
existing_key=""
if [ -f "$CONFIG_FILE" ]; then
    existing_key=$(grep -o '"api_key"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_FILE" 2>/dev/null | cut -d'"' -f4 || echo "")
    if [ -n "$existing_key" ]; then
        log "Found existing API key in $CONFIG_FILE"
        echo
        read -p "Overwrite existing key? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log "Keeping existing configuration."
            exit 0
        fi
    fi
fi

# Check environment variable
env_key="${OPENROUTER_API_KEY:-${XAI_API_KEY:-}}"
if [ -n "$env_key" ] && [ -z "$existing_key" ]; then
    log "Found API key in environment variable."
    mkdir -p "$CONFIG_DIR"
    echo "{\"api_key\": \"$env_key\"}" > "$CONFIG_FILE"
    chmod 600 "$CONFIG_FILE"
    log "Saved to $CONFIG_FILE"
    exit 0
fi

# Prompt for key
echo "To use Grok Swarm, you need an OpenRouter API key."
echo
echo "Get one at: https://openrouter.ai/keys"
echo
read -p "Enter your OpenRouter API key: " -s api_key
echo

if [ -z "$api_key" ]; then
    error "No API key provided. Aborting."
    exit 1
fi

# Save to config
mkdir -p "$CONFIG_DIR"
echo "{\"api_key\": \"$api_key\"}" > "$CONFIG_FILE"
chmod 600 "$CONFIG_FILE"

log "API key saved to $CONFIG_FILE"
log "Setup complete!"
echo
echo "Usage:"
echo "  grok-swarm analyze --prompt 'Your task'"
