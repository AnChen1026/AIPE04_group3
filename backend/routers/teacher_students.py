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
from backend.models.student import CourseBinding
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

    return _bound_students(db, teacher)

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

    return _bound_students(db, teacher)


def _bound_students(db: Session, teacher: TeacherDB) -> list[dict]:
    """學生名單來自課程綁定，不再讀工作室綁定表。"""
    bindings = (
        db.query(CourseBinding)
        .filter(
            CourseBinding.teacher_id == teacher.user_id,
            CourseBinding.status == "bound",
        )
        .all()
    )
    students = []
    seen_student_ids = set()
    for binding in bindings:
        if binding.student_id in seen_student_ids:
            continue
        seen_student_ids.add(binding.student_id)
        student = (
            db.query(User)
            .filter(
                User.id == binding.student_id,
                User.role == "student",
                User.is_active.is_(True),
            )
            .first()
        )
        if student is None:
            continue
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

