"""In-process pub/sub for WebSocket fan-out (FR-1.3 realtime dashboard).

A production deployment replaces this with OPC-UA Pub/Sub or MQTT (COM-1/COM-2);
the publish() call sites stay identical.
"""
from __future__ import annotations

import asyncio
import contextlib
import json
from typing import Any

from fastapi import WebSocket


class Hub:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        async with self._lock:
            self._clients.add(ws)

    async def disconnect(self, ws: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(ws)

    async def publish(self, topic: str, payload: Any) -> None:
        msg = json.dumps({"topic": topic, "data": payload}, default=str)
        async with self._lock:
            dead = []
            for ws in self._clients:
                try:
                    await ws.send_text(msg)
                except Exception:  # noqa: BLE001
                    dead.append(ws)
            for ws in dead:
                self._clients.discard(ws)

    def publish_soon(self, topic: str, payload: Any) -> None:
        """Fire-and-forget from sync code (ingest runs in a threadpool)."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(self.publish(topic, payload))
        else:
            with contextlib.suppress(RuntimeError):
                asyncio.run(self.publish(topic, payload))

    @property
    def client_count(self) -> int:
        return len(self._clients)


hub = Hub()
