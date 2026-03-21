#!/bin/bash
# grok-swarm-agent command for Claude Code
# Invokes the grok_agent.py Python script with Claude Code context

set -e

# Find the plugin root (3 levels up from commands/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
AGENT_SCRIPT="$PLUGIN_ROOT/src/agent/grok_agent.py"

# Default: preview mode
APPLY_FLAG=""
MAX_ITERATIONS="5"
VERIFY_CMD=""
TARGET="."

# Parse arguments
TASK=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --apply)
            APPLY_FLAG="--apply"
            shift
            ;;
        --target)
            TARGET="$2"
            shift 2
            ;;
        --max-iterations)
            MAX_ITERATIONS="$2"
            shift 2
            ;;
        --verify-cmd)
            VERIFY_CMD="$2"
            shift 2
            ;;
        -*)
            echo "Unknown option: $1" >&2
            echo "Usage: grok-swarm-agent [task description] [--apply] [--target DIR] [--max-iterations N] [--verify-cmd CMD]" >&2
            exit 1
            ;;
        *)
            # First non-flag is the task
            if [[ -z "$TASK" ]]; then
                TASK="$1"
            fi
            shift
            ;;
    esac
done

if [[ -z "$TASK" ]]; then
    echo "Usage: grok-swarm-agent [task description] [--apply] [--target DIR] [--max-iterations N] [--verify-cmd CMD]"
    echo ""
    echo "Example:"
    echo "  grok-swarm-agent refactor the auth module"
    echo "  grok-swarm-agent add tests --apply --verify-cmd pytest"
    exit 1
fi

# Build argument array
ARGS=(
    "$AGENT_SCRIPT"
    "--platform" "claude"
    "--target" "$TARGET"
    "--max-iterations" "$MAX_ITERATIONS"
)

if [[ -n "$APPLY_FLAG" ]]; then
    ARGS+=("$APPLY_FLAG")
fi

if [[ -n "$VERIFY_CMD" ]]; then
    ARGS+=("--verify-cmd" "$VERIFY_CMD")
fi

ARGS+=("--task" "$TASK")

# Execute
python3 "${ARGS[@]}"