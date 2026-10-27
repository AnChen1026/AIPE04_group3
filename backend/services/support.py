"""管理員和老師、學生之間的對話。

每位使用者一段，所有管理員共用。老師審核通過、學生註冊成功時，系統以管理員身分送出歡迎訊息；
送訊息失敗不影響審核或註冊本身。
"""

import logging
import uuid
from datetime import datetime, timezone

from fastapi import status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.models.support import SupportConversation, SupportMessage
from backend.models.user import User
from backend.services.student import StudentBusinessError, _commit

logger = logging.getLogger(__name__)

TEACHER_WELCOME = """{name} 老師您好，您的老師申請已經審核通過，現在可以開始使用教師管理後台了！

簡單使用須知：
1. 先到「工作室管理」填寫您的工作室資料，編號會由系統產生。
2. 到「課程」新增課程並發布，學生才找得到、能聯繫您。
3. 學生的洽詢會出現在「聊天」。決定收這位學生時，在對話裡或課程頁發給他綁定碼。
4. 學生綁定後，可以在「作業」發作業給他，附上參考 MIDI 與教材。
5. 學生的約課、請假、調課申請在「課表」確認。

使用上有任何問題，直接在這裡回覆，管理員會盡快協助您。"""

STUDENT_WELCOME = """{name} 您好，歡迎加入 melo！

簡單使用須知：
1. 在首頁找喜歡的課程，按「聯繫老師」就能和老師聊聊。
2. 老師給您綁定碼後，到「老師」頁輸入，就能看課表、收作業。
3. 在「作業」可以下載老師給的教材與參考曲，錄音繳交後會收到音高與節奏的回饋。

使用上有任何問題，直接在這裡留言給管理員。"""


def get_or_create_conversation(db: Session, user_id: uuid.UUID) -> SupportConversation:
    conversation = db.scalar(select(SupportConversation).where(SupportConversation.user_id == user_id))
    if conversation is not None:
        return conversation
    conversation = SupportConversation(user_id=user_id)
    db.add(conversation)
    try:
        _commit(db)
    except IntegrityError:
        # 同時建立時，另一邊已經建好了
        db.rollback()
        return db.scalar(select(SupportConversation).where(SupportConversation.user_id == user_id))
    db.refresh(conversation)
    return conversation


def add_support_message(
    db: Session,
    conversation: SupportConversation,
    sender: User,
    body: str,
    client_message_id: str | None = None,
) -> SupportMessage:
    """sender 必須是這段對話的使用者本人，或管理員。"""
    text = body.strip()
    if text == "":
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "訊息不能是空白。")
    if sender.id != conversation.user_id and sender.role != "admin":
        raise StudentBusinessError(status.HTTP_403_FORBIDDEN, "不能在這段對話發言。")
    client_id = (client_message_id or "").strip() or None
    if client_id is not None and len(client_id) > 64:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "訊息編號太長。")
    if client_id is not None:
        existing = db.scalar(
            select(SupportMessage).where(
                SupportMessage.conversation_id == conversation.id, SupportMessage.client_message_id == client_id
            )
        )
        if existing is not None:
            return existing

    message = SupportMessage(conversation_id=conversation.id, sender_id=sender.id, client_message_id=client_id, body=text)
    db.add(message)
    _commit(db)
    db.refresh(message)
    return message


def list_support_messages(db: Session, conversation_id: uuid.UUID) -> list[SupportMessage]:
    return list(
        db.scalars(
            select(SupportMessage)
            .where(SupportMessage.conversation_id == conversation_id)
            .order_by(SupportMessage.created_at.asc())
        )
    )


def mark_read(db: Session, conversation: SupportConversation, reader: User) -> None:
    """使用者讀到管理員的訊息；管理員讀到使用者的訊息。"""
    messages = list_support_messages(db, conversation.id)
    now = datetime.now(timezone.utc)
    changed = False
    for message in messages:
        from_user = message.sender_id == conversation.user_id
        if message.read_at is None and (from_user if reader.role == "admin" else not from_user):
            message.read_at = now
            changed = True
    if changed:
        _commit(db)


def conversation_summary(db: Session, conversations: list[SupportConversation], for_admin: bool) -> list[dict]:
    """列表資訊：對方姓名、身分、未讀數、最後一則訊息。"""
    if not conversations:
        return []
    ids = [item.id for item in conversations]
    users = {user.id: user for user in db.scalars(select(User).where(User.id.in_({c.user_id for c in conversations})))}
    unread_rows = db.execute(
        select(SupportMessage.conversation_id, SupportMessage.sender_id, func.count())
        .where(SupportMessage.conversation_id.in_(ids), SupportMessage.read_at.is_(None))
        .group_by(SupportMessage.conversation_id, SupportMessage.sender_id)
    ).all()
    owners = {item.id: item.user_id for item in conversations}
    unread: dict[uuid.UUID, int] = {}
    for conversation_id, sender_id, count in unread_rows:
        from_user = sender_id == owners[conversation_id]
        if from_user == for_admin:
            unread[conversation_id] = unread.get(conversation_id, 0) + count
    last: dict[uuid.UUID, SupportMessage] = {}
    for message in db.scalars(
        select(SupportMessage).where(SupportMessage.conversation_id.in_(ids)).order_by(SupportMessage.created_at.asc())
    ):
        last[message.conversation_id] = message

    rows = []
    for item in conversations:
        user = users.get(item.user_id)
        latest = last.get(item.id)
        rows.append(
            {
                "id": item.id,
                "user_id": item.user_id,
                "user_name": user.name if user else "使用者",
                "user_role": user.role if user else "",
                "created_at": item.created_at,
                "unread_count": unread.get(item.id, 0),
                "last_message": latest.body if latest else None,
                "last_message_at": latest.created_at if latest else None,
            }
        )
    rows.sort(key=lambda row: row["last_message_at"] or row["created_at"], reverse=True)
    return rows


def _any_admin(db: Session) -> User | None:
    return db.scalar(
        select(User).where(User.role == "admin", User.is_active.is_(True)).order_by(User.created_at.asc()).limit(1)
    )


def send_welcome(db: Session, user: User, admin: User | None = None) -> None:
    """老師審核通過、學生註冊時呼叫。沒有管理員帳號或寫入失敗時只記 log，不讓原本的動作失敗。"""
    template = TEACHER_WELCOME if user.role == "teacher" else STUDENT_WELCOME
    try:
        sender = admin or _any_admin(db)
        if sender is None:
            logger.warning("沒有管理員帳號，略過歡迎訊息：%s", user.id)
            return
        conversation = get_or_create_conversation(db, user.id)
        add_support_message(db, conversation, sender, template.format(name=user.name))
    except Exception:
        db.rollback()
        logger.exception("歡迎訊息沒有送出：%s", user.id)
