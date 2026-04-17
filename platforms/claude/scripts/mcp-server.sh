#!/bin/bash
# Claude plugin MCP entrypoint. Bootstraps runtime before execing the server.

set -euo pipefail

PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
PYTHON_BIN="$("$PLUGIN_ROOT/scripts/bootstrap-runtime.sh")"

exec "$PYTHON_BIN" "$PLUGIN_ROOT/src/mcp/grok_server.py"
