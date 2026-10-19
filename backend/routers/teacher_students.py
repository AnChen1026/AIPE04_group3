import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.common import require_roles
from backend.dependencies.teacher import get_current_teacher
from backend.models.student import Course, CourseBinding
from backend.models.teacher import TeacherDB
from backend.models.user import User
from backend.services.student import StudentBusinessError, unbind_student

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
    titles = dict(
        db.query(Course.id, Course.title).filter(Course.id.in_({binding.course_id for binding in bindings})).all()
    )
    courses_by_student: dict = {}
    for binding in bindings:
        courses_by_student.setdefault(binding.student_id, []).append(
            {"course_id": binding.course_id, "course_title": titles.get(binding.course_id, "課程"), "bound_at": binding.bound_at}
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
            "courses": courses_by_student.get(student.id, []),
        })
    return students


@router.post("/teacher/courses/{course_id}/students/{student_id}/unbind")
def unbind(
    course_id: uuid.UUID,
    student_id: uuid.UUID,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_roles("teacher")),
):
    """解除這位學生在這門課的綁定。該課教學功能關閉，對話保留。"""
    try:
        binding = unbind_student(db, teacher, course_id, student_id)
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    return {"course_id": binding.course_id, "student_id": binding.student_id, "status": binding.status}
