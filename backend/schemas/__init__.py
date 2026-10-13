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
from backend.schemas.chat import MessageIn
from backend.schemas.course import CourseIn
from backend.schemas.practice import AssignmentIn
from backend.schemas.studio import BindingIn
from backend.schemas.teacher import TeacherIn

__all__ = [
    "AssignmentIn",
    "BindingIn",
    "CourseIn",
    "GoogleUrlResponse",
    "MessageIn",
    "TeacherApplicationForm",
    "TeacherApplicationResponse",
    "TeacherIn",
    "TeacherRegister",
    "UserRegister",
    "UserResponse",
    "UserUpdate",
]