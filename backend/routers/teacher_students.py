from datetime import datetime, date
from pathlib import Path
from uuid import UUID as UUIDType
import uuid
from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.user import User
from backend.dependencies.common import get_current_user
from backend.models import *
from backend.schemas import *
from backend.dependencies.teacher import get_current_teacher
from backend.services.teacher_sync import _ensure_teacher_profile
from backend.core.uploads import MATERIAL_UPLOAD_DIR

router = APIRouter()

@router.get("/teacher/students")
def get_my_students(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    bindings = (
        db.query(BindingDB)
        .filter(
            BindingDB.teacher_id == teacher.id,
            BindingDB.status == "active",
        )
        .all()
    )

    students = []

    for binding in bindings:

        student = (
            db.query(User)
            .filter(
                User.id == binding.student_id,
                User.role == "student",
                User.is_active.is_(True),
            )
            .first()
        )

        if student:
            students.append({
                "id": student.id,
                "email": student.email,
                "name": student.name,
                "phone_number": student.phone_number,
                "birthdate": student.birthdate,
                "sex": student.sex,
                "role": student.role,
                "is_active": student.is_active,
                "auth_provider": student.auth_provider,
                "created_at": student.created_at,
            })

    return students

@router.get("/teachers/{teacher_id}/students")
def get_teacher_students(
    teacher_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    if teacher.id != teacher_id:
        raise HTTPException(
            status_code=403,
            detail="不能查看其他教師的學生",
        )

    bindings = (
        db.query(BindingDB)
        .filter(
            BindingDB.teacher_id == teacher.id,
            BindingDB.status == "active",
        )
        .all()
    )

    students = []

    for binding in bindings:

        student = (
            db.query(User)
            .filter(
                User.id == binding.student_id,
                User.role == "student",
                User.is_active.is_(True),
            )
            .first()
        )

        if student:
            students.append({
                "id": student.id,
                "email": student.email,
                "name": student.name,
                "phone_number": student.phone_number,
                "birthdate": student.birthdate,
                "sex": student.sex,
                "role": student.role,
                "is_active": student.is_active,
                "auth_provider": student.auth_provider,
                "created_at": student.created_at,
            })

    return students

