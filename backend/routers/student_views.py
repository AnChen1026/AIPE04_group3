# 處理學生端 HTML 網頁模板渲染與傳統 POST 表單
# ====================================================================


import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies import get_session_user
from backend.repositories.student import StudentRepository

router = APIRouter()

# 對齊 auth.py 裡設定的 Jinja2Templates 路徑
BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/student", response_class=HTMLResponse)
def student_dashboard_view(request: Request, db: Session = Depends(get_db)):
    """【網頁端】學生主頁：從 Cookie Session 撈人，並用 Jinja2 動態渲染畫面"""
    user = get_session_user(request, db)
    # 安全驗證：沒登入或角色不是學生，直接踢回登入頁（完美對齊隊友攔截邏輯）
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user.role != "student":
        return RedirectResponse("/teacher", status_code=303)
        
    profile = StudentRepository.get_profile_by_user_id(db, user.id)
    
    # 撈出前端畫面所需的所有動態關聯資料
    schedule = StudentRepository.get_student_schedule(db, profile.id)
    inquiries = StudentRepository.get_student_inquiries(db, profile.id)
    enrollments = StudentRepository.get_student_enrollments(db, profile.id)
    assignments = StudentRepository.get_student_assignments(db, profile.id)

    return templates.TemplateResponse(
        request=request,
        name="student_dashboard.html",
        context={
            "user": user,
            "schedule": schedule,
            "inquiries": inquiries,
            "enrollments": enrollments,
            "assignments": assignments,
            "error": request.query_params.get("error"),
            "success": request.query_params.get("success")
        }
    )


@router.post("/student/change-requests/submit", response_class=HTMLResponse)
def submit_change_request_form(
    request: Request,
    enrollment_id: str = Form(...),
    request_type: str = Form(...),
    session_id: str = Form(None),
    reason: str = Form(None),
    proposed_date: str = Form(None),
    proposed_time: str = Form(None),
    db: Session = Depends(get_db)
):
    """【網頁端】處理學生從 student_dashboard.html 網頁表單 POST 送出的請假/調課申請"""
    user = get_session_user(request, db)
    if user is None or user.role != "student":
        return RedirectResponse("/login", status_code=303)

    profile = StudentRepository.get_profile_by_user_id(db, user.id)
    
    # 生成防連點的去重鍵
    client_request_id = uuid.uuid4()

    try:
        e_uuid = uuid.UUID(enrollment_id)
        enrollment = StudentRepository.get_enrollment_by_id_and_student(db, e_uuid, profile.id)
        if not enrollment:
            return RedirectResponse("/student?error=無此班級操作權限", status_code=303)

        # 處理並包裝期望調整的時間 payload 快照
        proposed_payload = {}
        if proposed_date and proposed_time:
            proposed_payload["starts_at"] = f"{proposed_date}T{proposed_time}:00"

        session_uuid = uuid.UUID(session_id) if session_id else None
        session = StudentRepository.get_session_by_id(db, session_uuid) if session_uuid else None

        StudentRepository.create_change_request(
            db=db,
            user_id=user.id,
            enrollment=enrollment,
            session=session,
            request_type=request_type,
            proposed_payload=proposed_payload,
            reason=reason,
            client_request_id=client_request_id
        )
    except Exception:
        return RedirectResponse("/student?error=申請資料格式不正確", status_code=303)

    return RedirectResponse("/student?success=申請已成功送出，等待老師審核", status_code=303)
