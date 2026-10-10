"""User Model 的資料庫存取。"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.user import User


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    """依 UUID 查詢一位使用者。"""
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    """依 Email 查詢一位使用者。"""
    statement = select(User).where(User.email == email)
    return db.scalar(statement)


def add_user(db: Session, user: User) -> None:
    """把新使用者加入目前的資料庫交易。"""
    db.add(user)


def list_users_by_role(db: Session, role: str) -> list[User]:
    """依角色列出使用者，新的在上面。"""
    statement = select(User).where(User.role == role).order_by(User.created_at.desc())
    return list(db.scalars(statement))
