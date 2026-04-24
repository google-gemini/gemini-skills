---
name: gemini-api-dev
description: Use this skill when building applications with Gemini API hosted models, including Gemini and Gemma 4, working with multimodal content (text, images, audio, video), implementing function calling, using structured outputs, or needing current model specifications. Covers SDK usage (google-genai for Python, @google/genai for JavaScript/TypeScript, com.google.genai:google-genai for Java, google.golang.org/genai for Go), model selection, and API capabilities.
---

# Gemini API Development Skill

## Overview

The Gemini API provides hosted access to Google's Gemini models and Gemma 4 models through the same SDKs and REST surface. Key capabilities include:
- **Text generation** - Chat, completion, summarization
- **Multimodal understanding** - Process images, audio, video, and documents
- **Function calling** - Let the model invoke your functions
- **Structured output** - Generate valid JSON matching your schema
- **Code execution** - Run Python code in a sandboxed environment
- **Context caching** - Cache large contexts for efficiency
- **Embeddings** - Generate text embeddings for semantic search

## Current Hosted Models

### Gemini
- `gemini-3-pro-preview`: 1M tokens, complex reasoning, coding, research
- `gemini-3-flash-preview`: 1M tokens, fast, balanced performance, multimodal
- `gemini-3-pro-image-preview`: 65k / 32k tokens, image generation and editing

### Gemma 4
- `gemma-4-31b-it`: instruction-tuned Gemma 4 model hosted via the Gemini API
- `gemma-4-26b-a4b-it`: instruction-tuned Gemma 4 model hosted via the Gemini API


> [!IMPORTANT]
> Models like `gemini-2.5-*`, `gemini-2.0-*`, `gemini-1.5-*` are legacy and deprecated. Prefer the current Gemini models above for Gemini work, and use the Gemma 4 model IDs above when the user specifically wants Gemma.

## SDKs

- **Python**: `google-genai` install with `pip install google-genai`
- **JavaScript/TypeScript**: `@google/genai` install with `npm install @google/genai`
- **Go**: `google.golang.org/genai` install with `go get google.golang.org/genai`
- **Java**:
  - groupId: `com.google.genai`, artifactId: `google-genai`
  - Latest version can be found here: https://central.sonatype.com/artifact/com.google.genai/google-genai/versions (let's call it `LAST_VERSION`) 
  - Install in `build.gradle`:
    ```
    implementation("com.google.genai:google-genai:${LAST_VERSION}")
    ```
  - Install Maven dependency in `pom.xml`:
    ```
    <dependency>
	    <groupId>com.google.genai</groupId>
	    <artifactId>google-genai</artifactId>
	    <version>${LAST_VERSION}</version>
	</dependency>
    ```

> [!WARNING]
> Legacy SDKs `google-generativeai` (Python) and `@google/generative-ai` (JS) are deprecated. Migrate to the new SDKs above urgently by following the Migration Guide.

## Quick Start

Gemma 4 uses the same authentication, SDKs, and REST endpoints as Gemini. In most cases, supporting Gemma means swapping the model ID and verifying the specific capability is available on that model.

### Python
```python
from google import genai

client = genai.Client()
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Explain quantum computing"
)
print(response.text)
```

### JavaScript/TypeScript
```typescript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI({});
const response = await ai.models.generateContent({
  model: "gemini-3-flash-preview",
  contents: "Explain quantum computing"
});
console.log(response.text);
```

### Go
```go
package main

import (
	"context"
	"fmt"
	"log"
	"google.golang.org/genai"
)

func main() {
	ctx := context.Background()
	client, err := genai.NewClient(ctx, nil)
	if err != nil {
		log.Fatal(err)
	}

	resp, err := client.Models.GenerateContent(ctx, "gemini-3-flash-preview", genai.Text("Explain quantum computing"), nil)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println(resp.Text)
}
```

### Java

```java
import com.google.genai.Client;
import com.google.genai.types.GenerateContentResponse;

public class GenerateTextFromTextInput {
  public static void main(String[] args) {
    Client client = new Client();
    GenerateContentResponse response =
        client.models.generateContent(
            "gemini-3-flash-preview",
            "Explain quantum computing",
            null);

    System.out.println(response.text());
  }
}
```

## Gemma 4 via Gemini API

Use this section when the user explicitly wants Gemma through the Gemini API rather than a Gemini model.

### What changes for Gemma

- Use a Gemma model ID such as `gemma-4-31b-it` or `gemma-4-26b-a4b-it`.
- Use the same API key flow, SDKs, file upload API, chat API, and `generateContent` endpoint as Gemini.
- Keep the existing Gemini API patterns for system instructions, multi-turn chat, function calling, and Google Search tools unless the model docs say otherwise.
- Verify capability support per model before relying on a specific feature.

### Gemma-specific notes

- Thinking is exposed as an on or off toggle. Enable it with `thinking_level="high"` in Python or `ThinkingLevel.HIGH` in JavaScript.
- Gemma 4 supports image understanding through the same uploaded-file flow used elsewhere in the Gemini API.
- When a user asks for Gemma, prefer showing Gemma model IDs in examples instead of Gemini model IDs.

### Basic example

#### Python
```python
from google import genai

client = genai.Client()

response = client.models.generate_content(
    model="gemma-4-26b-a4b-it",
    contents="Roses are red...",
)

print(response.text)
```

#### JavaScript/TypeScript
```typescript
import { GoogleGenAI } from "@google/genai";

const ai = new GoogleGenAI();

const response = await ai.models.generateContent({
  model: "gemma-4-26b-a4b-it",
  contents: "Roses are red...",
});
console.log(response.text);
```

### Thinking example

#### Python
```python
from google import genai
from google.genai import types

client = genai.Client()

response = client.models.generate_content(
    model="gemma-4-26b-a4b-it",
    contents="What is the water formula?",
    config=types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level="high")
    ),
)

print(response.text)
```

#### JavaScript/TypeScript
```typescript
import { GoogleGenAI, ThinkingLevel } from "@google/genai";

const ai = new GoogleGenAI();

const response = await ai.models.generateContent({
  model: "gemma-4-26b-a4b-it",
  contents: "What is the water formula?",
  config: {
    thinkingConfig: {
      thinkingLevel: ThinkingLevel.HIGH,
    },
  },
});
console.log(response.text);
```

### Doc references

- Gemini API quickstart: `https://ai.google.dev/gemini-api/docs/quickstart`
- Gemini API image understanding: `https://ai.google.dev/gemini-api/docs/image-understanding`
- Gemini API thinking: `https://ai.google.dev/gemini-api/docs/thinking`
- Gemma thinking: `https://ai.google.dev/gemma/docs/capabilities/thinking`
- Gemma image understanding: `https://ai.google.dev/gemma/docs/capabilities/vision/image`

## API spec (source of truth)

> [!IMPORTANT]
> Gemini and Gemma 4 share the same Gemini API surface, but do not assume every Gemini feature is available on every Gemma model. Verify model-specific support before implementing a capability.

**Always use the latest REST API discovery spec as the source of truth for API definitions** (request/response schemas, parameters, methods). Fetch the spec when implementing or debugging API integration:

- **v1beta** (default): `https://generativelanguage.googleapis.com/$discovery/rest?version=v1beta`  
  Use this unless the integration is explicitly pinned to v1. The official SDKs (google-genai, @google/genai, google.golang.org/genai) target v1beta.
- **v1**: `https://generativelanguage.googleapis.com/$discovery/rest?version=v1`  
  Use only when the integration is specifically set to v1.

When in doubt, use v1beta. Refer to the spec for exact field names, types, and supported operations.

## How to use the Gemini API

For detailed API documentation, fetch from the official docs index:

**llms.txt URL**: `https://ai.google.dev/gemini-api/docs/llms.txt`

This index contains links to all documentation pages in `.md.txt` format. Use web fetch tools to:

1. Fetch `llms.txt` to discover available documentation pages
2. Fetch specific pages (e.g., `https://ai.google.dev/gemini-api/docs/function-calling.md.txt`)

### Key Documentation Pages 

> [!IMPORTANT]
> Those are not all the documentation pages. Use the `llms.txt` index to discover available documentation pages

- [Models](https://ai.google.dev/gemini-api/docs/models.md.txt)
- [Google AI Studio quickstart](https://ai.google.dev/gemini-api/docs/ai-studio-quickstart.md.txt)
- [Nano Banana image generation](https://ai.google.dev/gemini-api/docs/image-generation.md.txt)
- [Function calling with the Gemini API](https://ai.google.dev/gemini-api/docs/function-calling.md.txt)
- [Structured outputs](https://ai.google.dev/gemini-api/docs/structured-output.md.txt)
- [Text generation](https://ai.google.dev/gemini-api/docs/text-generation.md.txt)
- [Image understanding](https://ai.google.dev/gemini-api/docs/image-understanding.md.txt)
- [Embeddings](https://ai.google.dev/gemini-api/docs/embeddings.md.txt)
- [Interactions API](https://ai.google.dev/gemini-api/docs/interactions.md.txt)
- [SDK migration guide](https://ai.google.dev/gemini-api/docs/migrate.md.txt)

## Gemini Live API

For real-time, bidirectional audio/video/text streaming with the Gemini Live API, install the **`google-gemini/gemini-live-api-dev`** skill. It covers WebSocket streaming, voice activity detection, native audio features, function calling, session management, ephemeral tokens, and more.