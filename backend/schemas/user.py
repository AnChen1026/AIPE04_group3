"""使用者註冊的輸入與輸出格式。"""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """一般使用者註冊資料；公開註冊不允許 admin。"""

    email: EmailStr
    password: str
    name: str = Field(min_length=1, max_length=100)
    phone_number: str | None = Field(default=None, max_length=50)
    birthdate: date | None = None
    sex: str | None = Field(default=None, max_length=32)
    role: Literal["teacher", "student"]


class UserResponse(BaseModel):
    """可以安全回傳給前端的使用者資料。"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    name: str
    phone_number: str | None
    birthdate: date | None
    sex: str | None
    role: str
    is_active: bool
    created_at: datetime
