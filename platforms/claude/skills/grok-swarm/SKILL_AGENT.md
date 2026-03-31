---
name: grok-swarm-agent-guide
description: Internal guide for AI agents using Grok Swarm in multi-agent workflows. Covers invocation patterns, limitations, and coordination protocols. Triggers: "delegate to grok", "grok swarm agent", "use grok for X", "grok sub-agent"
author: OpenClaw
version: 1.0.0
---

# Grok Swarm — Agent-to-Agent Integration Guide

This document explains how to integrate Grok Swarm into multi-agent workflows. For human-facing commands, see the main SKILL.md.

## Invocation Pattern

Grok Swarm is **not a native Claude sub-agent** — it's an external API. Use it via skill invocation:

```
/grok-swarm:reason <task>
/grok-swarm:analyze <task>
/grok-swarm:code <task>
/grok-swarm:refactor <task>
```

Or directly via CLI:
```bash
python3 src/bridge/grok_bridge.py --mode <mode> --prompt "<task>" [options]
```

## Modes Reference

| Mode | Use When | Output |
|------|----------|--------|
| `reason` | Multi-perspective analysis, reasoning tasks | Structured markdown response |
| `analyze` | Security audits, bug hunts, code review | Prioritized finding list |
| `code` | Generate new code with annotations | Fenced code blocks |
| `refactor` | Improve existing code | Diff-style with explanations |
| `orchestrate` | Custom system prompt | Varies |

## Thinking Levels

| Level | Agents | Trigger Phrases |
|-------|--------|-----------------|
| `low` (default) | 4 | Normal requests |
| `high` | 16 | "16 agent", "high thinking", deep research |

Example:
```
/grok-swarm:reason Explain consensus algorithms --thinking high
```

## File Context

Pass files for Grok to analyze:
```
/grok-swarm:analyze Find bugs --files src/auth/*.py
```

**Limitation**: Glob patterns (`*.py`) don't auto-expand. Pass explicit paths:
```bash
python3 src/bridge/grok_bridge.py --files src/auth/login.py src/auth/session.py --mode analyze --prompt "..."
```

## Output Modes

| Mode | Writes Files | Notes |
|------|-------------|-------|
| Default (dry-run) | ❌ No | Preview only |
| `--apply` | ✅ Yes | Actually writes |
| `--output-dir` | ✅ Yes | Write to specific dir |

**File annotation formats** Grok uses:
1. ````python:path/to/file.py` ````
2. `// FILE: path/to/file.py` inside block
3. `# filename.py` comment header

## Important Limitations

### 1. Stateless — No Multi-turn Sessions
Each invocation is **independent**. Grok has no memory of previous calls.

**Workaround**: Include all context in the prompt. If continuing work, summarize previous results explicitly.

```
# Bad — Grok won't remember
"Continue the security audit from before"

/# Good — Include previous findings
"Continue security audit. Previous findings: [paste findings]. Now check data validation."
```

### 2. Single Response — No Streaming
The bridge waits for full response before returning. No real-time updates.

### 3. No Native Agent Pool
Grok cannot be registered as a Claude sub-agent. Orchestration is manual:

- Run Grok in background: `python3 src/bridge/grok_bridge.py [args] &`
- Continue Claude work independently
- Collect Grok results when needed

### 4. No Tool Passthrough (Currently)
Built-in Grok tools (web search, code execution) are **not enabled** by default. The bridge uses Grok for reasoning only, not tool calling.

### 5. Rate Limiting
OpenRouter may rate limit. If seeing errors, add delays between calls:
```python
import time; time.sleep(2)  # Between calls
```

## Multi-Agent Coordination Patterns

### Pattern 1: Sequential Handoff
```
Claude → Grok (analyze) → Claude (review) → Grok (fix)
```

Include Grok output explicitly in subsequent Claude prompts.

### Pattern 2: Parallel Research
```bash
# Terminal 1
python3 src/bridge/grok_bridge.py --mode reason --prompt "Pros of microservices" --session-id micro1 &

# Terminal 2
python3 src/bridge/grok_bridge.py --mode reason --prompt "Cons of microservices" --session-id micro2 &

# Wait both, then Claude synthesizes
```

### Pattern 3: Background Worker
```bash
# Start Grok as background worker
nohup python3 src/bridge/grok_bridge.py --mode analyze --files src/ --prompt "Audit security" --output-dir /tmp/grok-results/ > grok.log 2>&1 &

# Continue Claude work...

# Later, check results
cat /tmp/grok-results/*.md
```

## Error Handling

| Error | Cause | Recovery |
|-------|-------|----------|
| `No OpenRouter API key found` | Key not configured | Run `/grok-swarm:setup` |
| `HTTP 400` | Invalid request/policy | Check prompt, reduce size |
| `HTTP 429` | Rate limited | Wait, retry with backoff |
| `HTTP 401` | Invalid/expired key | Re-authenticate |
| Timeout | Took too long | Increase `--timeout` |

## Security Notes for Agents

1. **API Key Exposure**: Keys are in `~/.config/grok-swarm/config.json`. Don't log or display.
2. **File Write Safety**: Use `--apply` only when explicitly authorized. Grok can write anywhere in target dir.
3. **Context Size**: Large file contexts count against token limits. Use selective file inclusion.

## Session/State Roadmap

See [Issue #30](https://github.com/KHAEntertainment/grok-multiagent-plugin/issues/30) for planned stateful session support. Currently all calls are stateless.

## Quick Reference

```bash
# Analyze
python3 src/bridge/grok_bridge.py --mode analyze --files src/*.py --prompt "Find bugs"

# Code with apply
python3 src/bridge/grok_bridge.py --mode code --prompt "Write a CLI" --output-dir ./src --apply

# High thinking
python3 src/bridge/grok_bridge.py --mode reason --prompt "Complex analysis" --thinking high

# With timeout (seconds)
python3 src/bridge/grok_bridge.py --mode reason --prompt "..." --timeout 180
```
