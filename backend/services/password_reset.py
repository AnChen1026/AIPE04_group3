"""忘記密碼（地端版本）：使用者送出 Email，管理員在後台替他重設成臨時密碼。

- 不管 Email 有沒有註冊，回給使用者的訊息都一樣，避免被拿來查誰有帳號。
- 只替學生與老師帳號建立申請；管理員帳號不走這個流程。
- 同一個帳號已有待處理的申請時不再新增，避免重複。
- 臨時密碼只在重設當下回給管理員一次，資料庫只存雜湊。
"""

import secrets
import uuid
from datetime import datetime, timezone

from fastapi import status
from sqlalchemy.orm import Session

from backend.core.security import hash_password
from backend.models.password_reset import PasswordResetRequest
from backend.models.user import User
from backend.repositories.password_reset import get_pending_request_for_user, get_request_by_id
from backend.repositories.user import get_user_by_email
from backend.services.student import StudentBusinessError

# 去掉容易看錯的 0/O、1/l/I，管理員念給使用者聽也不會弄錯
TEMPORARY_PASSWORD_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"
TEMPORARY_PASSWORD_LENGTH = 10


def generate_temporary_password() -> str:
    return "".join(secrets.choice(TEMPORARY_PASSWORD_ALPHABET) for _ in range(TEMPORARY_PASSWORD_LENGTH))


def submit_reset_request(db: Session, email: str) -> None:
    """依 Email 建立申請。帳號不存在、是管理員或已有待處理申請時什麼都不做，呼叫端一律回同樣的訊息。"""
    user = get_user_by_email(db, email.strip().lower())
    if user is None or user.role not in ("student", "teacher"):
        return
    if get_pending_request_for_user(db, user.id) is not None:
        return
    db.add(PasswordResetRequest(user_id=user.id, status="pending"))
    db.commit()


def _pending_request(db: Session, request_id: uuid.UUID) -> PasswordResetRequest:
    reset_request = get_request_by_id(db, request_id)
    if reset_request is None:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這筆重設申請。")
    if reset_request.status != "pending":
        raise StudentBusinessError(status.HTTP_409_CONFLICT, "這筆申請已經處理過。")
    return reset_request


def reset_password(db: Session, request_id: uuid.UUID, admin: User) -> tuple[PasswordResetRequest, str]:
    """替申請人設定新的臨時密碼，回傳 (申請, 臨時密碼)。臨時密碼不會存成明文。"""
    reset_request = _pending_request(db, request_id)
    temporary_password = generate_temporary_password()
    reset_request.user.password_hash = hash_password(temporary_password)
    reset_request.status = "completed"
    reset_request.handled_at = datetime.now(timezone.utc)
    reset_request.handled_by = admin.id
    db.commit()
    db.refresh(reset_request)
    return reset_request, temporary_password


def dismiss_request(db: Session, request_id: uuid.UUID, admin: User) -> PasswordResetRequest:
    """不處理這筆申請（例如確認不是本人送的）。密碼不變。"""
    reset_request = _pending_request(db, request_id)
    reset_request.status = "dismissed"
    reset_request.handled_at = datetime.now(timezone.utc)
    reset_request.handled_by = admin.id
    db.commit()
    db.refresh(reset_request)
    return reset_request
