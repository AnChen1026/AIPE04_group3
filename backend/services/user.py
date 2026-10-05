"""使用者註冊流程。"""

from sqlalchemy.orm import Session

from backend.core.security import hash_password, verify_password
from backend.models.user import User
from backend.repositories.user import add_user, get_user_by_email
from backend.schemas.user import UserRegister, UserUpdate


class EmailAlreadyRegisteredError(ValueError):
    """Email 已經被其他帳號使用。"""


def register_user(db: Session, register_data: UserRegister) -> User:
    """檢查 Email、雜湊密碼並建立學生帳號。"""
    normalized_email = str(register_data.email).strip().lower()

    existing_user = get_user_by_email(db, normalized_email)
    if existing_user is not None:
        raise EmailAlreadyRegisteredError("此 Email 已經註冊。")

    user = User(
        email=normalized_email,
        password_hash=hash_password(register_data.password),
        auth_provider="password",
        name=register_data.name,
        phone_number=register_data.phone_number,
        birthdate=register_data.birthdate,
        sex=register_data.sex,
        role="student",
        is_active=True,
    )

    add_user(db, user)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    return user


def update_user_profile(db: Session, user: User, profile_data: UserUpdate) -> User:
    """更新目前登入使用者的基本資料。"""
    user.name = profile_data.name
    user.phone_number = profile_data.phone_number
    user.birthdate = profile_data.birthdate
    user.sex = profile_data.sex

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """檢查帳號與密碼，成功時回傳使用者。"""
    normalized_email = email.strip().lower()
    user = get_user_by_email(db, normalized_email)

    if user is None:
        return None

    if user.password_hash is None:
        return None

    if verify_password(password, user.password_hash) is False:
        return None

    return user
