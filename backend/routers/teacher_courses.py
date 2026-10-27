from uuid import UUID as UUIDType

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.uploads import resolve_stored_path
from backend.dependencies.teacher import get_current_teacher
from backend.models.student import Course
from backend.models.teacher import TeacherDB
from backend.schemas.course import CourseIn, CourseUpdate
from backend.schemas.student import CourseResponse
from backend.services.course import (
    MAX_MIDI_BYTES,
    create_course,
    get_own_course,
    save_course_image,
    save_reference_midi,
    update_course,
)
from backend.services.images import MAX_IMAGE_BYTES
from backend.services.student import (
    StudentBusinessError,
    active_course_join_code,
    issue_course_join_code,
    revoke_course_join_code,
)

router = APIRouter()


def _raise(error: StudentBusinessError):
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.post("/courses", response_model=CourseResponse)
def create_my_course(
    data: CourseIn,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    try:
        return create_course(db, teacher.user_id, data.model_dump())
    except StudentBusinessError as error:
        _raise(error)


@router.get("/teacher/courses", response_model=list[CourseResponse])
def get_my_courses(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    return (
        db.query(Course)
        .filter(Course.teacher_id == teacher.user_id)
        .order_by(Course.created_at.desc())
        .all()
    )


@router.get("/courses/{course_id}", response_model=CourseResponse)
def get_course(
    course_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    try:
        return get_own_course(db, teacher.user_id, course_id)
    except StudentBusinessError as error:
        _raise(error)


@router.patch("/courses/{course_id}", response_model=CourseResponse)
def edit_course(
    course_id: UUIDType,
    data: CourseUpdate,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """修改課程欄位，也用來把草稿發布或封存。"""
    try:
        return update_course(db, teacher.user_id, course_id, data.model_dump(exclude_unset=True))
    except StudentBusinessError as error:
        _raise(error)


@router.delete("/courses/{course_id}")
def archive_course(
    course_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    try:
        update_course(db, teacher.user_id, course_id, {"status": "archived"})
    except StudentBusinessError as error:
        _raise(error)
    return {"message": "課程已封存"}


@router.post("/courses/{course_id}/reference-midi", response_model=CourseResponse)
def upload_reference_midi(
    course_id: UUIDType,
    midi: UploadFile = File(...),
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """上傳或更換這門課的參考 MIDI。學生的練習都跟這份比對。"""
    try:
        return save_reference_midi(
            db, teacher.user_id, course_id, midi.filename or "", midi.file.read(MAX_MIDI_BYTES + 1)
        )
    except StudentBusinessError as error:
        _raise(error)


@router.get("/courses/{course_id}/reference-midi")
def download_reference_midi(
    course_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    try:
        course = get_own_course(db, teacher.user_id, course_id)
    except StudentBusinessError as error:
        _raise(error)
    if not course.reference_midi_path:
        raise HTTPException(status_code=404, detail="這門課還沒有參考 MIDI。")
    return FileResponse(resolve_stored_path(course.reference_midi_path), media_type="audio/midi")


@router.post("/courses/{course_id}/image", response_model=CourseResponse)
def upload_course_image(
    course_id: UUIDType,
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """上傳或更換課程圖片。沒有上傳時，首頁用預設的課程圖。"""
    try:
        return save_course_image(db, teacher.user_id, course_id, image.file.read(MAX_IMAGE_BYTES + 1))
    except StudentBusinessError as error:
        _raise(error)


class JoinCodeIn(BaseModel):
    hours: int = 24


def _join_code_out(join_code) -> dict | None:
    if join_code is None:
        return None
    return {"code": join_code.code, "expires_at": join_code.expires_at.isoformat()}


@router.get("/teacher/courses/{course_id}/join-code")
def get_join_code(
    course_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """這門課目前還有效的限時綁定碼，沒有就回 null。"""
    try:
        course = get_own_course(db, teacher.user_id, course_id)
    except StudentBusinessError as error:
        _raise(error)
    return _join_code_out(active_course_join_code(db, teacher.user_id, course.id))


@router.post("/teacher/courses/{course_id}/join-code")
def create_join_code(
    course_id: UUIDType,
    data: JoinCodeIn,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """產生新的限時綁定碼，舊的立刻失效。期限內拿到碼的學生都能加入這門課。"""
    try:
        course = get_own_course(db, teacher.user_id, course_id)
        return _join_code_out(issue_course_join_code(db, course, data.hours))
    except StudentBusinessError as error:
        _raise(error)


@router.delete("/teacher/courses/{course_id}/join-code")
def delete_join_code(
    course_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    try:
        course = get_own_course(db, teacher.user_id, course_id)
    except StudentBusinessError as error:
        _raise(error)
    revoke_course_join_code(db, course)
    return {"message": "綁定碼已停用"}
