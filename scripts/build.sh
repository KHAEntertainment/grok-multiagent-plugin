#!/bin/bash
set -e

VERSION=$(cat VERSION)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$SCRIPT_DIR/dist"

log() { echo -e "[+] $1"; }
error() { echo -e "[✗] $1" >&2; }

echo "============================================"
echo "  Grok Swarm Build Script"
echo "  Version: $VERSION"
echo "============================================"
echo

# Clean dist
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR/openclaw" "$DIST_DIR/claude"

log "Building for OpenClaw + Claude Code..."

# Copy bridge to both
cp -r src/bridge "$DIST_DIR/openclaw/bridge"
cp -r src/bridge "$DIST_DIR/claude/bridge"

# Copy OpenClaw plugin
cp -r src/plugin "$DIST_DIR/openclaw/plugin"

# Copy Claude plugin
cp -r platforms/claude/.claude-plugin "$DIST_DIR/claude/"
cp -r platforms/claude/skills "$DIST_DIR/claude/"

# Copy shared skill
mkdir -p "$DIST_DIR/openclaw/skills"
cp -r skills/grok-refactor "$DIST_DIR/openclaw/skills/"

# Version substitution
find "$DIST_DIR" -type f \( -name "*.json" -o -name "*.md" -o -name "*.toml" \) -exec sed -i "s/1\.0\.0/$VERSION/g" {} \; 2>/dev/null || true

# Make scripts executable
chmod +x "$DIST_DIR/openclaw/bridge/"*.sh 2>/dev/null || true
chmod +x "$DIST_DIR/claude/bridge/"*.py 2>/dev/null || true

log "Build complete!"
echo
echo "Artifacts in dist/:"
echo "  dist/openclaw/  — OpenClaw plugin + skill"
echo "  dist/claude/    — Claude Code plugin"
echo
echo "To install:"
echo "  OpenClaw:  cp -r dist/openclaw/* ~/.openclaw/"
echo "  Claude:    cp -r dist/claude/* ~/.claude/plugins/"
