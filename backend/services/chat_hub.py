"""同一台程式裡，把已存檔的聊天訊息推給正在看這段對話的人。"""

import asyncio
import uuid
from datetime import datetime

from fastapi import WebSocket

from backend.models.student import ConversationMessage


class ChatHub:
    def __init__(self) -> None:
        self._rooms: dict[uuid.UUID, set[WebSocket]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self) -> None:
        """WebSocket 連上時記住事件迴圈，之後 HTTP 存檔也能推播。"""
        self._loop = asyncio.get_running_loop()

    async def connect(self, conversation_id: uuid.UUID, websocket: WebSocket) -> None:
        self._rooms.setdefault(conversation_id, set()).add(websocket)

    def disconnect(self, conversation_id: uuid.UUID, websocket: WebSocket) -> None:
        room = self._rooms.get(conversation_id)
        if room is None:
            return
        room.discard(websocket)
        if not room:
            self._rooms.pop(conversation_id, None)

    async def broadcast(self, conversation_id: uuid.UUID, payload: dict) -> None:
        room = self._rooms.get(conversation_id, set())
        disconnected = []
        for websocket in list(room):
            try:
                await websocket.send_json(payload)
            except Exception:
                disconnected.append(websocket)
        for websocket in disconnected:
            self.disconnect(conversation_id, websocket)

    def publish(self, conversation_id: uuid.UUID, payload: dict) -> None:
        """資料已寫入後才呼叫。沒有人在線上就略過，訊息仍留在資料庫。"""
        if self._loop is None or self._loop.is_closed() or not self._loop.is_running():
            return
        asyncio.run_coroutine_threadsafe(
            self.broadcast(conversation_id, payload),
            self._loop,
        )


chat_hub = ChatHub()


def message_event(message: ConversationMessage) -> dict:
    created_at = message.created_at
    if isinstance(created_at, datetime):
        created_at_text = created_at.isoformat()
    else:
        created_at_text = ""
    return {
        "type": "message",
        "id": str(message.id),
        "conversation_id": str(message.conversation_id),
        "sender_id": str(message.sender_id),
        "body": message.body,
        "created_at": created_at_text,
        "client_message_id": message.client_message_id,
    }
