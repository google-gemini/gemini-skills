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

- `gemini-2.5-flash-native-audio-preview-12-2025` — Native audio output, affective dialog, proactive audio, thinking. 128k context window. **This is the recommended model for all Live API use cases.**

> [!WARNING]
> The following Live API models are **deprecated** and will be shut down. Migrate to `gemini-2.5-flash-native-audio-preview-12-2025`.
> - `gemini-live-2.5-flash-preview` — Released June 17, 2025. Shutdown: December 9, 2025.
> - `gemini-2.0-flash-live-001` — Released April 9, 2025. Shutdown: December 9, 2025.

## SDKs

- **Python**: `google-genai` — `pip install google-genai`
- **JavaScript/TypeScript**: `@google/genai` — `npm install @google/genai`

> [!WARNING]
> Legacy SDKs `google-generativeai` (Python) and `@google/generative-ai` (JS) are deprecated. Use the new SDKs above.

## Partner Integrations

To streamline the development of real-time audio and video apps, you can use a third-party integration that supports the Gemini Live API over **WebRTC** or **WebSockets**:

- [LiveKit](https://docs.livekit.io/agents/models/realtime/plugins/gemini/) — Use the Gemini Live API with LiveKit Agents.
- [Pipecat by Daily](https://docs.pipecat.ai/guides/features/gemini-live) — Create a real-time AI chatbot using Gemini Live and Pipecat.
- [Fishjam by Software Mansion](https://docs.fishjam.io/tutorials/gemini-live-integration) — Create live video and audio streaming applications with Fishjam.
- [Vision Agents by Stream](https://visionagents.ai/integrations/gemini) — Build real-time voice and video AI applications with Vision Agents.
- [Voximplant](https://voximplant.com/products/gemini-client) — Connect inbound and outbound calls to Live API with Voximplant.
- [Firebase AI SDK](https://firebase.google.com/docs/ai-logic/live-api?api=dev) — Get started with the Gemini Live API using Firebase AI Logic.

## Implementation Approaches

There are two ways to connect to the Live API:

1. **Using the google-genai SDK** — The SDK handles WebSocket management, serialization, and provides a high-level API. This is the recommended approach.
2. **Using raw WebSockets** — Connect directly to the WebSocket endpoint for maximum control or when using a language without an official SDK.

> [!IMPORTANT]
> Use `send_realtime_input` / `sendRealtimeInput` for all real-time user input (audio, video, **and text**). This sends data via `BidiGenerateContentRealtimeInput` and is optimized for responsiveness. Use `send_client_content` / `sendClientContent` **only** for incremental conversation history updates (appending prior turns to context), not for sending new user messages.

> [!WARNING]
> Do **not** use `media` in `sendRealtimeInput`. Use the specific keys: `audio` for audio data, `video` for images/video frames, and `text` for text input.

## Audio Formats

- **Input**: Raw PCM, little-endian, 16-bit, mono. 16kHz native (will resample others). MIME type: `audio/pcm;rate=16000`
- **Output**: Raw PCM, little-endian, 16-bit, mono. 24kHz sample rate.

---

# Using the google-genai SDK

## Authentication

Authentication is handled by providing an API key when initializing the Gemini client.

* {Python}

    ```python
    from google import genai

    client = genai.Client(api_key="YOUR_API_KEY")
    ```

* {JavaScript}

    ```js
    import { GoogleGenAI } from '@google/genai';

    const ai = new GoogleGenAI({ apiKey: 'YOUR_API_KEY' });
    ```

## Connecting to the Live API

To start a live session, use the connection method with a model name and configuration.

* {Python}

    ```python
    from google.genai import types

    async def start_session():
        config = types.LiveConnectConfig(
            response_modalities=[types.Modality.AUDIO],
            system_instruction=types.Content(
                parts=[types.Part(text="You are a helpful assistant.")]
            )
        )
        
        async with client.aio.live.connect(model="gemini-2.5-flash-native-audio-preview-12-2025", config=config) as session:
            # Session is now active
            pass
    ```

* {JavaScript}

    ```js
    const session = await ai.live.connect({
      model: 'gemini-2.5-flash-native-audio-preview-12-2025',
      config: {
        responseModalities: ['audio'],
        systemInstruction: {
          parts: [{ text: 'You are a helpful assistant.' }]
        }
      },
      callbacks: {
        onopen: () => { console.log('Connected'); },
        onmessage: (response) => { console.log('Message:', response); },
        onerror: (error) => { console.error('Error:', error); },
        onclose: () => { console.log('Closed'); }
      }
    });
    ```

## Sending Text

Text can be sent using `send_realtime_input` (Python) or `sendRealtimeInput` (JavaScript).

* {Python}

    ```python
    await session.send_realtime_input(text="Hello, how are you?")
    ```

* {JavaScript}

    ```js
    session.sendRealtimeInput({
      text: 'Hello, how are you?'
    });
    ```

## Sending Audio

Audio needs to be sent as raw PCM data (raw 16-bit PCM audio, 16kHz, little-endian).

* {Python}

    ```python
    # Assuming 'chunk' is your raw PCM audio bytes
    await session.send_realtime_input(
        audio=types.Blob(
            data=chunk, 
            mime_type="audio/pcm;rate=16000"
        )
    )
    ```

* {JavaScript}

    ```js
    // Assuming 'chunk' is a Buffer of raw PCM audio
    session.sendRealtimeInput({
      audio: {
        data: chunk.toString('base64'),
        mimeType: 'audio/pcm;rate=16000'
      }
    });
    ```

## Sending Video

Video frames are sent as individual images (e.g., JPEG or PNG) at a specific frame rate (e.g., 1 frame per second).

* {Python}

    ```python
    # Assuming 'frame' is your JPEG-encoded image bytes
    await session.send_realtime_input(
        video=types.Blob(
            data=frame, 
            mime_type="image/jpeg"
        )
    )
    ```

* {JavaScript}

    ```js
    // Assuming 'frame' is a Buffer of JPEG-encoded image data
    session.sendRealtimeInput({
      video: {
        data: frame.toString('base64'),
        mimeType: 'image/jpeg'
      }
    });
    ```

## Receiving Audio

The model's audio responses are received as chunks of data.

* {Python}

    ```python
    async for response in session.receive():
        if response.server_content and response.server_content.model_turn:
            for part in response.server_content.model_turn.parts:
                if part.inline_data:
                    audio_data = part.inline_data.data
                    # Process or play the audio data
    ```

* {JavaScript}

    ```js
    // Inside the onmessage callback
    const content = response.serverContent;
    if (content?.modelTurn?.parts) {
      for (const part of content.modelTurn.parts) {
        if (part.inlineData) {
          const audioData = part.inlineData.data;
          // Process or play audioData (base64 encoded string)
        }
      }
    }
    ```

## Receiving Text

Transcriptions for both user input and model output are available in the server content.

* {Python}

    ```python
    async for response in session.receive():
        content = response.server_content
        if content:
            if content.input_transcription:
                print(f"User: {content.input_transcription.text}")
            if content.output_transcription:
                print(f"Gemini: {content.output_transcription.text}")
    ```

* {JavaScript}

    ```js
    // Inside the onmessage callback
    const content = response.serverContent;
    if (content?.inputTranscription) {
      console.log('User:', content.inputTranscription.text);
    }
    if (content?.outputTranscription) {
      console.log('Gemini:', content.outputTranscription.text);
    }
    ```

## Handling Tool Calls

The API supports tool calling (function calling). When the model requests a tool call, you must execute the function and send the response back.

* {Python}

    ```python
    async for response in session.receive():
        if response.tool_call:
            function_responses = []
            for fc in response.tool_call.function_calls:
                # 1. Execute the function locally
                result = my_tool_function(**fc.args)
                
                # 2. Prepare the response
                function_responses.append(types.FunctionResponse(
                    name=fc.name,
                    id=fc.id,
                    response={"result": result}
                ))
            
            # 3. Send the tool response back to the session
            await session.send_tool_response(function_responses=function_responses)
    ```

* {JavaScript}

    ```js
    // Inside the onmessage callback
    if (response.toolCall) {
      const functionResponses = [];
      for (const fc of response.toolCall.functionCalls) {
        const result = myToolFunction(fc.args);
        functionResponses.push({
          name: fc.name,
          id: fc.id,
          response: { result }
        });
      }
      session.sendToolResponse({ functionResponses });
    }
    ```

## Incremental Context Updates (Conversation History)

Use `send_client_content` / `sendClientContent` **only** to inject prior conversation history into the session context. All content sent this way is unconditionally appended to the conversation history and used as part of the prompt. This is useful for restoring session context or providing background turns — **not** for sending new user messages.

* {Python}

    ```python
    turns = [
        {"role": "user", "parts": [{"text": "What is the capital of France?"}]},
        {"role": "model", "parts": [{"text": "Paris"}]},
    ]
    await session.send_client_content(turns=turns, turn_complete=False)

    turns = [{"role": "user", "parts": [{"text": "What about Germany?"}]}]
    await session.send_client_content(turns=turns, turn_complete=True)
    ```

* {JavaScript}

    ```js
    let inputTurns = [
      { role: 'user', parts: [{ text: 'What is the capital of France?' }] },
      { role: 'model', parts: [{ text: 'Paris' }] },
    ];
    session.sendClientContent({ turns: inputTurns, turnComplete: false });

    inputTurns = [{ role: 'user', parts: [{ text: 'What about Germany?' }] }];
    session.sendClientContent({ turns: inputTurns, turnComplete: true });
    ```

---

# Using Raw WebSockets

## Authentication

Authentication is handled by including your API key as a query parameter in the WebSocket URL.

The endpoint format is:

```plaintext
wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key=YOUR_API_KEY
```

Replace `YOUR_API_KEY` with your actual API key.

## Authentication with Ephemeral Tokens

If you are using [ephemeral tokens](https://ai.google.dev/gemini-api/docs/ephemeral-tokens), you need to connect to the `v1alpha` endpoint. The ephemeral token needs to be passed as an `access_token` query parameter.

```plaintext
wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1alpha.GenerativeService.BidiGenerateContentConstrained?access_token={short-lived-token}
```

Replace `{short-lived-token}` with the actual ephemeral token.

## Connecting to the Live API

To start a live session, establish a WebSocket connection to the authenticated endpoint. The first message sent over the WebSocket must be a `LiveSessionRequest` containing the `config`. For the full configuration options, see the [Live API - WebSockets API reference](https://ai.google.dev/api/live).

* {Python}

    ```python
    import asyncio
    import websockets
    import json

    API_KEY = "YOUR_API_KEY"
    MODEL_NAME = "gemini-2.5-flash-native-audio-preview-12-2025"
    WS_URL = f"wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key={API_KEY}"

    async def connect_and_configure():
        async with websockets.connect(WS_URL) as websocket:
            print("WebSocket Connected")

            # 1. Send the initial configuration
            config_message = {
                "config": {
                    "model": f"models/{MODEL_NAME}",
                    "responseModalities": ["AUDIO"],
                    "systemInstruction": {
                        "parts": [{"text": "You are a helpful assistant."}]
                    }
                }
            }
            await websocket.send(json.dumps(config_message))
            print("Configuration sent")

            # Keep the session alive for further interactions
            await asyncio.sleep(3600)

    asyncio.run(connect_and_configure())
    ```

* {JavaScript}

    ```js
    const API_KEY = "YOUR_API_KEY";
    const MODEL_NAME = "gemini-2.5-flash-native-audio-preview-12-2025";
    const WS_URL = `wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent?key=${API_KEY}`;

    const websocket = new WebSocket(WS_URL);

    websocket.onopen = () => {
      console.log('WebSocket Connected');

      const configMessage = {
        config: {
          model: `models/${MODEL_NAME}`,
          responseModalities: ['AUDIO'],
          systemInstruction: {
            parts: [{ text: 'You are a helpful assistant.' }]
          }
        }
      };
      websocket.send(JSON.stringify(configMessage));
      console.log('Configuration sent');
    };

    websocket.onmessage = (event) => {
      const response = JSON.parse(event.data);
      console.log('Received:', response);
    };

    websocket.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };

    websocket.onclose = () => {
      console.log('WebSocket Closed');
    };
    ```

## Sending Text

To send text input, construct a `LiveSessionRequest` with the `realtimeInput` field populated with text.

* {Python}

    ```python
    async def send_text(websocket, text):
        text_message = {
            "realtimeInput": {
                "text": text
            }
        }
        await websocket.send(json.dumps(text_message))
    ```

* {JavaScript}

    ```js
    function sendTextMessage(text) {
      if (websocket.readyState === WebSocket.OPEN) {
        const textMessage = {
          realtimeInput: {
            text: text
          }
        };
        websocket.send(JSON.stringify(textMessage));
      }
    }
    ```

## Sending Audio

Audio should be sent as raw PCM data (raw 16-bit PCM audio, 16kHz, little-endian). Construct a `LiveSessionRequest` with the `realtimeInput` field, containing a `Blob` with the audio data.

* {Python}

    ```python
    import base64

    async def send_audio_chunk(websocket, chunk_bytes):
        encoded_data = base64.b64encode(chunk_bytes).decode('utf-8')
        audio_message = {
            "realtimeInput": {
                "audio": {
                    "data": encoded_data,
                    "mimeType": "audio/pcm;rate=16000"
                }
            }
        }
        await websocket.send(json.dumps(audio_message))
    ```

* {JavaScript}

    ```js
    function sendAudioChunk(chunk) {
      if (websocket.readyState === WebSocket.OPEN) {
        const audioMessage = {
          realtimeInput: {
            audio: {
              data: chunk.toString('base64'),
              mimeType: 'audio/pcm;rate=16000'
            }
          }
        };
        websocket.send(JSON.stringify(audioMessage));
      }
    }
    ```

## Sending Video

Video frames are sent as individual images (e.g., JPEG or PNG). Similar to audio, use `realtimeInput` with a `Blob`, specifying the correct `mimeType`.

* {Python}

    ```python
    import base64

    async def send_video_frame(websocket, frame_bytes, mime_type="image/jpeg"):
        encoded_data = base64.b64encode(frame_bytes).decode('utf-8')
        video_message = {
            "realtimeInput": {
                "video": {
                    "data": encoded_data,
                    "mimeType": mime_type
                }
            }
        }
        await websocket.send(json.dumps(video_message))
    ```

* {JavaScript}

    ```js
    function sendVideoFrame(frame, mimeType = 'image/jpeg') {
      if (websocket.readyState === WebSocket.OPEN) {
        const videoMessage = {
          realtimeInput: {
            video: {
              data: frame.toString('base64'),
              mimeType: mimeType
            }
          }
        };
        websocket.send(JSON.stringify(videoMessage));
      }
    }
    ```

## Receiving Responses

The WebSocket will send back `LiveSessionResponse` messages. You need to parse these JSON messages and handle different types of content.

* {Python}

    ```python
    async def receive_loop(websocket):
        async for message in websocket:
            response = json.loads(message)

            if "serverContent" in response:
                server_content = response["serverContent"]
                # Receiving Audio
                if "modelTurn" in server_content and "parts" in server_content["modelTurn"]:
                    for part in server_content["modelTurn"]["parts"]:
                        if "inlineData" in part:
                            audio_data_b64 = part["inlineData"]["data"]
                            # Process or play the base64 encoded audio data

                # Receiving Text Transcriptions
                if "inputTranscription" in server_content:
                    print(f"User: {server_content['inputTranscription']['text']}")
                if "outputTranscription" in server_content:
                    print(f"Gemini: {server_content['outputTranscription']['text']}")

            # Handling Tool Calls
            if "toolCall" in response:
                await handle_tool_call(websocket, response["toolCall"])
    ```

* {JavaScript}

    ```js
    websocket.onmessage = (event) => {
      const response = JSON.parse(event.data);

      if (response.serverContent) {
        const serverContent = response.serverContent;
        // Receiving Audio
        if (serverContent.modelTurn?.parts) {
          for (const part of serverContent.modelTurn.parts) {
            if (part.inlineData) {
              const audioData = part.inlineData.data; // Base64 encoded
              // Process or play audioData
            }
          }
        }

        // Receiving Text Transcriptions
        if (serverContent.inputTranscription) {
          console.log('User:', serverContent.inputTranscription.text);
        }
        if (serverContent.outputTranscription) {
          console.log('Gemini:', serverContent.outputTranscription.text);
        }
      }

      // Handling Tool Calls
      if (response.toolCall) {
        handleToolCall(response.toolCall);
      }
    };
    ```

## Handling Tool Calls

When the model requests a tool call, the `LiveSessionResponse` will contain a `toolCall` field. You must execute the function locally and send the result back via `toolResponse`.

* {Python}

    ```python
    async def handle_tool_call(websocket, tool_call):
        function_responses = []
        for fc in tool_call["functionCalls"]:
            result = my_tool_function(fc.get("args", {}))
            function_responses.append({
                "name": fc["name"],
                "id": fc["id"],
                "response": {"result": result}
            })

        tool_response_message = {
            "toolResponse": {
                "functionResponses": function_responses
            }
        }
        await websocket.send(json.dumps(tool_response_message))
    ```

* {JavaScript}

    ```js
    function handleToolCall(toolCall) {
      const functionResponses = [];
      for (const fc of toolCall.functionCalls) {
        const result = myToolFunction(fc.args || {});
        functionResponses.push({
          name: fc.name,
          id: fc.id,
          response: { result }
        });
      }

      if (websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({
          toolResponse: { functionResponses }
        }));
      }
    }
    ```

---

# Configuration Reference

## Voice Configuration

Set a custom voice from the available TTS voices. Listen to all voices in [AI Studio](https://aistudio.google.com/app/live).

* {Python}

    ```python
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Kore")
            )
        ),
    )
    ```

* {JavaScript}

    ```js
    const config = {
      responseModalities: ['AUDIO'],
      speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Kore' } } }
    };
    ```

> [!NOTE]
> Native audio output models automatically detect and switch languages. You cannot explicitly set a language code; specify language preferences in system instructions instead.

## Transcription Configuration

Enable transcription of model output and/or user input audio by adding these to the session config:

* {Python}

    ```python
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        output_audio_transcription=types.AudioTranscriptionConfig(),
        input_audio_transcription=types.AudioTranscriptionConfig(),
    )
    ```

* {JavaScript}

    ```js
    const config = {
      responseModalities: ['AUDIO'],
      outputAudioTranscription: {},
      inputAudioTranscription: {},
    };
    ```

## Native Audio Capabilities

These features require `gemini-2.5-flash-native-audio-preview-12-2025` and `v1alpha` API version.

### Affective Dialog

Adapts response style to the input expression and tone.

* {Python}

    ```python
    client = genai.Client(http_options={"api_version": "v1alpha"})

    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        enable_affective_dialog=True
    )
    ```

* {JavaScript}

    ```js
    const ai = new GoogleGenAI({ httpOptions: { apiVersion: 'v1alpha' } });

    const config = {
      responseModalities: ['AUDIO'],
      enableAffectiveDialog: true
    };
    ```

### Proactive Audio

Model intelligently decides when to respond (ignores irrelevant audio).

* {Python}

    ```python
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        proactivity={"proactive_audio": True}
    )
    ```

* {JavaScript}

    ```js
    const config = {
      responseModalities: ['AUDIO'],
      proactivity: { proactiveAudio: true }
    };
    ```

### Thinking

The native audio model supports thinking (enabled by default). Control with `thinkingBudget` (set to `0` to disable):

* {Python}

    ```python
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        thinking_config=types.ThinkingConfig(
            thinking_budget=1024,
            include_thoughts=True
        )
    )
    ```

* {JavaScript}

    ```js
    const config = {
      responseModalities: ['AUDIO'],
      thinkingConfig: { thinkingBudget: 1024, includeThoughts: true },
    };
    ```

## Voice Activity Detection (VAD)

VAD detects when the user is speaking and handles interruptions automatically. When an interruption is detected, ongoing generation is cancelled and a `serverContent.interrupted` signal is sent.

### Handling Interruptions

When interrupted, clear your audio playback queue:

* {Python}

    ```python
    async for response in session.receive():
        if response.server_content.interrupted is True:
            # Stop playback, clear audio queue
            pass
    ```

* {JavaScript}

    ```js
    if (response.serverContent?.interrupted) {
      // Stop playback, clear audio queue
    }
    ```

### VAD Configuration

Fine-tune VAD sensitivity:

* {Python}

    ```python
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        realtime_input_config=types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(
                disabled=False,
                start_of_speech_sensitivity=types.StartSensitivity.START_SENSITIVITY_LOW,
                end_of_speech_sensitivity=types.EndSensitivity.END_SENSITIVITY_LOW,
                prefix_padding_ms=20,
                silence_duration_ms=100,
            )
        )
    )
    ```

* {JavaScript}

    ```js
    import { StartSensitivity, EndSensitivity } from '@google/genai';

    const config = {
      responseModalities: ['AUDIO'],
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

* {Python}

    ```python
    await session.send_realtime_input(audio_stream_end=True)
    ```

* {JavaScript}

    ```js
    session.sendRealtimeInput({ audioStreamEnd: true });
    ```

### Manual VAD (Disable Automatic)

Disable automatic VAD and manage activity signals yourself:

* {Python}

    ```python
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        realtime_input_config=types.RealtimeInputConfig(
            automatic_activity_detection=types.AutomaticActivityDetection(disabled=True)
        )
    )

    await session.send_realtime_input(activity_start=types.ActivityStart())
    await session.send_realtime_input(audio=types.Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000"))
    await session.send_realtime_input(activity_end=types.ActivityEnd())
    ```

* {JavaScript}

    ```js
    session.sendRealtimeInput({ activityStart: {} });
    session.sendRealtimeInput({ audio: { data: base64Audio, mimeType: 'audio/pcm;rate=16000' } });
    session.sendRealtimeInput({ activityEnd: {} });
    ```

## Supported Tools

- **Google Search** — ✅ Supported
- **Function calling** — ✅ Supported (sync and async)
- **Google Maps** — ❌ Not supported
- **Code execution** — ❌ Not supported
- **URL context** — ❌ Not supported

> [!IMPORTANT]
> Unlike the `generateContent` API, the Live API does **not** support automatic tool response handling. You must handle tool responses manually.

### Asynchronous (Non-Blocking) Function Calling

Mark functions as `NON_BLOCKING` so conversation continues while the function executes:

* {Python}

    ```python
    turn_on_the_lights = {"name": "turn_on_the_lights", "behavior": "NON_BLOCKING"}

    # When responding, specify scheduling:
    function_response = types.FunctionResponse(
        id=fc.id, name=fc.name,
        response={"result": "ok", "scheduling": "INTERRUPT"}
        # scheduling options: "INTERRUPT", "WHEN_IDLE", "SILENT"
    )
    ```

* {JavaScript}

    ```js
    import { Behavior, FunctionResponseScheduling } from '@google/genai';

    const turn_on_the_lights = { name: 'turn_on_the_lights', behavior: Behavior.NON_BLOCKING };

    // When responding:
    const functionResponse = {
      id: fc.id, name: fc.name,
      response: { result: 'ok', scheduling: FunctionResponseScheduling.INTERRUPT }
      // scheduling options: INTERRUPT, WHEN_IDLE, SILENT
    };
    ```

Scheduling options:
- **`INTERRUPT`** — Immediately tell the user about the result
- **`WHEN_IDLE`** — Wait until current generation finishes
- **`SILENT`** — Use the knowledge later in the conversation

### Google Search Grounding

* {Python}

    ```python
    tools = [{'google_search': {}}]
    config = types.LiveConnectConfig(response_modalities=["AUDIO"], tools=tools)
    ```

* {JavaScript}

    ```js
    const tools = [{ googleSearch: {} }];
    const config = { responseModalities: ['AUDIO'], tools };
    ```

## Session Management

### Session Limits

- Audio-only session (no compression): **15 minutes**
- Audio+video session (no compression): **2 minutes**
- WebSocket connection lifetime: **~10 minutes**
- Context window (native audio models): **128k tokens**
- Context window (other Live API models): **32k tokens**
- Session resumption token validity: **2 hours**

### Context Window Compression

Enable sliding-window compression for unlimited session duration:

* {Python}

    ```python
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        context_window_compression=types.ContextWindowCompressionConfig(
            sliding_window=types.SlidingWindow(),
        ),
    )
    ```

* {JavaScript}

    ```js
    const config = {
      responseModalities: ['AUDIO'],
      contextWindowCompression: { slidingWindow: {} }
    };
    ```

### Session Resumption

Survive WebSocket reconnections without losing session state:

* {Python}

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
                    saved_handle = update.new_handle
    ```

* {JavaScript}

    ```js
    const config = {
      responseModalities: ['AUDIO'],
      sessionResumption: { handle: previousSessionHandle }
    };

    // In message handler:
    if (response.sessionResumptionUpdate) {
      if (response.sessionResumptionUpdate.resumable && response.sessionResumptionUpdate.newHandle) {
        const newHandle = response.sessionResumptionUpdate.newHandle;
        // Store for reconnection
      }
    }
    ```

### GoAway Message

Server signals an impending connection termination:

* {Python}

    ```python
    async for response in session.receive():
        if response.go_away is not None:
            print(f"Connection ending in: {response.go_away.time_left}")
            # Prepare to reconnect with session resumption
    ```

* {JavaScript}

    ```js
    if (response.goAway) {
      console.log('Time left:', response.goAway.timeLeft);
    }
    ```

### Generation Complete

Detect when the model finishes generating a response:

* {Python}

    ```python
    async for response in session.receive():
        if response.server_content.generation_complete is True:
            pass  # Generation is done
    ```

* {JavaScript}

    ```js
    if (response.serverContent?.generationComplete) {
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

* {Python}

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

* {JavaScript}

    ```js
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

* {Python}

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

* {JavaScript}

    ```js
    const ai = new GoogleGenAI({ apiKey: token.name });

    const session = await ai.live.connect({
      model: 'gemini-2.5-flash-native-audio-preview-12-2025',
      config: { responseModalities: ['AUDIO'] },
      callbacks: { ... },
    });
    ```

### Ephemeral Token Best Practices

- Set short `expire_time` values
- Always authenticate your own backend securely first
- Don't use ephemeral tokens for backend-to-Gemini connections (use API keys)
- Use `session_resumption` to reconnect within the same token's `expireTime` (works even with `uses: 1`)

## Media Resolution

Control input media resolution for bandwidth/quality tradeoff:

* {Python}

    ```python
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        media_resolution=types.MediaResolution.MEDIA_RESOLUTION_LOW,
    )
    ```

* {JavaScript}

    ```js
    import { MediaResolution } from '@google/genai';

    const config = {
      responseModalities: ['AUDIO'],
      mediaResolution: MediaResolution.MEDIA_RESOLUTION_LOW,
    };
    ```

## Limitations

- **Response modality** — Only `TEXT` **or** `AUDIO` per session, not both
- **Audio-only session** — 15 min without compression
- **Audio+video session** — 2 min without compression
- **Connection lifetime** — ~10 min (use session resumption)
- **Context window** — 128k tokens (native audio) / 32k tokens (standard)
- **Code execution** — Not supported
- **URL context** — Not supported
- **Google Maps** — Not supported

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
