#!/bin/bash
# grok-swarm:setup — Interactive API key setup for Claude Code
# Run automatically on first use or via /grok-swarm:setup

CLAUDE_DIR="${HOME}/.claude"
SETTINGS_FILE="${CLAUDE_DIR}/grok-swarm.local.md"
CONFIG_FILE="${HOME}/.config/grok-swarm/config.json"

# Check if API key exists
get_api_key() {
    if [ -f "$SETTINGS_FILE" ]; then
        grep -q "^api_key:" "$SETTINGS_FILE" && grep "^api_key:" "$SETTINGS_FILE" | cut -d' ' -f2-
        return 0
    fi
    if [ -f "$CONFIG_FILE" ]; then
        python3 -c "import json; print(json.load(open('$CONFIG_FILE')).get('api_key', ''))" 2>/dev/null
        return 0
    fi
    [ -n "$OPENROUTER_API_KEY" ] && echo "$OPENROUTER_API_KEY" && return 0
    return 1
}

if api_key=$(get_api_key) && [ -n "$api_key" ]; then
    echo "Grok Swarm is configured!"
    echo "API key found: ${api_key:0:8}..."
    echo
    echo "Run '/grok-swarm:analyze Find bugs in this codebase' to get started."
    exit 0
fi

# No API key - prompt for setup
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
exec "$SCRIPT_DIR/setup.sh"
