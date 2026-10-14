---
name: gemini-structured-output-dev
description: Use this skill when you need consistent, type-safe JSON output from the Gemini API, and when to combine structured output with function calling for agent workflows. Covers schema design, when to use each approach, and practical Python and TypeScript examples.
---

# Gemini Structured Output & Function Calling Skill

## Overview

This skill helps you get predictable, type-safe responses from Gemini models. It covers when to use **Structured Output** (formatting the final response) vs **Function Calling** (taking actions during conversation), and how to combine both for advanced agent workflows.

## When to Use Structured Output vs Function Calling

| Feature | Primary Use Case | When to Use |
|---|---|---|
| **Structured Outputs** | Formatting the final response in a specific format (JSON schema) | You want the model's answer in a specific, predictable format. Use for data extraction, classification, or generating structured inputs for tools/APIs. |
| **Function Calling** | Taking action during conversation. The model calls functions/tools you provide. | The model needs to perform a task before providing a final answer. Use for scheduling, data retrieval, controlling devices, or any external action. |

### Key Distinction

- **Structured Output**: The model generates the final response directly in your desired format. No external execution needed.
- **Function Calling**: The model requests you to execute a function, then uses the result to generate its response.

## Combining Structured Output + Function Calling

**Preview: This feature is available only to Gemini 3 series models** (`gemini-3.8-flash`, `gemini-3.6-flash`, `gemini-3.5-flash-lite`, `gemini-3.5-flash`, `gemini-3.1-pro-preview`, `gemini-3.1-flash-lite`, `gemini-3-flash-preview`).

> **"For Gemini 3 series models, combine function calling with structured output for consistently formatted responses."**

When you need both:
1. The model to call a function/tool during the conversation
2. The final response to be formatted as structured JSON

You can configure both `tools` (for function calling) and `response_format` (for structured output) simultaneously. The model will:
- Generate function calls when needed during the conversation
- Output the final response adhering to your JSON schema

### When to Combine Both

Use this pattern when building agents that:
- Need to call an external API/function during processing
- Must return a consistent, parseable JSON response to the user
- Want to validate/transform data using the function result, then present it structured

**Do not use** if you only need one or the other — choose the feature that matches your primary need.

## Schema Design Best Practices

### Supported Types

Structured output supports a subset of JSON Schema. The following types are supported:

| Type | Description |
|---|---|
| `string` | Text value |
| `integer` | Whole number |
| `number` | Floating-point number |
| `boolean` | True/false value |
| `object` | JSON object with properties |
| `array` | JSON array |
| `enum` | Restricted set of string values |

### Recommended Schema Structure

```json
{
  "type": "object",
  "properties": {
    "field_name": {
      "type": "string",
      "description": "Description guiding the model"
    }
  },
  "required": ["field_name"],
  "additionalProperties": false
}
```

### Best Practices

1. **Use clear descriptions**: The `description` field on each property guides the model toward the expected value type and meaning.

2. **Strong typing**: Use specific types (`integer` vs `number`) to get correct value kinds.

3. **Mark required fields**: List required properties in the `required` array so the model knows which fields must be present.

4. **Disable `additionalProperties`**: Set `additionalProperties: false` if you want only the defined fields — this prevents unexpected keys.

5. **Keep schemas simple**: Complex schemas with many nested properties can reduce model quality. Start simple and add complexity only as needed.

6. **Validate client-side**: While output is syntactically correct JSON, always validate values in your application (type checks, range validation, etc.).

## Practical Examples

### Python: Structured Output Only

```python
from google import genai
from pydantic import BaseModel, Field

class Recipe(BaseModel):
    name: str = Field(description="Recipe name")
    prep_time_minutes: int = Field(description="Preparation time in minutes")
    ingredients: list[str] = Field(description="List of ingredient names")
    instructions: str = Field(description="Cooking instructions")

client = genai.Client()

prompt = """Extract the recipe from the following text.
Gradually beat in the dry ingredients until just combined. Finally, stir in the chocolate chips. Drop by rounded tablespoons onto ungreased baking sheets and bake for 9 to 11 minutes."""

interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input=prompt,
    response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema": Recipe.model_json_schema(),
    },
)

recipe = Recipe.model_validate_json(interaction.output_text)
print(f"Recipe: {recipe.name}")
print(f"Prep time: {recipe.prep_time_minutes} minutes")
print(f"Ingredients: {', '.join(recipe.ingredients)}")
print(f"Instructions: {recipe.instructions}")
```

### JavaScript/TypeScript: Structured Output Only

```typescript
import { GoogleGenAI } from "@google/genai";

const client = new GoogleGenAI({});

const schema = {
  type: "object",
  properties: {
    name: { type: "string", description: "Recipe name" },
    prepTimeMinutes: { type: "integer", description: "Preparation time in minutes" },
    ingredients: {
      type: "array",
      items: { type: "string" },
      description: "List of ingredient names",
    },
    instructions: { type: "string", description: "Cooking instructions" },
  },
  required: ["name", "ingredients"],
  additionalProperties: false,
};

const interaction = await client.interactions.create({
  model: "gemini-3.8-flash",
  input: `Extract the recipe from the following text.
Gradually beat in the dry ingredients until just combined. Finally, stir in the chocolate chips. Drop by rounded tablespoons onto ungreased baking sheets and bake for 9 to 11 minutes.`,
  response_format: {
    type: "text",
    mimeType: "application/json",
    schema,
  },
});

const recipe = interaction.output_text
  ? JSON.parse(interaction.output_text)
  : null;
console.log("Recipe:", recipe);
```

### Python: Structured Output + Function Calling Combined

```python
from google import genai
from pydantic import BaseModel, Field

# Schema for the final structured response
class SearchResult(BaseModel):
    query: str = Field(description="The search query used")
    results: list[str] = Field(description="List of result titles or URLs")
    total_found: int = Field(description="Total number of results found")

# Function declaration for web search
web_search_tool = {
    "type": "function",
    "name": "google_search",
    "description": "Search the web for information",
    "parameters": {
        "type": "object",
        "properties": {
            "query": {"type": "string", description: "Search query"},
        },
        "required": ["query"],
    },
}

client = genai.Client()

prompt = "Search for information about Gemini API best practices and return a structured summary."

interaction = client.interactions.create(
    model="gemini-3.8-flash",
    input=prompt,
    tools=[web_search_tool],
    response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema": SearchResult.model_json_schema(),
    },
)

# The interaction steps will include function_call steps, and the final response
# will adhere to the SearchResult schema
print(f"Search Result: {interaction.output_text}")
```

> **Note**: The exact behavior of how function call results feed into the structured output depends on the model's flow. In practice, you may need to handle function call execution and pass results back through the interaction loop.

### JavaScript/TypeScript: Structured Output + Function Calling Combined

```typescript
import { GoogleGenAI } from "@google/genai";

const client = new GoogleGenAI({});

const resultSchema = {
  type: "object",
  properties: {
    query: { type: "string", description: "The search query used" },
    results: {
      type: "array",
      items: { type: "string" },
      description: "List of result titles or URLs",
    },
    totalFound: { type: "integer", description: "Total number of results found" },
  },
  required: ["query", "results"],
  additionalProperties: false,
};

const webSearchTool = {
  type: "function",
  name: "google_search",
  description: "Search the web for information",
  parameters: {
    type: "object",
    properties: {
      query: { type: "string", description: "Search query" },
    },
    required: ["query"],
  },
};

const interaction = await client.interactions.create({
  model: "gemini-3.8-flash",
  input: "Search for information about Gemini API best practices and return a structured summary.",
  tools: [webSearchTool],
  response_format: {
    type: "text",
    mimeType: "application/json",
    schema: resultSchema,
  },
});

console.log("Structured result:", interaction.output_text);
```

## Common Pitfalls & How to Avoid Them

| Pitfall | Solution |
|---|---|
| **Schema too complex** | Start with minimal fields. Add properties only when needed. |
| **Missing descriptions** | Always include `description` on properties — the model uses these to understand expectations. |
| **Using `any` or loose types** | Use specific JSON Schema types (`integer`, `number`, `string`) for correct value kinds. |
| **Forgetting `additionalProperties: false`** | If you only want defined fields, set `additionalProperties: false` to prevent unexpected keys. |
| **Combining structured output + function calling on Gemini 2.x models** | This combination is only supported on Gemini 3 series models. Check your model string. |
| **Not validating output client-side** | Structured output guarantees valid JSON syntax, but values still need validation (type checks, range validation, etc.). |
| **Using deprecated model names** | Avoid `gemini-2.0-*`, `gemini-1.5-*`, `gemini-3.1-flash-image`. Use current models listed in the main `gemini-api-dev` skill. |

## Authoritative Documentation Links

**Must-read pages (fetch before writing code):**

- [Structured Output](https://ai.google.dev/gemini-api/docs/structured-output.md.txt) — Official guide, schema support, examples
- [Function Calling](https://ai.google.dev/gemini-api/docs/function-calling.md.txt) — Official guide, modes, best practices
- [Structured Outputs with Tools](https://ai.google.dev/gemini-api/docs/structured-output.md.txt) — Gemini 3 series: combining structured output with built-in tools
- [Interactions API Overview](https://ai.google.dev/gemini-api/docs/interactions-overview.md.txt) — Recommended API entry point
- [Migration Guide: generateContent → Interactions](https://ai.google.dev/gemini-api/docs/migrate-to-interactions.md.txt) — If switching from legacy API
- [Models](https://ai.google.dev/gemini-api/docs/models/gemini-3.8-flash) — Current model card with supported features

> **Important**: When MCP documentation tools are available, use `search_docs` to query these pages as your source of truth rather than manual URL fetching.

## SDK Requirements

- **Python**: `google-genai` >= `2.30.1` → `pip install -U google-genai`
- **JavaScript/TypeScript**: `@google/genai` >= `2.29.1` → `npm install @google/genai`

> **Note**: SDK versions >= 2.0.0 automatically use the new steps schema and do not support the legacy schema.

## Quick Reference: When to Use Which Feature

| Your Goal | Use This Feature |
|---|---|
| Generate JSON from a prompt (no tool use) | Structured Output only |
| Have model call an API/function during conversation | Function Calling only |
| Both: call a function AND return structured JSON | Structured Output + Function Calling (Gemini 3 series only) |
| Extract specific data from text (no tools) | Structured Output only |
| Interact with external systems (databases, APIs) | Function Calling only |
| Extract data then present it in a specific format | Combine both (Gemini 3 series) |

---
*This skill is intended to complement (not duplicate) the existing `gemini-api-dev` skill. While that skill covers broad API usage, this skill focuses specifically on the structured output and function calling patterns with practical, ready-to-use examples.*