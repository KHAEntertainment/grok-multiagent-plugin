#!/usr/bin/env python3
"""
grok_bridge.py — General-purpose bridge to xAI Grok 4.20 Multi-Agent Beta via OpenRouter.

Supports multiple task modes, custom system prompts, file context ingestion,
and OpenAI-format tool use passthrough.

Usage:
    python3 grok_bridge.py --prompt "Refactor this" --mode refactor --files a.js b.js
    python3 grok_bridge.py --prompt "Analyze security" --mode analyze --files src/*.py
    python3 grok_bridge.py --prompt "Build feature" --mode orchestrate --system "You are a Go expert" --files main.go
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package required. Install: pip3 install openai", file=sys.stderr)
    sys.exit(1)


OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MODEL_ID = "x-ai/grok-4.20-multi-agent-beta"

# Mode-specific system prompts
MODE_PROMPTS = {
    "refactor": (
        "You are an expert code refactoring engineer. "
        "Improve code quality, maintainability, and performance while preserving behavior. "
        "Output refactored code with clear explanations of what changed and why."
    ),
    "analyze": (
        "You are a senior code analyst and security auditor. "
        "Examine the provided code for bugs, security vulnerabilities, performance issues, "
        "and architectural concerns. Be specific with file paths and line references. "
        "Prioritize findings by severity."
    ),
    "code": (
        "You are an expert software engineer. "
        "Write clean, production-ready code that follows best practices and idioms for the language. "
        "Include error handling, tests where appropriate, and clear comments."
    ),
    "reason": (
        "You are a collaborative multi-agent reasoning system. "
        "Consider multiple perspectives, weigh trade-offs, and provide well-reasoned analysis. "
        "Structure your response clearly with conclusions."
    ),
    "orchestrate": None,  # Requires --system flag
}


def get_api_key():
    """Resolve OpenRouter API key from OpenClaw auth profiles or env."""
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("OPENCLAW_OPENROUTER_DEFAULT_KEY")
    if key:
        return key

    auth_paths = [
        Path.home() / ".openclaw" / "agents" / "coder" / "agent" / "auth-profiles.json",
        Path.home() / ".openclaw" / "agents" / "main" / "agent" / "auth-profiles.json",
        Path.home() / ".openclaw" / "auth-profiles.json",
        Path.home() / ".config" / "openclaw" / "auth-profiles.json",
    ]
    for auth_path in auth_paths:
        if auth_path.exists():
            try:
                with open(auth_path) as f:
                    data = json.load(f)
                profiles = data.get("profiles", {})
                or_profile = profiles.get("openrouter:default", {})
                key = or_profile.get("key") or or_profile.get("apiKey")
                if key:
                    return key
                default = profiles.get("default", {})
                key = default.get("openrouter", {}).get("apiKey") or default.get("openrouter", {}).get("key")
                if key:
                    return key
            except (json.JSONDecodeError, KeyError):
                continue
    return None


def read_files(file_paths):
    """Read and concatenate files with path headers."""
    chunks = []
    total_size = 0
    max_size = 1_500_000

    for fpath in file_paths:
        p = Path(fpath)
        if not p.exists():
            print(f"WARNING: File not found: {fpath}", file=sys.stderr)
            continue
        if not p.is_file():
            print(f"WARNING: Not a file: {fpath}", file=sys.stderr)
            continue

        content = p.read_text(errors="replace")
        header = f"\n{'='*60}\nFILE: {p.absolute()}\n{'='*60}\n"
        chunk = header + content

        if total_size + len(chunk) > max_size:
            print(f"WARNING: Size limit reached, skipping remaining files", file=sys.stderr)
            break

        chunks.append(chunk)
        total_size += len(chunk)

    return "\n".join(chunks)


def load_tools(tools_path):
    """Load OpenAI-format tool definitions from a JSON file."""
    if not tools_path:
        return None
    p = Path(tools_path)
    if not p.exists():
        print(f"ERROR: Tools file not found: {tools_path}", file=sys.stderr)
        sys.exit(1)
    with open(p) as f:
        tools = json.load(f)
    if not isinstance(tools, list):
        print(f"ERROR: Tools file must be a JSON array", file=sys.stderr)
        sys.exit(1)
    return tools


def call_grok(prompt, mode="reason", context="", system_override=None, tools=None, timeout=120):
    """Make the API call to Grok 4.20 Multi-Agent Beta."""
    api_key = get_api_key()
    if not api_key:
        print("ERROR: No OpenRouter API key found.", file=sys.stderr)
        print("Set OPENROUTER_API_KEY env var or configure in OpenClaw auth-profiles.json", file=sys.stderr)
        sys.exit(1)

    # Resolve system prompt
    if system_override:
        system_content = system_override
    else:
        system_content = MODE_PROMPTS.get(mode)
        if system_content is None:
            print(f"ERROR: Mode '{mode}' requires --system flag", file=sys.stderr)
            sys.exit(1)

    # Append context to system prompt
    if context:
        system_content += f"\n\n## Codebase Context\n{context}"

    client = OpenAI(
        base_url=OPENROUTER_BASE,
        api_key=api_key,
        timeout=timeout,
    )

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": prompt},
    ]

    kwargs = {
        "model": MODEL_ID,
        "messages": messages,
        "max_tokens": 16384,
        "temperature": 0.3,
        "extra_body": {"agent_count": 4},
    }

    if tools:
        kwargs["tools"] = tools

    start = time.time()

    try:
        response = client.chat.completions.create(**kwargs)
    except Exception as e:
        elapsed = time.time() - start
        print(f"ERROR after {elapsed:.1f}s: {e}", file=sys.stderr)
        sys.exit(1)

    elapsed = time.time() - start

    if not response.choices:
        print(f"ERROR: Empty response after {elapsed:.1f}s", file=sys.stderr)
        sys.exit(1)

    choice = response.choices[0]

    # Log usage
    if hasattr(response, 'usage') and response.usage:
        u = response.usage
        print(f"USAGE: mode={mode} prompt={u.prompt_tokens} completion={u.completion_tokens} "
              f"total={u.total_tokens} time={elapsed:.1f}s", file=sys.stderr)

    # Handle content filtering
    if choice.finish_reason == "content_filter":
        print(f"WARNING: Response blocked by content filter after {elapsed:.1f}s", file=sys.stderr)
        if not choice.message.content:
            print("No content returned. Try rephrasing the prompt.", file=sys.stderr)
            sys.exit(2)

    content = choice.message.content or ""

    # Handle tool calls (return as JSON if present)
    if choice.message.tool_calls:
        tool_calls = []
        for tc in choice.message.tool_calls:
            tool_calls.append({
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
            })
        result = {
            "content": content,
            "tool_calls": tool_calls,
        }
        return json.dumps(result, indent=2)

    return content.strip()


def main():
    parser = argparse.ArgumentParser(
        description="General-purpose bridge to xAI Grok 4.20 Multi-Agent Beta"
    )
    parser.add_argument("--prompt", required=True, help="Task instruction or question")
    parser.add_argument("--mode", default="reason", choices=list(MODE_PROMPTS.keys()),
                        help="Task mode (default: reason)")
    parser.add_argument("--files", nargs="*", default=[], help="Local file paths for context")
    parser.add_argument("--system", help="Override system prompt (for orchestrate mode)")
    parser.add_argument("--tools", help="Path to JSON file with OpenAI-format tool definitions")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds (default: 120)")
    parser.add_argument("--output", help="Output file path (default: stdout)")

    args = parser.parse_args()

    # Validate orchestrate mode
    if args.mode == "orchestrate" and not args.system:
        print("ERROR: --mode orchestrate requires --system flag", file=sys.stderr)
        sys.exit(1)

    # Read context files
    context = ""
    if args.files:
        print(f"Reading {len(args.files)} files...", file=sys.stderr)
        context = read_files(args.files)
        print(f"Context size: {len(context):,} chars", file=sys.stderr)

    # Load tools
    tools = load_tools(args.tools)

    # Call Grok
    print(f"Calling {MODEL_ID} (mode={args.mode}, 4 agents, timeout={args.timeout}s)...", file=sys.stderr)
    result = call_grok(
        prompt=args.prompt,
        mode=args.mode,
        context=context,
        system_override=args.system,
        tools=tools,
        timeout=args.timeout,
    )

    # Output
    if args.output:
        Path(args.output).write_text(result)
        print(f"Written to: {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
