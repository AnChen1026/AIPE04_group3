from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.user import User
from backend.dependencies import get_current_user
from teacher.models import TeacherDB
from teacher.services.teacher_sync import _ensure_teacher_profile

def get_current_teacher(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # -----------------------------------------------------
    # 1. 必須是教師
    # -----------------------------------------------------

    if user.role != "teacher":
        raise HTTPException(
            status_code=403,
            detail="只有教師可以使用此功能",
        )

    # -----------------------------------------------------
    # 2. 教師帳號必須通過審核
    # -----------------------------------------------------

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="教師帳號尚未通過審核",
        )

    # -----------------------------------------------------
    # 3. 找到教師 profile
    # -----------------------------------------------------

    teacher = (
        db.query(TeacherDB)
        .filter(
            TeacherDB.user_id == user.id
        )
        .first()
    )

    if teacher is None:
        # 舊教師帳號：第一次使用教師功能時補建 profile。
        teacher = _ensure_teacher_profile(db, user)
        db.commit()
        db.refresh(teacher)

    if teacher is None:
        raise HTTPException(
            status_code=500,
            detail="教師帳號已通過審核，但建立教師資料失敗",
        )

    expected_status = "active" if user.is_active else "pending"
    if teacher.status != expected_status:
        teacher.status = expected_status
        db.commit()
        db.refresh(teacher)

    return teacher

