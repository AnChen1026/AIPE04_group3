from datetime import datetime, date
from pathlib import Path
from uuid import UUID as UUIDType
import uuid
from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.user import User
from backend.dependencies import get_current_user
from teacher.models import *
from teacher.schemas import *
from teacher.dependencies.teacher import get_current_teacher
from teacher.services.teacher_sync import _ensure_teacher_profile
from teacher.core.uploads import MATERIAL_UPLOAD_DIR

router = APIRouter()

@router.get("/teacher/me")
def get_my_teacher(
    teacher: TeacherDB = Depends(get_current_teacher),
):
    return teacher

@router.post("/teacher/profile")
def create_teacher(
    data: TeacherIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    # -----------------------------------------------------
    # 必須是 teacher
    # -----------------------------------------------------

    if user.role != "teacher":
        raise HTTPException(
            status_code=403,
            detail="只有教師可以建立教師資料",
        )

    # -----------------------------------------------------
    # 檢查是否已有教師資料
    # -----------------------------------------------------

    existing = (
        db.query(TeacherDB)
        .filter(
            TeacherDB.user_id == user.id
        )
        .first()
    )

    if existing:
        # 自動同步已先建立 profile，這裡改為更新資料。
        teacher = existing
        teacher.name = data.name
        teacher.gender = data.gender
        teacher.age = data.age
        teacher.seniority = data.seniority
        teacher.expertise = data.expertise
        teacher.short_intros = data.short_intros
        teacher.teaching_city = data.teaching_city
        teacher.teaching_district = data.teaching_district
        teacher.target_learning = data.target_learning
        teacher.teaching_method = data.teaching_method
        teacher.teaching_style = data.teaching_style
        teacher.status = "active" if user.is_active else data.status
        db.commit()
        db.refresh(teacher)
        return teacher

    # -----------------------------------------------------
    # 建立教師
    # -----------------------------------------------------

    teacher = TeacherDB(
        id=uuid.uuid4(),
        user_id=user.id,

        name=data.name,
        gender=data.gender,
        age=data.age,
        seniority=data.seniority,
        expertise=data.expertise,
        short_intros=data.short_intros,
        teaching_city=data.teaching_city,
        teaching_district=data.teaching_district,
        target_learning=data.target_learning,
        teaching_method=data.teaching_method,
        teaching_style=data.teaching_style,

        status=data.status,
    )

    db.add(teacher)
    db.commit()
    db.refresh(teacher)

    return teacher

@router.get("/teachers/{teacher_id}")
def get_teacher(
    teacher_id: UUIDType,
    db: Session = Depends(get_db),
    current_teacher: TeacherDB = Depends(
        get_current_teacher
    ),
):

    # 只能查看自己
    if current_teacher.id != teacher_id:
        raise HTTPException(
            status_code=403,
            detail="不能查看其他教師資料",
        )

    teacher = (
        db.query(TeacherDB)
        .filter(
            TeacherDB.id == teacher_id
        )
        .first()
    )

    if not teacher:
        raise HTTPException(
            status_code=404,
            detail="找不到教師",
        )

    return teacher

@router.get("/teacher/auth-status")
def teacher_auth_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    teacher = (
        db.query(TeacherDB)
        .filter(
            TeacherDB.user_id == user.id
        )
        .first()
    )

    # 舊的已核准教師帳號也在這裡補建 profile。
    if user.role == "teacher" and user.is_active and teacher is None:
        teacher = _ensure_teacher_profile(db, user)
        db.commit()
        db.refresh(teacher)

    return {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "has_teacher_profile":
            teacher is not None,
        "teacher_id":
            teacher.id if teacher else None,
        "teacher_profile_status":
            teacher.status if teacher else None,
    }

