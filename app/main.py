import base64
import json
import logging
from urllib.parse import urlparse

from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect

from . import config
from .session import Session

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
app = FastAPI()


@app.post("/voice")
async def voice():
    """Twilio asks what to do with the call: connect its audio to our websocket."""
    host = urlparse(config.PUBLIC_BASE_URL).netloc
    twiml = f'<?xml version="1.0" encoding="UTF-8"?><Response><Connect><Stream url="wss://{host}/stream"/></Connect></Response>'
    return Response(content=twiml, media_type="application/xml")


@app.websocket("/stream")
async def stream(ws: WebSocket):
    """Twilio Media Streams: connected / start / media / stop events."""
    await ws.accept()
    session = Session(ws)
    try:
        while True:
            msg = json.loads(await ws.receive_text())
            event = msg.get("event")
            if event == "start":
                session.stream_sid = msg["start"]["streamSid"]
                session.note(f"Call started {session.stream_sid}")
                session.start()
            elif event == "media":
                await session.on_media(base64.b64decode(msg["media"]["payload"]))
            elif event == "stop":
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        session.note(f"ERROR in stream loop: {e!r}")
    finally:
        await session.close()
