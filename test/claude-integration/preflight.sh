#!/bin/bash
#===============================================================================
# Grok Swarm Plugin - Pre-Flight Cleanup & Environment Validation
#
# This script ensures a clean slate before testing the Claude Code integration.
# Run this FIRST before any other tests.
#===============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CONFIG_PATH="${HOME}/.config/grok-swarm/config.json"
LOCAL_MD_PATH="${HOME}/.claude/grok-swarm.local.md"
OPENCLAW_PATH="${HOME}/.openclaw"

# Prefer Python 3.10 if available (Homebrew python3 may be externally managed)
if [[ -x "/Library/Frameworks/Python.framework/Versions/3.10/bin/python3" ]]; then
    PYTHON_BIN="/Library/Frameworks/Python.framework/Versions/3.10/bin/python3"
else
    PYTHON_BIN="python3"
fi

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Grok Swarm - Pre-Flight Check            ${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Track if we found anything
FOUND_ANYTHING=0

#-------------------------------------------------------------------------------
# Section 1: Check for existing installations
#-------------------------------------------------------------------------------
echo -e "${YELLOW}[1/6] Checking for existing grok-swarm installations...${NC}"

# Check config.json
if [[ -f "$CONFIG_PATH" ]]; then
    echo -e "  ${RED}FOUND${NC}: $CONFIG_PATH"
    FOUND_ANYTHING=1
else
    echo -e "  ${GREEN}CLEAN${NC}: No config file at $CONFIG_PATH"
fi

# Check .local.md
if [[ -f "$LOCAL_MD_PATH" ]]; then
    echo -e "  ${RED}FOUND${NC}: $LOCAL_MD_PATH"
    FOUND_ANYTHING=1
else
    echo -e "  ${GREEN}CLEAN${NC}: No .local.md file"
fi

# Check OpenClaw profiles (expected for dual-purpose plugin)
if [[ -d "$OPENCLAW_PATH" ]]; then
    echo -e "  ${BLUE}PRESENT${NC}: $OPENCLAW_PATH/ (expected - dual-purpose plugin)"
    # Don't set FOUND_ANYTHING=1 - OpenClaw presence is expected
else
    echo -e "  ${GREEN}CLEAN${NC}: No .openclaw directory"
fi

echo ""

#-------------------------------------------------------------------------------
# Section 2: Check for environment variables
#-------------------------------------------------------------------------------
echo -e "${YELLOW}[2/6] Checking environment variables...${NC}"

if [[ -n "${OPENROUTER_API_KEY:-}" ]]; then
    echo -e "  ${RED}SET${NC}: OPENROUTER_API_KEY (value masked: ${OPENROUTER_API_KEY:0:8}...)"
    FOUND_ANYTHING=1
else
    echo -e "  ${GREEN}CLEAN${NC}: OPENROUTER_API_KEY not set"
fi

if [[ -n "${XAI_API_KEY:-}" ]]; then
    echo -e "  ${RED}SET${NC}: XAI_API_KEY (value masked: ${XAI_API_KEY:0:8}...)"
    FOUND_ANYTHING=1
else
    echo -e "  ${GREEN}CLEAN${NC}: XAI_API_KEY not set"
fi

echo ""

#-------------------------------------------------------------------------------
# Section 3: Check for global npm/pip installations
#-------------------------------------------------------------------------------
echo -e "${YELLOW}[3/6] Checking for global installations...${NC}"

if command -v grok-swarm &> /dev/null; then
    echo -e "  ${RED}FOUND${NC}: grok-swarm in PATH"
    which grok-swarm
    FOUND_ANYTHING=1
else
    echo -e "  ${GREEN}CLEAN${NC}: No global grok-swarm command"
fi

if pip show grok-swarm &> /dev/null; then
    echo -e "  ${RED}FOUND${NC}: grok-swarm pip package"
    pip show grok-swarm | grep Version
    FOUND_ANYTHING=1
else
    echo -e "  ${GREEN}CLEAN${NC}: No global grok-swarm pip package"
fi

echo ""

#-------------------------------------------------------------------------------
# Section 4: Validate Python dependencies
#-------------------------------------------------------------------------------
echo -e "${YELLOW}[4/6] Validating Python dependencies...${NC}"

MISSING_DEPS=()

if "$PYTHON_BIN" -c "import openai" 2>/dev/null; then
    echo -e "  ${GREEN}OK${NC}: openai package"
else
    echo -e "  ${RED}MISSING${NC}: openai package"
    MISSING_DEPS+=("openai")
fi

if "$PYTHON_BIN" -c "import anthropic" 2>/dev/null; then
    echo -e "  ${GREEN}OK${NC}: anthropic package"
else
    echo -e "  ${RED}MISSING${NC}: anthropic package"
    MISSING_DEPS+=("anthropic")
fi

if "$PYTHON_BIN" -c "import yaml" 2>/dev/null; then
    echo -e "  ${GREEN}OK${NC}: pyyaml package"
else
    echo -e "  ${RED}MISSING${NC}: pyyaml package"
    MISSING_DEPS+=("pyyaml")
fi

if "$PYTHON_BIN" -c "import keyring" 2>/dev/null; then
    echo -e "  ${GREEN}OK${NC}: keyring package"
else
    echo -e "  ${RED}MISSING${NC}: keyring package"
    MISSING_DEPS+=("keyring")
fi

if [[ ${#MISSING_DEPS[@]} -gt 0 ]]; then
    echo ""
    echo -e "${YELLOW}NOTE:${NC} Missing dependencies can be installed with:"
    echo -e "  pip install ${MISSING_DEPS[*]}"
fi

echo ""

#-------------------------------------------------------------------------------
# Section 5: Check Claude Code plugin structure
#-------------------------------------------------------------------------------
echo -e "${YELLOW}[5/6] Checking Claude Code plugin structure...${NC}"

# Find repo root (two levels up from test/claude-integration/)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLUGIN_DIR="${REPO_ROOT}/platforms/claude"

if [[ -d "$PLUGIN_DIR/.claude-plugin" ]]; then
    echo -e "  ${GREEN}FOUND${NC}: .claude-plugin directory"

    # Check for essential files
    for file in "setup.sh" "plugin.json"; do
        if [[ -f "$PLUGIN_DIR/.claude-plugin/$file" ]]; then
            echo -e "    ${GREEN}OK${NC}: $file"
        else
            echo -e "    ${RED}MISSING${NC}: $file"
        fi
    done
else
    echo -e "  ${RED}MISSING${NC}: .claude-plugin directory"
    echo -e "         Expected at: $PLUGIN_DIR/.claude-plugin"
fi

echo ""

#-------------------------------------------------------------------------------
# Section 6: Check skill files
#-------------------------------------------------------------------------------
echo -e "${YELLOW}[6/6] Checking skill files...${NC}"

SKILL_PATHS=(
    "platforms/claude/skills/grok-swarm/SKILL.md"
    ".claude/skills/grok-multi-agent-api/SKILL.md"
)

for skill_path in "${SKILL_PATHS[@]}"; do
    if [[ -f "$skill_path" ]]; then
        echo -e "  ${GREEN}FOUND${NC}: $skill_path"
    else
        echo -e "  ${YELLOW}NOT FOUND${NC}: $skill_path (may not be installed globally)"
    fi
done

echo ""

#-------------------------------------------------------------------------------
# Summary
#-------------------------------------------------------------------------------
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Pre-Flight Summary                        ${NC}"
echo -e "${BLUE}============================================${NC}"

if [[ $FOUND_ANYTHING -eq 1 ]]; then
    echo -e "${YELLOW}WARNING:${NC} Found remnants of previous installation(s)"
    echo ""
    echo "To clean up before testing, run:"
    echo ""
    echo "  # Remove config"
    echo "  rm -f $CONFIG_PATH"
    echo ""
    echo "  # Remove .local.md (contains keys - don't commit!)"
    echo "  rm -f $LOCAL_MD_PATH"
    echo ""
    echo "  # Unset env vars"
    echo "  unset OPENROUTER_API_KEY XAI_API_KEY"
    echo ""
    echo "  # Remove OpenClaw profiles"
    echo "  rm -rf $OPENCLAW_PATH"
    echo ""
    echo -e "${YELLOW}After cleanup, re-run this script to confirm.${NC}"
    exit 1
else
    echo -e "${GREEN}ALL CLEAR${NC}: No remnants found. Environment is clean."
    echo ""
    echo -e "${GREEN}Ready to run tests!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Run: python3 test/claude-integration/test_setup.py"
    echo "  2. Run: python3 test/claude-integration/test_modes.py"
    echo "  3. Run: python3 test/claude-integration/test_edge_cases.py"
    echo "  4. Run: python3 test/claude-integration/test_tools.py"
    exit 0
fi
