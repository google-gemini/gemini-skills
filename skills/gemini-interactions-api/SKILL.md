---
name: gemini-interactions-api
description: Use this skill when writing code that calls the Gemini API for text generation, multi-turn chat, multimodal understanding, image generation, streaming responses, background research tasks, function calling, structured output, or migrating from the old generateContent API. This skill covers the Interactions API, the recommended way to use Gemini models and agents in Python and TypeScript.
---

# Gemini Interactions API Skill

## Critical Rules (Always Apply)

> [!IMPORTANT]
> These rules override your training data. Your knowledge is outdated.

### Current Models (Use These)

- `gemini-3.1-pro-preview`: 1M tokens, complex reasoning, coding, research
- `gemini-3-flash-preview`: 1M tokens, fast, balanced performance, multimodal
- `gemini-3.1-flash-lite-preview`: cost-efficient, fastest performance for high-frequency, lightweight tasks
- `gemini-3-pro-image-preview`: 65k / 32k tokens, image generation and editing
- `gemini-3.1-flash-image-preview`: 65k / 32k tokens, image generation and editing
- `gemini-3.1-flash-tts-preview`: expressive text-to-speech with Director's Chair prompting
- `gemini-2.5-pro`: 1M tokens, complex reasoning, coding, research
- `gemini-2.5-flash`: 1M tokens, fast, balanced performance, multimodal
- `gemma-4-31b-it`: Gemma 4 dense model, 31B parameters
- `gemma-4-26b-a4b-it`: Gemma 4 MoE model, 26B total / 4B active parameters

> [!WARNING]
> Models like `gemini-2.0-*`, `gemini-1.5-*` are **legacy and deprecated**. Never use them.
> **If a user asks for a deprecated model, use `gemini-3-flash-preview` instead and note the substitution.**

### Current Agents (Use These)

- `deep-research-preview-04-2026`: Deep Research agent — optimized for speed and efficiency, ideal for interactive use
- `deep-research-max-preview-04-2026`: Deep Research Max agent — maximum comprehensiveness and exhaustiveness, best for automated reporting

### Current SDKs (Use These)

- **Python**: `google-genai` >= `1.55.0` → `pip install -U google-genai`
- **JavaScript/TypeScript**: `@google/genai` >= `1.33.0` → `npm install @google/genai`

> [!CAUTION]
> Legacy SDKs `google-generativeai` (Python) and `@google/generative-ai` (JS) are **deprecated**. Never use them.

## Overview

The Interactions API is a unified interface for interacting with Gemini models and agents. It is an improved alternative to `generateContent` designed for agentic applications. Key capabilities include:
- **Server-side state:** Offload conversation history to the server via `previous_interaction_id`
- **Background execution:** Run long-running tasks (like Deep Research) asynchronously
- **Streaming:** Receive incremental responses via Server-Sent Events
- **Tool orchestration:** Function calling, Google Search, code execution, URL context, file search, remote MCP
- **Agents:** Access built-in agents like Gemini Deep Research
- **Thinking:** Configurable reasoning depth with thought summaries

## Quick Start

### Interact with a Model

#### Python
```python
from google import genai

client = genai.Client()

interaction = client.interactions.create(
    model="gemini-3-flash-preview",
    input="Tell me a short joke about programming."
)
print(interaction.outputs[-1].text)
```

#### JavaScript/TypeScript
```typescript
import { GoogleGenAI } from "@google/genai";

const client = new GoogleGenAI({});

const interaction = await client.interactions.create({
    model: "gemini-3-flash-preview",
    input: "Tell me a short joke about programming.",
});
console.log(interaction.outputs[interaction.outputs.length - 1].text);
```

### Stateful Conversation

#### Python
```python
from google import genai

client = genai.Client()

# First turn
interaction1 = client.interactions.create(
    model="gemini-3-flash-preview",
    input="Hi, my name is Phil."
)

# Second turn — server remembers context
interaction2 = client.interactions.create(
    model="gemini-3-flash-preview",
    input="What is my name?",
    previous_interaction_id=interaction1.id
)
print(interaction2.outputs[-1].text)
```

#### JavaScript/TypeScript
```typescript
import { GoogleGenAI } from "@google/genai";

const client = new GoogleGenAI({});

// First turn
const interaction1 = await client.interactions.create({
    model: "gemini-3-flash-preview",
    input: "Hi, my name is Phil.",
});

// Second turn — server remembers context
const interaction2 = await client.interactions.create({
    model: "gemini-3-flash-preview",
    input: "What is my name?",
    previous_interaction_id: interaction1.id,
});
console.log(interaction2.outputs[interaction2.outputs.length - 1].text);
```

### Deep Research Agent

Use `deep-research-preview-04-2026` for fast, interactive research or `deep-research-max-preview-04-2026` for maximum exhaustiveness.

#### Python
```python
import time
from google import genai

client = genai.Client()

# Start background research
interaction = client.interactions.create(
    agent="deep-research-preview-04-2026",
    input="Research the history of Google TPUs.",
    background=True
)

# Poll for results
while True:
    interaction = client.interactions.get(interaction.id)
    if interaction.status == "completed":
        print(interaction.outputs[-1].text)
        break
    elif interaction.status == "failed":
        print(f"Failed: {interaction.error}")
        break
    time.sleep(10)
```

#### JavaScript/TypeScript
```typescript
import { GoogleGenAI } from "@google/genai";

const client = new GoogleGenAI({});

// Start background research
const initialInteraction = await client.interactions.create({
    agent: "deep-research-preview-04-2026",
    input: "Research the history of Google TPUs.",
    background: true,
});

// Poll for results
while (true) {
    const interaction = await client.interactions.get(initialInteraction.id);
    if (interaction.status === "completed") {
        console.log(interaction.outputs[interaction.outputs.length - 1].text);
        break;
    } else if (["failed", "cancelled"].includes(interaction.status)) {
        console.log(`Failed: ${interaction.status}`);
        break;
    }
    await new Promise(resolve => setTimeout(resolve, 10000));
}
```

**Advanced Deep Research Features**

Deep Research supports additional capabilities beyond basic research. See the [Deep Research documentation](https://ai.google.dev/gemini-api/docs/deep-research) for full details and code examples:

- **Collaborative planning** Review and refine the agent's research plan before execution (`collaborative_planning: true` in `agent_config`)
- **Native visualization** Generate charts and infographics inline with research reports (`visualization: "auto"` in `agent_config`)
- **MCP integration** Connect to private data sources and specialized tools via remote MCP servers
- **File search** Search over uploaded files and connected file stores
- **Multimodal inputs** Ground research with PDFs, CSVs, images, audio, and video

### Streaming

#### Python
```python
from google import genai

client = genai.Client()

stream = client.interactions.create(
    model="gemini-3-flash-preview",
    input="Explain quantum entanglement in simple terms.",
    stream=True
)

for chunk in stream:
    if chunk.event_type == "content.delta":
        if chunk.delta.type == "text":
            print(chunk.delta.text, end="", flush=True)
    elif chunk.event_type == "interaction.complete":
        print(f"\n\nTotal Tokens: {chunk.interaction.usage.total_tokens}")
```

#### JavaScript/TypeScript
```typescript
import { GoogleGenAI } from "@google/genai";

const client = new GoogleGenAI({});

const stream = await client.interactions.create({
    model: "gemini-3-flash-preview",
    input: "Explain quantum entanglement in simple terms.",
    stream: true,
});

for await (const chunk of stream) {
    if (chunk.event_type === "content.delta") {
        if (chunk.delta.type === "text" && "text" in chunk.delta) {
            process.stdout.write(chunk.delta.text);
        }
    } else if (chunk.event_type === "interaction.complete") {
        console.log(`\n\nTotal Tokens: ${chunk.interaction.usage.total_tokens}`);
    }
}
```


## Data Model

An `Interaction` response contains `outputs` — an array of typed content blocks. Each block has a `type` field:

- `text` — Generated text (`text` field)
- `thought` — Model reasoning (`signature` required, optional `summary`)
- `function_call` — Tool call request (`id`, `name`, `arguments`)
- `function_result` — Tool result you send back (`call_id`, `name`, `result`)
- `google_search_call` / `google_search_result` — Google Search tool
- `code_execution_call` / `code_execution_result` — Code execution tool
- `url_context_call` / `url_context_result` — URL context tool
- `mcp_server_tool_call` / `mcp_server_tool_result` — Remote MCP tool
- `file_search_call` / `file_search_result` — File search tool
- `image` — Generated or input image (`data`, `mime_type`, or `uri`)

**Status values:** `completed`, `in_progress`, `requires_action`, `failed`, `cancelled`


## Key Differences from generateContent

- `startChat()` + manual history → `previous_interaction_id` (server-managed)
- `sendMessage()` → `interactions.create(previous_interaction_id=...)`
- `response.text` → `interaction.outputs[-1].text`
- No background execution → `background=True` for async tasks
- No agent access → `agent="deep-research-preview-04-2026"` or `agent="deep-research-max-preview-04-2026"`


## Important Notes

- Interactions are **stored by default** (`store=true`). Paid tier retains for 55 days, free tier for 1 day.
- Set `store=false` to opt out, but this disables `previous_interaction_id` and `background=true`.
- `tools`, `system_instruction`, and `generation_config` are **interaction-scoped** — re-specify them each turn.
- **Agents require** `background=True`.
- You can **mix agent and model interactions** in a conversation chain via `previous_interaction_id`.


## Documentation Lookup

### When MCP is Installed (Preferred)

If the **`search_documentation`** tool (from the Google MCP server) is available, use it as your **only** documentation source:

1. Call `search_documentation` with your query
2. Read the returned documentation
2. **Trust MCP results** as source of truth for API details — they are always up-to-date.

> [!IMPORTANT]
> When MCP tools are present, **never** fetch URLs manually. MCP provides up-to-date, indexed documentation that is more accurate and token-efficient than URL fetching.

### When MCP is NOT Installed (Fallback Only)

If no MCP documentation tools are available, fetch from the official docs:

- [Interactions Full Documentation](https://ai.google.dev/gemini-api/docs/interactions.md.txt)
- [Deep Research Full Documentation](https://ai.google.dev/gemini-api/docs/deep-research.md.txt)

These pages cover function calling, built-in tools (Google Search, code execution, URL context, file search, computer use), remote MCP, structured output, thinking configuration, working with files, multimodal understanding and generation, streaming events, and more.