# Claude Code Marketplace Guide

Claude Code uses a **decentralized marketplace model** — there is no central plugin store to submit to. Instead, you create a marketplace manifest file in your repository, host it on GitHub (or any git host), and users add your marketplace via the `/plugin marketplace add` command.

---

## How It Works

1. You create a `marketplace.json` file at `.claude-plugin/marketplace.json` in your repository
2. You push to GitHub (or any git host)
3. Users add your marketplace: `/plugin marketplace add <repo-url>`
4. Users install plugins from your marketplace: `/plugin install grok-swarm@<marketplace-name>`

---

## Marketplace File Structure

Create `.claude-plugin/marketplace.json` in your repository root:

```json
{
  "name": "khaentertainment",
  "owner": {
    "name": "KHA Entertainment",
    "email": "support@openclaw.dev"
  },
  "plugins": [
    {
      "name": "grok-swarm",
      "source": {
        "source": "git-subdir",
        "url": "https://github.com/KHAEntertainment/grok-multiagent-plugin",
        "path": "platforms/claude",
        "ref": "main"
      },
      "description": "Multi-agent intelligence powered by Grok 4.20 via OpenRouter. 4-agent swarm with ~2M token context.",
      "version": "1.0.0",
      "author": {
        "name": "OpenClaw"
      },
      "homepage": "https://github.com/KHAEntertainment/grok-multiagent-plugin",
      "license": "MIT",
      "keywords": ["grok", "multi-agent", "xai", "openrouter", "code-review", "refactoring"]
    }
  ]
}
```

---

## Publishing Steps

### Step 1: Ensure Your Plugin is Ready

Your plugin at `platforms/claude/` should have:
- `.claude-plugin/plugin.json` — plugin manifest ✓
- `skills/` — skill directories with `SKILL.md` files ✓
- `README.md` — documentation ✓

### Step 2: Create the Marketplace Manifest

The marketplace manifest goes at **repository root** (not inside the plugin subdirectory):

```
grok-multiagent-plugin/
├── .claude-plugin/
│   └── marketplace.json    ← Marketplace manifest (at repo root)
├── platforms/
│   └── claude/
│       ├── .claude-plugin/
│       │   └── plugin.json ← Plugin manifest (inside plugin)
│       ├── skills/
│       │   └── grok-swarm/
│       │       └── SKILL.md
│       └── README.md
└── ...
```

### Step 3: Push to GitHub

```bash
git add .claude-plugin/marketplace.json
git commit -m "docs: add Claude Code marketplace manifest"
git push origin main
```

### Step 4: Share the Installation Command

Users install your marketplace and plugin:

```bash
# Add the marketplace
/plugin marketplace add https://github.com/KHAEntertainment/grok-multiagent-plugin

# Install the plugin
/plugin install grok-swarm@khaentertainment
```

---

## Alternative: Direct GitHub Source

Instead of a marketplace, users can also install directly from GitHub:

```bash
# Clone and use --plugin-dir for local development
claude --plugin-dir ./platforms/claude

# Or for CI/testing, reference the subdirectory
/plugin install https://github.com/KHAEntertainment/grok-multiagent-plugin/tree/main/platforms/claude
```

---

## Updating Your Marketplace

Push changes to the `marketplace.json` and users update with:

```bash
/plugin marketplace update
```

For plugin version updates, users can:

```bash
/plugin upgrade grok-swarm@khaentertainment
```

---

## Source Types Reference

| Source Type | Config | Use Case |
|------------|--------|----------|
| `git-subdir` | `url`, `path`, `ref?` | Monorepo with plugin in subdirectory (recommended) |
| `github` | `repo`, `ref?` | Full repo as plugin |
| `url` | `url`, `ref?` | Any git URL |
| Relative | `"./my-plugin"` | Local marketplace development |

---

## Key Links

- [Claude Code Plugins Docs](https://code.claude.com/docs/en/plugins)
- [Plugin Marketplace Docs](https://code.claude.com/docs/en/plugin-marketplaces)
- [Plugin Reference](https://code.claude.com/docs/en/plugins-reference)
