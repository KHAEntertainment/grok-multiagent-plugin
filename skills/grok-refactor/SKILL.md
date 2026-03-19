# Grok Refactor Skill

**Expert code refactoring powered by Grok 4.20 Multi-Agent Beta**

- **Version:** 1.0.0
- **Platforms:** OpenClaw, Claude Code
- **Mode:** `refactor`

---

## Description

Uses Grok 4.20's 4-agent swarm to intelligently refactor code while:
- Preserving original behavior and intent
- Improving readability and maintainability
- Adding modern patterns (async/await, type hints, etc.)
- Explaining what changed and why

## Usage

```bash
# Via grok-swarm CLI
grok-swarm refactor --prompt "Improve this code" --files src/app.py

# Via Python
python3 -m bridge.cli refactor --prompt "Add type hints" --files utils.py
```

## OpenClaw Integration

In OpenClaw, this skill is automatically available via the `grok_swarm` tool:

```javascript
tools.grok_swarm({
  prompt: "Refactor this module for better maintainability",
  mode: "refactor",
  files: ["src/module.py"]
})
```

## Claude Code Integration

In Claude Code, use the skill directly:

```
/grok-swarm:refactor Convert this callback pattern to async/await
```

## Requirements

- Python 3.8+
- `openai>=1.0.0`
- OpenRouter API key with Grok 4.20 access
