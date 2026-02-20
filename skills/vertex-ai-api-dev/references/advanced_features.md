# Advanced Features

## Content Caching
Cache large documents or contexts to reduce cost and latency.

```python
from google import genai
from google.genai.types import Content, CreateCachedContentConfig, Part

client = genai.Client()

content_cache = client.caches.create(
    model="gemini-3-flash-preview",
    config=CreateCachedContentConfig(
        contents=[
            Content(
                role="user",
                parts=[Part.from_uri(file_uri="gs://your-bucket/large.pdf", mime_type="application/pdf")]
            )
        ],
        system_instruction="You are an expert researcher.",
        display_name="example-cache",
        ttl="86400s",
    ),
)

# Use the cache
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Summarize the pdf",
    config={"cached_content": content_cache.name}
)
```

## Batch Prediction
For processing large datasets asynchronously.

```python
import time
from google import genai
from google.genai.types import CreateBatchJobConfig, JobState

client = genai.Client()

job = client.batches.create(
    model="gemini-3-flash-preview",
    src="gs://your-bucket/prompts.jsonl",
    config=CreateBatchJobConfig(dest="gs://your-bucket/outputs"),
)

completed_states = {JobState.JOB_STATE_SUCCEEDED, JobState.JOB_STATE_FAILED, JobState.JOB_STATE_CANCELLED}
while job.state not in completed_states:
    time.sleep(30)
    job = client.batches.get(name=job.name)
```

## Thinking (Reasoning Mode)
Let the model "think" before responding to complex logic tasks.

```python
from google import genai
from google.genai.types import GenerateContentConfig, ThinkingConfig

client = genai.Client()
response = client.models.generate_content(
    model="gemini-3-pro-preview",
    contents="solve x^2 + 4x + 4 = 0",
    config=GenerateContentConfig(
        thinking_config=ThinkingConfig(include_thoughts=True, thinking_budget=1024)
    ),
)

for part in response.candidates[0].content.parts:
    if part.thought:
        print(f"Thought: {part.text}")
    else:
        print(f"Final Answer: {part.text}")
```
