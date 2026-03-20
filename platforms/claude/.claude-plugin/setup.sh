#!/bin/bash
# Interactive setup for Grok Swarm API key
# Stores configuration in .claude/grok-swarm.local.md

set -e

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
CLAUDE_DIR="${HOME}/.claude"
SETTINGS_FILE="${CLAUDE_DIR}/grok-swarm.local.md"
CONFIG_DIR="${HOME}/.config/grok-swarm"
CONFIG_FILE="${CONFIG_DIR}/config.json"

# Colors
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

# Check for existing key in multiple locations
get_existing_key() {
    # Check .local.md first
    if [ -f "$SETTINGS_FILE" ]; then
        local key=$(grep -oP '^api_key:\s*\K\S+' "$SETTINGS_FILE" 2>/dev/null || echo "")
        if [ -n "$key" ]; then echo "$key"; return 0; fi
    fi
    # Check config.json
    if [ -f "$CONFIG_FILE" ]; then
        local key=$(grep -oP '"api_key"\s*:\s*"\K[^"]+' "$CONFIG_FILE" 2>/dev/null || echo "")
        if [ -n "$key" ]; then echo "$key"; return 0; fi
    fi
    # Check env var
    local env_key="${OPENROUTER_API_KEY:-${XAI_API_KEY:-}}"
    if [ -n "$env_key" ]; then echo "$env_key"; return 0; fi
    return 1
}

# Check for existing key
if existing=$(get_existing_key 2>/dev/null); then
    log "Found existing API key"
    echo
    read -p "Overwrite? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log "Keeping existing configuration."
        exit 0
    fi
fi

# Prompt for key
echo "To use Grok Swarm, you need an OpenRouter API key."
echo "Get one at: https://openrouter.ai/keys"
echo
read -p "Enter your OpenRouter API key: " -s api_key
echo

if [ -z "$api_key" ]; then
    error "No API key provided. Aborting."
    exit 1
fi

# Create directories
mkdir -p "$CLAUDE_DIR"
mkdir -p "$CONFIG_DIR"

# Write to .local.md (Claude Code plugin settings pattern)
cat > "$SETTINGS_FILE" << EOF
---
api_key: ${api_key}
---

# Grok Swarm Configuration

This file is managed by the grok-swarm plugin setup.
Do not edit manually - run \`/grok-swarm:setup\` to reconfigure.
EOF

# Also write to config.json for CLI compatibility
cat > "$CONFIG_FILE" << EOF
{
  "api_key": "${api_key}"
}
EOF

chmod 600 "$SETTINGS_FILE" "$CONFIG_FILE"

log "API key saved!"
log "Configuration: $SETTINGS_FILE"
echo
echo "Run '/grok-swarm:analyze Find bugs in this codebase' to get started."
