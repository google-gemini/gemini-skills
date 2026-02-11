---
name: interactions-api
description: Use this skill when working with the Gemini Interactions API for building interactive chat experiences, managing conversation state, and implementing turn-based interactions with Gemini models. This is the preferred API over generateContent for improved state management and tool orchestration.
---

# Gemini Interactions API Skill

## Overview

The Interactions API (Beta) is a unified interface for interacting with Gemini models and agents. As an improved alternative to the `generateContent` API, it simplifies state management, tool orchestration, and long-running tasks. Key capabilities include:

- **Interactive Chat** - Build multi-turn conversations with automatic state management
- **State Management** - Maintain conversation context across interactions (stateful or stateless)
- **Turn-based Communication** - Structured request/response patterns
- **Session Handling** - Manage conversation sessions efficiently with interaction IDs
- **Multimodal Support** - Process text, images, audio, video, and documents

> **Note:** The Interactions API is currently in Beta. Features and schemas are subject to breaking changes.

## Quick Start

### Python
```python
import google.generativeai as genai

client = genai.Client()

# Simple interaction with text prompt
interaction = client.interactions.create(
    model="gemini-3-flash-preview",
    input="Tell me a short joke about programming."
)

print(interaction.outputs[-1].text)
```

### JavaScript/TypeScript
```typescript
import { GoogleGenAI } from "@google/genai";

const client = new GoogleGenAI({});

// Simple interaction with text prompt
const interaction = await client.interactions.create({
    model: "gemini-3-flash-preview",
    input: "Tell me a short joke about programming."
});

console.log(interaction.outputs[interaction.outputs.length - 1].text);
```

## Multi-turn Conversations

### Stateful Conversation (Recommended)

The Interactions API automatically manages conversation state by using interaction IDs. Pass the `previous_interaction_id` to continue a conversation:

#### Python
```python
from google import genai

client = genai.Client()

# First turn
interaction1 = client.interactions.create(
    model="gemini-3-flash-preview",
    input="Hi, my name is Phil."
)
print(f"Model: {interaction1.outputs[-1].text}")

# Second turn (referencing previous interaction)
interaction2 = client.interactions.create(
    model="gemini-3-flash-preview",
    input="What is my name?",
    previous_interaction_id=interaction1.id
)
print(f"Model: {interaction2.outputs[-1].text}")
```

#### JavaScript/TypeScript
```typescript
import { GoogleGenAI } from "@google/genai";

const client = new GoogleGenAI({});

// First turn
const interaction1 = await client.interactions.create({
    model: "gemini-3-flash-preview",
    input: "Hi, my name is Phil."
});
console.log(`Model: ${interaction1.outputs[interaction1.outputs.length - 1].text}`);

// Second turn (referencing previous interaction)
const interaction2 = await client.interactions.create({
    model: "gemini-3-flash-preview",
    input: "What is my name?",
    previous_interaction_id: interaction1.id
});
console.log(`Model: ${interaction2.outputs[interaction2.outputs.length - 1].text}`);
```

### Stateless Conversation

You can also manage conversation history manually on the client side:

#### Python
```python
from google import genai

client = genai.Client()

conversation_history = [
    {
        "role": "user",
        "content": "What are the three largest cities in Spain?"
    }
]

interaction1 = client.interactions.create(
    model="gemini-3-flash-preview",
    input=conversation_history
)

print(f"Model: {interaction1.outputs[-1].text}")

# Add to conversation history
conversation_history.append({"role": "model", "content": interaction1.outputs})
conversation_history.append({
    "role": "user",
    "content": "What is the most famous landmark in the second one?"
})

interaction2 = client.interactions.create(
    model="gemini-3-flash-preview",
    input=conversation_history
)

print(f"Model: {interaction2.outputs[-1].text}")
```

#### JavaScript/TypeScript
```typescript
import { GoogleGenAI } from "@google/genai";

const client = new GoogleGenAI({});

const conversationHistory = [
    {
        role: "user",
        content: "What are the three largest cities in Spain?"
    }
];

const interaction1 = await client.interactions.create({
    model: "gemini-3-flash-preview",
    input: conversationHistory
});

console.log(`Model: ${interaction1.outputs[interaction1.outputs.length - 1].text}`);

// Add to conversation history
conversationHistory.push({ role: "model", content: interaction1.outputs });
conversationHistory.push({
    role: "user",
    content: "What is the most famous landmark in the second one?"
});

const interaction2 = await client.interactions.create({
    model: "gemini-3-flash-preview",
    input: conversationHistory
});

console.log(`Model: ${interaction2.outputs[interaction2.outputs.length - 1].text}`);
```

## Retrieving Past Interactions

Using the interaction ID, you can retrieve previous turns of the conversation:

#### Python
```python
# Retrieve previous interaction
previous_interaction = client.interactions.get("<YOUR_INTERACTION_ID>")
print(previous_interaction)

# Include original input in response
interaction = client.interactions.get(
    "<YOUR_INTERACTION_ID>",
    include_input=True
)
print(f"Input: {interaction.input}")
print(f"Output: {interaction.outputs}")
```

#### JavaScript/TypeScript
```typescript
// Retrieve previous interaction
const previous_interaction = await client.interactions.get("<YOUR_INTERACTION_ID>");
console.log(previous_interaction);

// Include original input in response
const interaction = await client.interactions.get(
    "<YOUR_INTERACTION_ID>",
    { include_input: true }
);
console.log(`Input: ${JSON.stringify(interaction.input)}`);
console.log(`Output: ${JSON.stringify(interaction.outputs)}`);
```

## Multimodal Capabilities

The Interactions API supports multimodal inputs including images, audio, video, and documents:

### Image Understanding

#### Python
```python
from google import genai
client = genai.Client()

interaction = client.interactions.create(
    model="gemini-3-flash-preview",
    input=[
        {"type": "text", "text": "Describe the image."},
        {
            "type": "image",
            "uri": "YOUR_URL",
            "mime_type": "image/png"
        }
    ]
)
print(interaction.outputs[-1].text)
```

#### JavaScript/TypeScript
```typescript
import { GoogleGenAI } from "@google/genai";

const client = new GoogleGenAI({});

const interaction = await client.interactions.create({
    model: "gemini-3-flash-preview",
    input: [
        { type: "text", text: "Describe the image." },
        {
            type: "image",
            uri: "YOUR_URL",
            mime_type: "image/png"
        }
    ]
});
console.log(interaction.outputs[interaction.outputs.length - 1].text);
```

## Resources

- [Official Interactions API Documentation](https://ai.google.dev/gemini-api/docs/interactions)
- [Interactions API Quickstart Notebook](https://colab.sandbox.google.com/github/google-gemini/cookbook/blob/main/quickstarts/Get_started_interactions_api.ipynb)
- [API Reference](https://ai.google.dev/api/interactions-api)
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs/llms.txt)

## Best Practices

1. **Use Stateful Conversations**: Leverage `previous_interaction_id` for automatic state management instead of manually tracking history
2. **Handle Storage**: Interaction objects are saved by default (`store=true`). Be mindful of data retention policies
3. **Error Handling**: Implement robust error handling for network and API issues
4. **Rate Limiting**: Be mindful of API rate limits in interactive scenarios
5. **Beta Considerations**: The API is in Beta and subject to breaking changes

## Common Use Cases

- Multi-turn chatbots with context awareness
- Interactive assistants with session management
- Conversational interfaces with multimodal inputs
- Context-aware Q&A systems
- Document analysis and understanding
- Image, audio, and video processing workflows

## Data Storage

> **Important:** Interaction objects are saved by default to enable state management features and background execution. See the [Data Storage and Retention](https://ai.google.dev/gemini-api/docs/interactions#data-storage-retention) documentation for details on retention periods and how to delete stored data or opt out.

---

For more details, refer to the [official documentation](https://ai.google.dev/gemini-api/docs/interactions).