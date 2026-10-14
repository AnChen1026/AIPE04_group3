from datetime import datetime, date
from pathlib import Path
from uuid import UUID as UUIDType
import uuid
from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.user import User
from backend.dependencies.common import get_current_user, get_session_user
from backend.repositories.teacher_application import get_application_by_user_id
from backend.models import *
from backend.schemas import *
from backend.dependencies.teacher import get_current_teacher
from backend.services.teacher_sync import _ensure_teacher_profile
from backend.core.uploads import MATERIAL_UPLOAD_DIR

router = APIRouter()

templates = Jinja2Templates(directory=Path(__file__).resolve().parents[2] / "templates")

@router.get("/")
def index():
    return {
        "message": "教師端 API 運作中",
        "auth": "/api/auth",
    }

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
