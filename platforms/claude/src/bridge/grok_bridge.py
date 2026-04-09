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
import re
import sys
import time
from pathlib import Path

# Import shared patterns
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))
from patterns import get_filename_pattern_string

try:
    from openai import OpenAI
except ImportError:
    print(
        "ERROR: openai package required for this Grok Swarm runtime. "
        "Install from src/requirements.txt or run /grok-swarm:setup to bootstrap the plugin-local environment.",
        file=sys.stderr,
    )
    sys.exit(1)


OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MODEL_ID = "x-ai/grok-4.20-multi-agent"

# Agent counts per thinking level
AGENT_COUNTS = {
    "low": 4,
    "high": 16,
}

# Modes that typically return text (not annotated code blocks)
TEXT_MODES = {"analyze", "reason", "orchestrate"}

# PGP armored block detection — xAI multi-agent returns encrypted sub-agent state
PGP_BLOCK_PATTERN = re.compile(
    r"-----BEGIN PGP MESSAGE-----.*?-----END PGP MESSAGE-----",
    re.DOTALL,
)

# Plain-language phrases that trigger High Thinking mode automatically
HIGH_THINKING_PHRASES = [
    "16 agent swarm",
    "16-agent swarm",
    "high thinking",
    "high thinking mode",
    "thinking mode high",
    "--thinking high",
]

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
    """Resolve OpenRouter API key from config file, environment, or OpenClaw auth profiles."""

    # 1. Environment variables
    key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("XAI_API_KEY")
    if key:
        return key

    # 2. Grok Swarm config file (for Claude Code without secret management)
    grok_config = Path.home() / ".config" / "grok-swarm" / "config.json"
    if grok_config.exists():
        try:
            with open(grok_config) as f:
                data = json.load(f)
            key = data.get("api_key")
            if key:
                return key
        except (json.JSONDecodeError, KeyError):
            pass

    # 2b. Claude Code plugin settings file (legacy: written by setup.sh)
    claude_settings = Path.home() / ".claude" / "grok-swarm.local.md"
    if claude_settings.exists():
        try:
            for line in claude_settings.read_text(encoding="utf-8").splitlines():
                if line.startswith("api_key:"):
                    key = line.split(":", 1)[1].strip()
                    if key:
                        return key
        except OSError:
            pass

    # 3. OpenClaw auth profiles (for OpenClaw integration)
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


def _safe_dest(output_path, file_path):
    """
    Resolve ``file_path`` relative to ``output_path`` and verify the result
    stays inside ``output_path``.  Returns the resolved Path or raises
    ValueError for unsafe paths (absolute, containing ``..``, etc.).
    """
    raw = Path(file_path)
    if raw.is_absolute():
        rebased = Path(raw.name)
        print(f"WARNING: Absolute path rebased to output dir: {file_path!r} → {rebased!r}", file=sys.stderr)
        raw = rebased
    if ".." in raw.parts:
        raise ValueError(f"Path traversal not allowed: {file_path!r}")
    dest = (output_path / raw).resolve()
    resolved_root = output_path.resolve()
    try:
        dest.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Path escapes output directory: {file_path!r}") from exc
    return dest


def strip_pgp_blocks(text):
    """Remove PGP-armored encrypted sub-agent state from response."""
    return PGP_BLOCK_PATTERN.sub("", text).strip()


def parse_and_write_files(response_text, output_dir):
    """
    Scan response for fenced code blocks with filename annotations and write to disk.

    Supports multiple annotation formats:
      ```python:/path/to/file.py ... ```  (lang:/path format)
      ```python
      // FILE: /path/to/file.py
      ... content ...
      ```  (C-style comment marker)
      ```python
      # FILE: /path/to/file.py
      ... content ...
      ```  (Python-style comment marker)
      ```python
      # filename.py
      ... content ...
      ```  (Just filename as comment - common Grok output)

    Returns list of (relative_path, byte_count) tuples written, where
    byte_count is the number of UTF-8 bytes written.
    """
    written = []
    output_path = Path(output_dir)

    # Pattern 1: lang:path/to/file (language tag contains path; relative OR absolute — broad match)
    lang_path_pattern = re.compile(r'^(\w+):([^\s\n]+)\n', re.MULTILINE)

    # Pattern 2: // FILE: /path or # FILE: /path
    file_marker_pattern = re.compile(
        r'^\s*(?:(?://|#)\s*)FILE:\s*(.+?)\s*$',
        re.MULTILINE
    )

    # Pattern 3: # filename.py (just filename as first line - common Grok output)
    filename_pattern = re.compile(
        get_filename_pattern_string(),
        re.MULTILINE
    )

    def _write_file(file_path, content):
        """Validate path, write content, and record result. Returns True on success."""
        try:
            dest = _safe_dest(output_path, file_path)
        except ValueError as exc:
            print(f"WARNING: Skipping unsafe path — {exc}", file=sys.stderr)
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        encoded = content.strip().encode("utf-8", errors="replace")
        dest.write_bytes(encoded)
        written.append((file_path, len(encoded)))
        return True

    # Split into code blocks by ``` fences.
    # Even indices are fence markers or text between fences; skip them.
    # Odd indices are the actual code block contents.
    parts = re.split(r'```', response_text)

    for i, part in enumerate(parts):
        if i % 2 == 0:
            # Skip even-indexed parts (fences/text between fences)
            continue

        # Check for lang:/path at start (language tag contains the path)
        lang_match = lang_path_pattern.match(part)
        if lang_match:
            _write_file(lang_match.group(2), part[lang_match.end():])
            continue

        # Check for // FILE: or # FILE: marker within the block
        marker_match = file_marker_pattern.search(part)
        if marker_match:
            path = marker_match.group(1).strip()
            # Remove the marker line from content
            marker_end = part.find('\n', marker_match.start())
            if marker_end != -1:
                content = part[marker_end + 1:]
            else:
                content = ""
            _write_file(path, content)
            continue

        # Check for # filename.py pattern (common Grok output)
        filename_match = filename_pattern.match(part)
        if filename_match:
            filename = filename_match.group(1)
            # Remove the filename line from content
            filename_end = part.find('\n', filename_match.end())
            if filename_end != -1:
                content = part[filename_end + 1:]
            else:
                content = ""
            _write_file(filename, content)
            continue

    return written

def detect_high_thinking(prompt):
    """Return True if the prompt contains a plain-language High Thinking trigger."""
    lower = prompt.lower()
    return any(phrase in lower for phrase in HIGH_THINKING_PHRASES)


def _get_client(api_key=None, timeout=120):
    """Create an OpenAI client configured for OpenRouter."""
    key = api_key or get_api_key()
    if not key:
        raise RuntimeError(
            "No OpenRouter API key found. "
            "Tried: OPENROUTER_API_KEY env, ~/.config/grok-swarm/config.json, "
            "~/.claude/grok-swarm.local.md, OpenClaw auth profiles. "
            "Run: python3 src/bridge/oauth_setup.py  or  /grok-swarm:setup"
        )
    return OpenAI(base_url=OPENROUTER_BASE, api_key=key, timeout=timeout)


def call_grok_with_messages(messages, tools=None, timeout=120, thinking="low", mode="reason"):
    """
    Call Grok with a pre-built message list.

    This is the low-level entry point used by sessions (multi-turn) and by
    call_grok() for single-turn requests.

    Args:
        messages: List of OpenAI-format message dicts (system, user, assistant, tool).
        tools: Optional list of OpenAI-format tool definitions.
        timeout: API timeout in seconds.
        thinking: "low" (4 agents) or "high" (16 agents).
        mode: Task mode (for usage logging).

    Returns:
        The raw ChatCompletion response object from the OpenAI SDK.

    Raises:
        RuntimeError: If no API key is found.
        Exception: Propagated from the OpenAI SDK on API errors.
    """
    client = _get_client(timeout=timeout)

    kwargs = {
        "model": MODEL_ID,
        "messages": messages,
        "max_tokens": 16384,
        "temperature": 0.3,
        "extra_body": {"agent_count": AGENT_COUNTS.get(thinking, AGENT_COUNTS["low"])},
    }

    if tools:
        kwargs["tools"] = tools

    start = time.time()
    response = client.chat.completions.create(**kwargs)
    elapsed = time.time() - start

    # Log usage
    if hasattr(response, "usage") and response.usage:
        u = response.usage
        agent_count = AGENT_COUNTS.get(thinking, AGENT_COUNTS["low"])
        print(
            f"USAGE: mode={mode} thinking={thinking} agents={agent_count} "
            f"prompt={u.prompt_tokens} completion={u.completion_tokens} "
            f"total={u.total_tokens} time={elapsed:.1f}s",
            file=sys.stderr,
        )
        # Record to persistent usage tracker (best-effort)
        try:
            from usage_tracker import record_usage
            record_usage(mode, thinking, u.prompt_tokens, u.completion_tokens, u.total_tokens, elapsed)
        except Exception as exc:
            print(f"DEBUG: Usage tracking failed: {exc}", file=sys.stderr)

    return response


def call_grok(prompt, mode="reason", context="", system_override=None, tools=None, timeout=120, thinking="low"):
    """Make the API call to Grok 4.20 Multi-Agent Beta."""
    api_key = get_api_key()
    if not api_key:
        print("ERROR: No OpenRouter API key found.", file=sys.stderr)
        print("Tried in order:", file=sys.stderr)
        print("  1. OPENROUTER_API_KEY / XAI_API_KEY env var", file=sys.stderr)
        print("  2. ~/.config/grok-swarm/config.json", file=sys.stderr)
        print("  3. ~/.claude/grok-swarm.local.md", file=sys.stderr)
        print("  4. OpenClaw auth profiles (~/.openclaw/)", file=sys.stderr)
        print("Run: python3 src/bridge/oauth_setup.py   or   /grok-swarm:setup", file=sys.stderr)
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

    messages = [
        {"role": "system", "content": system_content},
        {"role": "user", "content": prompt},
    ]

    try:
        response = call_grok_with_messages(
            messages=messages, tools=tools, timeout=timeout, thinking=thinking, mode=mode,
        )
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if not response.choices:
        print("ERROR: Empty response", file=sys.stderr)
        sys.exit(1)

    choice = response.choices[0]

    # Handle content filtering
    if choice.finish_reason == "content_filter":
        print("WARNING: Response blocked by content filter", file=sys.stderr)
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
    parser.add_argument("--write-files", action="store_true",
                        help="Parse response for annotated code blocks and write to --output-dir")
    parser.add_argument("--output-dir", default="./grok-output/",
                        help="Directory for file writes (default: ./grok-output/)")
    parser.add_argument("--thinking", default=None, choices=["low", "high"],
                        help="Thinking level: low (4 agents) or high (16 agents, High Thinking mode) (default: low)")

    args = parser.parse_args()

    # Auto-detect High Thinking mode from plain language in prompt (only if not explicitly set)
    thinking = args.thinking
    if thinking is None:
        if detect_high_thinking(args.prompt):
            thinking = "high"
            print("INFO: High Thinking mode detected from prompt — using 16-agent swarm", file=sys.stderr)
        else:
            thinking = "low"

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
    agent_count = AGENT_COUNTS.get(thinking, AGENT_COUNTS["low"])
    thinking_label = " [HIGH THINKING MODE — 16-agent swarm]" if thinking == "high" else ""
    print(f"Calling {MODEL_ID} (mode={args.mode}, {agent_count} agents, timeout={args.timeout}s){thinking_label}...", file=sys.stderr)
    result = call_grok(
        prompt=args.prompt,
        mode=args.mode,
        context=context,
        system_override=args.system,
        tools=tools,
        timeout=args.timeout,
        thinking=thinking,
    )

    # Output
    # Normalize response once - strip PGP blocks before any writes
    cleaned_result = strip_pgp_blocks(result)

    if args.output:
        Path(args.output).write_text(cleaned_result)
        print(f"Written to: {args.output}", file=sys.stderr)

    if args.write_files:
        written = parse_and_write_files(cleaned_result, args.output_dir)
        if written:
            total_bytes = sum(b for _, b in written)
            print(f"Wrote {len(written)} files to {args.output_dir}")
            for rel_path, byte_count in written:
                print(f"  {rel_path} ({byte_count:,} bytes)")
            print(f"Total: {total_bytes:,} bytes")
        elif args.mode in TEXT_MODES:
            # Text mode: no annotated files is a normal outcome
            print(cleaned_result)
        else:
            # Code mode: no files is unexpected but not fatal
            fallback_dir = Path(args.output_dir)
            fallback_dir.mkdir(parents=True, exist_ok=True)
            fallback_path = fallback_dir / "grok-response.txt"
            fallback_path.write_text(cleaned_result, encoding="utf-8")
            print(
                f"WARNING: No annotated files found in model response.\n"
                f"Full response saved to: {fallback_path}\n"
                f"Tip: ask Grok to annotate code blocks with  ```lang:path/to/file  or  # FILE: path/to/file",
                file=sys.stderr,
            )
    elif not args.output:
        print(result)


if __name__ == "__main__":
    main()
