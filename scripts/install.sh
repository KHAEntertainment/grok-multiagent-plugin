#!/bin/bash
# install.sh — Install Grok Swarm for OpenClaw and/or Claude Code
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION=$(cat "$PROJECT_DIR/VERSION" 2>/dev/null || echo "1.0.0")
TARGET="${1:-both}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1" >&2; }

usage() {
    echo "Usage: $0 [openclaw|claude|both]"
    echo "  openclaw  — Install for OpenClaw only"
    echo "  claude    — Install for Claude Code only"
    echo "  both      — Install for both (default)"
}

install_openclaw() {
    log "Installing Grok Swarm for OpenClaw..."

    # Run build if dist doesn't exist
    if [ ! -d "$PROJECT_DIR/dist/openclaw" ]; then
        warn "dist/ not found. Running build.sh first..."
        "$SCRIPT_DIR/build.sh"
    fi

    # Create directories
    mkdir -p ~/.openclaw/extensions/grok-swarm
    mkdir -p ~/.openclaw/skills/grok-refactor

    # Copy plugin
    cp -r "$PROJECT_DIR/dist/openclaw/plugin/"* ~/.openclaw/extensions/grok-swarm/

    # Copy skill
    cp -r "$PROJECT_DIR/dist/openclaw/bridge/"* ~/.openclaw/skills/grok-refactor/

    # Set up Python venv
    if command -v python3 &> /dev/null; then
        python3 -m venv ~/.openclaw/skills/grok-refactor/.venv
        ~/.openclaw/skills/grok-refactor/.venv/bin/pip install -q openai>=1.0.0
    fi

    log "OpenClaw installation complete!"
    log "Restart gateway: openclaw gateway restart"
}

install_claude() {
    log "Installing Grok Swarm for Claude Code..."

    mkdir -p ~/.claude/plugins

    # Run build if dist doesn't exist
    if [ ! -d "$PROJECT_DIR/dist/claude" ]; then
        warn "dist/ not found. Running build.sh first..."
        "$SCRIPT_DIR/build.sh"
    fi

    # Copy plugin
    cp -r "$PROJECT_DIR/dist/claude" ~/.claude/plugins/grok-swarm

    # Install CLI
    if [ -f "$PROJECT_DIR/pyproject.toml" ]; then
        pip install -e "$PROJECT_DIR" 2>/dev/null || warn "Could not pip install. Run: pip install -e $PROJECT_DIR"
    fi

    log "Claude Code installation complete!"
    log "Restart Claude Code or run /reload-plugins"
}

echo "=========================================="
echo "  Grok Swarm Installer v$VERSION"
echo "=========================================="
echo

case "$TARGET" in
    openclaw)
        install_openclaw
        ;;
    claude)
        install_claude
        ;;
    both|all|"")
        install_openclaw
        echo
        install_claude
        ;;
    *)
        error "Unknown target: $TARGET"
        usage
        exit 1
        ;;
esac

echo
log "Done!"
