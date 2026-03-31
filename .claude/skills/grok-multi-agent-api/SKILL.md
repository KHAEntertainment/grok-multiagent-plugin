---
name: grok-multi-agent-api
description: xAI Grok Multi-Agent API reference for developing and maintaining this plugin. Triggers: "multi-agent api", "grok api", "agent_count", "reasoning effort", "openai sdk usage", "grok-4.20-multi-agent", "api configuration"
version: 1.0.0
---

# xAI Grok 4.20 Multi-Agent API Reference

Reference for the Realtime Multi-agent Research API that this plugin wraps. Use this when modifying `src/bridge/grok_bridge.py`, `src/agent/grok_agent.py`, or any bridge code that communicates with xAI/OpenRouter.

## Model ID

```
grok-4.20-multi-agent
```

> **Note:** This plugin uses `x-ai/grok-4.20-multi-agent` via OpenRouter (now out of beta). The direct xAI API uses `grok-4.20-multi-agent`.

## API Endpoints

| Provider | Base URL | Endpoint |
|----------|----------|----------|
| xAI Direct | `https://api.x.ai/v1` | `/responses` |
| OpenRouter | `https://openrouter.ai/api/v1` | `/chat/completions` |

**This plugin uses OpenRouter** as the gateway. The bridge sends requests to OpenRouter which proxies to xAI.

## Agent Count Configuration

| SDK / API | Parameter | 4 Agents | 16 Agents |
|-----------|-----------|----------|-----------|
| xAI SDK | `agent_count` | `4` | `16` |
| OpenAI SDK | `reasoning.effort` | `"low"` or `"medium"` | `"high"` or `"xhigh"` |
| Vercel AI SDK | `reasoningEffort` | `"low"` or `"medium"` | `"high"` or `"xhigh"` |
| REST API | `reasoning.effort` | `"low"` or `"medium"` | `"high"` or `"xhigh"` |

- **4 agents**: Quick research, focused queries, lower cost
- **16 agents**: Deep research, complex multi-faceted topics, higher token usage

In this plugin's bridge code (`grok_bridge.py`), agent count is sent as `extra_body={"agent_count": N}` via the OpenAI SDK.

## Built-in Tools

xAI provides server-side tools that can be enabled per request:

| Tool | Description |
|------|-------------|
| `web_search` | Web search |
| `x_search` | X/Twitter search |
| `code_execution` | Code execution |
| `collections_search` | Collections search |

When enabled, the server runs the agent loop automatically, invoking tools until the final answer is generated. These incur additional cost.

**Important for this plugin:** The bridge currently does NOT pass through built-in tools — it uses the agents for pure reasoning over provided file context. If adding tool support, pass them in the `tools` parameter.

## Output Behavior

- Only the **leader agent's** final response and tool calls are returned to the caller
- Sub-agent state (intermediate reasoning, tool calls, outputs) is encrypted
- Encrypted sub-agent state is included only when `use_encrypted_content=True` (xAI SDK)
- This keeps default responses clean while preserving context for multi-turn

## Multi-turn Conversations

Use `previous_response_id` to chain turns. The agents use prior context for more targeted follow-up answers.

## API Limitations

- **No Chat Completions API** — must use Responses API (`/responses`) or xAI SDK
- **No `max_tokens`** — parameter is not supported
- **No client-side/custom tools** — only built-in tools and remote MCP tools supported
- **Only leader output exposed** — sub-agent details are encrypted unless explicitly requested

## Example: Direct xAI API (Python OpenAI SDK)

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("XAI_API_KEY"),
    base_url="https://api.x.ai/v1",
)

# 4-agent setup
response = client.responses.create(
    model="grok-4.20-multi-agent",
    reasoning={"effort": "low"},
    input=[
        {"role": "user", "content": "Analyze this code..."},
    ],
)

# 16-agent setup
response = client.responses.create(
    model="grok-4.20-multi-agent",
    reasoning={"effort": "high"},
    input=[
        {"role": "user", "content": "Deep analysis..."},
    ],
)
```

## Example: Via OpenRouter (This Plugin's Path)

```python
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

response = client.chat.completions.create(
    model="x-ai/grok-4.20-multi-agent",
    extra_body={"agent_count": 4},  # or 16
    messages=[
        {"role": "system", "content": "You are..."},
        {"role": "user", "content": "Analyze..."},
    ],
)
```

## Prompting Best Practices

When constructing system prompts for the multi-agent model:

1. **Set scope and depth explicitly** — "Compare X across dimensions A, B, C" not "Tell me about X"
2. **Request structured output** — "Present as a comparison table with categories..."
3. **Specify sources/perspectives** — "Cite academic papers from 2024-2025"
4. **Break complex research into turns** — Start broad, narrow with follow-ups
5. **Provide context** — Include relevant constraints and prior knowledge

## Pricing Considerations

All tokens from **both leader and sub-agents** are billed (input, output, reasoning). Server-side tool calls by any agent also count. A single multi-agent request may use significantly more tokens than a standard request. Monitor via `usage` and `server_side_tool_usage` fields.

## Streaming

The xAI SDK supports streaming with `include=["verbose_streaming"]`:

```python
chat = client.chat.create(
    model="grok-4.20-multi-agent",
    include=["verbose_streaming"],
)
for response, chunk in chat.stream():
    if chunk.content:
        print(chunk.content, end="", flush=True)
```

This plugin's bridge does not currently stream — it waits for the full response. Streaming support would require changes to `grok_bridge.py:call_grok()` and `src/bridge/index.js`.
