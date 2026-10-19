from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.teacher import get_current_teacher
from backend.models.student import InquiryConversation
from backend.models.teacher import TeacherDB

router = APIRouter()

@router.get("/teacher/inquiries")
def get_my_inquiries(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    return (
        db.query(InquiryConversation)
        .filter(InquiryConversation.teacher_id == teacher.user_id)
        .all()
    )
