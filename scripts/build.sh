#!/bin/bash
set -e

# Resolve project root (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
VERSION=$(cat "$PROJECT_DIR/VERSION")
DIST_DIR="$PROJECT_DIR/dist"

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
cp -r "$PROJECT_DIR/src/bridge" "$DIST_DIR/openclaw/bridge"
cp -r "$PROJECT_DIR/src/bridge" "$DIST_DIR/claude/bridge"

# Copy OpenClaw plugin
cp -r "$PROJECT_DIR/src/plugin" "$DIST_DIR/openclaw/plugin"

# Copy Claude plugin
cp -r "$PROJECT_DIR/platforms/claude/.claude-plugin" "$DIST_DIR/claude/"
cp -r "$PROJECT_DIR/platforms/claude/skills" "$DIST_DIR/claude/"

# Copy shared skill
mkdir -p "$DIST_DIR/openclaw/skills"
cp -r "$PROJECT_DIR/skills/grok-refactor" "$DIST_DIR/openclaw/skills/"

# Version substitution (targeted to avoid rewriting dependency constraints)
find "$DIST_DIR" -type f \( -name "*.json" -o -name "*.md" -o -name "*.toml" \) | while read -r file; do
    # Create temp file for portable sed (works on macOS and Linux)
    tmp_file="${file}.tmp"
    # Match only explicit version fields, not dependency constraints
    # JSON: "version": "1.0.0"  TOML: version = "1.0.0"  Badges: /v1.0.0 or -1.0.0-
    sed -e 's/\("version"\s*:\s*"\)1\.0\.0"/\1'"$VERSION"'"/g' \
        -e 's/\(version\s*=\s*"\)1\.0\.0"/\1'"$VERSION"'"/g' \
        -e 's/\(\/v\)1\.0\.0/\1'"$VERSION"'/g' \
        -e 's/\(-\)1\.0\.0\(-\)/\1'"$VERSION"'\2/g' \
        "$file" > "$tmp_file" && mv "$tmp_file" "$file"
done

# Make scripts executable
chmod +x "$DIST_DIR/openclaw/bridge/"*.py 2>/dev/null || true
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