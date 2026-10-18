"""老師測試頁：發布課程、貼綁定碼、處理課務申請、解除綁定。"""

import uuid
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.common import get_current_user, get_session_user
from backend.models.user import User
from backend.repositories.student import StudentRepository
from backend.repositories.teacher_application import get_application_by_user_id
from backend.services.course import MAX_MIDI_BYTES, create_course, save_reference_midi
from backend.services.student import (
    StudentBusinessError,
    decide_change_request,
    issue_binding_code,
    unbind_student,
)

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parents[2] / "templates")


def _approved_teacher_or_redirect(request: Request, db: Session):
    user = get_session_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user.role != "teacher":
        return RedirectResponse("/student", status_code=303)
    application = get_application_by_user_id(db, user.id)
    if application is None or application.status != "approved":
        return RedirectResponse("/teacher", status_code=303)
    return user


@router.get("/teacher/learning", response_class=HTMLResponse)
def teacher_learning_page(request: Request, db: Session = Depends(get_db)):
    user = _approved_teacher_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    conversations = []
    for conversation in StudentRepository.list_teacher_conversations(db, user.id):
        course = StudentRepository.get_course(db, conversation.course_id)
        student = StudentRepository.get_user(db, conversation.student_id)
        conversations.append(
            {
                "conversation": conversation,
                "course": course,
                "student": student,
                "bound": StudentRepository.is_bound(db, conversation.student_id, conversation.course_id),
                "messages": StudentRepository.list_messages(db, conversation.id),
            }
        )
    return templates.TemplateResponse(
        request=request,
        name="teacher/learning.html",
        context={
            "user": user,
            "courses": StudentRepository.list_teacher_courses(db, user.id),
            "conversations": conversations,
            "requests": StudentRepository.list_pending_requests_for_teacher(db, user.id),
            "error": request.query_params.get("error"),
            "success": request.query_params.get("success"),
        },
    )


@router.post("/teacher/learning/courses")
def teacher_create_course(
    request: Request,
    title: str = Form(...),
    level: str = Form(""),
    style: str = Form(""),
    delivery_mode: str = Form(""),
    region: str = Form(""),
    price_per_lesson: str = Form(""),
    time_slots: str = Form(""),
    publish: str = Form(""),
    reference_midi: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    user = _approved_teacher_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    price = int(price_per_lesson) if price_per_lesson.strip().isdigit() else None
    fields = {
        "title": title,
        "level": level,
        "style": style,
        "delivery_mode": delivery_mode,
        "region": region,
        "price_per_lesson": price,
        "time_slots": time_slots,
        "status": "published" if publish == "yes" else "draft",
    }
    try:
        course = create_course(db, user.id, fields)
    except StudentBusinessError as error:
        return RedirectResponse(f"/teacher/learning?error={quote(error.detail)}", status_code=303)
    if reference_midi is not None and reference_midi.filename:
        try:
            save_reference_midi(
                db, user.id, course.id, reference_midi.filename, reference_midi.file.read(MAX_MIDI_BYTES + 1)
            )
        except StudentBusinessError as error:
            message = "課程已建立，但參考 MIDI 沒有存成功：" + error.detail
            return RedirectResponse(f"/teacher/learning?error={quote(message)}", status_code=303)
    return RedirectResponse("/teacher/learning?success=" + quote("課程已儲存。"), status_code=303)


@router.post("/teacher/learning/conversations/{conversation_id}/binding-code")
def teacher_issue_code(conversation_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    user = _approved_teacher_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    try:
        binding_code = issue_binding_code(db, user, conversation_id)
    except StudentBusinessError as error:
        return RedirectResponse(f"/teacher/learning?error={quote(error.detail)}", status_code=303)
    return RedirectResponse(
        "/teacher/learning?success=" + quote(f"已把綁定碼 {binding_code.code} 貼進對話。"),
        status_code=303,
    )


def _require_teacher(user: User) -> None:
    if user.role != "teacher" or user.is_active is not True:
        raise HTTPException(status_code=403, detail="沒有使用權限。")


@router.get("/teacher/conversations")
def list_teacher_conversations_api(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """老師後台聊天頁：列出學生洽詢，用來產生綁定碼。"""
    _require_teacher(user)
    rows = []
    for conversation in StudentRepository.list_teacher_conversations(db, user.id):
        course = StudentRepository.get_course(db, conversation.course_id)
        student = StudentRepository.get_user(db, conversation.student_id)
        rows.append(
            {
                "id": conversation.id,
                "student_name": student.name if student is not None else "學生",
                "course_title": course.title if course is not None else "課程",
                "bound": StudentRepository.is_bound(
                    db, conversation.student_id, conversation.course_id
                ),
            }
        )
    return rows


@router.post("/teacher/conversations/{conversation_id}/binding-code")
def issue_binding_code_api(
    conversation_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """產生綁定碼，並當成一則訊息貼進這段接洽對話。"""
    _require_teacher(user)
    try:
        binding_code = issue_binding_code(db, user, conversation_id)
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    return {"code": binding_code.code, "conversation_id": conversation_id}


@router.post("/teacher/learning/change-requests/{request_id}")
def teacher_decide(request_id: uuid.UUID, request: Request, decision: str = Form(...), db: Session = Depends(get_db)):
    user = _approved_teacher_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    try:
        decide_change_request(db, user, request_id, decision == "approve")
    except StudentBusinessError as error:
        return RedirectResponse(f"/teacher/learning?error={quote(error.detail)}", status_code=303)
    return RedirectResponse("/teacher/learning?success=" + quote("課務申請已處理。"), status_code=303)


@router.post("/teacher/learning/courses/{course_id}/students/{student_id}/unbind")
def teacher_unbind(course_id: uuid.UUID, student_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    user = _approved_teacher_or_redirect(request, db)
    if isinstance(user, RedirectResponse):
        return user
    try:
        unbind_student(db, user, course_id, student_id)
    except StudentBusinessError as error:
        return RedirectResponse(f"/teacher/learning?error={quote(error.detail)}", status_code=303)
    return RedirectResponse("/teacher/learning?success=" + quote("已解除綁定，對話仍保留。"), status_code=303)
