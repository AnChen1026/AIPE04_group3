from datetime import datetime, date
from pathlib import Path
from uuid import UUID as UUIDType
import uuid
from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.user import User
from backend.dependencies import get_current_user
from teacher.models import *
from teacher.schemas import *
from teacher.dependencies.teacher import get_current_teacher
from teacher.services.teacher_sync import _ensure_teacher_profile
from teacher.core.uploads import MATERIAL_UPLOAD_DIR

router = APIRouter()

templates = Jinja2Templates(directory="templates")

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
def test_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="fastapi_teacher_test.html",
    )

