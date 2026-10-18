"""學生 JSON API。正式 Vue 之後也呼叫這裡。"""

import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.uploads import resolve_stored_path
from backend.dependencies.common import get_current_user, require_roles
from backend.models.user import User
from backend.repositories.student import StudentRepository
from backend.schemas.student import (
    ChangeRequestResponse,
    ConversationResponse,
    CourseResponse,
    FeedbackResponse,
    LessonResponse,
    MessageResponse,
    RecordingResponse,
)
from backend.services.practice import run_recording_analysis
from backend.services.student import (
    MAX_RECORDING_BYTES,
    StudentBusinessError,
    add_message,
    create_change_request,
    list_published_courses,
    mark_conversation_read,
    redeem_binding_code,
    require_bound,
    save_recording,
    start_conversation,
    student_can_read_conversation,
)

router = APIRouter(
    prefix="/api/student",
    tags=["學生"],
    dependencies=[Depends(require_roles("student"))],
)


def _raise_business_error(error: StudentBusinessError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.get("/courses", response_model=list[CourseResponse])
def api_published_courses(db: Session = Depends(get_db)):
    return list_published_courses(db)


@router.post("/courses/{course_id}/conversation", response_model=ConversationResponse)
def api_start_conversation(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return start_conversation(db, current_user, course_id)
    except StudentBusinessError as error:
        _raise_business_error(error)


@router.get("/conversations", response_model=list[ConversationResponse])
def api_my_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return StudentRepository.list_student_conversations(db, current_user.id)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def api_messages(
    conversation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = StudentRepository.get_conversation(db, conversation_id)
    if conversation is None or not student_can_read_conversation(conversation, current_user):
        raise HTTPException(status_code=404, detail="找不到這段對話。")
    mark_conversation_read(db, conversation.id, current_user.id)
    return StudentRepository.list_messages(db, conversation.id)


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
def api_send_message(
    conversation_id: uuid.UUID,
    body: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = StudentRepository.get_conversation(db, conversation_id)
    if conversation is None or not student_can_read_conversation(conversation, current_user):
        raise HTTPException(status_code=404, detail="找不到這段對話。")
    try:
        return add_message(db, conversation, current_user, body)
    except StudentBusinessError as error:
        _raise_business_error(error)


@router.post("/conversations/{conversation_id}/bind")
def api_bind(
    conversation_id: uuid.UUID,
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conversation = StudentRepository.get_conversation(db, conversation_id)
    if conversation is None or not student_can_read_conversation(conversation, current_user):
        raise HTTPException(status_code=404, detail="找不到這段對話。")
    try:
        redeem_binding_code(db, current_user, conversation, code)
    except StudentBusinessError as error:
        _raise_business_error(error)
    return {"bound": True, "course_id": str(conversation.course_id)}


@router.get("/courses/{course_id}/schedule", response_model=list[LessonResponse])
def api_schedule(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        require_bound(db, current_user.id, course_id)
    except StudentBusinessError as error:
        _raise_business_error(error)
    return StudentRepository.list_schedule(db, current_user.id, course_id)


@router.post("/courses/{course_id}/change-requests", response_model=ChangeRequestResponse)
def api_change_request(
    course_id: uuid.UUID,
    request_type: str,
    session_id: uuid.UUID | None = None,
    proposed_starts_at: datetime | None = None,
    proposed_ends_at: datetime | None = None,
    reason: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return create_change_request(
            db,
            current_user,
            course_id,
            request_type,
            session_id,
            proposed_starts_at,
            proposed_ends_at,
            reason,
        )
    except StudentBusinessError as error:
        _raise_business_error(error)


def _recording_response(db: Session, recording) -> RecordingResponse:
    feedback = StudentRepository.get_feedback(db, recording.id)
    return RecordingResponse(
        id=recording.id,
        course_id=recording.course_id,
        status=recording.status,
        submitted_at=recording.submitted_at,
        feedback=FeedbackResponse.model_validate(feedback) if feedback else None,
    )


def _own_recording(db: Session, user: User, recording_id: uuid.UUID):
    recording = StudentRepository.get_recording(db, recording_id)
    if recording is None or recording.student_id != user.id:
        raise HTTPException(status_code=404, detail="找不到這段錄音。")
    return recording


@router.post("/courses/{course_id}/recordings", response_model=RecordingResponse)
def api_upload_recording(
    course_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """送出後先回傳 pending，評分在背景跑完再更新；之後用 GET /api/student/recordings/{id} 查進度。"""
    try:
        recording = save_recording(
            db,
            current_user,
            course_id,
            audio.filename or "audio.webm",
            audio.file.read(MAX_RECORDING_BYTES + 1),
        )
    except StudentBusinessError as error:
        _raise_business_error(error)
    background_tasks.add_task(run_recording_analysis, recording.id)
    return _recording_response(db, recording)


@router.get("/courses/{course_id}/recordings", response_model=list[RecordingResponse])
def api_my_recordings(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        require_bound(db, current_user.id, course_id)
    except StudentBusinessError as error:
        _raise_business_error(error)
    return [
        _recording_response(db, recording)
        for recording in StudentRepository.list_recordings(db, current_user.id, course_id)
    ]


@router.get("/recordings/{recording_id}", response_model=RecordingResponse)
def api_my_recording(
    recording_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _recording_response(db, _own_recording(db, current_user, recording_id))


@router.get("/recordings/{recording_id}/audio")
def api_my_recording_audio(
    recording_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    recording = _own_recording(db, current_user, recording_id)
    try:
        require_bound(db, current_user.id, recording.course_id)
    except StudentBusinessError as error:
        _raise_business_error(error)
    return FileResponse(resolve_stored_path(recording.file_path))


@router.get("/courses/{course_id}/reference-midi")
def api_reference_midi(
    course_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """已綁定的學生可以下載老師指定的參考曲來練習。"""
    try:
        course = require_bound(db, current_user.id, course_id)
    except StudentBusinessError as error:
        _raise_business_error(error)
    if not course.reference_midi_path:
        raise HTTPException(status_code=404, detail="這門課還沒有參考 MIDI。")
    return FileResponse(resolve_stored_path(course.reference_midi_path), media_type="audio/midi")
