---
name: setup
description: Authorize Grok Swarm with your OpenRouter account via OAuth. No API key handling in-context.
argument-hint: None
allowed-tools:
  - Bash
---

# Setup Grok Swarm

Follow these steps exactly. Do not ask the user for their API key — the OAuth
flow ensures the key never passes through this conversation.

## Step 1 — Check for existing key

Run:
```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | head -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "Grok Swarm plugin not found."; exit 1; }
PYTHON_BIN="$PLUGIN_ROOT/.venv/bin/python3"
[ -x "$PYTHON_BIN" ] || PYTHON_BIN=python3
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/oauth_setup.py" --check 2>/dev/null
```

If the check exits 0, tell the user their key is already configured and offer
to run a test query. Continue to Step 2 anyway if they also want MCP registration refreshed.

## Step 2 — Run the OAuth flow

Run the plugin's setup script so it can:
- bootstrap the plugin-local `.venv`
- install Python dependencies from `src/requirements.txt`
- run OAuth if needed
- register the MCP server using the plugin-local interpreter

Run:

```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | head -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "Grok Swarm plugin not found."; exit 1; }
bash "$PLUGIN_ROOT/.claude-plugin/setup.sh"
```

The setup script will keep an existing key if one is already configured and
still refresh the plugin-local runtime plus MCP registration.

## Step 3 — Present the auth URL

If the setup script launched OAuth, show the user the URL it printed and tell them:

> **Click this link to authorize Grok Swarm with your OpenRouter account.**
> After approving in your browser, return here — setup completes automatically.

## Step 4 — Report result

- If the script exits 0: confirm success and suggest running `/grok-swarm:analyze Hello world`
- If it exits 1: show the error message from the script
  and suggest the manual fallback:
  Direct them to https://openrouter.ai/keys for a key.

## xAI Direct Users

If the user says they want to use xAI directly (not OpenRouter), run:
```bash
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-$(find ~/.claude/plugins -path '*/grok-swarm/.claude-plugin/plugin.json' -exec dirname {} \; 2>/dev/null | head -1 | xargs -I{} dirname {})}"
[ -z "$PLUGIN_ROOT" ] && { echo "Grok Swarm plugin not found."; exit 1; }
PYTHON_BIN="$PLUGIN_ROOT/.venv/bin/python3"
[ -x "$PYTHON_BIN" ] || PYTHON_BIN=python3
"$PYTHON_BIN" "$PLUGIN_ROOT/src/bridge/oauth_setup.py" --provider xai
```
This prints manual credential instructions without attempting OAuth.
