"""使用者註冊流程。"""

from sqlalchemy.orm import Session

from backend.core.security import hash_password, verify_password
from backend.models.user import User
from backend.repositories.user import add_user, get_user_by_email
from backend.repositories.teacher_application import get_application_by_user_id
from backend.schemas.user import UserRegister, UserResponse, UserUpdate


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


def build_user_response(db: Session, user: User) -> UserResponse:
    """把使用者轉成前端可用的 JSON；老師會附上申請狀態。"""
    application_status = None
    if user.role == "teacher":
        application = get_application_by_user_id(db, user.id)
        if application is not None:
            application_status = application.status

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        phone_number=user.phone_number,
        birthdate=user.birthdate,
        sex=user.sex,
        role=user.role,
        is_active=user.is_active,
        auth_provider=user.auth_provider,
        application_status=application_status,
        created_at=user.created_at,
    )
