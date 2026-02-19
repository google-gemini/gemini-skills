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
relevent context to your agents. This repo contains skills related to building
apps powered by the Gemini API.

### Performance

Our evaluations found that adding this skill improved an agent's ability to
generate correct API code following best practices to 87% with Gemini 3 Flash
and 96% with Gemini 3 Pro.

## Installation

Install from this repository using `npx skills`.

```sh
# Show me what you got.
npx skills add google-gemini/gemini-skills --list

# Install a specific skill.
npx skills add google-gemini/gemini-skills --skill gemini-api-dev --global
```

Or use the Context7 skills CLI.

```sh
# Interactively browse and install skills.
npx ctx7 skills install /google-gemini/gemini-skills

# Install a specific skill.
npx ctx7 skills install /google-gemini/gemini-skills gemini-api-dev
```

## Skills in this repo

### gemini-api-dev

Skill for developing Gemini-powered apps. Provides the best practices for
building apps that use the Gemini API.

```sh
# Vercel skills
npx skills add google-gemini/gemini-skills --skill gemini-api-dev --global
```

```sh
# Context7 skills
npx ctx7 skills install /google-gemini/gemini-skills gemini-api-dev
```
### interactions-api

Skill for building interactive chat experiences with the Gemini Interactions API.
Provides best practices for managing conversation state and turn-based interactions.

```sh
npx skills add google-gemini/gemini-skills --skill interactions-api --global
```

## Disclaimer

This is not an officially supported Google product. This project is not
eligible for the [Google Open Source Software Vulnerability Rewards
Program](https://bughunters.google.com/open-source-security).
