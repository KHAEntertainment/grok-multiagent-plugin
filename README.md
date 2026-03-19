# Grok Swarm Tool

**Bridge to xAI Grok 4.20 Multi-Agent Beta for OpenClaw**

- **Version:** 1.0.0
- **Status:** Functional ✅ (Built 2026-03-16)
- **Repo:** https://github.com/KHAEntertainment/grok-multiagent-plugin

---

## Overview

Grok Swarm is an OpenClaw integration that bridges to xAI's Grok 4.20 Multi-Agent Beta — a 4-agent collaborative swarm with ~2M token context window.

It provides any OpenClaw agent with access to powerful multi-agent reasoning for:
- Codebase analysis and refactoring
- Architecture review and pattern detection
- Complex reasoning and research synthesis
- Code generation with agent handoff

---

## Project Structure

```
grok-multiagent-plugin/
├── src/
│   ├── bridge/
│   │   ├── grok_bridge.py    # Python API bridge
│   │   └── index.js          # Node.js wrapper
│   └── plugin/
│       ├── index.ts          # OpenClaw plugin
│       ├── openclaw.plugin.json
│       └── package.json
├── tests/
│   └── TEST_RESULTS.md
├── docs/                     # (future)
├── README.md
├── CLAWHUB.md
├── CHANGELOG.md
├── requirements.txt
└── .gitignore
```

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/KHAEntertainment/grok-multiagent-plugin.git
cd grok-multiagent-plugin
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up the skill

```bash
mkdir -p ~/.openclaw/skills/grok-refactor
cp -r src/bridge/* ~/.openclaw/skills/grok-refactor/
```

### 4. Set up the plugin

```bash
mkdir -p ~/.openclaw/extensions/grok-swarm
cp -r src/plugin/* ~/.openclaw/extensions/grok-swarm/
```

### 5. Configure OpenClaw

Add to `openclaw.json`:

```json
{
  "plugins": {
    "allow": ["grok-swarm"],
    "entries": {
      "grok-swarm": {
        "enabled": true,
        "config": {}
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

### 6. Restart OpenClaw

```bash
openclaw gateway restart
```

---

## Usage

### Via OpenClaw Tool

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
  --mode analyze \
  --prompt "Find security vulnerabilities in this codebase" \
  --files src/*.ts
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

1. **Content Filter** — Grok may block overly terse prompts. Use natural language.
2. **Subtle Bugs** — Generated code may have undefined variables. Human review recommended.
3. **Latency** — Multi-agent coordination adds 30-90s for complex tasks.
4. **Python venv** — The `.venv` directory is not in this repo. Create it via `pip install -r requirements.txt`.

---

## Testing

See [tests/TEST_RESULTS.md](tests/TEST_RESULTS.md) for documented test runs.

---

## Architecture

```
OpenClaw Agent
       │
       ▼
grok_swarm tool (plugin)
       │
       ▼
index.js (Node wrapper, timeout enforcement)
       │
       ▼
grok_bridge.py (Python, OpenAI SDK → OpenRouter)
       │
       ▼
xAI Grok 4.20 Multi-Agent Beta (4 agents)
       │
       ▼
Response (reasoning stripped, content only)
```

---

## License

MIT

---

## Support

- Issues: https://github.com/KHAEntertainment/grok-multiagent-plugin/issues
- Discord: https://discord.com/invite/clawd
