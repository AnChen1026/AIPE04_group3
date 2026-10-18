from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.teacher import get_current_teacher
from backend.models.student import LessonSession
from backend.models.teacher import TeacherDB

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
