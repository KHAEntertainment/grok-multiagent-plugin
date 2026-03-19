# Grok Swarm

**Multi-agent intelligence powered by Grok 4.20 Multi-Agent Beta**

- **Version:** 1.0.0
- **Platforms:** OpenClaw, Claude Code
- **Modes:** analyze, refactor, code, reason, orchestrate

---

## Overview

Give your AI coding agent access to a 4-agent swarm with ~2M token context. Grok 4.20 coordinates multiple agents to analyze codebases, refactor modules, generate features, and reason through complex problems.

## Features

- **4-Agent Coordination** — Orchestrator + specialists + critics working together
- **Massive Context** — ~2M token window, handles entire codebases
- **5 Task Modes** — Analyze, Refactor, Code, Reason, Orchestrate
- **File Writing** — Write annotated code blocks directly to disk
- **Tool Passthrough** — Pass OpenAI-format tool schemas for function calling

## Usage

### OpenClaw

```javascript
tools.grok_swarm({
  prompt: "Analyze the security of this auth module",
  mode: "analyze",
  files: ["src/auth/*.ts"],
  write_files: true,
  output_dir: "./grok-output/"
});
```

### Claude Code

```
/grok-swarm:analyze Review the security of my auth module
/grok-swarm:refactor Convert this to async/await
/grok-swarm:code Write a FastAPI endpoint for user registration
/grok-swarm:reason Compare microservices vs monolith
```

### CLI

```bash
node bridge/index.js --mode analyze --prompt "Find security issues" --files src/*.ts
```

## Task Modes

| Mode | Description |
|------|-------------|
| `analyze` | Security audits, architecture review, bug finding |
| `refactor` | Modernization, migration, cleanup |
| `code` | Feature generation, tests, boilerplate |
| `reason` | Multi-perspective reasoning, research |
| `orchestrate` | Custom agent handoff |

## Requirements

- Python 3.8+
- Node.js 18+
- `openai>=1.0.0`
- OpenRouter API key with Grok 4.20 access

## API Key Setup

```bash
# Environment variable
export OPENROUTER_API_KEY=sk-or-v1-...

# Or configure in ~/.config/grok-swarm/config.json
echo '{"api_key": "sk-or-v1-..."}' > ~/.config/grok-swarm/config.json
```
