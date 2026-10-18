from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.teacher import get_current_teacher
from backend.models.student import CourseBinding
from backend.models.teacher import TeacherDB
from backend.models.user import User

router = APIRouter()

@router.get("/teacher/students")
def get_my_students(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

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
