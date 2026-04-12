---
name: grok-swarm-agent-guide
description: Internal guide for AI agents using Grok Swarm in multi-agent workflows. Covers invocation patterns, limitations, and coordination protocols. Triggers: "delegate to grok", "grok swarm agent", "use grok for X", "grok sub-agent"
author: OpenClaw
version: 1.0.0
---

# Grok Swarm — Agent-to-Agent Integration Guide

**CRITICAL: For AI agents only. Do NOT route large outputs through Claude's context window.**

This document explains how to integrate Grok Swarm into multi-agent workflows. For human-facing commands, see the main SKILL.md.

## ⚠️ Context Window Pollution Warning

**NEVER pass Grok's full output through Claude Code's context window.**

Grok has a **2M token context window**. Claude Code typically has **200K-1M tokens**. Passing Grok's full output through Claude would:
- Destroy smaller agents' context
- Cause context overflow/overwhelm
- Make Claude appear to have "forgotten" everything

**SAFE patterns:**
- Grok → writes files to disk → Claude reads files
- Grok → writes to shared directory → Claude reads results
- Use `--apply` and `--output-dir` to write directly, don't pass through context

**UNSAFE patterns:**
```
# BAD - context pollution
"Here are Grok's findings: [paste 50K token output]"
# Grok's full output would destroy Claude's context

# GOOD - file-based handoff
"Results written to /tmp/grok-analysis/. See files."
# Claude reads files independently
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│ Claude Code (200K-1M context)                                │
│ - Orchestrates tasks                                          │
│ - Calls Grok via native MCP tools                            │
│ - Synthesizes results                                         │
└─────────────────────┬───────────────────────────────────────┘
                      │ MCP tool call (native)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ Grok MCP Server (grok_server.py)                              │
│ - grok_query: stateless single call                          │
│ - grok_session_start/continue: multi-turn sessions           │
│ - grok_agent: autonomous agent loop                          │
│ - Reads files from disk, manages sessions in-memory          │
└─────────────────────┬───────────────────────────────────────┘
                      │ OpenAI SDK → OpenRouter API
                      ▼
┌─────────────────────────────────────────────────────────────┐
│ Grok 4.20 (2M token context)                                 │
│ - 4 or 16 agents work on task                                │
│ - Returns response + file annotations                         │
└─────────────────────────────────────────────────────────────┘
```

**Key insight:** File content goes `disk → MCP server → API → Grok`. It does NOT pass through Claude's context. Claude only receives the final response text.

## Invocation Pattern

### Preferred: MCP Tools (Native)

When the MCP server is registered, Grok tools appear as native tools — call them directly:

```
grok_query(prompt="Find bugs in auth module", mode="analyze", files=["src/auth.py"])
grok_session_start(mode="analyze", files=["src/auth.py"])
grok_session_continue(session_id="abc123", message="What about the password hashing?")
grok_agent(task="Refactor auth module", target="./src/auth", apply=true)
```

### Alternative: Skill Commands

```
/grok-swarm-reason <task>
/grok-swarm-analyze <task>
/grok-swarm-code <task>
/grok-swarm-refactor <task>
```

### Alternative: Direct CLI
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

## File Context

Pass files for Grok to analyze:
```
/grok-swarm-analyze Find bugs --files src/foo.py src/bar.py
```

**IMPORTANT — How file reading works:**
- The bridge reads files directly from disk (NOT through Claude's context)
- File paths are passed as **arguments**, not content
- Content is read by bridge and sent to Grok API
- Claude's context window is NOT used for file content

**⚠️ Limitation — Glob patterns don't auto-expand:**
```bash
# This does NOT work:
--files "src/**/*.py"

# You must pass explicit paths:
--files src/auth/login.py src/auth/session.py src/auth/utils.py
```

**Workaround for directory analysis:** Use the autonomous agent which discovers files itself:
```bash
python3 src/agent/grok_agent.py --task "Analyze security" --target ./src --apply
```

## Output Modes

| Mode | Writes Files | Notes |
|------|-------------|-------|
| Default (dry-run) | ❌ No | Preview only, returns to stdout |
| `--write-files` | ✅ Yes | Writes annotated blocks to `--output-dir` |
| `--output-dir` | ✅ Yes | Directory for written files |

**⚠️ IMPORTANT — File Writing Bypasses Claude's Context:**

When using `--write-files --output-dir /path`, Grok writes directly to disk. The response text returned to Claude is just a summary, NOT the full file content. This is the intended behavior for avoiding context pollution.

**File annotation formats** Grok uses for writing:
1. ` ```python:path/to/file.py` ````
2. `// FILE: path/to/file.py` inside block
3. `# filename.py` comment header

## Multi-Turn Sessions

The MCP server supports **stateful multi-turn sessions** — Grok remembers previous messages:

```
# Start a session
grok_session_start(mode="analyze", files=["src/auth.py"])
→ returns session_id: "abc123"

# Continue the conversation — Grok remembers
grok_session_continue(session_id="abc123", message="What about the password hashing?")
grok_session_continue(session_id="abc123", message="Suggest fixes for the issues found")
```

Sessions have:
- **30-minute TTL** — auto-expire after inactivity
- **Token budget tracking** — warns when approaching cost limits
- **Max 10 concurrent sessions** — oldest evicted when full

## Limitations

### 1. ⚠️ NO Streaming — Single Response Only
The bridge waits for full response before returning. No real-time updates.

### 2. ⚠️ NO Tool Passthrough (Currently)
Built-in Grok tools (web search, code execution) are **not enabled** by default. Sub-agent tools (read_file, write_file, search_code) are planned for Phase 3.

### 3. ⚠️ Rate Limiting
OpenRouter may rate limit. If seeing errors, add delays between calls.

## Safe Multi-Agent Coordination Patterns

### Pattern 1: Sequential Handoff (SAFE)
```
Claude → Grok (analyze) → Claude (review) → Grok (fix)
```

Include Grok output explicitly in subsequent prompts. Results are small text summaries, not file dumps.

### Pattern 2: Parallel Research (SAFE)
```bash
# Terminal 1
python3 src/bridge/grok_bridge.py --mode reason --prompt "Pros of microservices" --output-dir /tmp/grok/pros &

# Terminal 2
python3 src/bridge/grok_bridge.py --mode reason --prompt "Cons of microservices" --output-dir /tmp/grok/cons &

# Wait both, then Claude synthesizes
```

### Pattern 3: Background Worker (SAFE)
```bash
# Start Grok as background worker
nohup python3 src/bridge/grok_bridge.py --mode analyze --files src/ --prompt "Audit security" --output-dir /tmp/grok-results --write-files > grok.log 2>&1 &

# Continue Claude work...

# Later, check results (small text files)
cat /tmp/grok-results/*.md
```

### Pattern 4: Agent Loop (SAFE for Large Tasks)
```bash
python3 src/agent/grok_agent.py --task "Refactor auth module" --target ./src/auth --apply --verify-cmd "pytest"
```

The agent loop iteratively improves code, writing directly to disk each iteration.

## Error Handling

| Error | Cause | Recovery |
|-------|-------|----------|
| `No OpenRouter API key found` | Key not configured | Run `/grok-swarm-setup` |
| `HTTP 400` | Invalid request/policy | Check prompt, reduce size |
| `HTTP 429` | Rate limited | Wait, retry with backoff |
| `HTTP 401` | Invalid/expired key | Re-authenticate |
| Timeout | Took too long | Increase `--timeout` |

## Security Notes for Agents

1. **API Key Exposure**: Keys are in `~/.config/grok-swarm/config.json`. Don't log or display.
2. **File Write Safety**: Use `--write-files` only when explicitly authorized. Grok writes to `--output-dir` only.
3. **Context Size**: Large file contexts count against Grok's 2M limit. Use selective file inclusion.

## Quick Reference

```bash
# Analyze (writes summary to stdout, files to --output-dir if specified)
python3 src/bridge/grok_bridge.py --mode analyze --files src/*.py --prompt "Find bugs"

# Code with apply (writes directly to disk, NOT through context)
python3 src/bridge/grok_bridge.py --mode code --prompt "Write a CLI" --output-dir ./src --write-files

# High thinking
python3 src/bridge/grok_bridge.py --mode reason --prompt "Complex analysis" --thinking high

# Autonomous agent (discovers files, iteratively improves)
python3 src/agent/grok_agent.py --task "Add tests" --target ./src --apply --verify-cmd "pytest"
```

## File Reading Caveats & Improvements

**Current limitation:** File paths must be passed explicitly — no glob expansion, no directory scanning.

**See Issue #31:** [Improve file discovery and tool usage for agents](https://github.com/KHAEntertainment/grok-multiagent-plugin/issues/31)