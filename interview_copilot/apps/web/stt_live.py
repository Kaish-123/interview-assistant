"""Live streaming STT — browser PCM → OpenAI Realtime transcription.

Mirrors Parakeet's listen path: continuous audio, incremental captions,
one completed transcript per interviewer turn. API key stays on the server.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from interview_copilot.apps.web.runtime import get_runtime
from interview_copilot.packages.stt.live_session import (
    DEFAULT_LIVE_MODEL,
    legacy_session_update_event,
    openai_realtime_urls,
    session_update_event,
)
from interview_copilot.shared.config.settings import get_settings
from interview_copilot.shared.logging import get_logger

logger = get_logger("stt.live")
router = APIRouter(prefix="/api")


def _event_text(ev: dict[str, Any]) -> str:
    for key in ("transcript", "delta", "text"):
        val = ev.get(key)
        if isinstance(val, str) and val:
            return val
    return ""


async def _connect_openai(url: str, api_key: str):
    import websockets

    headers = {
        "Authorization": f"Bearer {api_key}",
        "OpenAI-Beta": "realtime=v1",
    }
    kwargs: dict[str, Any] = {"max_size": 8_000_000, "open_timeout": 20}
    try:
        return await websockets.connect(url, additional_headers=headers, **kwargs)
    except TypeError:
        return await websockets.connect(url, extra_headers=headers, **kwargs)


async def _open_transcription_socket(api_key: str, model: str):
    last: Exception | None = None
    for url in openai_realtime_urls(model):
        try:
            sock = await _connect_openai(url, api_key)
            logger.info("realtime stt connected", extra={"stage": "stt", "url": url})
            return sock
        except Exception as exc:
            last = exc
            logger.warning(f"realtime connect failed {url}: {exc}", extra={"stage": "stt"})
    raise RuntimeError(f"Could not open OpenAI realtime transcription: {last}")


@router.websocket("/stt/live")
async def stt_live(ws: WebSocket, engine_id: str = "", language: str = "en"):
    await ws.accept()
    if engine_id:
        try:
            get_runtime().get(engine_id)
        except KeyError:
            await ws.send_json({"type": "error", "message": "Unknown engine"})
            await ws.close(code=4404)
            return

    settings = get_settings()
    api_key = (settings.openai_api_key or "").strip()
    if not api_key:
        await ws.send_json({"type": "error", "message": "OPENAI_API_KEY is not set"})
        await ws.close(code=4401)
        return

    model = (settings.stt.live_model or DEFAULT_LIVE_MODEL).strip()
    lang = (language or settings.stt.language or settings.default_language or "en").strip()
    oai = None
    try:
        oai = await _open_transcription_socket(api_key, model)
        await oai.send(json.dumps(session_update_event(model, language=lang)))
        await ws.send_json({"type": "ready", "model": model})

        async def from_browser() -> None:
            while True:
                msg = await ws.receive()
                if msg.get("type") == "websocket.disconnect":
                    return
                raw = msg.get("text")
                if not raw:
                    continue
                data = json.loads(raw)
                kind = data.get("type")
                if kind == "pcm" and data.get("audio"):
                    await oai.send(
                        json.dumps(
                            {
                                "type": "input_audio_buffer.append",
                                "audio": data["audio"],
                            }
                        )
                    )
                elif kind == "commit":
                    await oai.send(json.dumps({"type": "input_audio_buffer.commit"}))
                elif kind == "update":
                    await oai.send(
                        json.dumps(session_update_event(model, language=data.get("language") or lang))
                    )

        async def from_openai() -> None:
            sent_legacy = False
            async for raw in oai:
                ev = json.loads(raw)
                etype = ev.get("type") or ""
                if etype == "error" and not sent_legacy:
                    sent_legacy = True
                    try:
                        await oai.send(
                            json.dumps(legacy_session_update_event(model, language=lang))
                        )
                    except Exception:
                        pass
                    await ws.send_json(
                        {
                            "type": "error",
                            "message": (ev.get("error") or {}).get("message")
                            or ev.get("message")
                            or "realtime session error",
                        }
                    )
                    continue
                if etype == "conversation.item.input_audio_transcription.delta":
                    await ws.send_json({"type": "delta", "text": _event_text(ev)})
                elif etype == "conversation.item.input_audio_transcription.completed":
                    await ws.send_json({"type": "completed", "text": _event_text(ev)})
                elif etype == "input_audio_buffer.speech_started":
                    await ws.send_json({"type": "speech_started"})
                elif etype == "input_audio_buffer.speech_stopped":
                    await ws.send_json({"type": "speech_stopped"})

        await asyncio.gather(from_browser(), from_openai())
    except WebSocketDisconnect:
        pass
    except Exception as exc:
        logger.warning(f"live stt ended: {exc}", extra={"stage": "stt"})
        try:
            await ws.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
    finally:
        if oai is not None:
            try:
                await oai.close()
            except Exception:
                pass
