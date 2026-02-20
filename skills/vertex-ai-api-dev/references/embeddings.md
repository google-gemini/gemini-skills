# Text Embeddings

Generate embeddings for text content to perform semantic search, clustering, and other NLP tasks.

## Basic Usage

```python
from google import genai
from google.genai import types

client = genai.Client()
response = client.models.embed_content(
    model="gemini-embedding-001",
    contents=[
        "How do I get a driver's license/learner's permit?",
        "How long is my driver's license valid for?",
    ],
    # Optional Parameters
    config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=768),
)
print(response.embeddings)
```