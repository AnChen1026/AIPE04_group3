"""老師個人資料的規則：帳號資料（姓名、性別、手機、生日）和對學生顯示的介紹在同一頁維護，
照片以外都要填完，才能建立課程。對學生顯示的性別就是帳號性別，不另外選；年齡不再填。"""

from sqlalchemy.orm import Session

from backend.models.teacher import TeacherDB
from backend.models.user import User

# 存在 teacher_profiles 的介紹欄位（age 欄位留在資料表裡，但畫面不再填）
PROFILE_FIELDS = (
    "seniority",
    "expertise",
    "short_intros",
    "teaching_city",
    "teaching_district",
    "target_learning",
    "teaching_method",
    "teaching_style",
)
# 回傳給前端時多帶 age，舊資料還看得到
RESPONSE_FIELDS = ("age", *PROFILE_FIELDS)

SEX_TO_GENDER = {"male": "男", "female": "女"}


def gender_of(user: User | None) -> str | None:
    """帳號性別換成學生看到的「男／女」；沒填時是 None。"""
    return SEX_TO_GENDER.get(user.sex or "") if user else None


def profile_complete(teacher: TeacherDB, user: User | None) -> bool:
    """帳號的姓名、性別、手機、生日，以及介紹欄位都填了。照片不用。"""
    if user is None or not (user.name or "").strip() or gender_of(user) is None:
        return False
    if not user.phone_number or user.birthdate is None:
        return False
    return all(getattr(teacher, field) not in (None, "") for field in PROFILE_FIELDS)


def account_of(db: Session, teacher: TeacherDB) -> User | None:
    return db.get(User, teacher.user_id)
