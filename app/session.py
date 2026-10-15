"""Per-call state and conversation loop: Twilio audio -> Sarvam STT -> LLM -> Sarvam TTS -> Twilio, with barge-in."""
import asyncio
import base64
import json
import logging
import time

from . import audio, llm, stt, tts

log = logging.getLogger("voice")
SILENCE_TIMEOUT_S = 30


class Session:
    def __init__(self, ws):
        self.ws = ws
        self.stream_sid = None
        self.history = llm.initial_history()
        self.resample_state = None
        self.stt: stt.Stream | None = None
        self.speaking = False
        self.turn_task: asyncio.Task | None = None
        self.tasks: list[asyncio.Task] = []
        self.last_activity = time.monotonic()

    def note(self, msg: str):
        log.info(msg)

    # --- lifecycle ---
    def start(self):
        self.turn_task = asyncio.create_task(self.greet())
        self.tasks = [asyncio.create_task(self.listen()), asyncio.create_task(self.watchdog())]

    async def close(self):
        for task in [self.turn_task, *self.tasks]:
            if task and not task.done():
                task.cancel()
        self.note("Call ended")

    # --- incoming audio ---
    async def on_media(self, mulaw: bytes):
        if self.stt:
            pcm, self.resample_state = audio.mulaw8k_to_pcm16k(mulaw, self.resample_state)
            await self.stt.send(pcm)

    async def listen(self):
        """React to Sarvam speech events: interrupt the agent when the caller speaks, answer on transcripts."""
        try:
            async with stt.open_stream() as stream:
                self.stt = stream
                async for kind, value in stream.events():
                    self.last_activity = time.monotonic()
                    if kind == "start":
                        await self.barge_in()
                    elif kind == "text" and value:
                        await self.cancel_turn()
                        self.note(f"CALLER: {value}")
                        self.turn_task = asyncio.create_task(self.respond(value))
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.note(f"ERROR in speech-to-text stream: {e!r}")

    async def barge_in(self):
        """Caller started talking: stop the agent. We send audio faster than Twilio plays it, so always flush."""
        await self.send({"event": "clear", "streamSid": self.stream_sid})
        if self.speaking:
            self.note("BARGE-IN")
            self.turn_task.cancel()

    async def cancel_turn(self):
        if self.turn_task and not self.turn_task.done():
            self.turn_task.cancel()
            try:
                await self.turn_task
            except asyncio.CancelledError:
                pass

    # --- outgoing audio ---
    async def send(self, message: dict):
        await self.ws.send_text(json.dumps(message))

    async def speak(self, text: str):
        async for chunk in tts.stream(text):
            payload = base64.b64encode(chunk).decode()
            await self.send({"event": "media", "streamSid": self.stream_sid, "media": {"payload": payload}})

    async def greet(self):
        self.speaking = True
        try:
            await self.speak(llm.GREETING)
            self.note(f"AGENT: {llm.GREETING}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.note(f"ERROR in greeting: {e!r}")
        finally:
            self.speaking = False

    async def respond(self, text: str):
        """LLM -> TTS for one caller utterance. Cancelled on barge-in."""
        spoken = []
        self.speaking = True
        t0 = time.perf_counter()
        self.history.append({"role": "user", "content": text})
        try:
            timings, first_audio = {}, None
            async for sentence in llm.stream_sentences(self.history, timings):
                await self.speak(sentence)
                spoken.append(sentence)
                self.note(f"AGENT: {sentence}")
                first_audio = first_audio or time.perf_counter() - t0
            self.note(f"LATENCY llm_first={timings.get('llm_first_token', 0):.2f}s "
                      f"llm_total={timings.get('llm_total', 0):.2f}s first_audio={first_audio or 0:.2f}s")
        except asyncio.CancelledError:
            self.note("(interrupted by caller)")
            raise
        except Exception as e:  # never let one turn kill the call
            self.note(f"ERROR in turn: {e!r}")
        finally:
            # Keep history accurate: only what was actually spoken counts as the agent's turn.
            if spoken:
                self.history.append({"role": "assistant", "content": " ".join(spoken)})
            else:
                self.history.pop()
            self.speaking = False

    async def watchdog(self):
        """Hang up politely after a long silence."""
        while True:
            await asyncio.sleep(2)
            if time.monotonic() - self.last_activity > SILENCE_TIMEOUT_S and not self.speaking:
                self.note("Silence timeout, ending call")
                try:
                    await self.speak(llm.GOODBYE)
                    await asyncio.sleep(4)
                finally:
                    await self.ws.close()
                return
