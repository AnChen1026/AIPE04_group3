# Pydantic Schema。定義 API 的 request / response 格式
# 定義 API 收到和回傳的資料格式，並做資料驗證。

from backend.schemas.user import (
    GoogleUrlResponse,
    TeacherApplicationForm,
    TeacherApplicationResponse,
    TeacherRegister,
    UserRegister,
    UserResponse,
    UserUpdate,
)

__all__ = [
    "GoogleUrlResponse",
    "TeacherApplicationForm",
    "TeacherApplicationResponse",
    "TeacherRegister",
    "UserRegister",
    "UserResponse",
    "UserUpdate",
]