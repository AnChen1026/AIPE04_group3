"""老師和學生的接洽對話 WebSocket。訊息先寫資料庫，再推給在線的人。"""

import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from backend.core.database import SessionLocal
from backend.models.student import InquiryConversation
from backend.models.user import User
from backend.repositories.student import StudentRepository
from backend.repositories.user import get_user_by_id
from backend.services.chat_hub import chat_hub, message_event
from backend.services.student import StudentBusinessError, add_message

router = APIRouter()


def _session_user_id(websocket: WebSocket) -> uuid.UUID | None:
    user_id_text = websocket.session.get("user_id")
    if user_id_text is None:
        return None
    try:
        return uuid.UUID(str(user_id_text))
    except ValueError:
        return None


def _member(db: Session, conversation_id: uuid.UUID, user_id: uuid.UUID) -> tuple[User, InquiryConversation] | None:
    user = get_user_by_id(db, user_id)
    conversation = StudentRepository.get_conversation(db, conversation_id)
    if user is None or user.is_active is False or user.role not in ("student", "teacher"):
        return None
    if conversation is None:
        return None
    if user.id not in (conversation.student_id, conversation.teacher_id):
        return None
    return user, conversation


@router.websocket("/ws/conversations/{conversation_id}")
async def conversation_socket(websocket: WebSocket, conversation_id: uuid.UUID):
    await websocket.accept()
    chat_hub.bind_loop()
    user_id = _session_user_id(websocket)
    if user_id is None:
        await websocket.close(code=4401)
        return

    db = SessionLocal()
    try:
        member = _member(db, conversation_id, user_id)
    finally:
        db.close()
    if member is None:
        await websocket.close(code=4403)
        return

    await chat_hub.connect(conversation_id, websocket)
    try:
        while True:
            raw = await websocket.receive_text()
            await _handle_text(websocket, conversation_id, user_id, raw)
    except WebSocketDisconnect:
        pass
    finally:
        chat_hub.disconnect(conversation_id, websocket)


async def _handle_text(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    raw: str,
) -> None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        await websocket.send_json({"type": "error", "detail": "訊息格式不正確。"})
        return
    if not isinstance(data, dict):
        await websocket.send_json({"type": "error", "detail": "訊息格式不正確。"})
        return

    kind = data.get("type")
    if kind == "sync":
        await _sync(websocket, conversation_id, user_id, data.get("after_message_id"))
        return
    if kind == "message":
        await _send_message(
            websocket,
            conversation_id,
            user_id,
            str(data.get("body") or ""),
            data.get("client_message_id"),
        )
        return
    await websocket.send_json({"type": "error", "detail": "不支援這個操作。"})


async def _sync(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    after_message_id,
) -> None:
    db = SessionLocal()
    try:
        if _member(db, conversation_id, user_id) is None:
            await websocket.close(code=4403)
            return
        messages = StudentRepository.list_messages(db, conversation_id)
        if after_message_id:
            try:
                after_id = uuid.UUID(str(after_message_id))
            except ValueError:
                await websocket.send_json({"type": "error", "detail": "訊息編號不正確。"})
                return
            found = False
            pending = []
            for message in messages:
                if found:
                    pending.append(message)
                elif message.id == after_id:
                    found = True
            if not found:
                await websocket.send_json({"type": "error", "detail": "找不到接續的訊息。"})
                return
            messages = pending
        else:
            messages = []
        payloads = [message_event(message) for message in messages]
    finally:
        db.close()
    for payload in payloads:
        await websocket.send_json(payload)


async def _send_message(
    websocket: WebSocket,
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    body: str,
    client_message_id,
) -> None:
    client_id = str(client_message_id).strip() if client_message_id else None
    db = SessionLocal()
    try:
        member = _member(db, conversation_id, user_id)
        if member is None:
            await websocket.close(code=4403)
            return
        user, conversation = member
        try:
            add_message(db, conversation, user, body, client_id)
        except StudentBusinessError as error:
            await websocket.send_json({"type": "error", "detail": error.detail})
    finally:
        db.close()
