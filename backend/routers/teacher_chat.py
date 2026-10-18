"""老師的接洽對話：列表、讀訊息、回訊息、貼綁定碼。只看得到自己課程的對話。"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.common import require_roles
from backend.models.user import User
from backend.repositories.student import StudentRepository
from backend.schemas.student import ConversationResponse, MessageIn, MessageResponse
from backend.services.conversation import conversation_rows
from backend.services.student import (
    StudentBusinessError,
    add_message,
    issue_binding_code,
    mark_conversation_read,
)

router = APIRouter(prefix="/teacher/conversations", tags=["老師聊天"])

current_teacher_user = require_roles("teacher")


def _own_conversation(db: Session, teacher: User, conversation_id: uuid.UUID):
    conversation = StudentRepository.get_conversation(db, conversation_id)
    if conversation is None or conversation.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="找不到這段對話。")
    return conversation


@router.get("", response_model=list[ConversationResponse])
def list_conversations(
    teacher: User = Depends(current_teacher_user),
    db: Session = Depends(get_db),
):
    """學生洽詢列表：學生、課程、是否已綁定、未讀數。有新訊息的排前面。"""
    return conversation_rows(db, StudentRepository.list_teacher_conversations(db, teacher.id), teacher.id)


@router.get("/{conversation_id}", response_model=ConversationResponse)
def read_conversation(
    conversation_id: uuid.UUID,
    teacher: User = Depends(current_teacher_user),
    db: Session = Depends(get_db),
):
    conversation = _own_conversation(db, teacher, conversation_id)
    return conversation_rows(db, [conversation], teacher.id)[0]


@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
def list_messages(
    conversation_id: uuid.UUID,
    teacher: User = Depends(current_teacher_user),
    db: Session = Depends(get_db),
):
    """讀這段對話的訊息，並把學生傳來的訊息標成已讀。"""
    conversation = _own_conversation(db, teacher, conversation_id)
    mark_conversation_read(db, conversation.id, teacher.id)
    return StudentRepository.list_messages(db, conversation.id)


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
def send_message(
    conversation_id: uuid.UUID,
    data: MessageIn,
    teacher: User = Depends(current_teacher_user),
    db: Session = Depends(get_db),
):
    conversation = _own_conversation(db, teacher, conversation_id)
    try:
        return add_message(db, conversation, teacher, data.body, data.client_message_id)
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.post("/{conversation_id}/binding-code")
def create_binding_code(
    conversation_id: uuid.UUID,
    teacher: User = Depends(current_teacher_user),
    db: Session = Depends(get_db),
):
    """產生綁定碼，並當成一則訊息貼進這段接洽對話。"""
    try:
        binding_code = issue_binding_code(db, teacher, conversation_id)
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    return {"code": binding_code.code, "conversation_id": conversation_id}
