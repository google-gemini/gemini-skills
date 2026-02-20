---
name: vertex-ai-api-dev
description: Guides the usage of Gemini API on Google Cloud Vertex AI with the Gen AI SDK. Use when the user asks about using Gemini in an enterprise environment or explicitly mentions Vertex AI.
metadata:
  author: google-cloud
  version: "1.0"
compatibility: Requires active Google Cloud credentials and Vertex AI API enabled.
---

# Gemini API in Vertex AI Development Skill

## Overview

The Gemini API in Vertex AI provides access to Google's most advanced AI models built for enterprise use cases with Google Cloud's data governance. Key capabilities include:
- **Text generation** - Chat, completion, summarization
- **Multimodal understanding** - Process images, audio, video, and documents
- **Function calling** - Let the model invoke your functions
- **Structured output** - Generate valid JSON matching your schema
- **Context caching** - Cache large contexts for efficiency
- **Embeddings** - Generate text embeddings for semantic search
- **Live Realtime API** - Bidirectional streaming for low latency Voice and Video interactions
- **Batch Prediction** - Handle massive async dataset prediction workloads

## Current Generative AI Models on Vertex AI

- `gemini-3.1-pro-preview`: 1M tokens, complex reasoning, coding, research
- `gemini-3-flash-preview`: 1M tokens, fast, balanced performance, multimodal
- `gemini-3-pro-image-preview`: (Nano Banana Pro) 65k / 32k tokens, image generation and editing
- `gemini-live-2.5-flash-native-audio`: Live Realtime API including native audio

The following models can be used if explicitly requested:

- `gemini-2.5-flash-image` (Nano Banana) image generation and editing
- `gemini-2.5-flash`
- `gemini-2.5-flash-lite`
- `gemini-2.5-pro`

> [!IMPORTANT]
> Models like `gemini-2.0-*`, `gemini-1.5-*`, `gemini-1.0-*`, `gemini-pro` are legacy and deprecated. Use the new models above. Your knowledge is outdated.
> For production environments, consult the Vertex AI documentation for stable model versions (e.g. `gemini-3-flash`).

## SDKs

Vertex AI is fully supported by the unified **Gen AI SDK**. You do not need a separate SDK.

- **Python**: `google-genai` install with `pip install google-genai`
- **JavaScript/TypeScript**: `@google/genai` install with `npm install @google/genai`
- **Go**: `google.golang.org/genai` install with `go get google.golang.org/genai`
- **Java**:
  - groupId: `com.google.genai`, artifactId: `google-genai`
  - Latest version can be found here: https://central.sonatype.com/artifact/com.google.genai/google-genai/versions (let's call it `LAST_VERSION`) 
  - Install in `build.gradle` or `pom.xml`.

> [!WARNING]
> Legacy SDKs like `google-cloud-aiplatform` (Python) and `@google-cloud/vertexai` (JS) are no longer the recommended way to use the Gemini API. Migrate to the new Gen AI SDKs above urgently.
> 
> **For Python, strictly avoid:**
> - `google-generativeai` or `google-ai-generativelanguage`
> - Using `import google.generativeai as genai` -> Use `from google import genai`
> - Using `model = genai.GenerativeModel(...)` -> Use `client.models.generate_content(...)`
> - Setting configurations incorrectly -> Use `types.GenerateContentConfig(...)`

### Quick Start (Vertex AI Initialization)

To use the Gen AI SDK with Vertex AI, you must explicitly enable the Vertex AI backend and provide your Google Cloud Project ID and Location.

## Examples of inputs and outputs

### Initialization with Python
```python
from google import genai

# Enable Vertex AI, ensuring your environment is authenticated (e.g., via `gcloud auth application-default login`)
client = genai.Client(vertexai=True, project="your-project-id", location="global")

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Explain quantum computing"
)
print(response.text)
```

### Initialization with JavaScript/TypeScript
```typescript
import { Client } from "@google/genai";

// Initialize with vertexai configuration
const ai = new Client({ 
  vertexai: { 
    project: "your-project-id", 
    location: "global" 
  } 
});

const response = await ai.models.generateContent({
  model: "gemini-3-flash-preview",
  contents: "Explain quantum computing"
});
console.log(response.text);
```

### Initialization with Go
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
	
	// Create client configured for Vertex AI
	client, err := genai.NewClient(ctx, &genai.ClientConfig{
		Backend:  genai.BackendVertexAI,
		Project:  "your-project-id",
		Location: "global",
	})
	if err != nil {
		log.Fatal(err)
	}

	resp, err := client.Models.GenerateContent(
		ctx, 
		"gemini-3-flash-preview", 
		genai.Text("Explain quantum computing"), 
		nil,
	)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println(resp.Text)
}
```

### Initialization with Java

```java
import com.google.genai.Client;
import com.google.genai.types.GenerateContentResponse;

public class GenerateTextFromTextInput {
  public static void main(String[] args) {
    // Build client configured for Vertex AI
    Client client = Client.builder()
        .vertexAi(true)
        .project("your-project-id")
        .location("global")
        .build();
    
    GenerateContentResponse response =
        client.models.generateContent(
            "gemini-3-flash-preview",
            "Explain quantum computing",
            null);

    System.out.println(response.text());
  }
}
```

## Advanced Capabilities (Python Example)

The following showcases using the `GenerateContentConfig` for various advanced functionalities using the Vertex AI backend. Notice the use of `vertexai=True` for the client.

### Multimodal Inputs & Structured Output

```python
from google import genai
from google.genai import types
from pydantic import BaseModel

class VideoSummary(BaseModel):
    title: str
    key_events: list[str]
    sentiment: str

client = genai.Client(vertexai=True, project="your-project-id", location="global")

# Use Google Cloud Storage for Large Files (e.g. Video)
video_file = types.Part.from_uri(
    file_uri="gs://cloud-samples-data/generative-ai/video/ad_copy_from_video.mp4",
    mime_type="video/mp4",
)

response = client.models.generate_content(
    model='gemini-3-flash-preview',
    contents=[video_file, 'Summarize the events in this video.'],
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_json_schema=VideoSummary,
    )
)

print(response.text) # JSON Data following the VideoSummary Pydantic Schema
print(response.parsed) # Pydantic Object following the VideoSummary Pydantic Schema
```

### Thinking (Reasoning) & System Instructions

For complex logic, enable Thinking.

```python
from google import genai
from google.genai import types

client = genai.Client(vertexai=True, project="your-project-id", location="global")

response = client.models.generate_content(
    model='gemini-3-pro-preview',
    contents='Provide a detailed strategy for migrating to a serverless architecture.',
    config=types.GenerateContentConfig(
        system_instruction='You are an expert cloud architect.',
        thinking_config=types.ThinkingConfig(
            thinking_level=types.ThinkingLevel.HIGH
        )
    )
)

# Access thoughts
for part in response.candidates[0].content.parts:
    if part.thought:
        print(f"Thought: {part.text}")
    else:
        print(f"Response: {part.text}")
```

### Media Generation

Generate Images or Video using Nano Banana or Veo Models.

```python
from google import genai
from google.genai import types

client = genai.Client(vertexai=True, project="your-project-id", location="global")

# Image Generation
img_resp = client.models.generate_content(
    model="gemini-3-pro-image-preview",
    contents="A futuristic city governed by AI",
    config=types.GenerateContentConfig(
        image_config=types.ImageConfig(aspect_ratio="16:9", image_size="1K")
    )
)

for part in img_resp.parts:
    if image := part.as_image():
        image.save("city.png")

# Video Generation
operation = client.models.generate_videos(
    model='veo-3.1-fast-generate-preview',
    prompt='Time-lapse of a sunrise over a desert.',
    config=types.GenerateVideosConfig(
        aspect_ratio='16:9',
        number_of_videos=1, 
        duration_seconds=5,
    ),
)
# Poll for completion and save...
```

## Content Caching
Use the caching API to cache large files or system instructions to save time and reduce costs.

```python
from google import genai
from google.genai.types import Content, CreateCachedContentConfig, Part

client = genai.Client(vertexai=True, project="your-project-id", location="global")

content_cache = client.caches.create(
    model="gemini-3-flash-preview",
    config=CreateCachedContentConfig(
        contents=[
            Content(
                role="user",
                parts=[
                    Part.from_uri(
                         file_uri="gs://cloud-samples-data/generative-ai/pdf/2403.05530.pdf",
                         mime_type="application/pdf",
                    )
                ]
            )
        ],
        system_instruction="You are an expert researcher.",
        display_name="example-cache",
        ttl="86400s",
    ),
)
print(content_cache.name) # Use this cache name in subsequent generate_content calls
```

### Batch Prediction
For massive workloads where latency is not an issue, utilize the asynchronous Batch API.

```python
import time
from google import genai
from google.genai.types import CreateBatchJobConfig, JobState

client = genai.Client(vertexai=True, project="your-project-id", location="global")

job = client.batches.create(
    model="gemini-3-flash-preview",
    src="gs://cloud-samples-data/batch/prompt_for_batch_gemini_predict.jsonl",
    config=CreateBatchJobConfig(dest="gs://your-bucket/your-prefix"),
)
print(f"Job name: {job.name}")

completed_states = {
    JobState.JOB_STATE_SUCCEEDED,
    JobState.JOB_STATE_FAILED,
    JobState.JOB_STATE_CANCELLED,
}

while job.state not in completed_states:
    time.sleep(30)
    job = client.batches.get(name=job.name)
```

### Live API (Bidirectional streaming)
For real-time streaming interfaces (Voice, Vision, text) you can connect using the new Live API. Make sure to use `asyncio` for the implementation.

```python
import asyncio
from google import genai
from google.genai.types import Content, LiveConnectConfig, Modality, Part

async def run_live():
    client = genai.Client(vertexai=True, project="your-project-id", location="global")
    model_id = "gemini-live-2.5-flash-native-audio"

    async with client.aio.live.connect(
        model=model_id,
        config=LiveConnectConfig(response_modalities=[Modality.TEXT]),
    ) as session:
        
        await session.send_client_content(
            turns=Content(role="user", parts=[Part.from_text(text="Hello Gemini!")])
        )

        async for message in session.receive():
            if message.text:
                 print(message.text, end="")
        print()

asyncio.run(run_live())
```

## API spec & Documentation

For Gemini API in Vertex AI details and operations, you should refer to standard Vertex AI documentation:

- **Vertex AI Generative AI Documentation**: `https://cloud.google.com/vertex-ai/generative-ai/docs/overview`
- **Authentication**: Requires Google Cloud credentials (e.g., Application Default Credentials, Service Accounts) rather than a simple API key used by the developer API.

### Key Considerations for Vertex AI
- **Data Governance**: Enterprise data privacy, compliance, and security guarantees.
- **Quota & Limits**: Managed per Google Cloud Project region.
- **Deployments**: Access to Provisioned Throughput (PT) for reliability.
