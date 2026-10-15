# Voice Agent

A phone call between a person and an AI agent, built on websockets end to end. Twilio carries the call, Sarvam does streaming speech-to-text and text-to-speech, and an LLM (Groq by default, or any OpenAI-compatible API) writes the replies.

## How it works

```
Phone <-> Twilio <== websocket ==> this server <== websocket ==> Sarvam STT (also detects speech start/end)
                                        |
                                        +-- LLM (streams sentences) --> Sarvam TTS websocket --> Twilio
```

1. **Outbound call:** `make_call.py` asks Twilio to ring a number. When it's answered, Twilio POSTs to `/voice`.
   **Inbound call:** `receive_calls.py` points your Twilio number at `/voice`, so when someone calls it, Twilio POSTs to the same place.
2. **Handling the call:** `/voice` replies with TwiML that opens a Media Stream. Twilio then connects to the `/stream` websocket and sends the caller's audio (8 kHz mulaw).
3. The audio is forwarded to Sarvam's streaming speech-to-text, which also reports when the caller starts and stops speaking and returns the transcript.
4. The transcript goes to the LLM. Each sentence is sent to Sarvam's streaming text-to-speech as soon as it's complete, and the mulaw audio is streamed straight back to Twilio.
5. If the caller starts talking while the agent is speaking, the queued audio is cleared and the reply is cancelled (barge-in).

## Code layout

| File | Purpose |
|---|---|
| `make_call.py` | Starts an outbound call through Twilio |
| `receive_calls.py` | Points your Twilio number at this server so incoming calls are answered |
| `app/main.py` | FastAPI app: `/voice` webhook and `/stream` websocket (receives the call) |
| `app/session.py` | Per-call state and the conversation loop, barge-in, silence timeout |
| `app/stt.py` | Sarvam streaming speech-to-text |
| `app/tts.py` | Sarvam streaming text-to-speech |
| `app/llm.py` | LLM client (streams replies sentence by sentence), system prompt, greeting |
| `app/audio.py` | 8 kHz mulaw (Twilio) to 16 kHz PCM (Sarvam) conversion |
| `app/config.py` | Settings loaded from `.env` |

## Setup

Requires Python 3.11+ (on 3.13 the `audioop-lts` package is installed automatically).

```
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # then fill in the values
```

You need:
- A Twilio account and phone number. **Media Streams are not available on Twilio trial accounts**, so the account must be upgraded.
- A Sarvam API key and an API key for an OpenAI-compatible LLM (Groq by default).
- A public HTTPS URL for your server, e.g. from [ngrok](https://ngrok.com) or a deployment. Put it in `PUBLIC_BASE_URL`.

## Run

```
uvicorn app.main:app --port 8000
ngrok http 8000                  # set PUBLIC_BASE_URL in .env to the https URL it prints
python make_call.py              # outbound: rings TARGET_PHONE_NUMBER
python receive_calls.py          # inbound: calls to TWILIO_PHONE_NUMBER now reach the agent
```

If the Twilio account is a trial, the target number must be verified in Twilio.

## Configuration

Set in `.env` (see `.env.example`): Twilio credentials and numbers, `PUBLIC_BASE_URL`, `SARVAM_API_KEY`, `LLM_API_KEY`, `LLM_MODEL`; `LLM_BASE_URL` defaults to Groq. Optional: `LANGUAGE` (default `en-IN`), `TTS_SPEAKER` (default `priya`), `STT_MODE` (default `transcribe`; `codemix` for mixed Hindi/English).

The agent's behaviour is the `SYSTEM_PROMPT` constant in `app/llm.py`.

## Tests

```
pytest
```
