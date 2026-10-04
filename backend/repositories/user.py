"""User Model 的資料庫存取。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.user import User


def get_user_by_email(db: Session, email: str) -> User | None:
    """依 Email 查詢一位使用者。"""
    statement = select(User).where(User.email == email)
    return db.scalar(statement)


def add_user(db: Session, user: User) -> None:
    """把新使用者加入目前的資料庫交易。"""
    db.add(user)
