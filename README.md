# Grok Swarm Tool

**Dual-Platform: OpenClaw + Claude Code**

Give any AI coding agent access to Grok 4.20's 4-agent swarm with ~2M token context.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Features

- **4-Agent Swarm** — Grok 4.20 coordinates multiple agents
- **Massive Context** — ~2M token window
- **5 Modes** — Analyze, Refactor, Code, Reason, Orchestrate
- **Dual Platform** — Works with both OpenClaw and Claude Code

---

## Requirements

- Python 3.8+
- OpenRouter API key with Grok 4.20 access

---

## Quick Start

### 1. Clone & Build

```bash
git clone https://github.com/KHAEntertainment/grok-multiagent-plugin.git
cd grok-multiagent-plugin
./scripts/build.sh
```

### 2. Install

**Both platforms:**
```bash
./scripts/install.sh both
```

**OpenClaw only:**
```bash
./scripts/install.sh openclaw
```

**Claude Code only:**
```bash
./scripts/install.sh claude
```

---

## OpenClaw Usage

```bash
# Via CLI
node ~/.openclaw/skills/grok-refactor/index.js --mode analyze --prompt "Review auth/" --files src/auth/

# Via agent tool
tools.grok_swarm({ prompt: "...", mode: "analyze" })
```

---

## Claude Code Usage

```bash
# Via skill
/grok-swarm:analyze Review the security of the auth module
/grok-swarm:refactor Convert this to async/await
/grok-swarm:code Write a FastAPI user registration endpoint
/grok-swarm:reason Compare these two architectural approaches
```

---

## Modes

| Mode | Description |
|------|-------------|
| `analyze` | Code review, security audit, architecture |
| `refactor` | Large-scale refactoring, modernization |
| `code` | Generate features, tests, boilerplate |
| `reason` | Research, decision making |
| `orchestrate` | Custom agent handoff |

---

## Project Structure

```
├── src/bridge/           # Core bridge (shared)
├── platforms/
│   ├── openclaw/         # OpenClaw plugin
│   └── claude/           # Claude Code plugin
├── dist/                 # Built artifacts
├── scripts/
│   ├── build.sh          # Build for both platforms
│   └── install.sh       # Install script
└── VERSION
```

---

## License

MIT — see [LICENSE](LICENSE)
