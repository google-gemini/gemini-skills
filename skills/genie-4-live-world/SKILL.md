---
name: genie-4-live-world
description: Use this skill when building real-time interactive world generation and simulation apps with Genie 4 (models/genie-4) over the Live Interactions API (interactions.connect via WebRTC or WebSocket), or migrating early-access raw WebRTC/WebSocket world-model prototypes to the google-genai and @google/genai SDKs. Covers ephemeral auth tokens (interactions.auth_tokens / interactions.authTokens), world_setup initialization from text and/or reference images, keyboard and action controls (user_action), mid-session prompt steering, continuous 16:9 24 fps video + 48 kHz stereo audio streaming, and session lifecycle (complete vs detach). Don't use for clip-based video generation (use gemini-omni-flash-api) or conversational voice Live API (use gemini-live-api-dev).
---

# Genie 4 Interactive World Skill

## Overview

**Genie 4 (`models/genie-4`)** generates interactive, controllable `16:9` widescreen 3D/video worlds at `24 fps` with synchronized `48 kHz` stereo audio in real time over a stateful **Live Interactions** (`v1beta`) session. Unlike clip-based video generation (`gemini-omni-1.2-flash`), Genie 4 responds frame-by-frame to continuous keyboard actions (`user_action`) and mid-session text steering (`input`).

### Model Specifications & Hard Constraints

- **Model ID**: `"models/genie-4"` (replaces any legacy early-access world-model ID). Always target `api_version="v1beta"` (`apiVersion: "v1beta"` in JS/TS).
- **Output stream & pricing**: `16:9` widescreen video (`1280x720` / `720p`) at `24 fps` (`240` video tokens/frame = `5,760` video tokens/s) bundled with `48 kHz` 16-bit stereo audio (`$1.50 / 1M` input tokens, `$9.00 / 1M` text output tokens, `$17.50 / 1M` video+audio output tokens — `~$0.101 / sec`, `~$6.05 / min`).
- **Paid tier & rate limits**: Free tier is not supported (`0` streams). Limits scale by billing tier: `Tier 1` (`2` concurrent sessions, `50` RPD), `Tier 2` (`5` concurrent sessions, `250` RPD), `Tier 3` (`10` concurrent sessions, `1,000` RPD).
- **Bounded session duration & no resumption**: Sessions cap at **`120 seconds`** (`2` minutes; visual coherence and object permanence are strongest during the first `45-90s`) and **cannot be resumed** once completed, cancelled, or expired.
- **Stop billing explicitly with `complete()`**: Calling `detach()` (or exiting Python's `async with` block without `complete()`) disconnects the local socket **without** terminating the server-side session. Always call `await conn.complete()` (Python) or `await session.complete()` (JS/TS) when the user exits.
- **Unsupported Gemini features**: Audio input, function calling / tools, Google Search grounding, structured output (`response_format`), and `system_instruction` are rejected on `models/genie-4`.
- **Availability & regional latency**: Available in all Gemini API supported regions on the paid tier, with dedicated serving clusters in the **United States, Western Europe, and Japan**. Optimal responsiveness (`< 150 ms` RTT, `24 fps`) is expected in **North America** (`US`, `CA`), **Western and Central Europe** (`EU` member states, `GB`, `CH`, `NO`, `IS`, `AD`, `LI`, `MC`, `SM`), and **East Asia** (`JP`, `KR`, `TW`). Outside these regions, `> 150 ms` RTT adds steering lag and `> 333 ms` RTT can reduce frame rate below `24 fps` (down toward `~10 fps` at `800 ms`).

## SDKs & Transports

- **Python**: `google-genai >= 3.5.0` (`Python >= 3.11`) → `pip install -U google-genai`
- **JavaScript / TypeScript**: `@google/genai >= 3.5.0` (`Node.js >= 22`) → `npm install @google/genai`

| Runtime | Supported Transports | Recommended Choice |
| :--- | :--- | :--- |
| **Browser (`@google/genai`)** | **WebRTC** (`{ transport: "webrtc" }`) & **WebSocket** (`{ transport: "websocket" }`) | **WebRTC** — lowest latency; video + stereo audio attach directly to an HTML `<video>` element while JSON events use the `"events"` `RTCDataChannel`. |
| **Python (`google-genai`)** | **Async WebSocket** (`client.aio.interactions.connect`) | **Async WebSocket** — Python does not expose a WebRTC transport; yields base64 JPEG frames and `48 kHz` PCM16LE stereo chunks on `step.delta`. |
| **Node.js (`@google/genai`)** | **WebSocket** (`{ transport: "websocket" }`, default) | **WebSocket** — use for server-side frame processing or headless pipelines; mint ephemeral tokens on Node.js when serving browsers. |

## Ephemeral Auth Tokens (Browser Security)

**Never ship `GEMINI_API_KEY` to browser clients.** Mint the interaction and a short-lived, interaction-scoped ephemeral token (`auth_tokens/...`) on your backend, then pass `auth_token` as `apiKey` (`api_key` in Python) when constructing the client:

- **No `auth_token` parameter on `connect()`**: Pass the ephemeral token via `new GoogleGenAI({ apiKey: authToken, apiVersion: "v1beta" })` (JS/TS) or `genai.Client(api_key=auth_token, http_options={"api_version": "v1beta"})` (Python).
- **Required for browser WebSockets**: Browser `WebSocket` APIs cannot set `x-goog-api-key` headers; when `apiKey` starts with `"auth_tokens/"`, `@google/genai` authenticates via `?auth_token=...` on the handshake URL automatically.

## Quickstart: Browser WebRTC + Backend Token (`@google/genai`)

### 1. Backend Endpoint (Node.js / TypeScript)

```typescript
import { GoogleGenAI } from "@google/genai";

const serverAi = new GoogleGenAI({
    apiKey: process.env.GEMINI_API_KEY,
    apiVersion: "v1beta",
});

export async function createGenieSession() {
    const interaction = await serverAi.interactions.create(
        {
            model: "models/genie-4",
            api_version: "v1beta",
        },
        { timeout_ms: 30_000 },
    );

    try {
        const tokenResp = await serverAi.interactions.authTokens.create(
            interaction.id,
            { api_version: "v1beta" },
            { timeout_ms: 30_000 },
        );

        return {
            interactionId: interaction.id,
            authToken: tokenResp.auth_token, // "auth_tokens/..."
        };
    } catch (err) {
        await serverAi.interactions
            .cancel(interaction.id, { api_version: "v1beta" }, { timeout_ms: 15_000 })
            .catch(() => {});
        throw err;
    }
}
```

### 2. Browser Client (WebRTC Media + DataChannel Controls)

> [!IMPORTANT]
> Pass `{ transport: "webrtc" }` directly to `clientAi.interactions.connect(...)` and attach media via `session.transport.setVideoElement(videoEl)` — prefer this built-in transport option over manually instantiating `InteractionWebRTCTransport`.

```typescript
import { GoogleGenAI } from "@google/genai";

const KEY_MAP: Record<string, string> = {
    KeyW: "key_w",
    KeyA: "key_a",
    KeyS: "key_s",
    KeyD: "key_d",
    ArrowUp: "arrow_up",
    ArrowDown: "arrow_down",
    ArrowLeft: "arrow_left",
    ArrowRight: "arrow_right",
};

export async function startWorld(
    videoEl: HTMLVideoElement,
    promptText: string,
) {
    // 1. Fetch interactionId + ephemeral auth_token from your backend
    const { interactionId, authToken } = await fetch("/api/genie-session", {
        method: "POST",
    }).then((r) => r.json());

    // 2. Authenticate browser client with the ephemeral token
    const clientAi = new GoogleGenAI({
        apiKey: authToken,
        apiVersion: "v1beta",
    });

    // 3. Open WebRTC connection (SDP exchange + "events" RTCDataChannel)
    const session = await clientAi.interactions.connect(
        interactionId,
        { transport: "webrtc", api_version: "v1beta" },
        { timeout_ms: 30_000 },
    );

    // Attach remote 16:9 video + 48 kHz stereo audio tracks to <video autoplay playsinline>
    session.transport.setVideoElement(videoEl);

    // 4. Consume lifecycle and error events in the background (one active receive() loop)
    const eventLoop = (async () => {
        try {
            for await (const event of session.receive()) {
                if (event.event_type === "error") {
                    console.error("Genie 4 error:", event.error);
                } else if (event.event_type === "interaction.completed") {
                    break;
                }
            }
        } catch (err) {
            console.error("Genie 4 stream closed:", err);
        }
    })();

    // 5. Send mandatory initial world_setup before any actions or steering
    await session.send({
        event_type: "world_setup",
        world_prompt: { text: promptText },
    });

    // 6. Wire non-repeating key_down / key_up controls (release held keys on blur)
    const heldKeys = new Set<string>();

    const onKeyDown = (e: KeyboardEvent) => {
        if (e.repeat) return;
        const input = KEY_MAP[e.code];
        if (!input || heldKeys.has(input)) return;
        e.preventDefault();
        heldKeys.add(input);
        void session
            .send({
                event_type: "user_action",
                action: "key_down",
                input,
            })
            .catch(console.error);
    };

    const onKeyUp = (e: KeyboardEvent) => {
        const input = KEY_MAP[e.code];
        if (!input || !heldKeys.delete(input)) return;
        e.preventDefault();
        void session
            .send({
                event_type: "user_action",
                action: "key_up",
                input,
            })
            .catch(console.error);
    };

    const releaseAllKeys = () => {
        for (const input of heldKeys) {
            void session
                .send({
                    event_type: "user_action",
                    action: "key_up",
                    input,
                })
                .catch(console.error);
        }
        heldKeys.clear();
    };

    window.addEventListener("keydown", onKeyDown);
    window.addEventListener("keyup", onKeyUp);
    window.addEventListener("blur", releaseAllKeys);

    return {
        steer: (text: string) => session.send(text),
        stop: async () => {
            window.removeEventListener("keydown", onKeyDown);
            window.removeEventListener("keyup", onKeyUp);
            window.removeEventListener("blur", releaseAllKeys);
            releaseAllKeys();
            // Ends server-side generation and billing immediately
            await session.complete();
            await eventLoop;
        },
    };
}
```

> [!WARNING]
> **64 KB WebRTC DataChannel Cap (`reference_image`)**: Over WebRTC, `session.send(...)` serializes JSON onto an SCTP `RTCDataChannel` limited to **`65,536` bytes (`64 KB`)**. When sending a `reference_image` inside `world_setup` over WebRTC, downscale to `16:9` (`1280x720` or `640x360`) and compress as `image/jpeg` below **`42 KB` raw bytes** (`< 56 KB` base64) so the serialized JSON payload stays strictly under `65,536` bytes, or use `{ transport: "websocket" }`.

## Quickstart: Python Async WebSocket (`google-genai`)

`conn.receive()` streams continuously across generation steps until `interaction.completed`, `interaction.canceled`, or `conn.detach()` — **do not wrap `conn.receive()` in an outer `while True:` loop**.

```python
import asyncio
import base64
from google import genai

client = genai.Client(http_options={"api_version": "v1beta"})


async def run_genie_world() -> None:
    # 1. Create the live interaction on v1beta
    interaction = await client.aio.interactions.create(
        model="models/genie-4",
        api_version="v1beta",
        timeout=30.0,
    )

    # Optional: mint an ephemeral token for a downstream client
    # token_resp = await client.aio.interactions.auth_tokens.create(
    #     interaction.id, api_version="v1beta", timeout=30.0
    # )

    completed = False
    try:
        # 2. Connect over WebSocket
        async with client.aio.interactions.connect(
            interaction.id,
            api_version="v1beta",
            timeout=30.0,
        ) as conn:

            async def consume_events() -> None:
                async for event in conn.receive():
                    if event.event_type == "step.delta":
                        delta = event.delta
                        if delta.type == "video" and delta.data:
                            jpeg_bytes = base64.b64decode(delta.data)
                            # Render or write 16:9 JPEG frame (24 fps)
                            _ = len(jpeg_bytes)
                        elif delta.type == "audio" and delta.data:
                            pcm_48k_stereo = base64.b64decode(delta.data)
                            # Play 48 kHz, 16-bit signed little-endian, 2-channel PCM
                            _ = len(pcm_48k_stereo)
                    elif event.event_type == "error":
                        print(f"Stream error: {event.error}")
                        break
                    elif event.event_type == "interaction.completed":
                        break

            consumer = asyncio.create_task(consume_events())
            try:
                # 3. Initialize the world (required first event)
                await conn.send({
                    "event_type": "world_setup",
                    "world_prompt": {
                        "text": (
                            "First-person view walking along a sunlit cobblestone canal path "
                            "inside a thick impasto oil painting. Audio: footsteps on stone, "
                            "water lapping against canal walls, leaves rustling in a light breeze."
                        ),
                    },
                })

                await asyncio.sleep(2.0)

                # 4. Drive movement with key_down / key_up
                await conn.send({
                    "event_type": "user_action",
                    "action": "key_down",
                    "input": "key_w",
                })
                await asyncio.sleep(2.5)
                await conn.send({
                    "event_type": "user_action",
                    "action": "key_up",
                    "input": "key_w",
                })

                # 5. Steer the world mid-session (string shorthand wraps into event_type="input")
                await conn.send(
                    "Soft snow begins falling across the canal and lanterns light up."
                )
                await asyncio.sleep(3.0)

                # 6. Complete the interaction to stop billing before exiting async with
                await conn.complete()
                completed = True
                await consumer
            except Exception:
                try:
                    await conn.cancel()
                except Exception:
                    pass
                else:
                    completed = True
                raise
            finally:
                if not consumer.done():
                    consumer.cancel()
                await asyncio.gather(consumer, return_exceptions=True)
    finally:
        if not completed:
            try:
                await client.aio.interactions.cancel(
                    interaction.id,
                    api_version="v1beta",
                    timeout=15.0,
                )
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(run_genie_world())
```

## JavaScript / TypeScript WebSocket Fallback

When connecting with `{ transport: "websocket" }` (Node.js or browser canvas fallback), `step.delta` events deliver base64 `video` (`image/jpeg`) and `audio` (`48 kHz`, 16-bit signed LE, stereo PCM):

```typescript
const session = await clientAi.interactions.connect(
    interactionId,
    { transport: "websocket", api_version: "v1beta" },
    { timeout_ms: 30_000 },
);

for await (const event of session.receive()) {
    if (event.event_type === "step.delta") {
        if (event.delta?.type === "video" && event.delta.data) {
            // Base64-encoded 16:9 JPEG frame (`data:image/jpeg;base64,${event.delta.data}`)
        } else if (event.delta?.type === "audio" && event.delta.data) {
            // Base64-encoded 48 kHz 16-bit signed LE stereo PCM
        }
    } else if (event.event_type === "interaction.completed") {
        break;
    }
}
```

## Wire Protocol & Controls Reference

### 1. `world_setup` (Mandatory First Client Event)

Send one `world_setup` event immediately after connecting, containing `world_prompt` (a `{"text": "..."}` `WorldPromptContent` block or plain string — do **not** include `"type"`), a **top-level** `reference_image` (`16:9` landscape recommended, `{"mime_type": "...", "data": "..."}` — do **not** include `"type"`; sibling of `world_prompt`, **never** nested inside `world_prompt`), or both:

```json
{
  "event_type": "world_setup",
  "world_prompt": {
    "text": "First-person walk through a lantern-lit Kyoto alley in light rain. Audio: footsteps on wet stone, rain pattering on wooden eaves."
  },
  "reference_image": {
    "mime_type": "image/jpeg",
    "data": "<base64-encoded-16x9-image>"
  }
}
```

- **Prompting guidelines**: Prefer **first-person walking perspectives** (much stabler than third-person cameras or high-speed vehicle driving) and specify concrete **physical contact Foley audio** (footsteps on gravel/stone, water lapping, ceramic clinks, rustling leaves) rather than musical soundtracks or continuous engine drones.

### 2. `user_action` (Real-Time Controls)

```json
{
  "event_type": "user_action",
  "action": "key_down",
  "input": "key_w"
}
```

| Field | Allowed Values | Behavior |
| :--- | :--- | :--- |
| `action` | `"key_down"`, `"key_up"`, `"key_click"` | `"key_down"` holds the input active until a matching `"key_up"`. `"key_click"` triggers a discrete tap. Always ignore `KeyboardEvent.repeat` and emit `"key_up"` for held keys on window `blur`. |
| `input` | `"key_w"`, `"key_a"`, `"key_s"`, `"key_d"`, `"arrow_up"`, `"arrow_down"`, `"arrow_left"`, `"arrow_right"`, `"key_e"`, `"space"` | `key_w/a/s/d` and `arrow_*` drive primary movement and camera navigation (`"key_e"` and `"space"` are also accepted by the `UserActionInput` schema; for custom world actions such as toggling weather or interacting with scene props, bind keys on the client to send a short `input` text event via `session.send(...)`). |

### 3. Mid-Session `input` Steering & Dialogue

Send a plain string (`await conn.send("...")` / `await session.send("...")`) or explicit `input` event to mutate weather, lighting, hazards, or NPC speech mid-stream:

```json
{
  "event_type": "input",
  "content": [
    {
      "type": "text",
      "text": "A wooden shop door opens ahead and a merchant waves, saying \"Come in out of the rain!\""
    }
  ]
}
```

### 4. Connection Lifecycle & Errors

| Method / Exception | Purpose |
| :--- | :--- |
| `await conn.complete()` / `await session.complete()` | Sends `interaction.complete`, persists final state, and **stops video token billing**. Drain `receive()` until `interaction.completed`. |
| `await conn.cancel()` / `await session.cancel()` | Aborts the active interaction immediately (`interaction.cancel`). |
| `await conn.detach()` / `session.detach()` | Sends `interaction.disconnect` and closes the local transport **without** ending the server-side interaction (`close()` does not exist). |
| `APIWebSocketError` / `APIWebRTCError` | Subclasses of `APIConnectionError` carrying `close_code` / `closeCode`, `http_status` / `httpStatus`, and `server_code` / `serverCode`. Only **one** `receive()` iterator may be active per connection at a time. |

## Migrating Early-Access Prototypes to `models/genie-4`

- [ ] Replaced any early-access world-model identifier with `"models/genie-4"` (`api_version="v1beta"`).
- [ ] Upgraded SDKs to `google-genai >= 3.5.0` (Python) and `@google/genai >= 3.5.0` (JS/TS).
- [ ] Replaced custom HTTP `:webrtc` SDP `fetch`, manual `RTCPeerConnection` setup, and raw `new WebSocket(...)` clients with `interactions.create(...)` + `interactions.auth_tokens.create(...)` / `interactions.authTokens.create(...)` + `interactions.connect(...)`.
- [ ] Placed `reference_image` (`{"mime_type": ..., "data": ...}` — no `"type"` field) at the top level of `world_setup` alongside `world_prompt` (`{"text": ...}` or plain string — no `"type"` field).
- [ ] Passed ephemeral tokens via client initialization (`new GoogleGenAI({ apiKey: authToken })` / `genai.Client(api_key=auth_token)`), not to `connect()`.
- [ ] Used `{ transport: "webrtc" }` + `session.transport.setVideoElement(videoEl)` in browser code (preferring the built-in transport option over manual `InteractionWebRTCTransport` instantiation), and compressed WebRTC `reference_image` JPEGs so the JSON event stays under `64 KB`.
- [ ] Removed outer `while True:` loops around `conn.receive()` / `session.receive()`, and ensured teardown calls `await conn.complete()` / `await session.complete()` rather than `detach()` alone.

## Documentation Lookup

### When MCP is Installed (Preferred)

If **`gemini_search_docs`** (or **`search_docs`**) is available from the Gemini Docs MCP server (`https://gemini-api-docs-mcp.dev`), use `gemini_search_docs` or `gemini_get_doc` as your primary documentation source instead of manual URL fetching.

### When MCP is NOT Installed (Fallback)

Fetch these canonical raw Markdown docs when verifying parameters or updates:

- **Genie 4 Model Card & Guide**: [aistudio.google.com/docs/models/genie-4.md](https://aistudio.google.com/docs/models/genie-4.md)
- **Interactions API Overview**: [aistudio.google.com/docs/interactions-overview.md](https://aistudio.google.com/docs/interactions-overview.md)
- **Full Documentation Index**: [aistudio.google.com/llms.txt](https://aistudio.google.com/llms.txt)
