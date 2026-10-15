import re
import time

from openai import AsyncOpenAI

from . import config

SYSTEM_PROMPT = """You are a helpful voice assistant on a phone call. Your replies are read aloud.
Reply in 1-2 short sentences. Never use lists, markdown, or emoji.
Be friendly and helpful. If the caller's words seem unclear, politely ask them to repeat.
Be honest that you are an AI if asked."""

GREETING = "Hello! This is an AI assistant. How can I help you today?"
GOODBYE = "I haven't heard anything, so I'll hang up now. Goodbye!"

MAX_TOKENS = 70  # short replies keep latency low
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_client = AsyncOpenAI(api_key=config.LLM_API_KEY, base_url=config.LLM_BASE_URL)


def initial_history() -> list:
    return [
        {"role": "user", "content": "(call connected)"},
        {"role": "assistant", "content": GREETING},
    ]


async def _chunks(history: list):
    """Yield text deltas from the LLM (any OpenAI-compatible API)."""
    stream = await _client.chat.completions.create(
        model=config.LLM_MODEL, max_tokens=MAX_TOKENS, stream=True,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
    )
    async for event in stream:
        if event.choices and event.choices[0].delta.content:
            yield event.choices[0].delta.content


async def stream_sentences(history: list, timings: dict | None = None):
    """Yield complete sentences as the LLM streams. The caller appends the assistant turn to history."""
    t0 = time.perf_counter()
    buf = ""
    async for chunk in _chunks(history):
        if timings is not None:
            timings.setdefault("llm_first_token", time.perf_counter() - t0)
        buf += chunk
        *done, buf = _SENTENCE_END.split(buf)
        for sentence in done:
            if sentence.strip():
                yield sentence.strip()
    if buf.strip():
        yield buf.strip()
    if timings is not None:
        timings["llm_total"] = time.perf_counter() - t0
