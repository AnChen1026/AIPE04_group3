from uuid import UUID as UUIDType
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.student import Course
from backend.models.teacher import TeacherDB
from backend.schemas.course import CourseIn
from backend.schemas.student import CourseResponse
from backend.dependencies.teacher import get_current_teacher

router = APIRouter()

ALLOWED_STATUS = {"draft", "published", "archived"}


def get_own_course(db: Session, teacher: TeacherDB, course_id: UUIDType) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if course is None:
        raise HTTPException(status_code=404, detail="找不到課程")
    if course.teacher_id != teacher.user_id:
        raise HTTPException(status_code=403, detail="不能查看其他教師的課程")
    return course


@router.post("/courses", response_model=CourseResponse)
def create_course(
    data: CourseIn,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    title = data.title.strip()
    if title == "":
        raise HTTPException(status_code=400, detail="課程名稱不能是空白。")
    if data.status not in ALLOWED_STATUS:
        raise HTTPException(status_code=400, detail="課程狀態只能是草稿、已發布或已封存。")

    course = Course(
        id=uuid.uuid4(),
        teacher_id=teacher.user_id,
        title=title,
        level=data.level,
        style=data.style,
        delivery_mode=data.delivery_mode,
        region=data.region,
        price_per_lesson=data.price_per_lesson,
        time_slots=data.time_slots,
        status=data.status,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.get("/teacher/courses", response_model=list[CourseResponse])
def get_my_courses(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    courses = (
        db.query(Course)
        .filter(Course.teacher_id == teacher.user_id)
        .all()
    )
    return courses


@router.get("/teachers/{teacher_id}/courses", response_model=list[CourseResponse])
def get_teacher_courses(
    teacher_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    if teacher.id != teacher_id:
        raise HTTPException(status_code=403, detail="不能查看其他教師的課程")

    courses = (
        db.query(Course)
        .filter(Course.teacher_id == teacher.user_id)
        .all()
    )
    return courses


@router.get("/courses/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    return get_own_course(db, teacher, course_id)


@router.delete("/courses/{course_id}")
def archive_course(
    course_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    course = get_own_course(db, teacher, course_id)
    course.status = "archived"
    db.commit()
    return {"message": "課程已封存"}
