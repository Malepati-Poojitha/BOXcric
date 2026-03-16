from fastapi import WebSocket
from typing import Dict, Set


class LiveScoreManager:
    """Manages WebSocket connections for live score broadcasting."""

    def __init__(self):
        # match_id -> set of connected websockets
        self.connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, match_id: int):
        await websocket.accept()
        if match_id not in self.connections:
            self.connections[match_id] = set()
        self.connections[match_id].add(websocket)

    def disconnect(self, websocket: WebSocket, match_id: int):
        if match_id in self.connections:
            self.connections[match_id].discard(websocket)
            if not self.connections[match_id]:
                del self.connections[match_id]

    async def broadcast(self, match_id: int, data: dict):
        """Send live score update to all connected clients for a match."""
        if match_id not in self.connections:
            return
        dead = []
        for ws in self.connections[match_id]:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.connections[match_id].discard(ws)


manager = LiveScoreManager()
