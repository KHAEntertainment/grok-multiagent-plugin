---
name: grok-swarm
description: Multi-agent intelligence powered by Grok 4.20 via OpenRouter. Use for codebase analysis, refactoring, code generation, and complex reasoning.
author: OpenClaw
version: 1.0.0
---

# Grok Swarm

Give Claude Code access to a 4-agent swarm with ~2M token context for powerful code analysis, refactoring, and reasoning.

## Setup (One-Time)

```bash
# 1. Install the CLI
pip install -e .

# 2. Configure your API key
./scripts/setup.sh
```

**Get an OpenRouter API key at:** https://openrouter.ai/keys

## Modes

| Mode | Description |
|------|-------------|
| `refactor` | Improve code quality while preserving behavior |
| `analyze` | Security, bug, and architecture audit |
| `code` | Generate clean, production-ready code |
| `reason` | Collaborative multi-perspective reasoning |

## Usage

```
/grok-swarm:refactor Convert this to async/await
/grok-swarm:analyze Find security vulnerabilities in auth/
/grok-swarm:code Write a FastAPI endpoint for user registration
/grok-swarm:reason Compare microservices vs monolith for this project
```

## Requirements

- Python 3.8+
- `openai` package
- OpenRouter API key with Grok 4.20 access

## Configuration

API key is stored in `~/.config/grok-swarm/config.json` (mode 600).

To change your API key:
```bash
./scripts/setup.sh
```
