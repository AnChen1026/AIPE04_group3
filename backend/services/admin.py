"""測試環境建立管理員帳號。"""

from sqlalchemy.orm import Session

from backend.core.config import read_env_value
from backend.core.security import hash_password
from backend.models.user import User
from backend.repositories.user import add_user, get_user_by_email


def seed_admin_if_needed(db: Session) -> None:
    """若 .env 有管理員帳密，且資料庫還沒有這個 Email，就建立 admin。"""
    email = read_env_value("ADMIN_EMAIL")
    password = read_env_value("ADMIN_PASSWORD")
    if email is None or password is None:
        return

    normalized_email = email.strip().lower()
    existing = get_user_by_email(db, normalized_email)
    if existing is not None:
        return

    admin = User(
        email=normalized_email,
        password_hash=hash_password(password),
        auth_provider="password",
        name="平台管理員",
        phone_number=None,
        birthdate=None,
        sex=None,
        role="admin",
        is_active=True,
    )
    add_user(db, admin)
    db.commit()
