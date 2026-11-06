"""老師個人資料的規則：照片以外都要填完，才能建立課程。"""

from backend.models.teacher import TeacherDB

PROFILE_FIELDS = (
    "age",
    "seniority",
    "expertise",
    "short_intros",
    "teaching_city",
    "teaching_district",
    "target_learning",
    "teaching_method",
    "teaching_style",
)


def profile_complete(teacher: TeacherDB) -> bool:
    """照片以外的欄位都填了，性別也是男或女。"""
    if teacher.gender not in ("男", "女") or not (teacher.name or "").strip():
        return False
    return all(getattr(teacher, field) not in (None, "") for field in PROFILE_FIELDS)
