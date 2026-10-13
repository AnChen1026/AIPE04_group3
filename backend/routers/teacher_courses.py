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

@router.post("/courses")
def create_course(
    data: CourseIn,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    # -----------------------------------------------------
    # 如果有指定學生，確認是不是自己的學生
    # -----------------------------------------------------

    if data.student_id is not None:

        binding = (
            db.query(BindingDB)
            .filter(
                BindingDB.teacher_id == teacher.id,
                BindingDB.student_id == data.student_id,
                BindingDB.status == "active",
            )
            .first()
        )

        if not binding:
            raise HTTPException(
                status_code=403,
                detail="此學生不是目前教師的學生",
            )

    # -----------------------------------------------------
    # 建立課程
    # -----------------------------------------------------

    course = CourseDB(
        id=uuid.uuid4(),

        studio_id=data.studio_id,

        teacher_profile_id=teacher.id,

        course_name=data.course_name,
        course_intros=data.course_intros,

        course_price=data.course_price,

        class_date=data.class_date,

        price_per_lesson=data.price_per_lesson,

        start_at=data.start_at,
        end_at=data.end_at,

        duration_minutes=data.duration_minutes,

        status=data.status,

        student_id=data.student_id,
    )

    db.add(course)
    db.commit()
    db.refresh(course)

    return course

@router.get("/teacher/courses")
def get_my_courses(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    return (
        db.query(CourseDB)
        .filter(
            CourseDB.teacher_profile_id == teacher.id
        )
        .all()
    )

@router.get("/teachers/{teacher_id}/courses")
def get_teacher_courses(
    teacher_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    if teacher.id != teacher_id:
        raise HTTPException(
            status_code=403,
            detail="不能查看其他教師的課程",
        )

    return (
        db.query(CourseDB)
        .filter(
            CourseDB.teacher_profile_id == teacher.id
        )
        .all()
    )

@router.get("/courses/{course_id}")
def get_course(
    course_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    course = (
        db.query(CourseDB)
        .filter(
            CourseDB.id == course_id
        )
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=404,
            detail="找不到課程",
        )

    if course.teacher_profile_id != teacher.id:
        raise HTTPException(
            status_code=403,
            detail="不能查看其他教師的課程",
        )

    return course

@router.delete("/courses/{course_id}")
def archive_course(
    course_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    course = (
        db.query(CourseDB)
        .filter(
            CourseDB.id == course_id
        )
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=404,
            detail="找不到課程",
        )

    if course.teacher_profile_id != teacher.id:
        raise HTTPException(
            status_code=403,
            detail="不能封存其他教師的課程",
        )

    course.status = "archived"

    db.commit()

    return {
        "message": "課程已封存"
    }

