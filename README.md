# Gemini API skills

A library of skills for the Gemini API, SDK and model interactions.

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
