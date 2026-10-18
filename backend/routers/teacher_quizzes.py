from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.teacher import get_current_teacher
from backend.models.quiz import QuizDB
from backend.models.teacher import TeacherDB

router = APIRouter()

@router.get("/teacher/quizzes")
def get_my_quizzes(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    return (
        db.query(QuizDB)
        .filter(
            QuizDB.teacher_id == teacher.id
        )
        .all()
    )
