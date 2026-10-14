from datetime import date
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import event
from backend.models.user import User
from backend.models import TeacherDB

def _calculate_age(birthdate: date | None) -> int:
    if birthdate is None:
        return 0
    today = date.today()
    return today.year - birthdate.year - (
        (today.month, today.day) < (birthdate.month, birthdate.day)
    )

def _ensure_teacher_profile(session: Session, user: User) -> TeacherDB | None:
    """確保 teacher 使用者一定有 teacher_profiles。"""
    if user.role != "teacher":
        return None

    teacher = (
        session.query(TeacherDB)
        .filter(TeacherDB.user_id == user.id)
        .first()
    )

    if teacher is not None:
        teacher.status = "active" if user.is_active else "pending"
        return teacher

    teacher = TeacherDB(
        id=uuid.uuid4(),
        user_id=user.id,
        name=user.name,
        gender=user.sex or "未填寫",
        age=_calculate_age(user.birthdate),
        seniority=0,
        expertise="未填寫",
        short_intros="未填寫",
        teaching_city="未填寫",
        teaching_district="未填寫",
        target_learning="未填寫",
        teaching_method="未填寫",
        teaching_style="未填寫",
        status="active" if user.is_active else "pending",
    )
    session.add(teacher)
    return teacher

@event.listens_for(Session, "after_flush")
def sync_teacher_profile_after_user_flush(session: Session, flush_context) -> None:
    """共用 auth router 建立／更新 User 時，同步 teacher_profiles。"""
    users_to_sync = []

    for obj in list(session.new):
        if isinstance(obj, User) and obj.role == "teacher":
            users_to_sync.append(obj)

    for obj in list(session.dirty):
        if isinstance(obj, User) and obj.role == "teacher":
            users_to_sync.append(obj)

    seen = set()
    for user in users_to_sync:
        if user.id in seen:
            continue
        seen.add(user.id)
        _ensure_teacher_profile(session, user)
