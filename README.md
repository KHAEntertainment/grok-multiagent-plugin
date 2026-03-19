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
- **Secure Config** — API key stored locally, never exposed

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

### 2. Install & Configure

**OpenClaw:**
```bash
./scripts/install.sh openclaw
openclaw gateway restart
```

**Claude Code:**
```bash
./scripts/install.sh claude
./scripts/setup.sh   # Enter your OpenRouter API key
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

```
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

## Configuration

### Claude Code Setup

Claude Code doesn't have built-in secret management. We use a simple file-based approach:

```bash
./scripts/setup.sh
```

API key is stored in `~/.config/grok-swarm/config.json` with mode 600 (readable only by you).

### OpenClaw Setup

Uses OpenClaw's built-in auth profiles:
```
~/.openclaw/agents/coder/agent/auth-profiles.json
```

---

## Project Structure

```
├── src/bridge/           # Core bridge (shared)
├── platforms/
│   ├── openclaw/         # OpenClaw plugin
│   └── claude/           # Claude Code plugin
├── scripts/
│   ├── build.sh          # Build for both platforms
│   ├── install.sh        # Install script
│   └── setup.sh          # API key setup (Claude Code)
└── VERSION
```

---

## License

MIT — see [LICENSE](LICENSE)
