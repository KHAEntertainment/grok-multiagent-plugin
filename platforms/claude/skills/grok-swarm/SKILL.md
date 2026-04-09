---
name: grok-swarm
description: Multi-agent intelligence powered by Grok 4.20 via OpenRouter. Use for codebase analysis, refactoring, code generation, and complex reasoning. Triggers: "use grok swarm", "grok 4.20", "multi-agent analysis", "codebase audit", "grok refactor", "16 agent mode"
author: OpenClaw
version: 1.3.3
---

# Grok Swarm

Give Claude Code access to a 4-agent swarm with ~2M token context for powerful code analysis, refactoring, and reasoning.

## First-Time Setup

On first use, Grok Swarm will automatically prompt for your API key:

```
/grok-swarm:analyze Find bugs in this codebase
→ "I need an OpenRouter API key to use Grok Swarm. Would you like me to help you set one up?"
→ "Yes, here's my key: sk-or-v1-..."
→ Setup complete! Now analyzing...
```

**Get a free API key at:** https://openrouter.ai/keys

### Manual Setup

If you prefer manual setup:

```bash
/grok-swarm:setup
```

This stores your API key in `~/.config/grok-swarm/config.json` and also refreshes the bundled MCP runtime.

## Modes

| Mode | Description |
|------|-------------|
| `refactor` | Improve code quality while preserving behavior |
| `analyze` | Security, bug, and architecture audit |
| `code` | Generate clean, production-ready code |
| `reason` | Collaborative multi-perspective reasoning |

## Basic Usage

```text
/grok-swarm:refactor Convert this to async/await
/grok-swarm:analyze Find security vulnerabilities in auth/
/grok-swarm:code Write a FastAPI endpoint for user registration
/grok-swarm:reason Compare microservices vs monolith for this project
```

## MCP Tools (Native Integration)

When installed via the plugin system or `claude mcp add`, Grok Swarm registers as a native MCP server. These tools are available directly — no slash commands needed:

| Tool | Description |
|------|-------------|
| `grok_query` | Stateless single call — analyze, refactor, code, or reason |
| `grok_session_start` | Begin a multi-turn conversation with Grok |
| `grok_session_continue` | Continue an existing session (Grok remembers history) |
| `grok_agent` | Run the autonomous agent loop (discover → modify → verify) |

### Multi-Turn Sessions

```
grok_session_start(mode="analyze", files=["src/auth.py"])
→ { session_id: "abc123" }

grok_session_continue(session_id="abc123", message="What about password hashing?")
→ Grok remembers the previous analysis
```

## First-Time Setup

Grok Swarm uses a PKCE OAuth flow to obtain your OpenRouter API key. **Your key never passes through the LLM context window.**

```
/grok-swarm:setup
→ Opens browser to OpenRouter authorization
→ Browser redirects back to localhost callback
→ Key saved to ~/.config/grok-swarm/config.json (mode 600)
```

**Get a free API key at:** https://openrouter.ai/keys

### Configuration Storage

API keys are resolved in priority order:

- **Environment**: `$OPENROUTER_API_KEY` or `$XAI_API_KEY` (highest priority)
- **CLI config**: `~/.config/grok-swarm/config.json`
- **OpenClaw auth profiles**: `~/.openclaw/auth-profiles.json`

## Advanced Features

### File Writing Modes

**Dry-Run (Preview Only)**
```text
/grok-swarm:code Write a FastAPI user endpoint --output-dir ./src
```

**Apply Mode (Write Files)**
```text
/grok-swarm:code Write a FastAPI user endpoint --output-dir ./src --apply
```

**Execute After Generation**
```text
/grok-swarm:refactor Improve auth/ --apply --execute "pytest tests/"
```

### High Thinking Mode (16-Agent)

For complex tasks, use High Thinking for deeper reasoning:
```text
/grok-swarm:analyze Security audit --thinking high
```
Or: "grok 16 agent swarm, analyze this codebase"

### Morph LLM Integration

For partial file edits:
```text
/grok-swarm:refactor Convert to async --use-morph --apply
```

Requires Morph LLM MCP: `claude mcp add morphllm`

## Cost Tracking

Monitor your API usage:
```text
/grok-swarm:stats
```

This shows tokens used and estimated cost based on OpenRouter pricing.

## Configuration

View or change settings:
```bash
/grok-swarm:setup  # Re-run setup
```

## CLI Flags Reference

| Flag | Description |
|------|-------------|
| `--output-dir` | Directory to write files (used with `--apply`) |
| `--apply` | Actually write files (default is dry-run) |
| `--execute` | Run a command after generation |
| `--use-morph` | Use Morph LLM MCP for partial edits |
| `--thinking` | Thinking level: `standard` or `high` |
| `--timeout` | API timeout in seconds (default: 120) |

## Requirements

- Python 3.8+
- OpenRouter API key with Grok 4.20 access
- Optional: Morph LLM MCP (`claude mcp add morphllm`)
