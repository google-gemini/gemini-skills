---
name: gemini-nano-dev
description: Use this skill when building web applications or Chrome Extensions that use Chrome's built-in AI powered by Gemini Nano. Covers the Prompt API (LanguageModel), Summarizer API, Writer API, Rewriter API, Proofreader API, Language Detector API, and Translator API for client-side, on-device AI inference with no server required.
---

# Gemini Nano (Chrome Built-in AI) Development Skill

## Overview

Chrome's built-in AI APIs let you perform AI-powered tasks directly in the browser using the **Gemini Nano** model — no server-side deployment, no API keys, no network requests after the initial model download. All inference runs on-device.

Key capabilities:
- **Prompt API** — General-purpose text generation with the `LanguageModel` interface
- **Multimodal input** — Image and audio understanding via the Prompt API
- **Summarizer API** — One-click text summarization
- **Writer API** — Generate text for a specific purpose
- **Rewriter API** — Rewrite existing text with different tone or length
- **Proofreader API** — Grammar and spelling correction
- **Language Detector API** — Detect the language of input text
- **Translator API** — Translate text between languages
- **Structured output** — JSON Schema-constrained responses
- **Session management** — Multi-turn conversations with context tracking
- **Chrome Extensions** — All APIs work in extensions

> [!NOTE]
> Gemini Nano is a **client-side** model. No data is sent to Google or any third party when using the model. The network is only required for the initial model download.

---

## Critical Rules (Always Apply)

### Hardware Requirements

The Prompt API, Summarizer, Writer, Rewriter, and Proofreader APIs require:
- **OS**: Windows 10/11, macOS 13+ (Ventura+), Linux, or ChromeOS (Chromebook Plus)
- **Storage**: At least 22 GB free on the volume containing the Chrome profile
- **GPU or CPU**: GPU with >4 GB VRAM, OR CPU with 16+ GB RAM and 4+ cores
- **Network**: Unmetered connection (only for initial model download)

Language Detector and Translator APIs work on Chrome desktop without the above GPU/RAM requirements.

### Supported Languages

From Chrome 140, Gemini Nano supports **English**, **Spanish**, and **Japanese** for input and output text.

### TypeScript Support

Install TypeScript definitions:
```bash
npm install @types/dom-chromium-ai
```

---

## Quick Start

### 1. Check Model Availability

Always check if the model is ready before creating a session:

```javascript
const availability = await LanguageModel.availability({
  expectedInputs: [{ type: 'text', languages: ['en'] }],
  expectedOutputs: [{ type: 'text', languages: ['en'] }],
});

// Returns: "unavailable" | "downloadable" | "downloading" | "available"
```

### 2. Create a Session

```javascript
const session = await LanguageModel.create({
  monitor(m) {
    m.addEventListener('downloadprogress', (e) => {
      console.log(`Downloaded ${e.loaded * 100}%`);
    });
  },
});
```

> [!IMPORTANT]
> If the model isn't downloaded yet, the user must interact with the page first (click, tap, keypress) before `create()` can be triggered. Check `navigator.userActivation.isActive`.

### 3. Prompt the Model

#### Request-based (wait for full response)
```javascript
const result = await session.prompt('Explain quantum computing in simple terms.');
console.log(result);
```

#### Streaming (show partial results)
```javascript
const stream = session.promptStreaming('Write a poem about the ocean.');
for await (const chunk of stream) {
  process.stdout.write(chunk);
}
```

### 4. Stop a Prompt

```javascript
const controller = new AbortController();
stopButton.onclick = () => controller.abort();

const result = await session.prompt('Write a poem!', {
  signal: controller.signal,
});
```

---

## Prompt API Features

### System Prompts and Context

Use `initialPrompts` to set system instructions and conversation history:

```javascript
const session = await LanguageModel.create({
  initialPrompts: [
    { role: 'system', content: 'You are a helpful coding assistant.' },
    { role: 'user', content: 'What is the capital of France?' },
    { role: 'assistant', content: 'The capital of France is Paris.' },
  ],
});
```

### Response Prefix

Guide the model's response format with a prefix:

```javascript
const result = await session.prompt([
  { role: 'user', content: 'Create a JSON character sheet for a warrior' },
  { role: 'assistant', content: '```json\n', prefix: true },
]);
```

### Multimodal Input (Image + Audio)

```javascript
const session = await LanguageModel.create({
  expectedInputs: [
    { type: 'text', languages: ['en'] },
    { type: 'image' },
    { type: 'audio' },
  ],
  expectedOutputs: [{ type: 'text', languages: ['en'] }],
});

// Image input (supports Blob, HTMLImageElement, HTMLCanvasElement, etc.)
const imageBlob = await (await fetch('photo.jpg')).blob();
const result = await session.prompt([
  {
    role: 'user',
    content: [
      { type: 'text', value: 'Describe what you see in this image:' },
      { type: 'image', value: imageBlob },
    ],
  },
]);

// Audio input (supports AudioBuffer, ArrayBuffer, Blob, etc.)
const audioBuffer = await captureMicrophoneInput();
const audioResult = await session.prompt([
  {
    role: 'user',
    content: [
      { type: 'text', value: 'Transcribe this audio:' },
      { type: 'audio', value: audioBuffer },
    ],
  },
]);
```

> [!NOTE]
> Audio input requires a GPU. Supported input types: `AudioBuffer`, `ArrayBufferView`, `ArrayBuffer`, `Blob`. Image input supports: `HTMLImageElement`, `SVGImageElement`, `HTMLVideoElement`, `HTMLCanvasElement`, `ImageBitmap`, `OffscreenCanvas`, `VideoFrame`, `Blob`, `ImageData`.

### Structured Output (JSON Schema)

```javascript
const session = await LanguageModel.create();

const schema = {
  type: 'object',
  properties: {
    sentiment: { type: 'string', enum: ['positive', 'negative', 'neutral'] },
    confidence: { type: 'number' },
  },
  required: ['sentiment', 'confidence'],
};

const result = await session.prompt(
  'Analyze the sentiment: "This product is amazing, I love it!"',
  { responseConstraint: schema }
);
console.log(JSON.parse(result));
// { sentiment: "positive", confidence: 0.95 }
```

### Append Messages

Pre-populate context without triggering inference:

```javascript
const session = await LanguageModel.create({
  initialPrompts: [
    { role: 'system', content: 'You are a document analyst.' },
  ],
});

// Pre-load documents without generating a response
await session.append([
  {
    role: 'user',
    content: [
      { type: 'text', value: 'Here is a document to analyze: ...' },
    ],
  },
]);

// Now prompt with a question about the pre-loaded content
const analysis = await session.prompt('Summarize the key points.');
```

---

## Session Management

### Context Window Tracking

```javascript
console.log(`Context usage: ${session.contextUsage}/${session.contextWindow}`);
```

### Context Overflow Handling

```javascript
session.addEventListener('contextoverflow', () => {
  console.log('Context window exceeded — older messages will be dropped.');
});
```

### Clone a Session

```javascript
const clonedSession = await session.clone();
// Forked conversation preserves context and initial prompts
```

### Destroy a Session

```javascript
session.destroy();
// Frees resources. Session can no longer be used.
```

---

## Specialized APIs

### Summarizer API

```javascript
const summarizer = await Summarizer.create();
const summary = await summarizer.summarize(longText);
```

### Writer API

```javascript
const writer = await Writer.create();
const text = await writer.write('Write a professional email declining a meeting.');
```

### Rewriter API

```javascript
const rewriter = await Rewriter.create();
const rewritten = await rewriter.rewrite('make this more formal: hey can u help me');
```

### Proofreader API

```javascript
const proofreader = await Proofreader.create();
const corrected = await proofreader.proofread('teh quikc brown fox jumpd');
```

### Language Detector API

```javascript
const detector = await LanguageDetector.create();
const result = await detector.detect('Bonjour le monde');
// { detectedLanguage: 'fr', confidence: 0.99 }
```

### Translator API

```javascript
const translator = await Translator.create({
  sourceLanguage: 'en',
  targetLanguage: 'es',
});
const translated = await translator.translate('Hello, how are you?');
// "Hola, ¿cómo estás?"
```

---

## Chrome Extensions

All built-in AI APIs work in Chrome Extensions. For extensions using the Prompt API, you can customize model parameters:

```javascript
const params = await LanguageModel.params();
// { defaultTopK: 3, maxTopK: 128, defaultTemperature: 1, maxTemperature: 2 }

const session = await LanguageModel.create({
  temperature: params.defaultTemperature,
  topK: params.defaultTopK,
});
```

> [!NOTE]
> Remove the expired origin trial permission `"aiLanguageModelOriginTrial"` from your manifest if present.

---

## Enable on Localhost

1. Go to `chrome://flags/#optimization-guide-on-device-model` → **Enabled**
2. Go to `chrome://flags/#prompt-api-for-gemini-nano` → **Enabled** or **Enabled multilingual**
3. For multimodal input: `chrome://flags/#prompt-api-for-gemini-nano-multimodal-input` → **Enabled**
4. Restart Chrome
5. Verify: Open DevTools console, run `await LanguageModel.availability()`

---

## Best Practices

1. **Always check availability** before creating a session — the model may not be downloaded yet
2. **Inform users** about model download progress using the `monitor` callback
3. **Use streaming** for longer responses to provide immediate feedback
4. **Track context window usage** to handle overflow gracefully
5. **Destroy sessions** when no longer needed to free resources
6. **Use structured output** (JSON Schema) when you need parseable, predictable responses
7. **Prefer specialized APIs** (Summarizer, Writer, etc.) over the Prompt API for their specific tasks — they're optimized for those use cases
8. **Handle errors** — `QuotaExceededError` when context window is exceeded, `NotSupportedError` for unsupported modalities/languages
9. **Use `append()`** to pre-load context without triggering inference
10. **Test with real devices** — performance varies significantly across hardware

---

## Documentation Lookup

### Official Documentation

- [Get started with built-in AI](https://developer.chrome.com/docs/ai/get-started) — setup, requirements, model download
- [Prompt API](https://developer.chrome.com/docs/ai/prompt-api) — LanguageModel, multimodal, structured output
- [Session management](https://developer.chrome.com/docs/ai/session-management) — context window, cloning, destroying
- [Structured output](https://developer.chrome.com/docs/ai/structured-output-for-prompt-api) — JSON Schema constraints
- [Summarizer API](https://developer.chrome.com/docs/ai/summarizer-api) — text summarization
- [Writer API](https://developer.chrome.com/docs/ai/writer-api) — text generation
- [Rewriter API](https://developer.chrome.com/docs/ai/rewriter-api) — text rewriting
- [Proofreader API](https://developer.chrome.com/docs/ai/proofreader-api) — grammar correction
- [Language Detector API](https://developer.chrome.com/docs/ai/language-detection) — language detection
- [Translator API](https://developer.chrome.com/docs/ai/translator-api) — on-device translation
- [Cache models](https://developer.chrome.com/docs/ai/cache-models) — best practices for model caching
- [Debug Gemini Nano](https://developer.chrome.com/docs/ai/debug-gemini-nano) — troubleshooting
- [AI in Extensions](https://developer.chrome.com/docs/extensions/ai) — extension-specific guidance

### Demos

- [Prompt API Playground](https://chrome.dev/web-ai-demos/prompt-api-playground/)
- [Audio Prompt Demo](https://chrome.dev/web-ai-demos/mediarecorder-audio-prompt)
- [Image Prompt Demo](https://chrome.dev/web-ai-demos/canvas-image-prompt/)
- [Extension Sample](https://github.com/GoogleChrome/chrome-extensions-samples/tree/main/functional-samples/ai.gemini-on-device)
