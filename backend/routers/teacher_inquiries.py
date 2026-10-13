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

@router.get("/teacher/inquiries")
def get_my_inquiries(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    courses = (
        db.query(CourseDB)
        .filter(
            CourseDB.teacher_profile_id == teacher.id
        )
        .all()
    )

    course_ids = [
        course.id
        for course in courses
    ]

    if not course_ids:
        return []

    return (
        db.query(InquiryDB)
        .filter(
            InquiryDB.course_id.in_(course_ids)
        )
        .all()
    )

@router.get("/teachers/{teacher_id}/inquiries")
def get_teacher_inquiries(
    teacher_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    if teacher.id != teacher_id:
        raise HTTPException(
            status_code=403,
            detail="不能查看其他教師的詢問",
        )

    courses = (
        db.query(CourseDB)
        .filter(
            CourseDB.teacher_profile_id == teacher.id
        )
        .all()
    )

    course_ids = [
        course.id
        for course in courses
    ]

    if not course_ids:
        return []

    return (
        db.query(InquiryDB)
        .filter(
            InquiryDB.course_id.in_(course_ids)
        )
        .all()
    )

