import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies import get_session_user
from backend.repositories.student import StudentRepository
from backend.schemas.student import ChangeRequestCreate


from backend.services.student import process_student_change_request, StudentBusinessError

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/student", response_class=HTMLResponse)
def student_dashboard_view(request: Request, db: Session = Depends(get_db)):
    """【網頁端】學生主頁：從 Cookie Session 撈人，並用 Jinja2 動態渲染畫面"""
    user = get_session_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user.role != "student":
        return RedirectResponse("/teacher", status_code=303)
        
    profile = StudentRepository.get_profile_by_user_id(db, user.id)
    
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
    """【網頁端】處理學生從網頁表單 POST 送出的請假/調課申請"""
    user = get_session_user(request, db)
    if user is None or user.role != "student":
        return RedirectResponse("/login", status_code=303)

    profile = StudentRepository.get_profile_by_user_id(db, user.id)
    client_request_id = uuid.uuid4()

    try:
        # 組裝前端傳入的時間字串
        proposed_payload = {}
        if proposed_date and proposed_time:
            proposed_payload["starts_at"] = f"{proposed_date}T{proposed_time}:00"

        # 將網頁表單的原始資料，包裝成 Pydantic 的 Schema 快照
        payload = ChangeRequestCreate(
            enrollment_id=uuid.UUID(enrollment_id),
            session_id=uuid.UUID(session_id) if session_id else None,
            request_type=request_type,
            proposed_payload=proposed_payload,
            reason=reason,
            client_request_id=client_request_id
        )

        
        process_student_change_request(db, user.id, profile.id, payload)

    except StudentBusinessError as e:
        # 業務邏輯檢查沒通過（例如越權或時段錯誤），漂亮地把原因當作 query string 回傳給畫面渲染
        return RedirectResponse(f"/student?error={e.detail}", status_code=303)
    except Exception:
        return RedirectResponse("/student?error=表單資料格式不正確", status_code=303)

    return RedirectResponse("/student?success=申請已成功送出，等待老師審核", status_code=303)
