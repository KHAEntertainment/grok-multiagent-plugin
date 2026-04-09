---
name: set-key
description: Manually save an OpenRouter API key to config. Last-resort fallback when OAuth fails. WARNING - key will be visible in conversation context.
argument-hint: YOUR_API_KEY
allowed-tools:
  - Bash
---

# Set Grok Swarm API Key (Manual Fallback)

**Use this only when the OAuth flow (`/grok-swarm-setup`) has failed repeatedly.**

## Step 1 — Display security warning

Before doing anything else, output this warning verbatim to the user:

---

> **WARNING: Security Risk**
>
> You are about to paste your OpenRouter API key directly into this conversation.
> This means your API key **will be visible in the LLM context window** and may be
> stored in conversation logs.
>
> **Only proceed if you understand and accept these risks.** The recommended method
> is `/grok-swarm-setup` which uses OAuth so your key never enters the conversation.
>
> Type **yes** to confirm you accept this risk, or anything else to cancel.

---

Wait for the user's response. If they do not reply with exactly `yes` (case-insensitive), stop here and remind them to use `/grok-swarm-setup` instead.

## Step 2 — Validate the key argument

The API key is the argument passed to this command (e.g. `/grok-swarm-set-key sk-or-v1-...`).

If no argument was provided, ask the user to re-run with their key:
```
/grok-swarm-set-key YOUR_API_KEY_HERE
```
Do not ask them to type the key in a follow-up message.

## Step 3 — Save the key

Run (pass the key via environment variable so it is never interpolated into shell or Python source):
```bash
mkdir -p ~/.config/grok-swarm
GROK_SET_KEY="<the key argument>" python3 -c "
import json, os
from pathlib import Path

api_key = os.environ['GROK_SET_KEY']
config_file = Path.home() / '.config' / 'grok-swarm' / 'config.json'
existing = {}
if config_file.exists():
    try:
        existing = json.loads(config_file.read_text())
    except Exception:
        pass
existing['api_key'] = api_key
json_bytes = (json.dumps(existing, indent=2) + '\n').encode()
tmp = str(config_file.parent / f'.config.json.tmp.{os.getpid()}')
fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
try:
    os.write(fd, json_bytes)
    os.fsync(fd)
finally:
    os.close(fd)
os.replace(tmp, str(config_file))
print('saved')
"
```

## Step 4 — Confirm success

Tell the user:
- Key saved to `~/.config/grok-swarm/config.json` (permissions: 600)
- Show only the first 8 characters: `sk-or-v1-...` → `sk-or-v1-` + `[redacted]`
- Suggest running `/grok-swarm-analyze Hello world` to verify the key works

## Notes

- This command exists as a last resort. Always prefer `/grok-swarm-setup` (OAuth flow).
- The key is saved with file permissions 600 (owner read/write only).
- If you need to rotate the key later, run this command again or re-run `/grok-swarm-setup`.
