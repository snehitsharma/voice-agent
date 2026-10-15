"""Streaming text-to-speech over a Sarvam websocket. Output is 8 kHz mulaw, ready to send to Twilio."""
import base64

from sarvamai import AsyncSarvamAI, AudioOutput, EventResponse

from . import config

_client = AsyncSarvamAI(api_subscription_key=config.SARVAM_API_KEY)


async def stream(text: str):
    """Yield mulaw audio chunks for `text` as Sarvam produces them."""
    async with _client.text_to_speech_streaming.connect(model=config.TTS_MODEL, send_completion_event="true") as ws:
        await ws.configure(
            target_language_code=config.LANGUAGE,
            speaker=config.TTS_SPEAKER,
            speech_sample_rate=8000,
            output_audio_codec="mulaw",
        )
        await ws.convert(text)
        await ws.flush()
        async for msg in ws:
            if isinstance(msg, AudioOutput):
                yield base64.b64decode(msg.data.audio)
            elif isinstance(msg, EventResponse) and msg.data.event_type == "final":
                break
