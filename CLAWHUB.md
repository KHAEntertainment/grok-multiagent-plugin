# Grok Swarm Tool — ClawHub Publication

## Package

| Field | Value |
|-------|-------|
| **Name** | `grok-swarm` |
| **Version** | `1.3.2` |
| **Min OpenClaw** | `2026.3.0` |

## Installation

```bash
# Option 1: Via ClawHub
clawhub install grok-swarm

# Option 2: Via install script
git clone https://github.com/KHAEntertainment/grok-multiagent-plugin.git
cd grok-multiagent-plugin
./install.sh

# Option 3: Manual
cp -r src/bridge ~/.openclaw/skills/grok-refactor/
cp -r src/plugin ~/.openclaw/extensions/grok-swarm/
```

## Configuration

### 1. Add to plugins.allow
```json
"plugins": {
  "allow": ["grok-swarm"]
}
```

### 2. Enable plugin
```json
"plugins": {
  "entries": {
    "grok-swarm": {
      "enabled": true
    }
  }
}
```

### 3. Grant tool access to agents
```json
"agents": {
  "list": [{
    "id": "coder",
    "tools": {
      "allow": ["grok_swarm"]
    }
  }]
}
```

### 4. Set OpenRouter API key

In `~/.openclaw/agents/coder/agent/auth-profiles.json`:
```json
{
  "profiles": {
    "openrouter:default": {
      "key": "sk-or-v1-..."
    }
  }
}
```

## Dependencies

- Python 3.8+ with `openai>=2.28.0`
- Node.js 18+

## Categories

- `ai`
- `coding`
- `analysis`
- `refactoring`

## Keywords

```
openclaw grok multi-agent xai openrouter code-review security
```
