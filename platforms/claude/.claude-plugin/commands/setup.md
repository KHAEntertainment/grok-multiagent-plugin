---
name: setup
description: Set up your OpenRouter API key for Grok Swarm. Run this before first use if prompted.
argument-hint: None
allowed-tools:
  - Bash
---

# Setup Grok Swarm

This command guides you through configuring your OpenRouter API key for Grok Swarm.

## Usage

```
/grok-swarm:setup
```

## What it does

1. Checks for existing API key in:
   - `~/.claude/grok-swarm.local.md` (plugin settings)
   - `~/.config/grok-swarm/config.json` (CLI config)
   - `$OPENROUTER_API_KEY` environment variable

2. If no key found, prompts you to enter one

3. Saves configuration to plugin settings file

## First-time setup

If you're seeing this for the first time:

1. Get an OpenRouter API key at https://openrouter.ai/keys
2. Run `/grok-swarm:setup`
3. Paste your API key when prompted

## Troubleshooting

- **Invalid key error**: Make sure you copied the key correctly from OpenRouter
- **Key starts with `sk-`**: That's correct! OpenRouter keys begin with `sk-or-v1-`
- **Permission denied**: The setup script needs to write to `~/.claude/` and `~/.config/`
