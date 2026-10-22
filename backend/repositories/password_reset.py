"""PasswordResetRequest 的資料庫存取。"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.models.password_reset import PasswordResetRequest


def get_pending_request_for_user(db: Session, user_id: uuid.UUID) -> PasswordResetRequest | None:
    statement = select(PasswordResetRequest).where(
        PasswordResetRequest.user_id == user_id,
        PasswordResetRequest.status == "pending",
    )
    return db.scalar(statement)


def get_request_by_id(db: Session, request_id: uuid.UUID) -> PasswordResetRequest | None:
    statement = (
        select(PasswordResetRequest)
        .options(joinedload(PasswordResetRequest.user))
        .where(PasswordResetRequest.id == request_id)
    )
    return db.scalar(statement)


def list_requests(db: Session, limit: int = 100) -> list[PasswordResetRequest]:
    """待處理的在前面，其餘依時間新到舊。"""
    statement = (
        select(PasswordResetRequest)
        .options(joinedload(PasswordResetRequest.user))
        .order_by((PasswordResetRequest.status != "pending"), PasswordResetRequest.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement).unique())
