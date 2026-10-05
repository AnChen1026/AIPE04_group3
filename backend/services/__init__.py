# 業務邏輯。處理功能流程與資料處理規則
# 功能的主要邏輯，例如新增課程前要做哪些判斷。

from backend.services.user import (
    EmailAlreadyRegisteredError,
    authenticate_user,
    register_user,
    update_user_profile,
)
from backend.services.teacher import (
    InvalidProofFileError,
    TeacherApplicationExistsError,
    approve_teacher_application,
    register_teacher,
    reject_teacher_application,
    submit_teacher_application,
)

__all__ = [
    "EmailAlreadyRegisteredError",
    "authenticate_user",
    "register_user",
    "update_user_profile",
    "InvalidProofFileError",
    "TeacherApplicationExistsError",
    "approve_teacher_application",
    "register_teacher",
    "reject_teacher_application",
    "submit_teacher_application",
]