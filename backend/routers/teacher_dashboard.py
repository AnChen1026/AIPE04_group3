from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.common import get_session_user
from backend.repositories.teacher_application import get_application_by_user_id

router = APIRouter()

templates = Jinja2Templates(directory=Path(__file__).resolve().parents[2] / "templates")

@router.get("/health")
def health():
    return {
        "status": "ok"
    }

@router.get("/test")
def test_page(request: Request, db: Session = Depends(get_db)):
    """審核通過的老師才進入組員做的完整老師頁。"""
    user = get_session_user(request, db)
    if user is not None:
        if user.role == "student":
            return RedirectResponse("/student", status_code=303)
        if user.role == "admin":
            return RedirectResponse("/admin", status_code=303)
        if user.role == "teacher":
            application = get_application_by_user_id(db, user.id)
            approved = (
                application is not None
                and application.status == "approved"
                and user.is_active is True
            )
            if approved is False:
                return RedirectResponse("/teacher", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="teacher/dashboard.html",
    )
