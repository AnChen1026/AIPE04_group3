"""登入與註冊測試頁面。"""

from datetime import date
from pathlib import Path
import re

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session
from email_validator import EmailNotValidError, validate_email

from backend.core.database import get_db
from backend.dependencies import get_current_user, get_session_user
from backend.models.user import User
from backend.schemas.user import UserLogin, UserRegister, UserResponse, UserUpdate
from backend.services.user import (
    EmailAlreadyRegisteredError,
    authenticate_user,
    register_user,
    update_user_profile,
)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def email_format_is_valid(email: str) -> bool:
    """檢查 Email 是否為 name@example.com 這種格式。"""
    try:
        validate_email(email, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def phone_format_is_valid(phone_number: str) -> bool:
    """檢查台灣手機號碼：09 開頭，共 10 碼數字。"""
    return re.fullmatch(r"09\d{8}", phone_number.strip()) is not None


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
    password_confirm: str = Form(...),
    name: str = Form(...),
    phone_number: str = Form(...),
    birthdate: str = Form(...),
    sex: str = Form(...),
    db: Session = Depends(get_db),
):
    """驗證表單並建立老師或學生帳號。"""
    if role not in ("teacher", "student"):
        return RedirectResponse("/register", status_code=303)

    if email_format_is_valid(email) is False:
        return templates.TemplateResponse(
            request=request,
            name="register_form.html",
            context={"role": role, "error": "請輸入正確的 Email 格式。"},
            status_code=400,
        )

    if phone_format_is_valid(phone_number) is False:
        return templates.TemplateResponse(
            request=request,
            name="register_form.html",
            context={"role": role, "error": "請輸入正確的電話格式，例如 0912345678。"},
            status_code=400,
        )

    if password != password_confirm:
        return templates.TemplateResponse(
            request=request,
            name="register_form.html",
            context={"role": role, "error": "兩次輸入的密碼不一致。"},
            status_code=400,
        )

    try:
        register_data = UserRegister(
            email=email,
            password=password,
            name=name,
            phone_number=phone_number,
            birthdate=date.fromisoformat(birthdate),
            sex=sex,
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
    if email_format_is_valid(email) is False:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "請輸入正確的 Email 格式。", "registered": False},
            status_code=400,
        )

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


@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    """顯示目前登入使用者的基本資料。"""
    user = get_session_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"user": user, "error": None, "updated": False},
    )


@router.post("/profile", response_class=HTMLResponse)
def submit_profile(
    request: Request,
    name: str = Form(...),
    phone_number: str = Form(""),
    birthdate: str = Form(""),
    sex: str = Form(""),
    db: Session = Depends(get_db),
):
    """更新目前登入使用者的基本資料。"""
    user = get_session_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)

    if phone_number and phone_format_is_valid(phone_number) is False:
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={
                "user": user,
                "error": "請輸入正確的電話格式，例如 0912345678。",
                "updated": False,
            },
            status_code=400,
        )

    try:
        birthdate_value = date.fromisoformat(birthdate) if birthdate else None
        profile_data = UserUpdate(
            name=name,
            phone_number=phone_number or None,
            birthdate=birthdate_value,
            sex=sex or None,
        )
        update_user_profile(db, user, profile_data)
    except (ValidationError, ValueError):
        error_message = "基本資料格式不正確，請重新檢查。"
    else:
        return templates.TemplateResponse(
            request=request,
            name="profile.html",
            context={"user": user, "error": None, "updated": True},
        )

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={"user": user, "error": error_message, "updated": False},
        status_code=400,
    )


@router.post("/logout")
def logout(request: Request):
    """清除登入 Session。"""
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@router.post("/api/auth/register", response_model=UserResponse, status_code=201)
def api_register(
    register_data: UserRegister,
    db: Session = Depends(get_db),
):
    """接收 JSON 註冊資料並建立使用者。"""
    try:
        return register_user(db, register_data)
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


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


@router.post("/api/auth/logout")
def api_logout(request: Request) -> dict[str, str]:
    """清除前端登入使用的 Session。"""
    request.session.clear()
    return {"message": "登出成功。"}


@router.get("/api/auth/me", response_model=UserResponse)
def current_user(user: User = Depends(get_current_user)):
    """回傳目前登入的使用者資料。"""
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
