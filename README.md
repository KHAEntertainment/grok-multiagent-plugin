# Grok Swarm Tool

**Dual-Platform: OpenClaw + Claude Code**

Give any AI coding agent access to Grok 4.20's 4-agent swarm with ~2M token context.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The Story

You've been building with AI coding agents for a while now. They're great — they can write features, refactor modules, analyze codebases. But there's always been this ceiling. The models they run on are designed for single-turn conversations.

**Enter Grok 4.20 Multi-Agent Beta.**

It's different. Instead of one model responding, it's *four agents coordinating* in real-time. An orchestrator, specialists, critics — all working together to break down your request and reason through it from multiple angles. It can hold ~2M tokens of context — that's entire codebases in a single request.

**The Problem:**

Grok 4.20 is groundbreaking, but it doesn't play nicely with current coding tools. Claude Code doesn't have a Grok integration. OpenClaw's tooling system doesn't support multi-agent swarms. If you wanted to use Grok, you'd have to hack together custom scripts or modify your platform's core components. Not ideal.

**The Solution:**

This plugin bridges that gap. It makes Grok 4.20 available as a tool that any agent in Claude Code or OpenClaw can call. No core modifications, no hacking — just install and go.

Now when your agent needs deep codebase analysis, large-scale refactoring, or complex reasoning, it can delegate to Grok's swarm and get back the kind of coordinated, multi-perspective thinking that single models can't deliver.

---

## Features

- **4-Agent Swarm** — Grok 4.20 coordinates multiple agents for deeper analysis
- **Massive Context** — ~2M token window, handles entire codebases
- **5 Modes** — Analyze, Refactor, Code, Reason, Orchestrate
- **Tool Passthrough** — Pass OpenAI-format tool schemas for function calling
- **File Writing** — Write annotated code blocks directly to disk
- **Dual Platform** — Works with both Claude Code and OpenClaw

---

## File Writing

When `write_files=true`, Grok parses code blocks for filename annotations and writes them directly to disk, returning only a compact summary instead of the full response.

### Supported Patterns

**Fenced code blocks with path in the language tag:**

    ```typescript:src/auth/login.ts
    export function login() { ... }
    ```

**Fenced code blocks with `// FILE:` marker:**

    ```typescript
    // FILE: src/auth/login.ts
    export function login() { ... }
    ```

### Example

```javascript
const result = await tools.grok_swarm({
  prompt: "Write a FastAPI auth module with JWT",
  mode: "code",
  write_files: true,
  output_dir: "./src"
});
// Returns: "Wrote 3 files to ./src
//   src/auth.py (1,234 bytes)
//   src/jwt_utils.py (567 bytes)
//   src/middleware.py (890 bytes)"
```

### Why This Matters

Grok can generate ~350K token responses. Without file writing, that floods your orchestrator's context window. With file writing, you get a brief summary and the files on disk.

---

## Requirements

- OpenClaw v2026.3.0+ (for OpenClaw integration)
- Python 3.8+
- Node.js 18+
- OpenRouter API key with Grok 4.20 access

---

## Quick Start

### For Claude Code

```bash
# 1. Clone the repo
git clone https://github.com/KHAEntertainment/grok-multiagent-plugin.git
cd grok-multiagent-plugin

# 2. Install for Claude Code
./scripts/install.sh claude

# 3. Set up your API key
./scripts/setup.sh
# Paste your OpenRouter API key (get one at https://openrouter.ai/keys)
```

Then use it directly:

```
/grok-swarm:analyze Review the security of my auth module
/grok-swarm:refactor Convert these callbacks to async/await
/grok-swarm:code Write a FastAPI endpoint for user registration
/grok-swarm:reason Compare microservices vs monolith for this project
```

### For OpenClaw

```bash
# 1. Clone the repo
git clone https://github.com/KHAEntertainment/grok-multiagent-plugin.git
cd grok-multiagent-plugin

# 2. Install for OpenClaw
./scripts/install.sh openclaw
```

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

Restart gateway:

```bash
openclaw gateway restart
```

Verify:

```bash
openclaw status | grep grok
```

---

## Usage

### Claude Code

```
/grok-swarm:analyze Review the security of my auth module
/grok-swarm:refactor Convert this to async/await
/grok-swarm:code Write a FastAPI user registration endpoint
/grok-swarm:reason Compare these two architectural approaches
```

### OpenClaw

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

| Mode | Description | Use Case |
|------|-------------|----------|
| `analyze` | Deep code review, security audit, architecture assessment | Security reviews, PR reviews, tech debt assessment |
| `refactor` | Improve code quality while preserving behavior | Modernization, migration, cleanup of legacy code |
| `code` | Generate clean, production-ready code | Building features, writing tests, boilerplate |
| `reason` | Collaborative multi-perspective reasoning | Research synthesis, decision making, trade-off analysis |
| `orchestrate` | Custom agent handoff with your system prompt | When you need full control over swarm's behavior |

---

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | Yes | — | Task instruction |
| `mode` | string | No | `reason` | Task mode |
| `files` | string[] | No | — | Files for context |
| `system` | string | No | — | Custom system prompt |
| `timeout` | number | No | 120 | Timeout in seconds |
| `write_files` | boolean | No | false | Write annotated code blocks to disk |
| `output_dir` | string | No | ./grok-output/ | Directory for file writes |

---

## OpenRouter API Key

Grok Swarm resolves your API key in this order (highest to lowest priority):

1. **Environment variables** — `OPENROUTER_API_KEY` or `XAI_API_KEY`
2. **Local config file** — `~/.config/grok-swarm/config.json` with `{"api_key": "..."}`
3. **OpenClaw auth profiles** — `~/.openclaw/agents/coder/agent/auth-profiles.json`

```bash
# If you set an env var, it takes precedence over config files:
export OPENROUTER_API_KEY="sk-or-v1-xxx"   # This overrides ~/.config/grok-swarm/config.json!

# To use the local config file instead, unset the env var:
unset OPENROUTER_API_KEY
```

**Get a key at:** https://openrouter.ai/keys

---

## Morph LLM Integration

For **partial file edits** (not full replacement), use the `--use-morph` flag:

```bash
grok-swarm refactor --prompt "Convert this function to async" --use-morph --apply
```

This requires Morph LLM MCP installed:

```bash
claude mcp add morphllm
```

---

## Architecture

```
OpenClaw Agent / Claude Code
         │
         ▼
grok_swarm tool / skill
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
