"""Streaming speech-to-text over a Sarvam websocket. Sarvam also reports when the caller starts and stops speaking."""
import base64
from contextlib import asynccontextmanager

from sarvamai import AsyncSarvamAI

from . import audio, config

_client = AsyncSarvamAI(api_subscription_key=config.SARVAM_API_KEY)


class Stream:
    def __init__(self, ws):
        self._ws = ws

    async def send(self, pcm16k: bytes):
        await self._ws.transcribe(
            audio=base64.b64encode(pcm16k).decode(), encoding="audio/wav", sample_rate=audio.STT_RATE)

    async def events(self):
        """Yield ('start', None) / ('end', None) around speech, and ('text', transcript) when ready."""
        async for msg in self._ws:
            if msg.type == "events":
                yield ("start" if msg.data.signal_type == "START_SPEECH" else "end", None)
            elif msg.type == "data":
                yield ("text", msg.data.transcript.strip())
            elif msg.type == "error":
                raise RuntimeError(f"Sarvam STT error: {msg.data}")


@asynccontextmanager
async def open_stream():
    async with _client.speech_to_text_streaming.connect(
        language_code=config.LANGUAGE,
        model=config.STT_MODEL,
        mode=config.STT_MODE,
        sample_rate=str(audio.STT_RATE),
        input_audio_codec="pcm_s16le",
        vad_signals="true",
    ) as ws:
        yield Stream(ws)
