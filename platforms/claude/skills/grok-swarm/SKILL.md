---
name: grok-swarm
description: Multi-agent intelligence powered by Grok 4.20 via OpenRouter. Use for codebase analysis, refactoring, code generation, and complex reasoning.
author: OpenClaw
version: 1.0.0
---

# Grok Swarm

Give Claude Code access to a 4-agent swarm with ~2M token context for powerful code analysis, refactoring, and reasoning.

## Modes

| Mode | Description |
|------|-------------|
| `refactor` | Improve code quality while preserving behavior |
| `analyze` | Security, bug, and architecture audit |
| `code` | Generate clean, production-ready code |
| `reason` | Collaborative multi-perspective reasoning |

## Installation

1. Install the bridge CLI:
   ```bash
   pip install -e .
   ```

2. Link this plugin:
   ```bash
   ln -s ~/.claude/plugins/grok-swarm ~/.claude/plugins/
   ```

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
