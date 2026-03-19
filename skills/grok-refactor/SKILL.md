# Grok Swarm

**Multi-agent intelligence powered by Grok 4.20 Multi-Agent Beta**

Give any AI coding agent access to a 4-agent swarm with ~2M token context for code analysis, refactoring, generation, and complex reasoning.

- **Version:** 1.0.2
- **Platforms:** OpenClaw, Claude Code
- **Modes:** analyze, refactor, code, reason, orchestrate

---

## Overview

Grok 4.20 coordinates 4 agents (orchestrator + specialists + critics) to:
- Analyze codebases for security, architecture, and bugs
- Refactor code while preserving behavior
- Generate features, tests, and boilerplate
- Reason through complex architectural decisions

## Features

- **4-Agent Coordination** — Multi-perspective reasoning on every request
- **Massive Context** — ~2M token window, handles entire codebases
- **File Writing** — Write annotated code blocks directly to disk
- **Tool Passthrough** — Use OpenAI-format tools with Grok

## Usage

### OpenClaw

```javascript
tools.grok_swarm({
  prompt: "Analyze security of this auth module",
  mode: "analyze",
  files: ["src/auth/*.ts"],
  write_files: true,
  output_dir: "./grok-output/"
});
```

### Claude Code

```
/grok-swarm:analyze Review auth module security
/grok-swarm:refactor Convert to async/await
/grok-swarm:code Write FastAPI endpoint
```

### CLI

```bash
node bridge/index.js --mode analyze --prompt "Find bugs" --files src/*.ts
```

## Task Modes

| Mode | Description |
|------|-------------|
| `analyze` | Security audits, architecture review |
| `refactor` | Modernization, migration |
| `code` | Feature generation, tests |
| `reason` | Multi-perspective reasoning |
| `orchestrate` | Custom agent handoff |

## Requirements

- Python 3.8+
- Node.js 18+
- `openai>=1.0.0`
- OpenRouter API key with Grok 4.20 access

## API Key Configuration

The skill searches for your API key in this order:

1. `OPENROUTER_API_KEY` or `XAI_API_KEY` environment variable
2. `~/.config/grok-swarm/config.json` with `{"api_key": "..."}`
3. OpenClaw auth profiles at `~/.openclaw/*/auth-profiles.json`

**Recommended:** Set `OPENROUTER_API_KEY` or use `~/.config/grok-swarm/config.json`.

## ⚠️ Security Notes

### File Writing

By default, `--write-files` is a dry-run. To actually write files:

```bash
--write-files --apply
```

Review generated files before using in production.

### Shell Execution

The `--execute` option runs arbitrary shell commands. **Use with caution** — never run generated commands without reviewing them first.

### API Key Access

The skill reads from multiple config locations to find your API key. Ensure you're comfortable with it reading `~/.openclaw/*/auth-profiles.json` for existing OpenRouter keys.

## Installation

```bash
# Via ClawHub
clawhub install grok-swarm

# Via npm
npm install @khaentertainment/grok-swarm
```
