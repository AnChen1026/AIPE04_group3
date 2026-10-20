"""使用者註冊的輸入與輸出格式。"""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """一般使用者註冊資料；公開註冊不允許 admin。"""

    email: EmailStr
    password: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=100)
    phone_number: str = Field(pattern=r"^09\d{8}$")
    birthdate: date
    sex: Literal["male", "female"]
    role: Literal["student"] = "student"


class TeacherRegister(BaseModel):
    """老師帳密註冊；公開註冊後仍須管理員審核。"""

    email: EmailStr
    password: str = Field(min_length=1)
    name: str = Field(min_length=1, max_length=100)
    phone_number: str = Field(pattern=r"^09\d{8}$")
    birthdate: date
    sex: Literal["male", "female"]
    teaching_subjects: str = Field(min_length=1, max_length=200)
    teaching_experience: str = Field(min_length=1)
    bio: str = Field(min_length=1)
    role: Literal["teacher"] = "teacher"


class TeacherApplicationForm(BaseModel):
    """已有帳號的老師補填申請資料，例如 Google 註冊後。"""

    teaching_subjects: str = Field(min_length=1, max_length=200)
    teaching_experience: str = Field(min_length=1)
    bio: str = Field(min_length=1)


class UserLogin(BaseModel):
    """前端登入時需要傳送的資料。"""

    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """登入後可自行修改的基本資料；Email、角色與密碼不在這一步。"""

    name: str = Field(min_length=1, max_length=100)
    phone_number: str | None = Field(default=None, pattern=r"^09\d{8}$")
    birthdate: date | None = None
    sex: Literal["male", "female"]


class PasswordChange(BaseModel):
    """修改密碼。只用 Google 註冊、還沒有密碼的帳號不用填目前密碼。"""

    current_password: str | None = None
    new_password: str = Field(min_length=8, max_length=128)


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
    auth_provider: str
    application_status: str | None = None
    has_password: bool = True
    """只用 Google 註冊、還沒設定密碼時為 False，修改密碼頁就不用填目前密碼。"""
    created_at: datetime


class UserBrief(BaseModel):
    """申請列表裡需要的使用者摘要。"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    name: str
    role: str
    is_active: bool


class TeacherApplicationResponse(BaseModel):
    """老師申請資料，給前端判斷 pending／approved／rejected。"""

    id: uuid.UUID
    teaching_subjects: str
    teaching_experience: str
    bio: str
    proof_file_name: str | None
    has_proof: bool
    status: str
    created_at: datetime
    user: UserBrief


class GoogleUrlResponse(BaseModel):
    """前端拿到這個網址後，導向 Google。"""

    url: str

