import asyncio
import logging
from typing import Any

from starlette.websockets import WebSocket


logger = logging.getLogger(__name__)


class ConnectionManager:
    """Keeps the open dashboard WebSocket connections and broadcasts to them.

    The event bus is synchronous and its publishers run in worker threads
    (FastAPI sync routes, the MQTT thread) or in the event loop (the
    sampler). broadcast_threadsafe() schedules the async send on the loop
    that owns the sockets, so publishers never deal with asyncio.
    """

    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    @property
    def connection_count(self) -> int:
        return len(self._connections)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._loop = asyncio.get_running_loop()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, message: dict[str, Any]) -> None:
        for websocket in list(self._connections):
            try:
                await websocket.send_json(message)
            except Exception:
                # A closed or broken socket is dropped; others still get
                # the message.
                self.disconnect(websocket)

    def broadcast_threadsafe(self, message: dict[str, Any]) -> None:
        loop = self._loop

        if loop is None or loop.is_closed() or not self._connections:
            return

        asyncio.run_coroutine_threadsafe(self.broadcast(message), loop)
