"""接洽對話的列表資訊：課程、對方姓名、是否已綁定、未讀數與最後一則訊息。

學生與老師的對話列表共用。每個人只會拿到自己參與的對話。
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.student import BindingCode, ConversationMessage, Course, CourseBinding, InquiryConversation
from backend.models.user import User


def conversation_rows(
    db: Session,
    conversations: list[InquiryConversation],
    reader_id: uuid.UUID,
    include_code: bool = False,
) -> list[dict]:
    """include_code 只給老師用：帶上已發出、學生還沒使用的綁定碼。"""
    if not conversations:
        return []
    ids = [conversation.id for conversation in conversations]

    courses = {
        course.id: course
        for course in db.scalars(select(Course).where(Course.id.in_({c.course_id for c in conversations})))
    }
    people_ids = {c.student_id for c in conversations} | {c.teacher_id for c in conversations}
    names = dict(db.execute(select(User.id, User.name).where(User.id.in_(people_ids))).all())
    bound = {
        (binding.student_id, binding.course_id)
        for binding in db.scalars(
            select(CourseBinding).where(
                CourseBinding.course_id.in_({c.course_id for c in conversations}),
                CourseBinding.status == "bound",
            )
        )
    }
    unread = dict(
        db.execute(
            select(ConversationMessage.conversation_id, func.count())
            .where(
                ConversationMessage.conversation_id.in_(ids),
                ConversationMessage.sender_id != reader_id,
                ConversationMessage.read_at.is_(None),
            )
            .group_by(ConversationMessage.conversation_id)
        ).all()
    )
    latest_time = (
        select(ConversationMessage.conversation_id, func.max(ConversationMessage.created_at).label("latest"))
        .where(ConversationMessage.conversation_id.in_(ids))
        .group_by(ConversationMessage.conversation_id)
        .subquery()
    )
    last_messages = {
        message.conversation_id: message
        for message in db.scalars(
            select(ConversationMessage).join(
                latest_time,
                (ConversationMessage.conversation_id == latest_time.c.conversation_id)
                & (ConversationMessage.created_at == latest_time.c.latest),
            )
        )
    }

    codes: dict = {}
    if include_code:
        for code in db.scalars(
            select(BindingCode)
            .where(BindingCode.conversation_id.in_(ids), BindingCode.used_at.is_(None))
            .order_by(BindingCode.created_at.asc())
        ):
            codes[code.conversation_id] = code.code

    rows = []
    for conversation in conversations:
        course = courses.get(conversation.course_id)
        last = last_messages.get(conversation.id)
        rows.append(
            {
                "id": conversation.id,
                "course_id": conversation.course_id,
                "teacher_id": conversation.teacher_id,
                "student_id": conversation.student_id,
                "created_at": conversation.created_at,
                "course_title": course.title if course else "課程",
                "course_style": course.style if course else None,
                "course_level": course.level if course else None,
                "teacher_name": names.get(conversation.teacher_id, "老師"),
                "student_name": names.get(conversation.student_id, "學生"),
                "bound": (conversation.student_id, conversation.course_id) in bound,
                "unread_count": unread.get(conversation.id, 0),
                "last_message": last.body if last else None,
                "last_message_at": last.created_at if last else None,
                "binding_code": codes.get(conversation.id),
            }
        )
    # 有新訊息的對話排前面
    rows.sort(key=lambda row: row["last_message_at"] or row["created_at"], reverse=True)
    return rows
