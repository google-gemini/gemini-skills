---
name: gemini-live-api-dev
description: Use this skill when building real-time, bidirectional streaming applications with the Gemini Live API. Covers WebSocket-based audio/video/text streaming, voice activity detection (VAD), native audio features, function calling, session management, ephemeral tokens for client-side auth, and all Live API configuration options. SDKs covered - google-genai (Python), @google/genai (JavaScript/TypeScript).
---

# Gemini Live API Development Skill

## Overview

The Live API enables **low-latency, real-time voice and video interactions** with Gemini over WebSockets. It processes continuous streams of audio, video, or text to deliver immediate, human-like spoken responses.

Key capabilities:
- **Bidirectional audio streaming** — real-time mic-to-speaker conversations
- **Video streaming** — send camera/screen frames alongside audio
- **Text input/output** — send and receive text within a live session
- **Audio transcriptions** — get text transcripts of both input and output audio
- **Voice Activity Detection (VAD)** — automatic interruption handling
- **Native audio** — affective dialog, proactive audio, thinking
- **Function calling** — synchronous and asynchronous tool use
- **Google Search grounding** — ground responses in real-time search results
- **Session management** — context compression, session resumption, GoAway signals
- **Ephemeral tokens** — secure client-side authentication

> [!NOTE]
> The Live API currently **only supports WebSockets**. For WebRTC support or simplified integration, use a [partner integration](#partner-integrations).

## Models

| Model | Description |
|-------|-------------|
| `gemini-2.5-flash-native-audio-preview-12-2025` | Native audio output, affective dialog, proactive audio, thinking. 128k context window. |
| `gemini-live-2.5-flash-preview` | Standard Live API model. 32k context window. |

> [!IMPORTANT]
> Use `gemini-2.5-flash-native-audio-preview-12-2025` for the best audio experience with native audio features. Use `gemini-live-2.5-flash-preview` for text-only responses from audio input.

## SDKs

- **Python**: `google-genai` — `pip install google-genai`
- **JavaScript/TypeScript**: `@google/genai` — `npm install @google/genai`

> [!WARNING]
> Legacy SDKs `google-generativeai` (Python) and `@google/generative-ai` (JS) are deprecated. Use the new SDKs above.

## Partner Integrations

To streamline the development of real-time audio and video apps, you can use a third-party integration that supports the Gemini Live API over **WebRTC** or **WebSockets**:

| Partner | Description |
|---------|-------------|
| [LiveKit](https://docs.livekit.io/agents/models/realtime/plugins/gemini/) | Use the Gemini Live API with LiveKit Agents. |
| [Pipecat by Daily](https://docs.pipecat.ai/guides/features/gemini-live) | Create a real-time AI chatbot using Gemini Live and Pipecat. |
| [Fishjam by Software Mansion](https://docs.fishjam.io/tutorials/gemini-live-integration) | Create live video and audio streaming applications with Fishjam. |
| [Vision Agents by Stream](https://visionagents.ai/integrations/gemini) | Build real-time voice and video AI applications with Vision Agents. |
| [Voximplant](https://voximplant.com/products/gemini-client) | Connect inbound and outbound calls to Live API with Voximplant. |
| [Firebase AI SDK](https://firebase.google.com/docs/ai-logic/live-api?api=dev) | Get started with the Gemini Live API using Firebase AI Logic. |

## Architecture: Server-to-Server vs Client-to-Server

| Approach | Description | Best For |
|----------|-------------|----------|
| **Server-to-server** | Backend connects to Live API via WebSocket. Client streams data to your server, which forwards it. | Production apps where you control the backend and want to keep API keys secure. |
| **Client-to-server** | Frontend connects directly to Live API via WebSocket, bypassing your backend. | Lower latency for audio/video. Use **ephemeral tokens** instead of API keys for security. |

> [!IMPORTANT]
> For client-to-server production deployments, always use [ephemeral tokens](#ephemeral-tokens) instead of standard API keys.

## Quick Start

### Python — Bidirectional Audio

```python
import asyncio
from google import genai
import pyaudio

client = genai.Client()

FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

pya = pyaudio.PyAudio()

MODEL = "gemini-2.5-flash-native-audio-preview-12-2025"
CONFIG = {
    "response_modalities": ["AUDIO"],
    "system_instruction": "You are a helpful and friendly AI assistant.",
}

audio_queue_output = asyncio.Queue()
audio_queue_mic = asyncio.Queue(maxsize=5)

async def listen_audio():
    mic_info = pya.get_default_input_device_info()
    stream = await asyncio.to_thread(
        pya.open, format=FORMAT, channels=CHANNELS,
        rate=SEND_SAMPLE_RATE, input=True,
        input_device_index=mic_info["index"],
        frames_per_buffer=CHUNK_SIZE,
    )
    while True:
        data = await asyncio.to_thread(stream.read, CHUNK_SIZE, exception_on_overflow=False)
        await audio_queue_mic.put({"data": data, "mime_type": "audio/pcm"})

async def send_audio(session):
    while True:
        msg = await audio_queue_mic.get()
        await session.send_realtime_input(audio=msg)

async def receive_audio(session):
    while True:
        turn = session.receive()
        async for response in turn:
            if response.server_content and response.server_content.model_turn:
                for part in response.server_content.model_turn.parts:
                    if part.inline_data and isinstance(part.inline_data.data, bytes):
                        audio_queue_output.put_nowait(part.inline_data.data)
        # Clear queue on interruption
        while not audio_queue_output.empty():
            audio_queue_output.get_nowait()

async def play_audio():
    stream = await asyncio.to_thread(
        pya.open, format=FORMAT, channels=CHANNELS,
        rate=RECEIVE_SAMPLE_RATE, output=True,
    )
    while True:
        data = await audio_queue_output.get()
        await asyncio.to_thread(stream.write, data)

async def run():
    async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
        print("Connected! Start speaking.")
        async with asyncio.TaskGroup() as tg:
            tg.create_task(send_audio(session))
            tg.create_task(listen_audio())
            tg.create_task(receive_audio(session))
            tg.create_task(play_audio())

if __name__ == "__main__":
    asyncio.run(run())
```

### JavaScript — Bidirectional Audio

```javascript
import { GoogleGenAI, Modality } from '@google/genai';
import mic from 'mic';
import Speaker from 'speaker';

const ai = new GoogleGenAI({});
const model = 'gemini-2.5-flash-native-audio-preview-12-2025';
const config = {
  responseModalities: [Modality.AUDIO],
  systemInstruction: "You are a helpful and friendly AI assistant.",
};

async function live() {
  const responseQueue = [];
  const audioQueue = [];
  let speaker;

  async function waitMessage() {
    while (responseQueue.length === 0) {
      await new Promise((resolve) => setImmediate(resolve));
    }
    return responseQueue.shift();
  }

  const session = await ai.live.connect({
    model, config,
    callbacks: {
      onopen: () => console.log('Connected to Gemini Live API'),
      onmessage: (message) => responseQueue.push(message),
      onerror: (e) => console.error('Error:', e.message),
      onclose: (e) => console.log('Closed:', e.reason),
    },
  });

  // Setup microphone (16kHz, 16-bit, mono)
  const micInstance = mic({ rate: '16000', bitwidth: '16', channels: '1' });
  const micInputStream = micInstance.getAudioStream();

  micInputStream.on('data', (data) => {
    session.sendRealtimeInput({
      audio: { data: data.toString('base64'), mimeType: "audio/pcm;rate=16000" }
    });
  });

  micInstance.start();
  console.log('Microphone started. Speak now...');
}

live().catch(console.error);
```

## Audio Formats

| Direction | Format | Sample Rate | Encoding |
|-----------|--------|-------------|----------|
| **Input** | Raw PCM, little-endian, 16-bit, mono | 16kHz (native, will resample others) | `audio/pcm;rate=16000` |
| **Output** | Raw PCM, little-endian, 16-bit, mono | 24kHz | — |

> [!NOTE]
> Always set the MIME type on input audio blobs (e.g. `audio/pcm;rate=16000`). The API will resample if a different rate is sent.

## Establishing a Connection

### Python

```python
import asyncio
from google import genai

client = genai.Client()
model = "gemini-2.5-flash-native-audio-preview-12-2025"
config = {"response_modalities": ["AUDIO"]}

async def main():
    async with client.aio.live.connect(model=model, config=config) as session:
        # Send and receive content...
        pass

asyncio.run(main())
```

### JavaScript

```javascript
import { GoogleGenAI, Modality } from '@google/genai';

const ai = new GoogleGenAI({});
const model = 'gemini-2.5-flash-native-audio-preview-12-2025';
const config = { responseModalities: [Modality.AUDIO] };

const session = await ai.live.connect({
  model, config,
  callbacks: {
    onopen: () => console.debug('Opened'),
    onmessage: (message) => console.debug(message),
    onerror: (e) => console.debug('Error:', e.message),
    onclose: (e) => console.debug('Close:', e.reason),
  },
});

// Send content...
session.close();
```

## Sending Input

> [!IMPORTANT]
> Use `send_realtime_input` / `sendRealtimeInput` for all real-time user input (audio, video, **and text**). This sends data via `BidiGenerateContentRealtimeInput` and is optimized for responsiveness. Use `send_client_content` / `sendClientContent` **only** for incremental conversation history updates (appending prior turns to context), not for sending new user messages.

> [!WARNING]
> Do **not** use `media` in `sendRealtimeInput`. Use the specific keys: `audio` for audio data, `video` for images/video frames, and `text` for text input.

### Realtime Audio Input

**Python:**
```python
await session.send_realtime_input(
    audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
)
```

**JavaScript:**
```javascript
session.sendRealtimeInput({
  audio: { data: base64Audio, mimeType: "audio/pcm;rate=16000" }
});
```

### Realtime Text Input

Send text to the model using `send_realtime_input` / `sendRealtimeInput`:

**Python:**
```python
await session.send_realtime_input(text="Hello, how are you?")
```

**JavaScript:**
```javascript
session.sendRealtimeInput({ text: 'Hello, how are you?' });
```

### Incremental Context Updates (Conversation History)

Use `send_client_content` / `sendClientContent` **only** to inject prior conversation history into the session context. All content sent this way is unconditionally appended to the conversation history and used as part of the prompt. This is useful for restoring session context or providing background turns — **not** for sending new user messages.

**Python:**
```python
turns = [
    {"role": "user", "parts": [{"text": "What is the capital of France?"}]},
    {"role": "model", "parts": [{"text": "Paris"}]},
]
await session.send_client_content(turns=turns, turn_complete=False)

turns = [{"role": "user", "parts": [{"text": "What about Germany?"}]}]
await session.send_client_content(turns=turns, turn_complete=True)
```

### Video Input

Stream video frames as JPEG images alongside audio using `send_realtime_input`:

**Python:**
```python
import base64

# Capture frame as JPEG bytes
await session.send_realtime_input(
    video=types.Blob(data=frame_bytes, mime_type="image/jpeg")
)
```

## Audio Transcriptions

Enable transcription of model output and/or user input audio.

### Output Transcription

**Python:**
```python
config = {
    "response_modalities": ["AUDIO"],
    "output_audio_transcription": {}
}

async with client.aio.live.connect(model=model, config=config) as session:
    async for response in session.receive():
        if response.server_content.output_transcription:
            print("Transcript:", response.server_content.output_transcription.text)
```

**JavaScript:**
```javascript
const config = {
  responseModalities: [Modality.AUDIO],
  outputAudioTranscription: {}
};
// In message handler:
if (turn.serverContent && turn.serverContent.outputTranscription) {
  console.log('Transcript:', turn.serverContent.outputTranscription.text);
}
```

### Input Transcription

**Python:**
```python
config = {
    "response_modalities": ["AUDIO"],
    "input_audio_transcription": {},
}

async for msg in session.receive():
    if msg.server_content.input_transcription:
        print('Transcript:', msg.server_content.input_transcription.text)
```

**JavaScript:**
```javascript
const config = {
  responseModalities: [Modality.AUDIO],
  inputAudioTranscription: {}
};
```

## Voice Configuration

Set a custom voice from the available TTS voices. Listen to all voices in [AI Studio](https://aistudio.google.com/app/live).

**Python:**
```python
config = {
    "response_modalities": ["AUDIO"],
    "speech_config": {
        "voice_config": {"prebuilt_voice_config": {"voice_name": "Kore"}}
    },
}
```

**JavaScript:**
```javascript
const config = {
  responseModalities: [Modality.AUDIO],
  speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: "Kore" } } }
};
```

> [!NOTE]
> Native audio output models automatically detect and switch languages. You cannot explicitly set a language code; specify language preferences in system instructions instead.

## Native Audio Capabilities

These features require `gemini-2.5-flash-native-audio-preview-12-2025`.

### Affective Dialog

Adapts response style to the input expression and tone. Requires `v1alpha` API version.

**Python:**
```python
client = genai.Client(http_options={"api_version": "v1alpha"})

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    enable_affective_dialog=True
)
```

**JavaScript:**
```javascript
const ai = new GoogleGenAI({ httpOptions: {"apiVersion": "v1alpha"} });

const config = {
  responseModalities: [Modality.AUDIO],
  enableAffectiveDialog: true
};
```

### Proactive Audio

Model intelligently decides when to respond (ignores irrelevant audio). Requires `v1alpha`.

**Python:**
```python
client = genai.Client(http_options={"api_version": "v1alpha"})

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    proactivity={'proactive_audio': True}
)
```

**JavaScript:**
```javascript
const ai = new GoogleGenAI({ httpOptions: {"apiVersion": "v1alpha"} });

const config = {
  responseModalities: [Modality.AUDIO],
  proactivity: { proactiveAudio: true }
};
```

### Thinking

The native audio model supports thinking (enabled by default). Control with `thinkingBudget`:

**Python:**
```python
config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    thinking_config=types.ThinkingConfig(
        thinking_budget=1024,       # Set to 0 to disable
        include_thoughts=True       # Optional: get thought summaries
    )
)
```

**JavaScript:**
```javascript
const config = {
  responseModalities: [Modality.AUDIO],
  thinkingConfig: {
    thinkingBudget: 1024,
    includeThoughts: true
  },
};
```

## Voice Activity Detection (VAD)

VAD detects when the user is speaking and handles interruptions automatically. When an interruption is detected, ongoing generation is cancelled and a `serverContent.interrupted` signal is sent.

### Handle Interruptions

**Python:**
```python
async for response in session.receive():
    if response.server_content.interrupted is True:
        # Stop playback, clear audio queue
        pass
```

**JavaScript:**
```javascript
if (turn.serverContent && turn.serverContent.interrupted) {
  // Stop playback, clear audio queue
}
```

### VAD Configuration

Fine-tune VAD sensitivity:

**Python:**
```python
from google.genai import types

config = {
    "response_modalities": ["TEXT"],
    "realtime_input_config": {
        "automatic_activity_detection": {
            "disabled": False,
            "start_of_speech_sensitivity": types.StartSensitivity.START_SENSITIVITY_LOW,
            "end_of_speech_sensitivity": types.EndSensitivity.END_SENSITIVITY_LOW,
            "prefix_padding_ms": 20,
            "silence_duration_ms": 100,
        }
    }
}
```

**JavaScript:**
```javascript
import { StartSensitivity, EndSensitivity } from '@google/genai';

const config = {
  responseModalities: [Modality.TEXT],
  realtimeInputConfig: {
    automaticActivityDetection: {
      disabled: false,
      startOfSpeechSensitivity: StartSensitivity.START_SENSITIVITY_LOW,
      endOfSpeechSensitivity: EndSensitivity.END_SENSITIVITY_LOW,
      prefixPaddingMs: 20,
      silenceDurationMs: 100,
    }
  }
};
```

### Audio Stream End

When mic is paused for > 1 second, send `audioStreamEnd` to flush cached audio:

**Python:**
```python
await session.send_realtime_input(audio_stream_end=True)
```

**JavaScript:**
```javascript
session.sendRealtimeInput({ audioStreamEnd: true });
```

### Manual VAD (Disable Automatic)

Disable automatic VAD and manage activity signals yourself:

**Python:**
```python
config = {
    "response_modalities": ["TEXT"],
    "realtime_input_config": {"automatic_activity_detection": {"disabled": True}},
}

await session.send_realtime_input(activity_start=types.ActivityStart())
await session.send_realtime_input(audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000"))
await session.send_realtime_input(activity_end=types.ActivityEnd())
```

**JavaScript:**
```javascript
const config = {
  responseModalities: [Modality.TEXT],
  realtimeInputConfig: {
    automaticActivityDetection: { disabled: true }
  }
};

session.sendRealtimeInput({ activityStart: {} });
session.sendRealtimeInput({ audio: { data: base64Audio, mimeType: "audio/pcm;rate=16000" } });
session.sendRealtimeInput({ activityEnd: {} });
```

## Function Calling (Tool Use)

### Supported Tools

| Tool | Supported |
|------|-----------|
| **Google Search** | ✅ |
| **Function calling** | ✅ |
| **Google Maps** | ❌ |
| **Code execution** | ❌ |
| **URL context** | ❌ |

> [!IMPORTANT]
> Unlike the `generateContent` API, the Live API does **not** support automatic tool response handling. You must handle tool responses manually.

### Synchronous Function Calling

**Python:**
```python
turn_on_the_lights = {"name": "turn_on_the_lights"}
turn_off_the_lights = {"name": "turn_off_the_lights"}

tools = [{"function_declarations": [turn_on_the_lights, turn_off_the_lights]}]
config = {"response_modalities": ["AUDIO"], "tools": tools}

async with client.aio.live.connect(model=model, config=config) as session:
    await session.send_realtime_input(text="Turn on the lights please")

    async for response in session.receive():
        if response.tool_call:
            function_responses = []
            for fc in response.tool_call.function_calls:
                function_responses.append(types.FunctionResponse(
                    id=fc.id, name=fc.name,
                    response={"result": "ok"}
                ))
            await session.send_tool_response(function_responses=function_responses)
```

**JavaScript:**
```javascript
const tools = [{ functionDeclarations: [
  { name: "turn_on_the_lights" },
  { name: "turn_off_the_lights" }
]}];

const config = { responseModalities: [Modality.AUDIO], tools };

// In message handler:
if (turn.toolCall) {
  const functionResponses = turn.toolCall.functionCalls.map(fc => ({
    id: fc.id, name: fc.name,
    response: { result: "ok" }
  }));
  session.sendToolResponse({ functionResponses });
}
```

### Asynchronous (Non-Blocking) Function Calling

Mark functions as `NON_BLOCKING` so conversation continues while the function executes:

**Python:**
```python
turn_on_the_lights = {"name": "turn_on_the_lights", "behavior": "NON_BLOCKING"}

# When responding, specify scheduling:
function_response = types.FunctionResponse(
    id=fc.id, name=fc.name,
    response={
        "result": "ok",
        "scheduling": "INTERRUPT"  # or "WHEN_IDLE" or "SILENT"
    }
)
```

**JavaScript:**
```javascript
import { Behavior, FunctionResponseScheduling } from '@google/genai';

const turn_on_the_lights = { name: "turn_on_the_lights", behavior: Behavior.NON_BLOCKING };

// When responding:
const functionResponse = {
  id: fc.id, name: fc.name,
  response: {
    result: "ok",
    scheduling: FunctionResponseScheduling.INTERRUPT  // or WHEN_IDLE or SILENT
  }
};
```

Scheduling options:
- **`INTERRUPT`** — Immediately tell the user about the result
- **`WHEN_IDLE`** — Wait until current generation finishes
- **`SILENT`** — Use the knowledge later in the conversation

### Google Search Grounding

**Python:**
```python
tools = [{'google_search': {}}]
config = {"response_modalities": ["AUDIO"], "tools": tools}
```

**JavaScript:**
```javascript
const tools = [{ googleSearch: {} }];
const config = { responseModalities: [Modality.AUDIO], tools };
```

### Combining Multiple Tools

```python
tools = [
    {"google_search": {}},
    {"function_declarations": [turn_on_the_lights, turn_off_the_lights]},
]
config = {"response_modalities": ["AUDIO"], "tools": tools}
```

## Session Management

### Session Limits

| Limit | Value |
|-------|-------|
| Audio-only session (no compression) | **15 minutes** |
| Audio+video session (no compression) | **2 minutes** |
| WebSocket connection lifetime | **~10 minutes** |
| Context window (native audio models) | **128k tokens** |
| Context window (other Live API models) | **32k tokens** |
| Session resumption token validity | **2 hours** |

### Context Window Compression

Enable sliding-window compression for unlimited session duration:

**Python:**
```python
from google.genai import types

config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    context_window_compression=types.ContextWindowCompressionConfig(
        sliding_window=types.SlidingWindow(),
    ),
)
```

**JavaScript:**
```javascript
const config = {
  responseModalities: [Modality.AUDIO],
  contextWindowCompression: { slidingWindow: {} }
};
```

### Session Resumption

Survive WebSocket reconnections without losing session state:

**Python:**
```python
config = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    session_resumption=types.SessionResumptionConfig(
        handle=previous_session_handle  # None for new session
    ),
)

async with client.aio.live.connect(model=model, config=config) as session:
    async for message in session.receive():
        if message.session_resumption_update:
            update = message.session_resumption_update
            if update.resumable and update.new_handle:
                # Store new_handle for reconnection
                saved_handle = update.new_handle
```

**JavaScript:**
```javascript
const config = {
  responseModalities: [Modality.AUDIO],
  sessionResumption: { handle: previousSessionHandle }
};

// In message handler:
if (turn.sessionResumptionUpdate) {
  if (turn.sessionResumptionUpdate.resumable && turn.sessionResumptionUpdate.newHandle) {
    const newHandle = turn.sessionResumptionUpdate.newHandle;
    // Store for reconnection
  }
}
```

### GoAway Message

Server signals an impending connection termination:

**Python:**
```python
async for response in session.receive():
    if response.go_away is not None:
        print(f"Connection ending in: {response.go_away.time_left}")
        # Prepare to reconnect with session resumption
```

**JavaScript:**
```javascript
if (turn.goAway) {
  console.log('Time left:', turn.goAway.timeLeft);
}
```

### Generation Complete

Detect when the model finishes generating a response:

**Python:**
```python
async for response in session.receive():
    if response.server_content.generation_complete is True:
        # Generation is done
        pass
```

**JavaScript:**
```javascript
if (turn.serverContent && turn.serverContent.generationComplete) {
  // Generation is done
}
```

## Ephemeral Tokens

Ephemeral tokens provide secure, short-lived authentication for **client-to-server** Live API connections. They are the recommended way to authenticate browser and mobile clients.

> [!IMPORTANT]
> Ephemeral tokens only work with the Live API and require `v1alpha` API version for creation.

### How It Works

1. Client authenticates with your backend
2. Your backend requests an ephemeral token from the Gemini API
3. Backend sends the token to the client
4. Client uses the token like an API key for WebSocket connection

### Create an Ephemeral Token (Server-Side)

**Python:**
```python
import datetime

client = genai.Client(http_options={'api_version': 'v1alpha'})
now = datetime.datetime.now(tz=datetime.timezone.utc)

token = client.auth_tokens.create(
    config={
        'uses': 1,
        'expire_time': now + datetime.timedelta(minutes=30),
        'new_session_expire_time': now + datetime.timedelta(minutes=1),
        'http_options': {'api_version': 'v1alpha'},
    }
)
# Send token.name to the client
```

**JavaScript:**
```javascript
const client = new GoogleGenAI({});

const token = await client.authTokens.create({
  config: {
    uses: 1,
    expireTime: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
    newSessionExpireTime: new Date(Date.now() + 1 * 60 * 1000),
    httpOptions: { apiVersion: 'v1alpha' },
  },
});
// Send token.name to the client
```

### Lock Token to Configuration (Optional)

```python
token = client.auth_tokens.create(
    config={
        'uses': 1,
        'live_connect_constraints': {
            'model': 'gemini-2.5-flash-native-audio-preview-12-2025',
            'config': {
                'session_resumption': {},
                'temperature': 0.7,
                'response_modalities': ['AUDIO']
            }
        },
        'http_options': {'api_version': 'v1alpha'},
    }
)
```

### Use Token on Client

```javascript
const ai = new GoogleGenAI({ apiKey: token.name });

const session = await ai.live.connect({
  model: 'gemini-2.5-flash-native-audio-preview-12-2025',
  config: { responseModalities: [Modality.AUDIO] },
  callbacks: { ... },
});
```

> [!NOTE]
> Without using the SDK, pass ephemeral tokens via the `access_token` query parameter or in the HTTP `Authorization` header with the `Token` auth-scheme.

### Ephemeral Token Best Practices

- Set short `expire_time` values
- Always authenticate your own backend securely first
- Don't use ephemeral tokens for backend-to-Gemini connections (use API keys)
- Use `session_resumption` to reconnect within the same token's `expireTime` (works even with `uses: 1`)

## Media Resolution

Control input media resolution for bandwidth/quality tradeoff:

**Python:**
```python
config = {
    "response_modalities": ["AUDIO"],
    "media_resolution": types.MediaResolution.MEDIA_RESOLUTION_LOW,
}
```

**JavaScript:**
```javascript
import { MediaResolution } from '@google/genai';

const config = {
  responseModalities: [Modality.AUDIO],
  mediaResolution: MediaResolution.MEDIA_RESOLUTION_LOW,
};
```

## Token Usage

Monitor token consumption:

**Python:**
```python
async for message in session.receive():
    if message.usage_metadata:
        usage = message.usage_metadata
        print(f"Total tokens: {usage.total_token_count}")
        for detail in usage.response_tokens_details:
            match detail:
                case types.ModalityTokenCount(modality=modality, token_count=count):
                    print(f"{modality}: {count}")
```

**JavaScript:**
```javascript
if (turn.usageMetadata) {
  console.log('Total tokens:', turn.usageMetadata.totalTokenCount);
  for (const detail of turn.usageMetadata.responseTokensDetails) {
    console.log(detail);
  }
}
```

## Limitations

| Constraint | Detail |
|------------|--------|
| **Response modality** | Only `TEXT` **or** `AUDIO` per session — not both |
| **Audio-only session** | 15 min without compression |
| **Audio+video session** | 2 min without compression |
| **Connection lifetime** | ~10 min (use session resumption) |
| **Context window** | 128k tokens (native audio) / 32k tokens (standard) |
| **Code execution** | Not supported |
| **URL context** | Not supported |
| **Google Maps** | Not supported |

## Best Practices

1. **Use headphones** when testing mic audio to prevent echo/self-interruption
2. **Enable context window compression** for sessions longer than 15 minutes
3. **Implement session resumption** to handle connection resets gracefully
4. **Handle GoAway messages** to prepare for reconnection before termination
5. **Use ephemeral tokens** for any client-side deployments — never expose API keys in browsers
6. **Lock ephemeral tokens** to specific configurations to enforce system instructions server-side
7. **Send `audioStreamEnd`** when the mic is paused to flush cached audio
8. **Clear audio playback queues** on interruption signals to avoid stale audio playback
9. **Use `send_realtime_input`** for all real-time user input (audio, video, and text). Reserve `send_client_content` only for injecting conversation history into the context
10. **Use non-blocking function calls** for long-running operations so conversation continues

## Official Documentation Reference

For the most up-to-date information, fetch from these official docs:

- [Live API Overview](https://ai.google.dev/gemini-api/docs/live.md.txt)
- [Live API Capabilities Guide](https://ai.google.dev/gemini-api/docs/live-guide.md.txt)
- [Live API Tool Use](https://ai.google.dev/gemini-api/docs/live-tools.md.txt)
- [Session Management](https://ai.google.dev/gemini-api/docs/live-session.md.txt)
- [Ephemeral Tokens](https://ai.google.dev/gemini-api/docs/ephemeral-tokens.md.txt)
- [WebSockets API Reference](https://ai.google.dev/api/live)
- [REST API Discovery Spec (v1beta)](https://generativelanguage.googleapis.com/$discovery/rest?version=v1beta)

## Supported Languages

The Live API supports 70 languages including: English, Spanish, French, German, Italian, Portuguese, Chinese, Japanese, Korean, Hindi, Arabic, Russian, and many more. Native audio models automatically detect and switch languages.
