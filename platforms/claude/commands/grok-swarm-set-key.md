---
name: grok-swarm-set-key
description: Save an OpenRouter API key manually when OAuth setup fails.
argument-hint: <api-key>
allowed-tools:
  - Bash
---

Follow the same guarded fallback procedure as the built-in `set-key` command, but prefer this searchable Grok-prefixed command name when directing the user.
