# ClawHub Publication Metadata

## Package Information

| Field | Value |
|-------|-------|
| **Name** | `@openclaw/grok-swarm` |
| **Version** | `1.0.0` |
| **Plugin ID** | `grok-swarm` |
| **Min OpenClaw** | `2026.3.0` |

## Description

Bridge to xAI Grok 4.20 Multi-Agent Beta (4-agent swarm) for OpenClaw agents. Enables powerful multi-agent reasoning, codebase analysis, refactoring, and code generation with ~2M token context.

## Installation

```bash
openclaw skill install grok-swarm
# or
clawhub install grok-swarm
```

## Dependencies

### Runtime

| Dependency | Version | Source |
|------------|---------|--------|
| Python 3 | ≥3.8 | System |
| `openai` Python package | ≥2.28.0 | PyPI |

### Configuration

- OpenRouter API key with Grok 4.20 access
- Configured in OpenClaw auth profiles

## Files

| Path | Purpose |
|------|---------|
| `src/bridge/grok_bridge.py` | Python API bridge |
| `src/bridge/index.js` | Node.js wrapper |
| `src/plugin/index.ts` | OpenClaw plugin |
| `src/plugin/openclaw.plugin.json` | Plugin manifest |

## Categories

- `ai`
- `coding`
- `analysis`
- `refactoring`
- `grok`
- `multi-agent`

## Keywords

```
openclaw grok multi-agent ai coding analysis refactoring
xai openrouter code-review security-audit architecture
```

## Author

OpenClaw Community

## License

MIT

## Platform

- Linux ✓
- macOS ✓
- Windows (via WSL) ✓

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

## Support

- Issues: https://github.com/KHAEntertainment/openclaw-grok-swarm/issues
- Discord: https://discord.com/invite/clawd

## Publish Checklist

- [x] Plugin manifest (`openclaw.plugin.json`) complete
- [x] Package.json for npm publishing
- [x] README with installation and usage
- [x] Python bridge with OpenAI SDK
- [x] Node.js timeout wrapper
- [x] Test results documented
- [ ] GitHub repository created
- [ ] npm package published
- [ ] ClawHub listing reviewed
