#!/bin/bash
# install.sh — Install Grok Swarm Tool for OpenClaw
#
# Usage: ./install.sh [--uninstall]
#
# This script installs the Grok Swarm bridge and plugin to your OpenClaw setup.
# Requires OpenClaw v2026.3.0 or later.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OPENCLAW_HOME="${OPENCLAW_HOME:-$HOME/.openclaw}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1" >&2; }

# Check prerequisites
check_prereqs() {
    log "Checking prerequisites..."

    # OpenClaw
    if ! command -v openclaw &> /dev/null; then
        error "OpenClaw not found. Install from https://docs.openclaw.ai"
        exit 1
    fi

    # Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3 not found"
        exit 1
    fi

    # Node
    if ! command -v node &> /dev/null; then
        error "Node.js not found"
        exit 1
    fi

    log "Prerequisites OK"
}

# Install Python dependencies
install_python_deps() {
    log "Installing Python dependencies..."

    # Create venv in skill directory
    SKILL_DIR="$OPENCLAW_HOME/skills/grok-refactor"
    mkdir -p "$SKILL_DIR"

    if command -v python3 &> /dev/null; then
        if [ ! -d "$SKILL_DIR/.venv" ]; then
            python3 -m venv "$SKILL_DIR/.venv"
        fi
        "$SKILL_DIR/.venv/bin/pip" install -q openai>=2.28.0
        log "Python dependencies installed"
    else
        warn "Python not found, skipping venv setup"
    fi
}

# Install bridge skill
install_bridge() {
    log "Installing Grok Swarm bridge skill..."

    SKILL_DIR="$OPENCLAW_HOME/skills/grok-refactor"
    mkdir -p "$SKILL_DIR"

    cp -r "$SCRIPT_DIR/src/bridge/"* "$SKILL_DIR/"

    # Set up venv
    install_python_deps

    log "Bridge skill installed to $SKILL_DIR"
}

# Install plugin
install_plugin() {
    log "Installing Grok Swarm plugin..."

    PLUGIN_DIR="$OPENCLAW_HOME/extensions/grok-swarm"
    mkdir -p "$PLUGIN_DIR"

    cp -r "$SCRIPT_DIR/src/plugin/"* "$PLUGIN_DIR/"

    log "Plugin installed to $PLUGIN_DIR"
}

# Update OpenClaw config
update_config() {
    log "Updating OpenClaw configuration..."

    CONFIG_FILE="$OPENCLAW_HOME/openclaw.json"

    if [ ! -f "$CONFIG_FILE" ]; then
        warn "OpenClaw config not found at $CONFIG_FILE"
        return
    fi

    # Check if grok-swarm is in plugins.allow
    if ! grep -q '"grok-swarm"' "$CONFIG_FILE"; then
        warn "grok-swarm not in plugins.allow — you may need to add it manually"
    fi

    # Check if grok_swarm is in agent tools
    if ! grep -q '"grok_swarm"' "$CONFIG_FILE"; then
        warn "grok_swarm not in agent tools — you may need to add it manually"
    fi

    log "Config check complete"
}

# Restart OpenClaw
restart_openclaw() {
    log "Restarting OpenClaw gateway..."

    if command -v openclaw &> /dev/null; then
        openclaw gateway restart 2>/dev/null || warn "Could not restart gateway. Run: openclaw gateway restart"
    else
        warn "Run 'openclaw gateway restart' when ready"
    fi
}

# Main
main() {
    echo "=========================================="
    echo "  Grok Swarm Tool Installer"
    echo "  xAI Grok 4.20 Multi-Agent Bridge"
    echo "=========================================="
    echo

    check_prereqs
    install_bridge
    install_plugin
    update_config

    echo
    log "Installation complete!"
    echo
    echo "Next steps:"
    echo "  1. Configure OpenRouter API key in OpenClaw"
    echo "  2. Restart gateway: openclaw gateway restart"
    echo "  3. Verify: openclaw status | grep grok"
    echo
    echo "Usage:"
    echo "  node ~/.openclaw/skills/grok-refactor/index.js --prompt 'Your task' --mode analyze"
    echo
}

main "$@"
