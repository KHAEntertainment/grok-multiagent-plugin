---
name: grok-swarm
description: Multi-agent intelligence powered by Grok 4.20 via OpenRouter. Use for codebase analysis, refactoring, code generation, and complex reasoning.
author: OpenClaw
version: 1.1.0
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

## Basic Usage

```text
/grok-swarm:refactor Convert this to async/await
/grok-swarm:analyze Find security vulnerabilities in auth/
/grok-swarm:code Write a FastAPI endpoint for user registration
/grok-swarm:reason Compare microservices vs monolith for this project
```

## File Writing Modes

### Dry-Run (Preview Only)

Generate code and preview what files would be created:

```text
/grok-swarm:code Write a FastAPI user endpoint --output-dir ./src
```

This shows the code blocks Grok returns without writing anything to disk.

### Apply Mode (Write Files)

Use `--apply` to actually write the generated files:

```text
/grok-swarm:code Write a FastAPI user endpoint --output-dir ./src --apply
```

Files are written based on code block headers (e.g., `python src/routes/users.py`).

### Execute After Generation

Use `--execute` to run a command after Grok responds:

```text
/grok-swarm:refactor Modernize auth/ --output-dir ./auth --apply --execute "pytest tests/"
```

This is useful for generate → test workflows.

## Morph LLM Integration

For partial file edits (not full file replacement), use the `--use-morph` flag:

```text
/grok-swarm:refactor Convert this function to async --use-morph --apply
```

This requires Morph LLM MCP to be installed:

```bash
claude mcp add morphllm
```

**When to use Morph:**
- Editing a specific function within a file
- Making targeted changes without overwriting the entire file
- Working with large existing files

**When to skip Morph (use default):**
- Generating entirely new files
- Working with files you don't have locally
- Creating multiple files at once

## CLI Flags Reference

| Flag | Alias | Description |
|------|-------|-------------|
| `--output-dir` | `-d` | Directory to write files to (used with `--apply`) |
| `--apply` | `-a` | Actually write files (default is dry-run) |
| `--execute` | `-e` | Run a command after generation |
| `--use-morph` | | Use Morph LLM MCP for partial edits |
| `--timeout` | | API timeout in seconds (default: 120) |
| `--output` | | Write raw Grok response to file |

## Examples

### Preview new code:

```text
/grok-swarm:code Write a Python CLI with argparse --output-dir ./cli
```

### Generate and write:

```text
/grok-swarm:code Write a React component --apply --output-dir ./components
```

### Generate, write, and test:

```text
/grok-swarm:refactor Improve error handling in api/ --apply --execute "make test"
```

### Analyze with Morph edits:

```text
/grok-swarm:refactor Add type hints to main.py --use-morph --apply
```

## Requirements

- Python 3.8+
- `openai` package
- OpenRouter API key with Grok 4.20 access
- Optional: Morph LLM MCP (`claude mcp add morphllm`)

## Configuration

API key is stored in `~/.config/grok-swarm/config.json` (mode 600).

To change your API key:
```bash
./scripts/setup.sh
```