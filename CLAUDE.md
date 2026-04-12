# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A dual-platform plugin (Claude Code + OpenClaw) that bridges to xAI's **Grok 4.20 Multi-Agent Beta** via the **OpenRouter** API. It gives AI coding agents access to Grok's multi-agent swarm (4 or 16 agents) with ~2M token context for code analysis, refactoring, and generation.

## Build & Development Commands

```bash
# Build (copies Python bridge + Node wrapper to dist/)
npm run build

# Test (only checks CLI --help flag)
npm test

# Lint
npm run lint

# Clean
npm run clean

# Install to local platforms
./install.sh openclaw    # copies to ~/.openclaw/
./install.sh claude      # copies to ~/.claude/plugins/grok-swarm/
./install.sh both        # both platforms

# Python deps
pip3 install -r requirements.txt
```

Requires Node.js >= 18 and Python 3.8+.

## Architecture

Layered bridge pattern — each layer has a single responsibility:

```
Plugin Layer (TypeScript/manifests)
    ↓ registers tools and skills
CLI Wrapper (Node.js — src/bridge/index.js)
    ↓ timeout enforcement, process spawning
Python Bridge (src/bridge/grok_bridge.py)
    ↓ OpenAI SDK → OpenRouter API
xAI Grok 4.20 Multi-Agent Beta
```

**Key modules:**

- `src/bridge/grok_bridge.py` — Core API logic: key resolution, mode-based system prompts, file context assembly, code block parsing. The `call_grok()` function is the central entry point.
- `src/bridge/cli.py` — Unified CLI that dispatches to grok_bridge with argparse.
- `src/bridge/apply.py` — Parses annotated code blocks and writes files to disk. Supports three annotation formats: `lang:path`, `FILE:` marker, and `# filename.py` comments.
- `src/bridge/index.js` — Node.js wrapper that enforces timeouts on Python subprocess.
- `src/bridge/oauth_setup.py` — PKCE OAuth flow for OpenRouter (keeps keys out of LLM context).
- `src/bridge/usage_tracker.py` — Persistent token/cost tracking.
- `src/agent/grok_agent.py` — Autonomous loop: discover files → call Grok → apply changes → verify → iterate.
- `src/shared/patterns.py` — Centralized regex patterns for filename detection, shared between bridge and agent.
- `src/plugin/index.ts` — OpenClaw plugin: registers `grok_swarm` (single call) and `grok_swarm_agent` (autonomous loop) tools.

**Claude Code plugin structure** (`platforms/claude/`):
- `.claude-plugin/plugin.json` — Plugin manifest (name, version, author, commands/skills/mcpServers paths)
- `.mcp.json` — Static MCP server declaration (stdio transport)
- `skills/grok-swarm/` — Skill directory with `SKILL.md` + `references/` + `scripts/` subdirs
- `src/mcp/grok_server.py` — MCP server exposing `grok_query`, `grok_session_start`, `grok_session_continue`, `grok_agent`

## API Key Resolution Priority

`grok_bridge.py:get_api_key()` checks in order:
1. `OPENROUTER_API_KEY` environment variable
2. `~/.config/grok-swarm/config.json`
3. `~/.claude/grok-swarm.local.md`
4. OpenClaw auth profiles

## Thinking Levels

- **Low** (default): 4-agent swarm — faster, cheaper
- **High**: 16-agent swarm — triggered by phrases like "16 agent swarm", "high thinking mode", or `--thinking high`

## File Annotation Formats

Code blocks can be annotated three ways for `apply.py` to write them:
1. Fenced block with language:path — ` ```python:src/main.py `
2. `FILE: path/to/file.py` marker inside the block
3. Comment header — `# filename.py` (uses `shared/patterns.py` regex)

## Task Tracking

Uses **bd (beads)** — not TodoWrite or markdown lists:
```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim
bd close <id>
```

## Code Duplication Note

`skills/grok-refactor/bridge/` and `skills/grok-refactor/shared/` are copies of `src/bridge/` and `src/shared/` respectively (not symlinks). Changes to bridge/shared code must be applied in both locations.

## Version Locations

Version is defined in multiple places and must be kept in sync: `package.json`, `VERSION`, `pyproject.toml`, `CLAWHUB.md`, `.claude-plugin/marketplace.json`, and `platforms/claude/.claude-plugin/plugin.json`. Use `<VERSION>` as the canonical placeholder when referencing version numbers.

## Release Workflow

After merging significant changes (new features, bug fixes, or enhancements), bump the version and publish a new release:

```bash
# 1. Update version in all locations (see Version Locations above)
#    Change from e.g. 1.3.0 → 1.4.0 for minor features or 2.0.0 for breaking changes

# 2. Create a git tag
git tag -a v<VERSION> -m "Release <VERSION>"
git push origin v<VERSION>

# 3. Create GitHub release (or via GitHub UI)
gh release create v<VERSION> --title "Release <VERSION>" --notes "See CHANGELOG.md"

# 4. NPM publish (if applicable)
npm publish
```

**When to release:**
- New features → minor version bump (1.3.0 → 1.4.0)
- Bug fixes → patch version bump (1.3.0 → 1.3.1)
- Breaking changes → major version bump (1.3.0 → 2.0.0)

**Marketplace users** pull from `master` branch via the `marketplace.json` — the NPM package is updated on publish.
