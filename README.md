# Gemini API skills

A library of skills for the Gemini API, SDK and model interactions.

## About

LLMs have fixed knowledge, being trained at a specific point in time. Software
dev is fast paced and changes often, where new libraries are launched every day
and best practices evolve quickly.

This leaves a knowledge gap that language models can't solve on their own. For
example, models don't know about themselves when they're trained, and they
aren't necessarily aware of subtle changes in best practices (like [thought
circulation](https://ai.google.dev/gemini-api/docs/thought-signatures)) or SDK
changes.

[Skills](https://agentskills.io/) are a lightweight technique for adding
relevant context to your agents. This repo contains skills related to building
apps powered by the Gemini API.

### Performance

Our evaluations found that adding this skill improved an agent's ability to
generate correct API code following best practices to 87% with Gemini 3 Flash
and 96% with Gemini 3.1 Pro. For more details, see our blog post:
[Closing the knowledge gap with agent skills](https://developers.googleblog.com/closing-the-knowledge-gap-with-agent-skills/).

## Skills in this repo

> [!IMPORTANT]
> The `vertex-ai-api-dev` skill has moved to
> [skills/cloud/gemini-api](https://github.com/google/skills/tree/main/skills/cloud/gemini-api).

| Skill | Description |
| :--- | :--- |
| [`gemini-api-dev`](skills/gemini-api-dev) | Skill for developing Gemini-powered apps. Provides the best practices for building apps that use the Gemini API. |
| [`gemini-live-api-dev`](skills/gemini-live-api-dev) | Skill for building real-time, bidirectional streaming apps with the Gemini Live API. Covers WebSocket-based audio/video/text streaming, voice activity detection, native audio features, function calling, and session management. |
| [`gemini-interactions-api`](skills/gemini-interactions-api) | Skill for building apps with the [Gemini Interactions API](https://ai.google.dev/gemini-api/docs/interactions?ua=chat). Covers text generation, multi-turn chat, streaming, function calling, structured output, image generation, Deep Research agents, deprecated model guardrails, and both Python and TypeScript SDKs. |
| [`gemini-omni-flash-api`](skills/gemini-omni-flash-api) | Specialized generative AI video skill focused on video editing, image-referenced generation, and first-frame-to-video capabilities using the Interactions API. |

## Installation

You can install these skills across your preferred AI coding assistants and package managers:

### Using [Vercel skills CLI](https://skills.sh)

```sh
# Interactively browse and install skills.
npx skills add google-gemini/gemini-skills --list

# Install a specific skill (e.g., gemini-interactions-api).
npx skills add google-gemini/gemini-skills --skill gemini-interactions-api
```

### Using [Context7 skills CLI](https://context7.com)

```sh
# Interactively browse and install skills.
npx ctx7 skills install /google-gemini/gemini-skills

# Install a specific skill (e.g., gemini-interactions-api).
npx ctx7 skills install /google-gemini/gemini-skills gemini-interactions-api
```

### Antigravity

The Gemini skills come bundled with Antigravity, find them under
⚙️ → Customizations → Build with Google Plugins.

Or install through the AGY CLI:

```sh
# Install it directly
agy plugin install https://github.com/google-gemini/gemini-skills
```

### Claude Code

```sh
# Register the marketplace
/plugin marketplace add google-gemini/gemini-skills

# Install the plugin
/plugin install gemini-skills@gemini-skills
```

### Cursor

Install directly from the Cursor plugin directory or via the editor command:

```text
/add-plugin google-gemini/gemini-skills
```

### OpenAI Codex

```sh
# Add the marketplace source
codex plugin marketplace add https://github.com/google-gemini/gemini-skills

# Install the plugin
codex plugin install gemini-skills
```

## More info

You can find additional information about setting up your coding assistant with
Gemini API MCP and Skills in [the docs](https://ai.google.dev/gemini-api/docs/coding-agents).

## Disclaimer

This is not an officially supported Google product. This project is not
eligible for the [Google Open Source Software Vulnerability Rewards
Program](https://bughunters.google.com/open-source-security).
