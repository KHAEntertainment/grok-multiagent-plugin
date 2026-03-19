#!/usr/bin/env python3
"""
Unified Grok Swarm CLI entrypoint.
Dispatches to refactor/analyze/code/reason modes using grok_bridge.py logic.
"""
import argparse
import sys
from pathlib import Path

# Support both source and installed package layouts
current = Path(__file__).parent
if str(current) not in sys.path:
    sys.path.insert(0, str(current))

from grok_bridge import call_grok, read_files, MODE_PROMPTS


def main():
    parser = argparse.ArgumentParser(
        description="Grok Swarm — Multi-agent CLI powered by Grok 4.20",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "mode",
        nargs="?",
        choices=list(MODE_PROMPTS.keys()),
        default="reason",
        help="Task mode (default: reason)",
    )
    parser.add_argument("--prompt", "-p", required=True, help="Task instruction or question")
    parser.add_argument("--files", "-f", nargs="*", default=[], help="Files to include as context")
    parser.add_argument("--system", "-s", help="Override system prompt")
    parser.add_argument("--tools", "-t", help="Path to OpenAI-format tools JSON")
    parser.add_argument("--timeout", type=int, default=120, help="Timeout in seconds")
    parser.add_argument("--output", "-o", help="Write output to file")

    args = parser.parse_args()

    if args.mode == "orchestrate" and not args.system:
        print("ERROR: orchestrate mode requires --system", file=sys.stderr)
        sys.exit(1)

    context = read_files(args.files) if args.files else ""

    if args.files:
        print(f"Read {len(args.files)} file(s) — {len(context):,} chars", file=sys.stderr)

    # Parse tools if provided
    tools = None
    if args.tools:
        import json
        with open(args.tools, 'r') as f:
            tools = json.load(f)

    print(f"Calling Grok 4.20 (mode={args.mode}, 4 agents)...", file=sys.stderr)

    result = call_grok(
        prompt=args.prompt,
        mode=args.mode,
        context=context,
        system_override=args.system,
        tools=tools,
        timeout=args.timeout,
    )

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result)
        print(f"Output written to {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()