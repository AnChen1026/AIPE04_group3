from datetime import datetime, date
from pathlib import Path
from uuid import UUID as UUIDType
import uuid
from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.user import User
from backend.dependencies import get_current_user
from teacher.models import *
from teacher.schemas import *
from teacher.dependencies.teacher import get_current_teacher
from teacher.services.teacher_sync import _ensure_teacher_profile
from teacher.core.uploads import MATERIAL_UPLOAD_DIR

router = APIRouter()

@router.post("/chat")
def send_message(
    data: MessageIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    # -----------------------------------------------------
    # 確認 conversation
    # -----------------------------------------------------

    conversation = (
        db.query(ConversationDB)
        .filter(
            ConversationDB.id ==
            data.conversation_id
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="找不到聊天",
        )

    # -----------------------------------------------------
    # 建立訊息
    # -----------------------------------------------------

    message = MessageDB(
        id=uuid.uuid4(),

        conversation_id=
            data.conversation_id,

        # ★ 發送者永遠使用目前登入者
        sender_id=user.id,

        receiver_id=data.receiver_id,

        content=data.content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message

