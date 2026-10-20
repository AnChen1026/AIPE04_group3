"""登入、註冊與 Google 驗證的 API。畫面都在 Vue。"""

from datetime import date
from urllib.parse import urlencode
import re
import secrets

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from pydantic import ValidationError
from sqlalchemy.orm import Session
from email_validator import EmailNotValidError, validate_email

from backend.core.database import get_db
from backend.core.config import get_frontend_url
from backend.dependencies.common import get_current_user
from backend.models.user import User
from backend.repositories.teacher_application import get_application_by_user_id
from backend.schemas.user import (
    GoogleUrlResponse,
    PasswordChange,
    TeacherApplicationForm,
    TeacherApplicationResponse,
    TeacherRegister,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
)
from backend.services.google_auth import (
    GoogleAuthError,
    GoogleAuthNotConfiguredError,
    build_google_auth_url,
    fetch_google_profile,
    get_google_settings,
    login_or_register_google_user,
)
from backend.services.teacher import (
    InvalidProofFileError,
    TeacherApplicationExistsError,
    build_application_response,
    register_teacher,
    submit_teacher_application,
)
from backend.services.user import (
    PasswordChangeError,
    change_password,
    EmailAlreadyRegisteredError,
    authenticate_user,
    build_user_response,
    register_user,
    update_user_profile,
)

router = APIRouter()

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


def redirect_to_frontend(path: str, **query: str) -> RedirectResponse:
    """Google 驗證完回到 Vue 的頁面。FRONTEND_URL 沒設定時用站內路徑。"""
    url = f"{get_frontend_url()}{path}"
    if query:
        url = f"{url}?{urlencode(query)}"
    return RedirectResponse(url, status_code=303)


def redirect_user_home(user: User) -> RedirectResponse:
    """依角色回到 Vue 的後台首頁。"""
    if user.role == "admin":
        return redirect_to_frontend("/admin")
    if user.role == "teacher":
        return redirect_to_frontend("/teacher")
    return redirect_to_frontend("/student")


@router.get("/auth/google/callback")
def google_callback(
    request: Request,
    db: Session = Depends(get_db),
    code: str | None = None,
    state: str | None = None,
):
    """Google 回來後建立或登入帳號，再回到 Vue。失敗時回登入頁並帶錯誤訊息。
    Google 老師還沒有申請資料時，Vue 的老師後台會請他補填。"""
    saved_state = request.session.get("google_oauth_state")
    intended_role = request.session.get("google_register_role", "student")
    google_intent = request.session.get("google_intent", "register")
    request.session.pop("google_oauth_state", None)
    request.session.pop("google_register_role", None)
    request.session.pop("google_intent", None)

    if not code or not state or state != saved_state:
        return redirect_to_frontend("/login", error="Google 驗證失敗，請再試一次。")

    try:
        profile = fetch_google_profile(code)
        user = login_or_register_google_user(
            db,
            profile["google_id"],
            profile["email"],
            profile["name"],
            intended_role,
            create_if_missing=google_intent == "register",
        )
    except (EmailAlreadyRegisteredError, GoogleAuthError, GoogleAuthNotConfiguredError) as error:
        return redirect_to_frontend("/login", error=str(error))

    request.session.clear()
    request.session["user_id"] = str(user.id)
    return redirect_user_home(user)


@router.post("/api/auth/register", response_model=UserResponse, status_code=201)
def api_register(
    register_data: UserRegister,
    db: Session = Depends(get_db),
):
    """JSON：建立學生帳號。"""
    try:
        user = register_user(db, register_data)
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return build_user_response(db, user)


@router.post("/api/auth/register/teacher", response_model=UserResponse, status_code=201)
def api_register_teacher(
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    name: str = Form(...),
    phone_number: str = Form(...),
    birthdate: str = Form(...),
    sex: str = Form(...),
    teaching_subjects: str = Form(...),
    teaching_experience: str = Form(...),
    bio: str = Form(...),
    proof_file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    """JSON／FormData：建立老師帳號與 pending 申請。證明文件選填。"""
    if email_format_is_valid(email) is False:
        raise HTTPException(status_code=400, detail="請輸入正確的 Email 格式。")
    if phone_format_is_valid(phone_number) is False:
        raise HTTPException(status_code=400, detail="請輸入正確的電話格式，例如 0912345678。")
    if password != password_confirm:
        raise HTTPException(status_code=400, detail="兩次輸入的密碼不一致。")

    try:
        register_data = TeacherRegister(
            email=email,
            password=password,
            name=name,
            phone_number=phone_number,
            birthdate=date.fromisoformat(birthdate),
            sex=sex,
            teaching_subjects=teaching_subjects,
            teaching_experience=teaching_experience,
            bio=bio,
        )
        user = register_teacher(db, register_data, proof_file)
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except InvalidProofFileError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except (ValidationError, ValueError) as error:
        raise HTTPException(status_code=400, detail="註冊資料格式不正確，請重新檢查。") from error
    return build_user_response(db, user)


@router.post("/api/auth/login", response_model=UserResponse)
def api_login(
    request: Request,
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """JSON：驗證帳密並建立 Session。"""
    user = authenticate_user(db, login_data.email, login_data.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Email 或密碼錯誤。")

    if user.is_active is False and user.role != "teacher":
        raise HTTPException(status_code=403, detail="此帳號目前無法登入。")

    request.session.clear()
    request.session["user_id"] = str(user.id)
    return build_user_response(db, user)


@router.post("/api/auth/logout")
def api_logout(request: Request) -> dict[str, str]:
    """JSON：清除 Session。"""
    request.session.clear()
    return {"message": "登出成功。"}


@router.get("/api/auth/me", response_model=UserResponse)
def api_current_user(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """JSON：目前登入者；老師會帶 application_status。"""
    return build_user_response(db, user)


@router.patch("/api/auth/me", response_model=UserResponse)
def api_update_me(
    profile_data: UserUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """JSON：更新基本資料。"""
    if user.role == "admin":
        raise HTTPException(status_code=403, detail="管理員不能修改基本資料。")

    try:
        update_user_profile(db, user, profile_data)
    except (ValidationError, ValueError) as error:
        raise HTTPException(status_code=400, detail="基本資料格式不正確，請重新檢查。") from error
    return build_user_response(db, user)


@router.post("/api/auth/me/password")
def api_change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    """修改自己的密碼。新密碼至少 8 個字元；有密碼的帳號要先輸入目前密碼。"""
    try:
        change_password(db, user, data)
    except PasswordChangeError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return {"message": "密碼已更新，下次登入請用新密碼。"}


@router.get("/api/auth/teacher-application", response_model=TeacherApplicationResponse)
def api_teacher_application(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """JSON：目前登入老師的申請狀態。"""
    if user.role != "teacher":
        raise HTTPException(status_code=403, detail="只有老師可以查看申請。")

    application = get_application_by_user_id(db, user.id)
    if application is None:
        raise HTTPException(status_code=404, detail="尚未送出老師申請。")
    application.user = user
    return build_application_response(application)


@router.post("/api/auth/teacher-application", response_model=TeacherApplicationResponse)
def api_submit_teacher_application(
    teaching_subjects: str = Form(...),
    teaching_experience: str = Form(...),
    bio: str = Form(...),
    proof_file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """JSON／FormData：Google 老師補送申請資料。"""
    if user.role != "teacher":
        raise HTTPException(status_code=403, detail="只有老師可以送出申請。")

    try:
        form_data = TeacherApplicationForm(
            teaching_subjects=teaching_subjects,
            teaching_experience=teaching_experience,
            bio=bio,
        )
        application = submit_teacher_application(db, user, form_data, proof_file)
    except TeacherApplicationExistsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except InvalidProofFileError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except (ValidationError, ValueError) as error:
        raise HTTPException(status_code=400, detail="申請資料格式不正確，請重新檢查。") from error
    application.user = user
    return build_application_response(application)


@router.get("/api/auth/google-url", response_model=GoogleUrlResponse)
def api_google_url(
    request: Request,
    role: str = "student",
    intent: str = "register",
):
    """JSON：回傳 Google 導向網址。前端拿到後再開這個網址。"""
    if get_google_settings() is None:
        raise HTTPException(status_code=503, detail="尚未設定 Google 登入。")
    if intent not in ("register", "login"):
        raise HTTPException(status_code=400, detail="intent 只能是 register 或 login。")
    if intent == "register" and role not in ("student", "teacher"):
        raise HTTPException(status_code=400, detail="請選擇 student 或 teacher。")

    state = secrets.token_urlsafe(16)
    request.session["google_oauth_state"] = state
    request.session["google_register_role"] = role
    request.session["google_intent"] = intent
    return GoogleUrlResponse(url=build_google_auth_url(state))


