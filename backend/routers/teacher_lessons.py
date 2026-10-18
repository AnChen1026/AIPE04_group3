from uuid import UUID as UUIDType

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.teacher import get_current_teacher
from backend.models.student import LessonSession
from backend.models.teacher import TeacherDB
from backend.schemas.student import LessonSummaryResponse
from backend.services.lesson_summary import get_lesson_summary
from backend.services.student import StudentBusinessError

router = APIRouter()

@router.get("/teacher/lessons")
def get_my_lessons(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    return (
        db.query(LessonSession)
        .filter(LessonSession.teacher_id == teacher.user_id)
        .all()
    )


@router.get("/teacher/lessons/{lesson_id}/summary", response_model=LessonSummaryResponse)
def lesson_summary(
    lesson_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """這堂課的課前摘要：上一堂結束到這一堂開始前的練習整理。"""
    try:
        return get_lesson_summary(db, teacher.user_id, lesson_id)
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
