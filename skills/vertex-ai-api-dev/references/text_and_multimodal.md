# Text and Multimodal Generation

## Basic Text Generation
```python
from google import genai

client = genai.Client()
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="How does AI work?"
)
print(response.text)
```

## Chat (Multi-turn conversations)
```python
from google import genai
from google.genai.types import ModelContent, Part, UserContent

client = genai.Client()
chat_session = client.chats.create(
    model="gemini-3-flash-preview",
    history=[
        UserContent(parts=[Part.from_text(text="Hello")]),
        ModelContent(parts=[Part.from_text(text="Great to meet you. What would you like to know?")]),
    ],
)
response = chat_session.send_message("Tell me a story.")
print(response.text)
```

## Multimodal Inputs (Images, Audio, Video)
You can provide files natively using Google Cloud Storage URIs or local bytes.

```python
from google import genai
from google.genai.types import Part

client = genai.Client()

gcs_image = Part.from_uri(file_uri="gs://cloud-samples-data/generative-ai/image/scones.jpg", mime_type="image/jpeg")

with open("local_image.jpg", "rb") as f:
    local_image = Part.from_bytes(data=f.read(), mime_type="image/jpeg")

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=[
        "Generate a list of all the objects contained in both images.",
        gcs_image,
        local_image,
    ],
)
print(response.text)
```

## Text Embeddings
```python
from google import genai
from google.genai.types import EmbedContentConfig

client = genai.Client()
response = client.models.embed_content(
    model="text-embedding-005",
    contents=[
        "How do I get a driver's license/learner's permit?",
        "How long is my driver's license valid for?",
    ],
    config=EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT", output_dimensionality=768),
)
print(response.embeddings)
```
