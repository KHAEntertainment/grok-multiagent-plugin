# Grok Swarm Tool

**Bridge to xAI Grok 4.20 Multi-Agent Beta for OpenClaw**

Give your OpenClaw agents access to a 4-agent swarm with ~2M token context for code analysis, refactoring, and reasoning.

[![OpenClaw](https://img.shields.io/badge/OpenClaw-v2026.3.0+-blue)](https://docs.openclaw.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Features

<<<<<<< HEAD
- **4-Agent Swarm** — Grok 4.20 coordinates multiple agents for deeper analysis
- **Massive Context** — ~2M token window, handles entire codebases
- **5 Modes** — Analyze, Refactor, Code, Reason, Orchestrate
- **Tool Passthrough** — Pass OpenAI-format tool schemas for function calling
- **Timeout Safety** — Process-level timeout enforcement prevents hangs
=======
You've been building with AI coding agents for a while now. They're great — they can write features, refactor modules, analyze codebases. But there's always been this ceiling. The models they run on are designed for single-turn conversations. They can collaborate with themselves behind the scenes to think through complex problems.

**Enter Grok 4.20 Multi-Agent Beta.**

It's different. Instead of one model responding, it's *four agents coordinating* in real-time. An orchestrator, specialists, critics — all working together to break down your request and reason through it from multiple angles. It can hold ~2M tokens of context — that's entire codebases in a single request.

**The Problem:**

Grok 4.20 is groundbreaking, but it doesn't play nicely with current coding tools. Claude Code doesn't have a Grok integration. OpenClaw's tooling system doesn't support multi-agent swarms. If you wanted to use Grok, you'd have to hack together custom scripts or modify your platform's core components. Not ideal.

**The Solution:**

This plugin bridges that gap. It makes Grok 4.20 available as a tool that any agent in Claude Code or OpenClaw can call. No core modifications, no hacking — just install and go.

Now when your agent needs deep codebase analysis, large-scale refactoring, or complex reasoning, it can delegate to Grok's swarm and get back the kind of coordinated, multi-perspective thinking that single models can't deliver.

---

## File Writing Capabilities

Grok Swarm can now **write files directly** from code blocks in its responses. This solves the context flooding problem — Grok writes files to disk, and only a brief summary returns to your agent.

### How It Works

Grok responses with code blocks like:
````
```python src/auth.py
import jwt
...
```
````

Are automatically parsed and written to the output directory.

### Usage

| Command | Behavior |
|---------|----------|
| `--output-dir ./src` | Preview files (dry-run) |
| `--apply --output-dir ./src` | Write files to `./src` |
| `--apply --execute "make test"` | Write files, then run tests |

### Example Workflow

```bash
# Ask Grok to generate a module and write it
python -m src.bridge.cli code \
  --prompt "Write a FastAPI auth module with JWT" \
  --output-dir ./src \
  --apply

# Then run tests
python -m src.bridge.cli code \
  --prompt "Refactor auth to use async" \
  --apply --execute "pytest tests/" \
  --output-dir ./src
```

### Morph LLM Integration

For **partial file edits** (not full replacement), use the `--use-morph` flag:

```bash
python -m src.bridge.cli refactor \
  --prompt "Convert this function to async" \
  --use-morph --apply
```

This requires Morph LLM MCP installed:

```bash
claude mcp add morphllm
```

---

## Known Limitations

> **Note:** When using `--apply`, Grok Swarm parses code blocks and writes files. For targeted edits within existing files, use `--use-morph` (requires Morph LLM MCP).

### Why This Matters

Grok can hold ~1.5M tokens of context and generate ~350K token responses. If that entire response floods back through your orchestrator's context window, you've just wasted precious tokens and slowed down your agent.

```text
Current Flow:
Files (1.5M tokens) → Grok → Full response (376K) → Orchestrator (flooded!)

Ideal Flow:
Files (1.5M tokens) → Grok → Writes files + brief summary → Orchestrator (clean)
```

### Current Use Cases

Grok Swarm now supports **direct file writing**:
- ✅ **Code generation with file output** — Grok writes files directly
- ✅ **Codebase analysis** — Security audits, architecture reviews
- ✅ **Refactoring with partial edits** — Use `--use-morph` for targeted changes
- ✅ **Complex reasoning** — Research synthesis, decision making

The `--apply` flag makes Grok write files to disk. Combined with `--execute`, you can build generate → test workflows.

---

## What It Does

| Feature | Why It Matters |
|----------|------------------|
| **4-Agent Coordination** | Multiple perspectives on every request |
| **2M Token Context** | Holds entire codebases without truncation |
| **5 Task Modes** | Analyze, Refactor, Generate, Reason, Orchestrate |
| **Dual Platform** | Works in both Claude Code and OpenClaw |
| **Zero Core Changes** | Drop-in tool, no platform modifications |
>>>>>>> 574902f (Add file writing and Morph LLM integration)

---

## Requirements

- OpenClaw v2026.3.0+
- Python 3.8+
- Node.js 18+
- OpenRouter API key with Grok 4.20 access

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/KHAEntertainment/grok-multiagent-plugin.git
cd grok-multiagent-plugin
./install.sh
```

### 2. Configure OpenClaw

Add to your `openclaw.json`:

```json
{
  "plugins": {
    "allow": ["grok-swarm"],
    "entries": {
      "grok-swarm": {
        "enabled": true
      }
    }
  },
  "agents": {
    "list": [{
      "id": "coder",
      "tools": {
        "allow": ["grok_swarm"]
      }
    }]
  }
}
```

### 3. Restart Gateway

```bash
openclaw gateway restart
```

### 4. Verify

```bash
openclaw status | grep grok
```

---

## Usage

### From CLI

```bash
# Analyze code
node ~/.openclaw/skills/grok-refactor/index.js \
  --mode analyze \
  --prompt "Find security vulnerabilities" \
  --files src/auth/*.ts

# Refactor code
node ~/.openclaw/skills/grok-refactor/index.js \
  --mode refactor \
  --prompt "Convert callbacks to async/await" \
  --files src/legacy/*.js

# Generate code
node ~/.openclaw/skills/grok-refactor/index.js \
  --mode code \
  --prompt "Write a rate limiter middleware"
```

### From OpenClaw Agent

```javascript
const result = await tools.grok_swarm({
  prompt: "Analyze the architecture of this codebase",
  mode: "analyze",
  files: ["src/", "tests/"],
  timeout: 180
});
```

---

## Modes

| Mode | Description |
|------|-------------|
| `analyze` | Code review, security audit, architecture assessment |
| `refactor` | Large-scale refactoring, modernization, migration |
| `code` | Generate new code, features, tests |
| `reason` | Complex reasoning, research synthesis |
| `orchestrate` | Custom agent handoff (requires `--system`) |

---

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | Yes | — | Task instruction |
| `mode` | string | No | `reason` | Task mode |
| `files` | string[] | No | — | Files for context |
| `system` | string | No | — | Custom system prompt |
| `timeout` | number | No | 120 | Timeout in seconds |

---

## Troubleshooting

### "Bridge script not found"
```bash
ls ~/.openclaw/skills/grok-refactor/grok_bridge.py
```

### "No OpenRouter API key"
Configure your key in OpenClaw auth profiles:
```bash
# Add to ~/.openclaw/agents/coder/agent/auth-profiles.json
{
  "profiles": {
    "openrouter:default": {
      "key": "your-key-here"
    }
  }
}
```

### Timeout errors
Increase timeout for large codebases:
```bash
node index.js --timeout 300 ...
```

---

## Architecture

```
OpenClaw Agent
      │
      ▼
grok_swarm tool
      │
      ▼
index.js (Node wrapper)
      │
      ▼
grok_bridge.py (Python/OpenAI SDK)
      │
      ▼
OpenRouter API
      │
      ▼
xAI Grok 4.20 Multi-Agent Beta
      │
      ▼
Response
```

---

## License

MIT — see [LICENSE](LICENSE)

---

## Support

- [Issues](https://github.com/KHAEntertainment/grok-multiagent-plugin/issues)
- [Discord](https://discord.com/invite/clawd)
