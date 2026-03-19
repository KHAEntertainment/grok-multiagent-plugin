# Grok Swarm Tool

**Bridge to xAI Grok 4.20 Multi-Agent Beta for OpenClaw**

Give your OpenClaw agents access to a 4-agent swarm with ~2M token context for code analysis, refactoring, and reasoning.

[![OpenClaw](https://img.shields.io/badge/OpenClaw-v2026.3.0+-blue)](https://docs.openclaw.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Features

- **4-Agent Swarm** — Grok 4.20 coordinates multiple agents for deeper analysis
- **Massive Context** — ~2M token window, handles entire codebases
- **5 Modes** — Analyze, Refactor, Code, Reason, Orchestrate
- **Tool Passthrough** — Pass OpenAI-format tool schemas for function calling
- **File Writing** — Write annotated code blocks directly to disk
- **Timeout Safety** — Process-level timeout enforcement prevents hangs

---

## File Writing

When `write_files=true`, Grok parses code blocks for filename annotations and writes them directly to disk, returning only a compact summary instead of the full response.

### Supported Patterns

**Fenced code blocks with path in the language tag:**
```markdown
```typescript:src/auth/login.ts
export function login() { ... }
```
```

**Fenced code blocks with `// FILE:` marker:**
```markdown
```typescript
// FILE: src/auth/login.ts
export function login() { ... }
```
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
| `write_files` | boolean | No | false | Write annotated code blocks to disk |
| `output_dir` | string | No | ./grok-output/ | Directory for file writes |

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
