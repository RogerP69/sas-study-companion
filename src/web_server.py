import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

_STATIC_DIR = Path(__file__).parent.parent / "static"

_connections: Set[WebSocket] = set()
_state: dict = {"monitoring": False, "processing": False}
_event_loop: asyncio.AbstractEventLoop | None = None


@asynccontextmanager
async def _lifespan(app: FastAPI):
    global _event_loop
    _event_loop = asyncio.get_running_loop()
    yield


app = FastAPI(lifespan=_lifespan)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/")
async def serve_panel() -> FileResponse:
    return FileResponse(str(_STATIC_DIR / "panel.html"))


@app.get("/status")
async def get_status() -> dict:
    return dict(_state)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    _connections.add(websocket)
    await websocket.send_json({"type": "status", **_state})
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        _connections.discard(websocket)


async def broadcast(message: dict) -> None:
    dead: Set[WebSocket] = set()
    for ws in list(_connections):
        try:
            await ws.send_json(message)
        except Exception:
            dead.add(ws)
    _connections.difference_update(dead)


def get_event_loop() -> asyncio.AbstractEventLoop | None:
    return _event_loop


def set_monitoring(active: bool) -> None:
    _state["monitoring"] = active


def set_processing(active: bool) -> None:
    _state["processing"] = active
