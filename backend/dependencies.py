"""FastAPI 共用的登入與角色權限檢查。"""

import uuid

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.user import User
from backend.repositories.user import get_user_by_id


def get_session_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    """依 Session Cookie 取得目前登入的使用者。"""
    user_id_text = request.session.get("user_id")
    if user_id_text is None:
        return None

    try:
        user_id = uuid.UUID(user_id_text)
    except ValueError:
        request.session.clear()
        return None

    user = get_user_by_id(db, user_id)
    if user is None:
        request.session.clear()
    return user


def get_current_user(
    user: User | None = Depends(get_session_user),
) -> User:
    """要求使用者必須已登入。"""
    if user is None:
        raise HTTPException(status_code=401, detail="尚未登入。")
    return user


def require_roles(*allowed_roles: str):
    """建立限制帳號啟用狀態與角色的共用檢查。"""

    def check_role(user: User = Depends(get_current_user)) -> User:
        if user.is_active is False:
            raise HTTPException(status_code=403, detail="帳號尚未啟用。")
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="沒有使用權限。")
        return user

    return check_role

# 學生端 Dependency 檢查
def get_current_student(
    user: User = Depends(require_roles("student"))
) -> User:
    """
    要求當前使用者必須登入，且角色必須是學生。
    通過後會直接回傳該位學生的 User 物件，方便在 API 中拿到 user.id。
    """
    return user

