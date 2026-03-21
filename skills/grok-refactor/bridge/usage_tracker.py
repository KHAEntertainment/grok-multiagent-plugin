#!/usr/bin/env python3
"""
usage_tracker.py — Persistent token/cost tracking for grok-swarm requests.

Logs each API call to ~/.config/grok-swarm/usage.json (newline-delimited JSON).
Provides aggregation and a human-readable stats report.

OpenRouter pricing for x-ai/grok-4.20-multi-agent-beta (as of 2026-03):
  Prompt tokens:     $5.00 / 1M tokens
  Completion tokens: $15.00 / 1M tokens
"""

import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

USAGE_FILE = Path.home() / ".config" / "grok-swarm" / "usage.json"

# OpenRouter pricing (USD per 1M tokens)
PROMPT_PRICE_PER_M = 5.00
COMPLETION_PRICE_PER_M = 15.00


def record_usage(mode, thinking, prompt_tokens, completion_tokens, total_tokens, elapsed_secs):
    """
    Append one usage record to the log file.
    Never raises — failures are printed to stderr and silently ignored.
    """
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "thinking": thinking,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": total_tokens,
        "elapsed_secs": round(elapsed_secs, 2),
        "cost_usd": round(
            (prompt_tokens / 1_000_000) * PROMPT_PRICE_PER_M
            + (completion_tokens / 1_000_000) * COMPLETION_PRICE_PER_M,
            6,
        ),
    }
    try:
        USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with USAGE_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError as exc:
        print(f"WARNING: Could not write usage log: {exc}", file=sys.stderr)


def get_stats(since_days=None):
    """
    Read the usage log and return aggregated stats dict.

    Args:
        since_days: If set, only include records from the last N days.

    Returns dict with keys:
        calls, prompt_tokens, completion_tokens, total_tokens,
        cost_usd, elapsed_secs, by_mode (dict of mode -> call count)
    """
    if not USAGE_FILE.exists():
        return None

    cutoff = None
    if since_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)

    stats = {
        "calls": 0,
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
        "cost_usd": 0.0,
        "elapsed_secs": 0.0,
        "by_mode": {},
    }

    try:
        with USAGE_FILE.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if cutoff:
                    try:
                        rec_ts = datetime.fromisoformat(rec["ts"])
                        # Normalize naive timestamps (assume UTC) so comparison is safe
                        if rec_ts.tzinfo is None:
                            rec_ts = rec_ts.replace(tzinfo=timezone.utc)
                        if rec_ts < cutoff:
                            continue
                    except (KeyError, ValueError, TypeError):
                        pass

                stats["calls"] += 1
                stats["prompt_tokens"] += rec.get("prompt_tokens", 0)
                stats["completion_tokens"] += rec.get("completion_tokens", 0)
                stats["total_tokens"] += rec.get("total_tokens", 0)
                stats["cost_usd"] += rec.get("cost_usd", 0.0)
                stats["elapsed_secs"] += rec.get("elapsed_secs", 0.0)

                mode = rec.get("mode", "unknown")
                stats["by_mode"][mode] = stats["by_mode"].get(mode, 0) + 1

    except OSError as exc:
        print(f"WARNING: Could not read usage log: {exc}", file=sys.stderr)
        return None

    return stats


def format_stats_report(stats, since_days=None):
    """Return a human-readable stats report string."""
    if stats is None or stats["calls"] == 0:
        return "No usage data recorded yet. Run a grok-swarm command to start tracking."

    period = f"last {since_days} day(s)" if since_days else "all time"
    lines = [
        "",
        "=" * 55,
        f"  grok-swarm usage stats ({period})",
        "=" * 55,
        f"  Requests:          {stats['calls']:>10,}",
        f"  Prompt tokens:     {stats['prompt_tokens']:>10,}",
        f"  Completion tokens: {stats['completion_tokens']:>10,}",
        f"  Total tokens:      {stats['total_tokens']:>10,}",
        f"  Estimated cost:    ${stats['cost_usd']:>10.4f}",
        f"  Total time:        {stats['elapsed_secs']:>9.1f}s",
    ]
    if stats["by_mode"]:
        lines.append("")
        lines.append("  By mode:")
        for mode, count in sorted(stats["by_mode"].items(), key=lambda x: -x[1]):
            lines.append(f"    {mode:<16} {count:>6,} call(s)")
    lines.append("=" * 55)
    lines.append(f"  Log file: {USAGE_FILE}")
    lines.append("=" * 55)
    return "\n".join(lines)
