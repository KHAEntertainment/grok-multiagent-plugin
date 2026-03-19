# Grok Swarm

**Give your AI agents superpowers with Grok 4.20's 4-agent swarm**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The Story

You've been building with AI coding agents for a while now. They're great — they can write features, refactor modules, analyze codebases. But there's always been this ceiling. The models they run on are designed for single-turn conversations. They can collaborate with themselves behind the scenes to think through complex problems.

**Enter Grok 4.20 Multi-Agent Beta.**

It's different. Instead of one model responding, it's *four agents coordinating* in real-time. An orchestrator, specialists, critics — all working together to break down your request and reason through it from multiple angles. It can hold ~2M tokens of context — that's entire codebases in a single request.

**The Problem:**

Grok 4.20 is groundbreaking, but it doesn't play nicely with current coding tools. Claude Code doesn't have a Grok integration. OpenClaw's tooling system doesn't support multi-agent swarms. If you wanted to use Grok, you'd have to hack together custom scripts or modify your platform's core components. Not ideal.

**The Solution:**

This plugin bridges the gap. It makes Grok 4.20 available as a tool that any agent in Claude Code or OpenClaw can call. No core modifications, no hacking — just install and go.

Now when your agent needs deep codebase analysis, large-scale refactoring, or complex reasoning, it can delegate to Grok's swarm and get back the kind of coordinated, multi-perspective thinking that single models can't deliver.

---

## What It Does

| Feature | Why It Matters |
|----------|------------------|
| **4-Agent Coordination** | Multiple perspectives on every request |
| **2M Token Context** | Holds entire codebases without truncation |
| **5 Task Modes** | Analyze, Refactor, Generate, Reason, Orchestrate |
| **Dual Platform** | Works in Claude Code AND OpenClaw |
| **Zero Core Changes** | Drop-in tool, no platform modifications |

---

## Quick Start

### For Claude Code

```bash
# 1. Clone the repo
git clone https://github.com/KHAEntertainment/grok-multiagent-plugin.git
cd grok-multiagent-plugin

# 2. Install for Claude Code
./scripts/install.sh claude

# 3. Set up your API key
./scripts/setup.sh
# Paste your OpenRouter API key (get one at https://openrouter.ai/keys)
```

Then use it directly:

```
/grok-swarm:analyze Review the security of my auth module
/grok-swarm:refactor Convert these callbacks to async/await patterns
/grok-swarm:code Write a FastAPI endpoint for user registration
/grok-swarm:reason Compare microservices vs monolith for this project
```

### For OpenClaw

```bash
# 1. Clone the repo
git clone https://github.com/KHAEntertainment/grok-multiagent-plugin.git
cd grok-multiagent-plugin

# 2. Install for OpenClaw
./scripts/install.sh openclaw

# 3. Configure your OpenClaw
# Edit ~/.openclaw/openclaw.json to add grok_swarm to your agent's tool list
```

Your agents can now call it:

```javascript
const result = await tools.grok_swarm({
  prompt: "Refactor this auth module to use modern patterns",
  mode: "refactor",
  files: ["src/auth/*.ts"]
});
```

---

## Task Modes

| Mode | What It Does | When To Use |
|------|-------------|-------------|
| `analyze` | Deep code review, security audit, architecture analysis | Before shipping code, when reviewing PRs, assessing tech debt |
| `refactor` | Improve code quality while preserving behavior | Modernization, migration, cleanup of legacy code |
| `code` | Generate clean, production-ready code | Building features, writing tests, boilerplate |
| `reason` | Complex multi-perspective reasoning | Research synthesis, decision making, trade-off analysis |
| `orchestrate` | Custom agent handoff with your system prompt | When you need full control over the swarm's behavior |

---

## Requirements

- Python 3.8+
- An OpenRouter API key with Grok 4.20 access
  - Get your key at: https://openrouter.ai/keys

---

## Configuration

### Claude Code Setup

Claude Code doesn't have built-in secret management, so we use a simple file-based approach:

```bash
./scripts/setup.sh
```

Your API key is stored in `~/.config/grok-swarm/config.json` with mode 600 — readable only by you. Never exposed to the platform, just loaded at runtime.

### OpenClaw Setup

OpenClaw has built-in secret management via auth profiles:

```bash
# Add to ~/.openclaw/agents/coder/agent/auth-profiles.json
{
  "profiles": {
    "openrouter:default": {
      "key": "sk-or-v1-your-key-here"
    }
  }
}
```

---

## What Makes It Different

| Aspect | Traditional Tools | Grok Swarm |
|--------|------------------|-------------|
| **Model Architecture** | Single model | 4 coordinating agents |
| **Context Window** | ~200K tokens | ~2M tokens |
| **Reasoning Approach** | Single perspective | Multi-perspective debate |
| **Use Cases** | Quick generation | Deep analysis, large-scale work |
| **Integration** | Built-in | This plugin bridges the gap |

---

## Examples

### Codebase Security Audit

```
/grok-swarm:analyze Review the security of my auth module
```

Grok's swarm breaks down the request: one agent focuses on authentication flows, another on potential injection points, a third on token handling. They coordinate and return a comprehensive audit with prioritized findings.

### Legacy Code Modernization

```
/grok-swarm:refactor Modernize this legacy module while preserving behavior
```

The swarm identifies patterns that can be improved, suggests modern alternatives, and provides refactored code with explanations of what changed and why.

### Architectural Decision Making

```
/grok-swarm:reason Should we switch from REST to GraphQL for this API?
```

Agents debate from multiple perspectives — one argues for GraphQL's type safety, another for REST's simplicity, a third considers migration costs. You get a balanced recommendation with trade-offs.

---

## Project Structure

```
grok-multiagent-plugin/
├── src/bridge/              # Core bridge (shared by both platforms)
├── platforms/
│   ├── openclaw/            # OpenClaw plugin
│   └── claude/              # Claude Code plugin
├── scripts/
│   ├── build.sh             # Build for both platforms
│   ├── install.sh           # Install with --openclaw/--claude/--both
│   └── setup.sh             # API key configuration (Claude Code)
├── dist/                     # Generated artifacts (gitignored)
└── VERSION
```

---

## License

MIT — see [LICENSE](LICENSE)

---

## Support

- [Issues](https://github.com/KHAEntertainment/grok-multiagent-plugin/issues)
- [Discord](https://discord.com/invite/clawd)
