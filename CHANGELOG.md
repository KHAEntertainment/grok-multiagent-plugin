# Changelog

All notable changes to the Grok Swarm tool.

## [1.0.0] - 2026-03-16

### Added

- Initial release

### Components

- **Core Bridge** (`~/.openclaw/skills/grok-refactor/`)
  - `grok_bridge.py` — Python bridge using OpenAI SDK → OpenRouter → Grok 4.20
  - `index.js` — Node.js wrapper with timeout enforcement
  - `SKILL.md` — Skill documentation
  - `.venv/` — Python virtual environment

- **OpenClaw Plugin** (`~/.openclaw/extensions/grok-swarm/`)
  - `openclaw.plugin.json` — Plugin manifest
  - `index.ts` — Native tool registration
  - `package.json` — Package configuration

- **Project Scaffold** (`~/projects/grok-multi-agent/`)
  - README, CHANGELOG, CLAWHUB documentation
  - Test results

### Features

- 5 task modes: refactor, analyze, code, reason, orchestrate
- File context ingestion with size limits
- Custom system prompts for orchestrate mode
- OpenAI-format tool use passthrough
- Configurable timeout (default: 120s)
- Content filter warning system

### Technical Details

- Model: `x-ai/grok-4.20-multi-agent-beta` (4-agent swarm)
- Context window: ~2M tokens
- Max context size: 1,500,000 chars per call
- Auth: OpenRouter API key via OpenClaw auth profiles

### Known Issues

- Content filter may trigger on terse prompts (use natural language)
- Generated code may have subtle bugs (human review recommended)
- Complex tasks may take 30-90s due to multi-agent coordination
