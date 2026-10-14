"""學生測試頁。正式使用者之後走 Vue，這一頁給後端確認流程。"""

import uuid
from datetime import datetime
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.common import get_session_user
from backend.models.user import User
from backend.repositories.student import StudentRepository
from backend.services.student import (
    StudentBusinessError,
    add_message,
    create_change_request,
    list_published_courses,
    mark_conversation_read,
    redeem_binding_code,
    save_recording,
    start_conversation,
)

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[2] / "templates")


def _student_or_redirect(request: Request, db: Session):
    user = get_session_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user.role != "student":
        return RedirectResponse("/teacher", status_code=303)
    return user


@router.get("/student", response_class=HTMLResponse)
def student_dashboard(request: Request, db: Session = Depends(get_db)):
    user = _student_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    conversations = StudentRepository.list_student_conversations(db, user.id)
    cards = []
    for conversation in conversations:
        course = StudentRepository.get_course(db, conversation.course_id)
        bound = StudentRepository.is_bound(db, user.id, conversation.course_id)
        mark_conversation_read(db, conversation.id, user.id)
        card = {
            "conversation": conversation,
            "course": course,
            "bound": bound,
            "messages": StudentRepository.list_messages(db, conversation.id),
            "schedule": [],
            "requests": [],
            "recordings": [],
            "teacher_name": None,
        }
        if bound:
            teacher = db.get(User, course.teacher_id)
            card["teacher_name"] = teacher.name if teacher is not None else None
            card["schedule"] = StudentRepository.list_schedule(db, user.id, course.id)
            card["requests"] = StudentRepository.list_change_requests_for_student(db, user.id, course.id)
            for recording in StudentRepository.list_recordings(db, user.id, course.id):
                card["recordings"].append(
                    {
                        "recording": recording,
                        "feedback": StudentRepository.get_feedback(db, recording.id),
                    }
                )
        cards.append(card)
    notice = request.query_params.get("error") or request.query_params.get("success")
    return templates.TemplateResponse(
        request=request,
        name="student/dashboard.html",
        context={
            "user": user,
            "courses": list_published_courses(db),
            "conversations": cards,
            "has_binding": any(item["bound"] for item in cards),
            "error": request.query_params.get("error"),
            "success": request.query_params.get("success"),
            "open_chat": notice is not None,
        },
    )


@router.post("/student/courses/{course_id}/inquire")
def inquire_course(course_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    user = _student_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    try:
        conversation = start_conversation(db, user, course_id)
    except StudentBusinessError as error:
        return RedirectResponse(f"/student?error={quote(error.detail)}", status_code=303)
    return RedirectResponse("/student", status_code=303)


@router.get("/student/conversations/{conversation_id}", response_class=HTMLResponse)
def conversation_page(conversation_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    user = _student_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    conversation = StudentRepository.get_conversation(db, conversation_id)
    if conversation is None or conversation.student_id != user.id:
        return RedirectResponse("/student?error=" + quote("找不到這段對話。"), status_code=303)
    return RedirectResponse("/student", status_code=303)


@router.post("/student/conversations/{conversation_id}/messages")
def post_message(
    conversation_id: uuid.UUID,
    request: Request,
    body: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _student_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    conversation = StudentRepository.get_conversation(db, conversation_id)
    if conversation is None or conversation.student_id != user.id:
        return RedirectResponse("/student", status_code=303)
    try:
        add_message(db, conversation, user, body)
    except StudentBusinessError as error:
        return RedirectResponse(f"/student?error={quote(error.detail)}", status_code=303)
    return RedirectResponse("/student", status_code=303)


@router.post("/student/conversations/{conversation_id}/bind")
def post_bind(
    conversation_id: uuid.UUID,
    request: Request,
    code: str = Form(...),
    db: Session = Depends(get_db),
):
    user = _student_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    conversation = StudentRepository.get_conversation(db, conversation_id)
    if conversation is None or conversation.student_id != user.id:
        return RedirectResponse("/student", status_code=303)
    try:
        redeem_binding_code(db, user, conversation, code)
    except StudentBusinessError as error:
        return RedirectResponse(f"/student?error={quote(error.detail)}", status_code=303)
    return RedirectResponse("/student?success=" + quote("已進入這門課。"), status_code=303)


@router.post("/student/courses/{course_id}/change-requests")
def post_change_request(
    course_id: uuid.UUID,
    request: Request,
    request_type: str = Form(...),
    session_id: str = Form(""),
    proposed_start: str = Form(""),
    proposed_end: str = Form(""),
    reason: str = Form(""),
    db: Session = Depends(get_db),
):
    user = _student_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    try:
        parsed_session = uuid.UUID(session_id) if session_id else None
        starts = datetime.fromisoformat(proposed_start).astimezone() if proposed_start else None
        ends = datetime.fromisoformat(proposed_end).astimezone() if proposed_end else None
        create_change_request(db, user, course_id, request_type, parsed_session, starts, ends, reason or None)
    except (StudentBusinessError, ValueError) as error:
        detail = error.detail if isinstance(error, StudentBusinessError) else "時間格式不正確。"
        return RedirectResponse(f"/student?error={quote(detail)}", status_code=303)
    return RedirectResponse("/student?success=" + quote("申請已送出，正式課表還沒有改變。"), status_code=303)


@router.post("/student/courses/{course_id}/recordings")
def post_recording(
    course_id: uuid.UUID,
    request: Request,
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user = _student_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    try:
        save_recording(db, user, course_id, audio.filename or "audio.webm", audio.file.read())
    except StudentBusinessError as error:
        return RedirectResponse(f"/student?error={quote(error.detail)}", status_code=303)
    return RedirectResponse("/student?success=" + quote("錄音已送出，練習回饋處理中。"), status_code=303)


@router.get("/student/recordings/{recording_id}/audio")
def download_own_recording(recording_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    user = _student_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    recording = StudentRepository.get_recording(db, recording_id)
    if recording is None or recording.student_id != user.id:
        return RedirectResponse("/student?error=" + quote("不能讀取這段錄音。"), status_code=303)
    if not StudentRepository.is_bound(db, user.id, recording.course_id):
        return RedirectResponse("/student?error=" + quote("解除綁定後不能聽這段錄音。"), status_code=303)
    return FileResponse(recording.file_path)
