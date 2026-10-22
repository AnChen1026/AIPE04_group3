# SQLAlchemy Model，定義資料庫 Table 與欄位關係。
# 定義 PostgreSQL 資料表在 Python 裡的樣子。

from backend.models.auth_identity import AuthIdentity
from backend.models.base import Base
from backend.models.material import MaterialDB
from backend.models.password_reset import PasswordResetRequest
from backend.models.quiz import QuizDB
from backend.models.teacher_application import TeacherApplication
from backend.models.teacher import TeacherDB
from backend.models.user import User

__all__ = [
    "AuthIdentity",
    "Base",
    "MaterialDB",
    "PasswordResetRequest",
    "QuizDB",
    "TeacherApplication",
    "TeacherDB",
    "User",
]
