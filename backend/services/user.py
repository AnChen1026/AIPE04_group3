"""使用者註冊流程。"""

from sqlalchemy.orm import Session

from backend.core.security import hash_password
from backend.models.user import User
from backend.repositories.user import add_user, get_user_by_email
from backend.schemas.user import UserRegister


class EmailAlreadyRegisteredError(ValueError):
    """Email 已經被其他帳號使用。"""


def register_user(db: Session, register_data: UserRegister) -> User:
    """檢查 Email、雜湊密碼並建立使用者。"""
    normalized_email = str(register_data.email).strip().lower()

    existing_user = get_user_by_email(db, normalized_email)
    if existing_user is not None:
        raise EmailAlreadyRegisteredError("此 Email 已經註冊。")

    user = User(
        email=normalized_email,
        password_hash=hash_password(register_data.password),
        name=register_data.name,
        phone_number=register_data.phone_number,
        birthdate=register_data.birthdate,
        sex=register_data.sex,
        role=register_data.role,
    )

    add_user(db, user)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    return user
