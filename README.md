# Gemini API skills

A library of skills for the Gemini API, SDK and model interactions.

## About

LLMs have fixed knowledge, being trained at a specific point in time. Software
dev is fast paced and changes often, where new libraries are launched every day
and best practices evolve quickly.

This leaves a knowledge gap that language models can't solve on their own. For
example, models don't know about themselves when they're trained, and they
aren't necessarily aware of subtle changes in best practices (like [thought
circulation](https://ai.google.dev/gemini-api/docs/thinking#signatures)) or SDK
changes.

[Skills](https://agentskills.io/) are a lightweight technique for adding
relevant context to your agents. This repo contains skills related to building
apps powered by the Gemini API.

### Performance

Our evaluations found that adding this skill improved an agent's ability to
generate correct API code following best practices to 87% with Gemini 3 Flash
and 96% with Gemini 3 Pro.

## Skills in this repo

| Skill | Description |
| :--- | :--- |
| [`gemini-api-dev`](skills/gemini-api-dev) | Skill for developing Gemini-powered apps. Provides the best practices for building apps that use the Gemini API. |
| [`vertex-ai-api-dev`](skills/vertex-ai-api-dev) | Skill for developing Gemini-powered apps on Google Cloud Vertex AI using the Gen AI SDK. Covers tools, multimodal generation, caching, and batch prediction. |
| [`gemini-live-api-dev`](skills/gemini-live-api-dev) | Skill for building real-time, bidirectional streaming apps with the Gemini Live API. Covers WebSocket-based audio/video/text streaming, voice activity detection, native audio features, function calling, and session management. |
| [`gemini-interactions-api`](skills/gemini-interactions-api) | Skill for building apps with the [Gemini Interactions API](https://ai.google.dev/gemini-api/docs/interactions?ua=chat). Covers text generation, multi-turn chat, streaming, function calling, structured output, image generation, Deep Research agents, deprecated model guardrails, and both Python and TypeScript SDKs. |

## Installation

You can browse and install skills using either the [Vercel skills CLI](https://skills.sh) or the [Context7 skills CLI](https://context7.com).

### Using [Vercel skills CLI](https://skills.sh)

```sh
# Interactively browse and install skills.
npx skills add google-gemini/gemini-skills --list

# Install a specific skill (e.g., gemini-api-dev).
npx skills add google-gemini/gemini-skills --skill gemini-api-dev --global
```

### Using [Context7 skills CLI](https://context7.com)

```sh
# Interactively browse and install skills.
npx ctx7 skills install /google-gemini/gemini-skills

# Install a specific skill (e.g., vertex-ai-api-dev).
npx ctx7 skills install /google-gemini/gemini-skills vertex-ai-api-dev
```

## Gemini Docs MCP

Gemini hosts a public Model Context Protocol (MCP) server at
`https://gemini-api-docs-mcp.dev`. Connecting your coding agent to this server ensures that
all queries have access to the latest APIs, code updates, and optimal configuration examples.

Run the following command in your agent's terminal or project root to install
the server:

    npx add-mcp "https://gemini-api-docs-mcp.dev"

This server adds a `search_documentation` function that your agent can use to
retrieve real-time API definitions and integration patterns from the official
Gemini documentation files.

## More Installation Documentation

You can find additional information about setting up your coding assistant with Gemini MCP and Skills here: https://ai.google.dev/gemini-api/docs/coding-agents

## Disclaimer

This is not an officially supported Google product. This project is not
eligible for the [Google Open Source Software Vulnerability Rewards
Program](https://bughunters.google.com/open-source-security).
