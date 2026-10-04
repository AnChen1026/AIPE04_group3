# 業務邏輯。處理功能流程與資料處理規則
# 功能的主要邏輯，例如新增課程前要做哪些判斷。

from backend.services.user import (
    EmailAlreadyRegisteredError,
    authenticate_user,
    register_user,
)

__all__ = [
    "EmailAlreadyRegisteredError",
    "authenticate_user",
    "register_user",
]