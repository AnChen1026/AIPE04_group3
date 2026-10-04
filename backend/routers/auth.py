"""登入與註冊測試頁面。"""

import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.user import User
from backend.repositories.user import get_user_by_id
from backend.schemas.user import UserLogin, UserRegister, UserResponse
from backend.services.user import (
    EmailAlreadyRegisteredError,
    authenticate_user,
    register_user,
)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def get_session_user(request: Request, db: Session) -> User | None:
    """依 Session Cookie 取得目前登入的使用者。"""
    user_id_text = request.session.get("user_id")
    if user_id_text is None:
        return None

    try:
        user_id = uuid.UUID(user_id_text)
    except ValueError:
        request.session.clear()
        return None

    user = get_user_by_id(db, user_id)
    if user is None:
        request.session.clear()
    return user


def redirect_user_home(user: User):
    """依角色導向對應測試頁面。"""
    if user.role == "teacher":
        return RedirectResponse("/teacher", status_code=303)
    return RedirectResponse("/student", status_code=303)


@router.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    """測試首頁。"""
    user = get_session_user(request, db)
    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"user": user},
    )


@router.get("/register", response_class=HTMLResponse)
def register_role_page(request: Request):
    """選擇要註冊老師或學生。"""
    return templates.TemplateResponse(
        request=request,
        name="register_role.html",
        context={},
    )


@router.get("/register/{role}", response_class=HTMLResponse)
def register_page(request: Request, role: str):
    """顯示老師或學生註冊表單。"""
    if role not in ("teacher", "student"):
        return RedirectResponse("/register", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="register_form.html",
        context={"role": role, "error": None},
    )


@router.post("/register/{role}", response_class=HTMLResponse)
def submit_register(
    request: Request,
    role: str,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    phone_number: str = Form(""),
    birthdate: str = Form(""),
    sex: str = Form(""),
    db: Session = Depends(get_db),
):
    """驗證表單並建立老師或學生帳號。"""
    if role not in ("teacher", "student"):
        return RedirectResponse("/register", status_code=303)

    try:
        birthdate_value = date.fromisoformat(birthdate) if birthdate else None
        register_data = UserRegister(
            email=email,
            password=password,
            name=name,
            phone_number=phone_number or None,
            birthdate=birthdate_value,
            sex=sex or None,
            role=role,
        )
        register_user(db, register_data)
    except EmailAlreadyRegisteredError as error:
        error_message = str(error)
    except (ValidationError, ValueError):
        error_message = "註冊資料格式不正確，請重新檢查。"
    else:
        return RedirectResponse("/login?registered=1", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="register_form.html",
        context={"role": role, "error": error_message},
        status_code=400,
    )


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """顯示登入表單。"""
    registered = request.query_params.get("registered") == "1"
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": None, "registered": registered},
    )


@router.post("/login", response_class=HTMLResponse)
def submit_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """檢查帳號密碼並建立登入 Session。"""
    user = authenticate_user(db, email, password)

    if user is None:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Email 或密碼錯誤。", "registered": False},
            status_code=401,
        )

    if user.is_active is False and user.role != "teacher":
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "此帳號目前無法登入。", "registered": False},
            status_code=403,
        )

    request.session.clear()
    request.session["user_id"] = str(user.id)
    return redirect_user_home(user)


@router.post("/logout")
def logout(request: Request):
    """清除登入 Session。"""
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@router.post("/api/auth/login", response_model=UserResponse)
def api_login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """驗證 JSON 登入資料並建立 Session。"""
    user = authenticate_user(db, login_data.email, login_data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Email 或密碼錯誤。")

    if user.is_active is False and user.role != "teacher":
        raise HTTPException(status_code=403, detail="此帳號目前無法登入。")

    request.session.clear()
    request.session["user_id"] = str(user.id)
    return user


@router.get("/api/auth/me", response_model=UserResponse)
def current_user(request: Request, db: Session = Depends(get_db)):
    """回傳目前登入的使用者資料。"""
    user = get_session_user(request, db)
    if user is None:
        raise HTTPException(status_code=401, detail="尚未登入。")

    return user


@router.get("/teacher", response_class=HTMLResponse)
def teacher_page(request: Request, db: Session = Depends(get_db)):
    """老師測試頁；未審核老師只顯示等待訊息。"""
    user = get_session_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user.role != "teacher":
        return RedirectResponse("/student", status_code=303)

    template_name = "teacher_dashboard.html"
    if user.is_active is False:
        template_name = "teacher_pending.html"

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={"user": user},
    )


@router.get("/student", response_class=HTMLResponse)
def student_page(request: Request, db: Session = Depends(get_db)):
    """學生測試頁。"""
    user = get_session_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user.role != "student":
        return RedirectResponse("/teacher", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="student_dashboard.html",
        context={"user": user},
    )
