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

@router.post("/bindings")
def create_binding(
    data: BindingIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    # -----------------------------------------------------
    # 檢查學生
    # -----------------------------------------------------

    student = (
        db.query(User)
        .filter(
            User.id == data.student_id,
            User.role == "student",
            User.is_active.is_(True),
        )
        .first()
    )

    if not student:
        raise HTTPException(
            status_code=404,
            detail="找不到學生",
        )

    # -----------------------------------------------------
    # 檢查工作室
    # -----------------------------------------------------

    studio = (
        db.query(StudioDB)
        .filter(
            StudioDB.id == data.studio_id
        )
        .first()
    )

    if not studio:
        raise HTTPException(
            status_code=404,
            detail="找不到工作室",
        )

    # -----------------------------------------------------
    # 檢查是否已經存在
    # -----------------------------------------------------

    existing = (
        db.query(BindingDB)
        .filter(
            BindingDB.studio_id == data.studio_id,
            BindingDB.teacher_id == teacher.id,
            BindingDB.student_id == data.student_id,
        )
        .first()
    )

    if existing:

        raise HTTPException(
            status_code=400,
            detail="這組師生關係已經存在",
        )

    # -----------------------------------------------------
    # 建立綁定
    # -----------------------------------------------------

    binding = BindingDB(
        id=uuid.uuid4(),

        studio_id=data.studio_id,

        teacher_id=teacher.id,

        student_id=data.student_id,

        requested_by_user_id=user.id,

        status="pending",
    )

    db.add(binding)
    db.commit()
    db.refresh(binding)

    return {
        "message": "師生綁定申請已建立",
        "binding_id": binding.id,
        "status": binding.status,
    }

@router.post("/bindings/{binding_id}/teacher-confirm")
def teacher_confirm_binding(
    binding_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    binding = (
        db.query(BindingDB)
        .filter(
            BindingDB.id == binding_id
        )
        .first()
    )

    if not binding:
        raise HTTPException(
            status_code=404,
            detail="找不到師生綁定",
        )

    # -----------------------------------------------------
    # 確認是不是自己的綁定
    # -----------------------------------------------------

    if binding.teacher_id != teacher.id:
        raise HTTPException(
            status_code=403,
            detail="不能確認其他教師的師生綁定",
        )

    binding.teacher_confirmed_at = datetime.now()

    # 如果學生也已確認
    if binding.student_confirmed_at is not None:
        binding.status = "active"

    db.commit()
    db.refresh(binding)

    return {
        "message": "教師已確認",
        "binding_id": binding.id,
        "status": binding.status,
    }

@router.post("/bindings/{binding_id}/student-confirm")
def student_confirm_binding(
    binding_id: UUIDType,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):

    if user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="只有學生可以確認學生端綁定",
        )

    student = user

    binding = (
        db.query(BindingDB)
        .filter(
            BindingDB.id == binding_id
        )
        .first()
    )

    if not binding:
        raise HTTPException(
            status_code=404,
            detail="找不到師生綁定",
        )

    if binding.student_id != student.id:
        raise HTTPException(
            status_code=403,
            detail="不能確認其他學生的綁定",
        )

    binding.student_confirmed_at = datetime.now()

    if binding.teacher_confirmed_at is not None:
        binding.status = "active"

    db.commit()
    db.refresh(binding)

    return {
        "message": "學生已確認",
        "binding_id": binding.id,
        "status": binding.status,
    }

