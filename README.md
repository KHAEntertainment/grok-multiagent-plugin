# Grok Swarm Tool

**Bridge to xAI Grok 4.20 Multi-Agent Beta for OpenClaw**

- **Version:** 1.0.0
- **Status:** Functional ✅ (Built 2026-03-16)
- **Assigned:** Billy, Barry

---

## Overview

Grok Swarm is an OpenClaw integration that bridges to xAI's Grok 4.20 Multi-Agent Beta — a 4-agent collaborative swarm with ~2M token context window.

It provides any OpenClaw agent with access to powerful multi-agent reasoning for:
- Codebase analysis and refactoring
- Architecture review and pattern detection
- Complex reasoning and research synthesis
- Code generation with agent handoff

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     OpenClaw Agent (Barry, etc.)                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
   ┌────────────────────┐          ┌─────────────────────┐
   │  Native Tool Call   │          │  Direct CLI Bridge  │
   │  (grok_swarm tool)  │          │  (skill/index.js)   │
   └────────────────────┘          └─────────────────────┘
                │                               │
                └───────────────┬───────────────┘
                                ▼
                    ┌───────────────────────┐
                    │   index.js (Node.js)   │
                    │   Timeout enforcement  │
                    │   Arg parsing          │
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │ grok_bridge.py (Python)│
                    │ OpenAI SDK → OpenRouter│
                    └───────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   OpenRouter API       │
                    │ x-ai/grok-4.20-multi-  │
                    │ agent-beta            │
                    └───────────────────────┘
                                │
                ┌───────────────┼───────────────┐
                ▼               ▼               ▼
         ┌──────────┐    ┌──────────┐    ┌──────────┐
         │ Agent 1  │    │ Agent 2  │    │ Agent 3  │  + 1 more
         │ Orchestr│    │ Specialist│    │ Critic   │
         └──────────┘    └──────────┘    └──────────┘
                                │
                                ▼
                         ┌──────────┐
                         │ Response │
                         │ (content │
                         │ only)    │
                         └──────────┘
```

---

## File Locations

| Component | Location | Description |
|-----------|----------|-------------|
| **Core Skill** | `~/.openclaw/skills/grok-refactor/` | Bridge scripts and documentation |
| **Plugin** | `~/.openclaw/extensions/grok-swarm/` | Native OpenClaw tool registration |
| **Project** | `~/projects/grok-multi-agent/` | Documentation and ClawHub packaging |

---

## Quick Start

### 1. Prerequisites

- OpenClaw v2026.3.0+
- Python 3.8+ with `openai` package
- OpenRouter API key with Grok 4.20 access

### 2. Installation

The plugin and skill are already installed. Verify:

```bash
openclaw status | grep grok
```

Should show: `grok-swarm: loaded`

### 3. Configuration

The OpenRouter API key should already be configured in your OpenClaw auth profiles:

```bash
# Test connectivity
node ~/.openclaw/skills/grok-refactor/index.js --prompt "Hello" --mode reason
```

### 4. Usage

```bash
# Analyze a codebase
node ~/.openclaw/skills/grok-refactor/index.js \
  --mode analyze \
  --prompt "Find security vulnerabilities in this codebase" \
  --files src/*.ts

# Refactor code
node ~/.openclaw/skills/grok-refactor/index.js \
  --mode refactor \
  --prompt "Convert this to async/await patterns" \
  --files src/legacy/*.js

# Generate code
node ~/.openclaw/skills/grok-refactor/index.js \
  --mode code \
  --prompt "Write a rate limiter middleware" \
  --files package.json
```

---

## Supported Modes

| Mode | Description | Best For |
|------|-------------|----------|
| `refactor` | Large-scale code refactoring | Modernization, migration, cleanup |
| `analyze` | Code review and analysis | Security audits, architecture review |
| `code` | Code generation | Features, tests, boilerplate |
| `reason` | Multi-perspective reasoning | Research, decision making |
| `orchestrate` | Custom agent orchestration | Agent handoffs with custom prompts |

---

## Configuration Options

### Plugin Config (`openclaw.json`)

```json
{
  "plugins": {
    "entries": {
      "grok-swarm": {
        "enabled": true,
        "config": {
          "defaultTimeout": 120,
          "pythonPath": "/path/to/python3",
          "bridgeScript": "/path/to/grok_bridge.py"
        }
      }
    }
  }
}
```

### Agent Tool Access

```json
{
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

---

## API Reference

### Via OpenClaw Tool (Native)

```javascript
const result = await tools.grok_swarm({
  prompt: "Analyze the security of this auth module",
  mode: "analyze",
  files: ["src/auth/login.js", "src/auth/session.js"],
  timeout: 180
});
```

### Via CLI

```bash
node ~/.openclaw/skills/grok-refactor/index.js \
  --prompt "<task>" \
  --mode <mode> \
  --files <file1> <file2> \
  --timeout <seconds>
```

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `prompt` | string | Yes | — | Task instruction |
| `mode` | string | No | `reason` | Task mode |
| `files` | string[] | No | — | Files for context |
| `system` | string | No | (mode default) | Custom system prompt |
| `tools` | string | No | — | JSON file with tool schemas |
| `timeout` | number | No | 120 | Seconds before timeout |

---

## Known Limitations

1. **Content Filter** — Grok may block overly terse/artificial prompts. Use natural language.

2. **Subtle Bugs** — Generated code may have undefined variables. Human review recommended before production use.

3. **Latency** — Multi-agent coordination adds 30-90s for complex tasks. Budget accordingly.

4. **No Tool Loop** — This is a single-shot call, not an agent loop. For tool use, pass `--tools` with OpenAI-format schema.

---

## Troubleshooting

### "Bridge script not found"

```bash
# Verify skill is installed
ls ~/.openclaw/skills/grok-refactor/grok_bridge.py
```

### "No OpenRouter API key found"

```bash
# Check auth profiles
cat ~/.openclaw/agents/coder/agent/auth-profiles.json | jq '.profiles.openrouter'
```

### Timeout errors

Increase timeout for large codebases:
```bash
node ~/.openclaw/skills/grok-refactor/index.js --timeout 300 ...
```

---

## Testing

See [tests/TEST_RESULTS.md](tests/TEST_RESULTS.md) for documented test runs.

---

## License

MIT

---

## Support

- OpenClaw Discord: https://discord.com/invite/clawd
- ClawHub: https://clawhub.com
