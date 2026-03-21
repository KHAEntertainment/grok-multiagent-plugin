---
name: grok-swarm-agent
description: Spawn an autonomous Grok agent to accomplish tasks. Use when asked to "use grok agent to refactor X", "let grok agent handle this", "grok agent mode", "autonomous grok". Triggers: "grok agent", "agent mode", "autonomous grok", "grok-swarm-agent"
author: OpenClaw
version: 1.0.0
---

# Grok Swarm Agent

Spawn an autonomous agent powered by Grok 4.20 Multi-Agent Beta that iteratively refactors, analyzes, or modifies your codebase.

## Usage

```
use grok agent to refactor src/auth/
grok agent mode: improve error handling in lib/
let grok swarm agent add tests to the backend
```

## How It Works

1. **Discover**: Agent finds relevant files in target directory
2. **Plan**: Agent creates modification plan using Grok 4.20
3. **Apply**: Agent writes changes using file tools
4. **Verify**: Agent validates changes (syntax check, tests)
5. **Iterate**: Agent refines until satisfied or max iterations reached

## Options

| Option | Description |
|--------|-------------|
| `--apply` | Actually write files (default is preview mode) |
| `--max-iterations N` | Max agent iterations (default: 5) |
| `--verify-cmd CMD` | Command to verify changes work |

## Examples

```
# Preview mode - shows what would change
grok agent refactor the auth module

# Actually apply changes
grok agent refactor the auth module --apply

# With verification
grok agent add tests --apply --verify-cmd "pytest tests/"

# Analyze with agent
grok agent analyze security vulnerabilities --target ./src
```

## Requirements

- Grok Swarm plugin installed and configured
- OpenRouter API key set up (run `/grok-swarm:setup` if needed)

## Output

The agent reports:
- Status (success, max iterations, or errors)
- Number of iterations used
- List of files changed
- Verification results if applicable
