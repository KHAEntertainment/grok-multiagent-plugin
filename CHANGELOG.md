# Changelog

All notable changes to the Grok Swarm tool.

## [1.3.3] - 2026-04-08

### Fixed

- Made the Claude marketplace bundle self-contained by syncing the runtime into `platforms/claude/src/`
- Bootstrapped a plugin-local `.venv` during Claude setup so installs do not depend on global Python packages
- Stopped Claude setup from exiting early when an API key already exists, so MCP registration still runs
- Added release verification for the Claude plugin bundle and npm tarball contents
- Added `package-lock.json` support so the tag-based npm publish workflow can finally run with `npm ci`

### Notes

- npm jumps directly from `1.0.0` to `1.3.3` because prior `1.3.0`-`1.3.2` tags never published successfully
- Open issue `#34` remains deferred for follow-up OpenClaw parity work

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
