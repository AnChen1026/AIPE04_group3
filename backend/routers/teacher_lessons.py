from uuid import UUID as UUIDType

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.common import require_roles
from backend.dependencies.teacher import get_current_teacher
from backend.models.student import ChangeRequest, Course, LessonSession
from backend.models.teacher import TeacherDB
from backend.models.user import User
from backend.schemas.student import (
    ChangeRequestDecision,
    LessonSummaryResponse,
    TeacherChangeRequestResponse,
    TeacherLessonIn,
    TeacherLessonResponse,
)
from backend.services.availability import cancel_teacher_lesson, create_teacher_lesson
from backend.services.lesson_summary import get_lesson_summary
from backend.services.student import StudentBusinessError, decide_change_request
from backend.services.weekly_schedule import extend_teacher_schedule

router = APIRouter()

@router.get("/teacher/lessons", response_model=list[TeacherLessonResponse])
def get_my_lessons(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """正式課表，含已取消的課。學生與課程名稱一起帶回，前端不用再查。"""
    extend_teacher_schedule(db, teacher.user_id)
    rows = (
        db.query(LessonSession, User.name, Course.title)
        .join(User, User.id == LessonSession.student_id)
        .join(Course, Course.id == LessonSession.course_id)
        .filter(LessonSession.teacher_id == teacher.user_id)
        .order_by(LessonSession.starts_at.asc())
        .all()
    )
    return [
        TeacherLessonResponse(
            id=lesson.id,
            course_id=lesson.course_id,
            starts_at=lesson.starts_at,
            ends_at=lesson.ends_at,
            status=lesson.status,
            student_id=lesson.student_id,
            student_name=student_name,
            course_title=course_title,
        )
        for lesson, student_name, course_title in rows
    ]


def _lesson_response(db: Session, lesson: LessonSession) -> TeacherLessonResponse:
    student = db.get(User, lesson.student_id)
    course = db.get(Course, lesson.course_id)
    return TeacherLessonResponse(
        id=lesson.id,
        course_id=lesson.course_id,
        starts_at=lesson.starts_at,
        ends_at=lesson.ends_at,
        status=lesson.status,
        student_id=lesson.student_id,
        student_name=student.name if student else "學生",
        course_title=course.title if course else "課程",
    )


@router.post("/teacher/lessons", response_model=TeacherLessonResponse)
def add_lesson(
    data: TeacherLessonIn,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """和學生約好了就直接排課，不用學生再送申請。學生要已綁定這門課。"""
    try:
        lesson = create_teacher_lesson(
            db, teacher.user_id, data.student_id, data.course_id, data.starts_at, data.ends_at, data.slot_id
        )
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    return _lesson_response(db, lesson)


@router.post("/teacher/lessons/{lesson_id}/cancel", response_model=TeacherLessonResponse)
def cancel_lesson(
    lesson_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """老師取消一堂課；它若來自可上課時段，時段回到可預約。"""
    try:
        lesson = cancel_teacher_lesson(db, teacher.user_id, lesson_id)
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    return _lesson_response(db, lesson)


@router.get("/teacher/change-requests", response_model=list[TeacherChangeRequestResponse])
def list_change_requests(
    status: str = "pending",
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """學生送來的約課、請假、調課。預設只列待處理的；status=all 列出全部。"""
    query = (
        db.query(ChangeRequest, User.name, Course.title)
        .join(User, User.id == ChangeRequest.student_id)
        .join(Course, Course.id == ChangeRequest.course_id)
        .filter(ChangeRequest.teacher_id == teacher.user_id)
    )
    if status != "all":
        query = query.filter(ChangeRequest.status == status)
    rows = query.order_by(ChangeRequest.created_at.desc()).all()
    sessions = {
        lesson.id: lesson
        for lesson in db.query(LessonSession).filter(
            LessonSession.id.in_([row[0].session_id for row in rows if row[0].session_id])
        )
    }
    result = []
    for change_request, student_name, course_title in rows:
        lesson = sessions.get(change_request.session_id)
        result.append(
            TeacherChangeRequestResponse(
                id=change_request.id,
                course_id=change_request.course_id,
                request_type=change_request.request_type,
                status=change_request.status,
                created_at=change_request.created_at,
                session_id=change_request.session_id,
                proposed_starts_at=change_request.proposed_starts_at,
                proposed_ends_at=change_request.proposed_ends_at,
                reason=change_request.reason,
                student_id=change_request.student_id,
                student_name=student_name,
                course_title=course_title,
                session_starts_at=lesson.starts_at if lesson else None,
                session_ends_at=lesson.ends_at if lesson else None,
            )
        )
    return result


@router.post("/teacher/change-requests/{request_id}/decision")
def decide(
    request_id: UUIDType,
    data: ChangeRequestDecision,
    db: Session = Depends(get_db),
    teacher: User = Depends(require_roles("teacher")),
):
    """同意或拒絕。同意時目標時段已被占用，會回 409，正式課表不變。"""
    try:
        change_request = decide_change_request(db, teacher, request_id, data.approve)
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    return {"id": change_request.id, "status": change_request.status}


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
