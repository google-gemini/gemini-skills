# Structured Output and Tools

## Structured Output (JSON Schema)
Force the model to return JSON matching a Pydantic schema or JSON schema.

```python
from google import genai
from google.genai.types import GenerateContentConfig
from pydantic import BaseModel

class Recipe(BaseModel):
    recipe_name: str
    ingredients: list[str]

client = genai.Client()
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="List a few popular cookie recipes.",
    config=GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=list[Recipe],
    ),
)
print(response.parsed) # Returns list of Recipe objects
```

## Function Calling
Let the model output function calls that you can execute.

```python
from google import genai
from google.genai.types import GenerateContentConfig

def get_current_weather(location: str) -> str:
    """Example method. Returns the current weather.
    Args: location: The city and state, e.g. San Francisco, CA
    """
    return "Sunny"

client = genai.Client()
response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="What is the weather like in Boston?",
    config=GenerateContentConfig(tools=[get_current_weather]),
)
print(response.text)
```

## Search Grounding
Ground the model's responses in Google Search or your own enterprise data (Vertex AI Search).

```python
from google import genai
from google.genai.types import GenerateContentConfig, GoogleSearch, Tool

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="When is the next total solar eclipse in the US?",
    config=GenerateContentConfig(
        tools=[Tool(google_search=GoogleSearch())],
    ),
)
print(response.text)
```

## Code Execution
Allow the model to run Python code to calculate answers precisely.

```python
from google import genai
from google.genai.types import GenerateContentConfig, Tool, ToolCodeExecution

client = genai.Client()

response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents="Calculate 20th fibonacci number.",
    config=GenerateContentConfig(
        tools=[Tool(code_execution=ToolCodeExecution())],
    ),
)
print(response.executable_code)
print(response.code_execution_result)
```
