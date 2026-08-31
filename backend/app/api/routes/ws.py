"""WebSocket endpoint for the realtime dashboard (FR-1.3, NFR-1.1)."""
from __future__ import annotations

import asyncio
import contextlib

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings
from app.services.realtime import hub

router = APIRouter()


@router.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await hub.connect(ws)
    try:
        await ws.send_json({"topic": "hello", "data": {"heartbeat": settings.ws_heartbeat_seconds}})
        while True:
            with contextlib.suppress(asyncio.TimeoutError):
                msg = await asyncio.wait_for(ws.receive_text(), timeout=settings.ws_heartbeat_seconds)
                if msg == "ping":
                    await ws.send_json({"topic": "pong", "data": {}})
            await ws.send_json({"topic": "heartbeat", "data": {"clients": hub.client_count}})
    except WebSocketDisconnect:
        pass
    finally:
        await hub.disconnect(ws)
