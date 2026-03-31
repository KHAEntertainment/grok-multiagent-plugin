#!/usr/bin/env python3
"""
grok_server.py — MCP (Model Context Protocol) server for Grok Swarm.

Exposes Grok 4.20 Multi-Agent as native tools over the MCP stdio transport
(JSON-RPC 2.0, newline-delimited, on stdin/stdout).

Installation:
    claude mcp add grok-swarm -- python3 /path/to/src/mcp/grok_server.py

Tools:
    grok_query            — Stateless single call to Grok
    grok_session_start    — Begin a multi-turn session
    grok_session_continue — Continue an existing session
    grok_agent            — Run the autonomous agent loop

Requires: Python 3.8+, openai package.
"""

import json
import logging
import sys
from pathlib import Path

# Ensure sibling packages are importable
_repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_repo_root / "src"))

from bridge.grok_bridge import (
    call_grok_with_messages,
    get_api_key,
    read_files,
    strip_pgp_blocks,
    MODE_PROMPTS,
    AGENT_COUNTS,
)

# Lazy import — only needed if grok_agent tool is called
_agent_module = None

# Session store — imported lazily to avoid circular deps at module level
_session_module = None

# ---------------------------------------------------------------------------
# Logging (stderr only — MCP spec reserves stdout for protocol messages)
# ---------------------------------------------------------------------------

logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format="[grok-mcp] %(levelname)s %(message)s",
)
log = logging.getLogger("grok-mcp")

# ---------------------------------------------------------------------------
# MCP Protocol constants
# ---------------------------------------------------------------------------

SERVER_NAME = "grok-swarm"
SERVER_VERSION = "1.3.0"
PROTOCOL_VERSION = "2024-11-05"

# ---------------------------------------------------------------------------
# Tool definitions (JSON Schema format for MCP, NOT OpenAI format)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "grok_query",
        "description": (
            "Send a single stateless query to the Grok 4.20 multi-agent swarm. "
            "Use for code analysis, refactoring, generation, or reasoning tasks. "
            "Optionally pass file paths for codebase context."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Task instruction or question for Grok.",
                },
                "mode": {
                    "type": "string",
                    "enum": ["refactor", "analyze", "code", "reason", "orchestrate"],
                    "default": "reason",
                    "description": "Task mode. 'orchestrate' requires the 'system' parameter.",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File paths to include as codebase context.",
                },
                "system": {
                    "type": "string",
                    "description": "Override system prompt (required for orchestrate mode).",
                },
                "thinking": {
                    "type": "string",
                    "enum": ["low", "high"],
                    "default": "low",
                    "description": "Thinking level: low = 4 agents, high = 16 agents.",
                },
                "timeout": {
                    "type": "integer",
                    "default": 120,
                    "description": "API timeout in seconds.",
                },
            },
            "required": ["prompt"],
        },
    },
    {
        "name": "grok_session_start",
        "description": (
            "Start a new multi-turn conversation session with Grok. "
            "Returns a session_id that can be used with grok_session_continue "
            "to maintain conversation history across multiple calls."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "mode": {
                    "type": "string",
                    "enum": ["refactor", "analyze", "code", "reason", "orchestrate"],
                    "default": "reason",
                    "description": "Task mode for this session.",
                },
                "system": {
                    "type": "string",
                    "description": "Override system prompt.",
                },
                "thinking": {
                    "type": "string",
                    "enum": ["low", "high"],
                    "default": "low",
                    "description": "Thinking level: low = 4 agents, high = 16 agents.",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File paths to include as initial context.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "grok_session_continue",
        "description": (
            "Continue an existing multi-turn session with Grok. "
            "Grok remembers all previous messages in the session."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID returned by grok_session_start.",
                },
                "message": {
                    "type": "string",
                    "description": "Follow-up message or instruction.",
                },
                "files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Additional file paths to add as context.",
                },
            },
            "required": ["session_id", "message"],
        },
    },
    {
        "name": "grok_agent",
        "description": (
            "Run the autonomous Grok agent loop. The agent discovers files, "
            "calls Grok, applies changes, and optionally verifies with a command. "
            "Iterates up to max_iterations times."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {
                    "type": "string",
                    "description": "Task instruction for the agent.",
                },
                "target": {
                    "type": "string",
                    "default": ".",
                    "description": "Target directory or file to operate on.",
                },
                "apply": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether to actually write changes (default: dry-run preview).",
                },
                "max_iterations": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum number of agent iterations.",
                },
                "verify_cmd": {
                    "type": "string",
                    "description": "Command to run after each iteration for verification (e.g. 'pytest').",
                },
            },
            "required": ["task"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

def _handle_grok_query(params):
    """Stateless single call to Grok."""
    prompt = params["prompt"]
    mode = params.get("mode", "reason")
    files = params.get("files", [])
    system = params.get("system")
    thinking = params.get("thinking", "low")
    timeout = params.get("timeout", 120)

    if mode == "orchestrate" and not system:
        return _error_content("orchestrate mode requires the 'system' parameter")

    # Resolve system prompt
    if system:
        system_content = system
    else:
        system_content = MODE_PROMPTS.get(mode)
        if system_content is None:
            return _error_content(f"Mode '{mode}' requires the 'system' parameter")

    # Read file context
    if files:
        context = read_files(files)
        log.info("Read %d files (%d chars context)", len(files), len(context))
        system_content += f"\n\n## Codebase Context\n{context}"

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": prompt},
    ]

    log.info("grok_query: mode=%s thinking=%s timeout=%d", mode, thinking, timeout)

    response = call_grok_with_messages(
        messages=messages, timeout=timeout, thinking=thinking, mode=mode,
    )

    if not response.choices:
        return _error_content("Empty response from Grok API")

    content = response.choices[0].message.content or ""
    return _text_content(strip_pgp_blocks(content))


def _handle_grok_session_start(params):
    """Start a new multi-turn session."""
    session_mod = _get_session_module()

    mode = params.get("mode", "reason")
    system = params.get("system")
    thinking = params.get("thinking", "low")
    files = params.get("files", [])

    # Read initial file context
    file_context = ""
    if files:
        file_context = read_files(files)

    session = session_mod.create_session(
        mode=mode,
        system_override=system,
        thinking=thinking,
        initial_file_context=file_context,
    )

    log.info("Session started: %s (mode=%s, thinking=%s)", session.session_id, mode, thinking)

    return _text_content(json.dumps({
        "session_id": session.session_id,
        "mode": session.mode,
        "thinking": session.thinking,
        "message": f"Session {session.session_id} started. Use grok_session_continue to send messages.",
    }))


def _handle_grok_session_continue(params):
    """Continue an existing session."""
    session_mod = _get_session_module()

    session_id = params["session_id"]
    message = params["message"]
    files = params.get("files", [])

    session = session_mod.get_session(session_id)
    if session is None:
        return _error_content(f"Session not found: {session_id}")

    # Read additional file context
    file_context = ""
    if files:
        file_context = read_files(files)

    try:
        response = session.send_message(message, file_context=file_context)
    except Exception as exc:
        log.error("Session %s error: %s", session_id, exc)
        return _error_content(f"Grok API error: {exc}")

    return _text_content(strip_pgp_blocks(response))


def _handle_grok_agent(params):
    """Run the autonomous agent loop."""
    global _agent_module
    if _agent_module is None:
        sys.path.insert(0, str(_repo_root / "src" / "agent"))
        from grok_agent import run_agent_loop, AgentState, AgentStatus, Platform
        _agent_module = sys.modules["grok_agent"]

    task = params["task"]
    target = params.get("target", ".")
    apply_changes = params.get("apply", False)
    max_iterations = params.get("max_iterations", 5)
    verify_cmd = params.get("verify_cmd")

    state = _agent_module.AgentState(
        task=task,
        target=target,
        platform=_agent_module.Platform.CLAUDE,
        apply=apply_changes,
        max_iterations=max_iterations,
        verify_cmd=verify_cmd,
    )

    log.info("Agent started: task=%r target=%s apply=%s max_iter=%d",
             task[:80], target, apply_changes, max_iterations)

    try:
        _agent_module.run_agent_loop(state)
    except Exception as exc:
        log.error("Agent error: %s", exc)
        return _error_content(f"Agent failed: {exc}")

    result = {
        "status": state.status.value,
        "iterations": state.iteration,
        "changes": state.changes,
        "errors": state.errors,
    }
    if state.last_response:
        result["last_response_preview"] = state.last_response[:500]

    return _text_content(json.dumps(result, indent=2))


# Tool dispatch table
TOOL_HANDLERS = {
    "grok_query": _handle_grok_query,
    "grok_session_start": _handle_grok_session_start,
    "grok_session_continue": _handle_grok_session_continue,
    "grok_agent": _handle_grok_agent,
}


# ---------------------------------------------------------------------------
# Helper: lazy module loading
# ---------------------------------------------------------------------------

def _get_session_module():
    global _session_module
    if _session_module is None:
        import mcp.session as mod
        _session_module = mod
    return _session_module


# ---------------------------------------------------------------------------
# MCP response helpers
# ---------------------------------------------------------------------------

def _text_content(text):
    """Wrap text in MCP tool result content format. Returns (content, is_error)."""
    return ([{"type": "text", "text": text}], False)


def _error_content(message):
    """Wrap error in MCP tool result content format. Returns (content, is_error)."""
    return ([{"type": "text", "text": message}], True)


# ---------------------------------------------------------------------------
# JSON-RPC 2.0 protocol layer
# ---------------------------------------------------------------------------

def _jsonrpc_response(req_id, result):
    """Build a JSON-RPC 2.0 success response."""
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _jsonrpc_error(req_id, code, message):
    """Build a JSON-RPC 2.0 error response."""
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def _handle_initialize(params):
    """Respond to MCP initialize handshake."""
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "capabilities": {"tools": {}},
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
    }


def _handle_tools_list(_params):
    """Return all registered tool definitions."""
    return {"tools": TOOLS}


def _handle_tools_call(params):
    """Dispatch a tool call to the appropriate handler."""
    tool_name = params.get("name")
    tool_args = params.get("arguments", {})

    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        content, _ = _error_content(f"Unknown tool: {tool_name}")
        return {"content": content, "isError": True}

    try:
        content, is_error = handler(tool_args)
        result = {"content": content}
        if is_error:
            result["isError"] = True
        return result
    except Exception as exc:
        log.exception("Tool %s failed", tool_name)
        content, _ = _error_content(f"Internal error in {tool_name}: {exc}")
        return {"content": content, "isError": True}


# Method dispatch table
METHOD_HANDLERS = {
    "initialize": _handle_initialize,
    "tools/list": _handle_tools_list,
    "tools/call": _handle_tools_call,
}

# Notification methods (no response expected)
NOTIFICATION_METHODS = {
    "notifications/initialized",
    "notifications/cancelled",
}


def _process_message(raw_line):
    """Parse one JSON-RPC message and return the response dict, or None for notifications."""
    try:
        msg = json.loads(raw_line)
    except json.JSONDecodeError as exc:
        return _jsonrpc_error(None, -32700, f"Parse error: {exc}")

    method = msg.get("method")
    req_id = msg.get("id")
    params = msg.get("params", {})

    # Notifications — no response
    if method in NOTIFICATION_METHODS:
        log.debug("Notification: %s", method)
        return None

    # Unknown method
    handler = METHOD_HANDLERS.get(method)
    if handler is None:
        log.warning("Unknown method: %s", method)
        return _jsonrpc_error(req_id, -32601, f"Method not found: {method}")

    try:
        result = handler(params)
        return _jsonrpc_response(req_id, result)
    except Exception as exc:
        log.exception("Method %s failed", method)
        return _jsonrpc_error(req_id, -32603, f"Internal error: {exc}")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    """Run the MCP server on stdin/stdout."""
    log.info("Grok Swarm MCP server starting (protocol %s)", PROTOCOL_VERSION)

    # Validate API key early
    if not get_api_key():
        log.warning("No API key configured — tool calls will fail until key is set")

    for raw_line in sys.stdin:
        raw_line = raw_line.strip()
        if not raw_line:
            continue

        response = _process_message(raw_line)
        if response is not None:
            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

    log.info("stdin closed, shutting down")


if __name__ == "__main__":
    main()
