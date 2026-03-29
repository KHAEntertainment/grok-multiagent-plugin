# Installation Methods

This document covers all ways to install the Grok Swarm plugin.

---

## Method 1: NPM (Recommended)

Install the CLI tool for direct terminal usage.

```bash
npm install -g @openclaw/grok-swarm
```

Or with a specific version:

```bash
npm install -g @openclaw/grok-swarm@1.0.0
```

### Post-install Setup

```bash
# Configure your OpenRouter API key
./scripts/setup.sh
# Or manually:
echo '{"api_key": "sk-or-v1-..."}' > ~/.config/grok-swarm/config.json
chmod 600 ~/.config/grok-swarm/config.json
```

**Get an API key at:** https://openrouter.ai/keys

---

## Method 2: ClawHub

For OpenClaw users, install via ClawHub.

```bash
clawhub install grok-swarm
```

### Post-install Configuration

1. Add to `openclaw.json`:

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

2. Set your OpenRouter API key in `~/.openclaw/agents/coder/agent/auth-profiles.json`:

```json
{
  "profiles": {
    "openrouter:default": {
      "key": "sk-or-v1-..."
    }
  }
}
```

3. Restart the gateway:

```bash
openclaw gateway restart
```

---

## Method 3: Claude Code Marketplace

Install the plugin from the Claude Code marketplace.

### Step 1: Add the Marketplace

```bash
/plugin marketplace add https://github.com/KHAEntertainment/grok-multiagent-plugin
```

### Step 2: Install the Plugin

```bash
/plugin install grok-swarm@khaentertainment
```

### Step 3: Configure API Key

Run `/grok-swarm:setup` inside Claude Code — an OAuth browser flow will
authorize your OpenRouter account without exposing your API key in-context.

### Usage in Claude Code

```
/grok-swarm:analyze Review the security of my auth module
/grok-swarm:refactor Convert these callbacks to async/await
/grok-swarm:code Write a FastAPI endpoint for user registration
/grok-swarm:reason Compare microservices vs monolith for this project
```

---

## Method 4: Git Clone

Clone the repository and run the install script.

```bash
# Clone the repo
git clone https://github.com/KHAEntertainment/grok-multiagent-plugin.git
cd grok-multiagent-plugin

# Install for your platform
./install.sh          # Auto-detect (Claude Code or OpenClaw)
./install.sh claude   # Install for Claude Code only
./install.sh openclaw # Install for OpenClaw only
./install.sh both     # Install for both platforms
```

### Manual Installation

```bash
# For Claude Code
cp -r platforms/claude ~/.claude/plugins/grok-swarm/

# For OpenClaw
cp -r src/bridge ~/.openclaw/skills/grok-refactor/
cp -r src/plugin ~/.openclaw/extensions/grok-swarm/
```

### Configure API Key

**For Claude Code:** Run `/grok-swarm:setup` — OAuth browser flow, no key in-context.

**For OpenClaw/CLI:** Run `./scripts/setup.sh` or set `OPENROUTER_API_KEY` manually.

---

## Method 5: pip (Python Bridge Only)

Install just the Python bridge for OpenClaw's Python integration.

```bash
pip install grok-swarm
```

This installs the `grok-swarm` CLI and Python package.

### Verify Installation

```bash
grok-swarm --help
```

---

## Quick Start After Installation

### For Claude Code

```
# Authorize via OAuth (no API key in-context)
/grok-swarm:setup

# Try it out
/grok-swarm:analyze Review my auth module for security issues
```

### For OpenClaw

```bash
# Restart gateway
openclaw gateway restart

# Test via API or agent
openclaw status | grep grok
```

---

## Requirements

- Python 3.8+
- Node.js 18+
- OpenRouter API key with Grok 4.20 access

## Troubleshooting

### "Command not found" after npm install

```bash
# Check if the bin is in your PATH
npm bin -g

# If not, add to PATH
export PATH="$(npm bin -g):$PATH"
```

### "Plugin not found" in Claude Code

```bash
# Reload plugins
/reload-plugins

# Or restart Claude Code
```

### API key not found

```bash
# Check config file exists
cat ~/.config/grok-swarm/config.json

# Or check environment
echo $OPENROUTER_API_KEY
```

---

## Updating

### NPM

```bash
npm update -g @openclaw/grok-swarm
```

### ClawHub

```bash
clawhub update grok-swarm
```

### Git Clone

```bash
git pull origin main
./install.sh
```

### Claude Code Marketplace

```bash
/plugin marketplace update
/plugin upgrade grok-swarm@khaentertainment
```

---

## Uninstalling

### NPM

```bash
npm uninstall -g @openclaw/grok-swarm
```

### ClawHub

```bash
clawhub uninstall grok-swarm
```

### Git Clone

```bash
rm -rf ~/.claude/plugins/grok-swarm
rm -rf ~/.openclaw/skills/grok-refactor
rm -rf ~/.openclaw/extensions/grok-swarm
rm -f ~/.config/grok-swarm/config.json
```

### Claude Code

```bash
/plugin uninstall grok-swarm@khaentertainment
/plugin marketplace remove khaentertainment
```
