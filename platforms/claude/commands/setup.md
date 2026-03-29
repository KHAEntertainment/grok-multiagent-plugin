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
OAUTH_PATH="$(find ~/.claude/plugins -name 'oauth_setup.py' 2>/dev/null | head -1)"
if [ -n "$OAUTH_PATH" ]; then
  python3 "$(dirname "$OAUTH_PATH")/oauth_setup.py" --check 2>/dev/null
else
  OAUTH_PATH="$(find /usr /usr/local ~/.local -name 'oauth_setup.py' 2>/dev/null | head -1)"
  [ -n "$OAUTH_PATH" ] && python3 "$OAUTH_PATH" --check 2>/dev/null
fi
```

Alternative (locate bridge relative to this command file):
```bash
OAUTH_PATH="$(find ~/.claude/plugins -name 'oauth_setup.py' 2>/dev/null | head -1)"
if [ -n "$OAUTH_PATH" ]; then
  BRIDGE_DIR="$(dirname "$OAUTH_PATH")"
else
  OAUTH_PATH="$(find /usr /usr/local ~/.local -name 'oauth_setup.py' 2>/dev/null | head -1)"
  [ -n "$OAUTH_PATH" ] && BRIDGE_DIR="$(dirname "$OAUTH_PATH")"
fi
if [ -f "$BRIDGE_DIR/oauth_setup.py" ]; then
  python3 "$BRIDGE_DIR/oauth_setup.py" --check
fi
```

If the check exits 0, tell the user their key is already configured and offer
to run a test query. **Stop here.**

## Step 2 — Run the OAuth flow

Locate `oauth_setup.py` in the plugin's `src/bridge/` directory and run it
with a 240 seconds timeout. The timeout is enforced by the Bash tool invocation
(via the `timeout` parameter in the tool call or CI runner timeout settings):

```bash
OAUTH_PATH="$(find ~/.claude/plugins -name 'oauth_setup.py' 2>/dev/null | head -1)"
if [ -n "$OAUTH_PATH" ]; then
  PLUGIN_ROOT="$(cd "$(dirname "$OAUTH_PATH")/../.." 2>/dev/null && pwd)"
else
  OAUTH_PATH="$(find /usr /usr/local ~/.local -name 'oauth_setup.py' 2>/dev/null | head -1)"
  [ -n "$OAUTH_PATH" ] && PLUGIN_ROOT="$(cd "$(dirname "$OAUTH_PATH")/../.." 2>/dev/null && pwd)"
fi
timeout 240s python3 "$PLUGIN_ROOT/src/bridge/oauth_setup.py"
```

**Note**: The `timeout 240s` wrapper ensures the command terminates if the OAuth
flow exceeds 240 seconds. The script itself has an internal OAUTH_TIMEOUT_SECS
(180s) for the callback phase plus roughly 30s for token exchange, so the 240s
outer limit provides a safe margin.

The script will:
1. Print an authorization URL
2. Start a local server on `localhost:3000`
3. Wait up to 180 seconds for the browser callback
4. Exchange the auth code for an API key
5. Save the key to `~/.config/grok-swarm/config.json` (chmod 600)

## Step 3 — Present the auth URL

Show the user the URL printed by the script and tell them:

> **Click this link to authorize Grok Swarm with your OpenRouter account.**
> After approving in your browser, return here — setup completes automatically.

## Step 4 — Report result

- If the script exits 0: confirm success and suggest running `/grok-swarm:analyze Hello world`
- If it exits 1 (timeout or port conflict): show the error message from the script
  and suggest the manual fallback:
  ```
  mkdir -p ~/.config/grok-swarm
  echo '{"api_key": "sk-or-v1-..."}' > ~/.config/grok-swarm/config.json
  chmod 600 ~/.config/grok-swarm/config.json
  ```
  Direct them to https://openrouter.ai/keys for a key.

## xAI Direct Users

If the user says they want to use xAI directly (not OpenRouter), run:
```bash
OAUTH_PATH="$(find ~/.claude/plugins -name 'oauth_setup.py' 2>/dev/null | head -1)"
if [ -n "$OAUTH_PATH" ]; then
  PLUGIN_ROOT="$(cd "$(dirname "$OAUTH_PATH")/../.." 2>/dev/null && pwd)"
else
  OAUTH_PATH="$(find /usr /usr/local ~/.local -name 'oauth_setup.py' 2>/dev/null | head -1)"
  [ -n "$OAUTH_PATH" ] && PLUGIN_ROOT="$(cd "$(dirname "$OAUTH_PATH")/../.." 2>/dev/null && pwd)"
fi
python3 "$PLUGIN_ROOT/src/bridge/oauth_setup.py" --provider xai
```
This prints manual credential instructions without attempting OAuth.