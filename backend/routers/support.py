"""管理員對話 API：老師、學生看自己和管理員的對話；管理員看所有人的對話並回覆。"""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.common import get_current_admin, require_roles
from backend.models.support import SupportConversation
from backend.models.user import User
from backend.schemas.student import MessageIn, MessageResponse
from backend.services.student import StudentBusinessError
from backend.services.support import (
    add_support_message,
    conversation_summary,
    ensure_member_conversations,
    get_or_create_conversation,
    list_support_messages,
    mark_read,
)

router = APIRouter(tags=["管理員對話"])


class SupportConversationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    user_role: str
    created_at: datetime
    unread_count: int
    last_message: str | None = None
    last_message_at: datetime | None = None


def _raise(error: StudentBusinessError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


# ---------- 老師、學生：自己和管理員的那一段

member = require_roles("teacher", "student")


@router.get("/api/support/conversation", response_model=SupportConversationResponse)
def api_my_support_conversation(db: Session = Depends(get_db), user: User = Depends(member)):
    """沒有對話時先建一段空的，聊天列表才能固定顯示「平台管理員」。"""
    conversation = get_or_create_conversation(db, user.id)
    return conversation_summary(db, [conversation], for_admin=False)[0]


@router.get("/api/support/messages", response_model=list[MessageResponse])
def api_my_support_messages(db: Session = Depends(get_db), user: User = Depends(member)):
    conversation = get_or_create_conversation(db, user.id)
    mark_read(db, conversation, user)
    return list_support_messages(db, conversation.id)


@router.post("/api/support/messages", response_model=MessageResponse)
def api_send_support_message(payload: MessageIn, db: Session = Depends(get_db), user: User = Depends(member)):
    conversation = get_or_create_conversation(db, user.id)
    try:
        return add_support_message(db, conversation, user, payload.body, payload.client_message_id)
    except StudentBusinessError as error:
        _raise(error)


# ---------- 管理員：所有人的對話


def _conversation(db: Session, conversation_id: uuid.UUID) -> SupportConversation:
    conversation = db.get(SupportConversation, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="找不到這段對話。")
    return conversation


@router.get("/api/admin/support/conversations", response_model=list[SupportConversationResponse])
def api_admin_conversations(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """所有老師、學生都在列表上，沒聊過的也能直接開口。"""
    ensure_member_conversations(db)
    conversations = list(db.scalars(select(SupportConversation)))
    return conversation_summary(db, conversations, for_admin=True)


@router.post("/api/admin/support/users/{user_id}/conversation", response_model=SupportConversationResponse)
def api_admin_open_conversation(
    user_id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)
):
    """管理員主動找某位老師或學生聊：沒有對話就建一段。"""
    user = db.get(User, user_id)
    if user is None or user.role not in ("teacher", "student"):
        raise HTTPException(status_code=404, detail="找不到這位使用者。")
    conversation = get_or_create_conversation(db, user.id)
    return conversation_summary(db, [conversation], for_admin=True)[0]


@router.get("/api/admin/support/conversations/{conversation_id}", response_model=SupportConversationResponse)
def api_admin_conversation(
    conversation_id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)
):
    return conversation_summary(db, [_conversation(db, conversation_id)], for_admin=True)[0]


@router.get("/api/admin/support/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def api_admin_messages(
    conversation_id: uuid.UUID, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)
):
    conversation = _conversation(db, conversation_id)
    mark_read(db, conversation, admin)
    return list_support_messages(db, conversation.id)


@router.post("/api/admin/support/conversations/{conversation_id}/messages", response_model=MessageResponse)
def api_admin_send(
    conversation_id: uuid.UUID,
    payload: MessageIn,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    try:
        return add_support_message(db, _conversation(db, conversation_id), admin, payload.body, payload.client_message_id)
    except StudentBusinessError as error:
        _raise(error)
