"""登入與註冊測試頁面。"""

from datetime import date
from pathlib import Path
import re
import secrets

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session
from email_validator import EmailNotValidError, validate_email

from backend.core.database import get_db
from backend.dependencies import get_current_user, get_session_user
from backend.models.user import User
from backend.repositories.teacher_application import get_application_by_user_id
from backend.schemas.user import (
    TeacherApplicationForm,
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
    register_teacher,
    submit_teacher_application,
)
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
    if user.role == "admin":
        return RedirectResponse("/admin/teacher-applications", status_code=303)
    if user.role == "teacher":
        return RedirectResponse("/teacher", status_code=303)
    return RedirectResponse("/student", status_code=303)


def teacher_status_template(user: User, db: Session) -> str | RedirectResponse:
    """老師頁要顯示儀表板、等待審核、已駁回，或去補申請資料。"""
    application = get_application_by_user_id(db, user.id)
    if application is None:
        return RedirectResponse("/register/teacher/application", status_code=303)
    if application.status == "rejected":
        return "teacher_rejected.html"
    if application.status != "approved" or user.is_active is False:
        return "teacher_pending.html"
    return "teacher_dashboard.html"


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
        context={"google_ready": get_google_settings() is not None},
    )


@router.get("/register/{role}", response_class=HTMLResponse)
def register_page(request: Request, role: str):
    """顯示老師或學生註冊表單。"""
    if role not in ("teacher", "student"):
        return RedirectResponse("/register", status_code=303)

    template_name = "register_form.html"
    if role == "teacher":
        template_name = "register_teacher.html"

    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={"role": role, "error": None, "google_ready": get_google_settings() is not None},
    )


@router.post("/register/student", response_class=HTMLResponse)
def submit_student_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    name: str = Form(...),
    phone_number: str = Form(...),
    birthdate: str = Form(...),
    sex: str = Form(...),
    db: Session = Depends(get_db),
):
    """驗證表單並建立學生帳號。"""
    if email_format_is_valid(email) is False:
        return templates.TemplateResponse(
            request=request,
            name="register_form.html",
            context={"role": "student", "error": "請輸入正確的 Email 格式。"},
            status_code=400,
        )

    if phone_format_is_valid(phone_number) is False:
        return templates.TemplateResponse(
            request=request,
            name="register_form.html",
            context={"role": "student", "error": "請輸入正確的電話格式，例如 0912345678。"},
            status_code=400,
        )

    if password != password_confirm:
        return templates.TemplateResponse(
            request=request,
            name="register_form.html",
            context={"role": "student", "error": "兩次輸入的密碼不一致。"},
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
        )
        register_user(db, register_data)
    except EmailAlreadyRegisteredError as error:
        error_message = str(error)
    except (ValidationError, ValueError):
        error_message = "註冊資料格式不正確，請重新檢查。"
    else:
        return RedirectResponse("/login?registered=student", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="register_form.html",
        context={"role": "student", "error": error_message},
        status_code=400,
    )


@router.post("/register/teacher", response_class=HTMLResponse)
def submit_teacher_register(
    request: Request,
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
    """建立老師帳號與申請資料，狀態為 pending。"""
    form_context = {"role": "teacher", "google_ready": get_google_settings() is not None}

    if email_format_is_valid(email) is False:
        return templates.TemplateResponse(
            request=request,
            name="register_teacher.html",
            context={**form_context, "error": "請輸入正確的 Email 格式。"},
            status_code=400,
        )

    if phone_format_is_valid(phone_number) is False:
        return templates.TemplateResponse(
            request=request,
            name="register_teacher.html",
            context={**form_context, "error": "請輸入正確的電話格式，例如 0912345678。"},
            status_code=400,
        )

    if password != password_confirm:
        return templates.TemplateResponse(
            request=request,
            name="register_teacher.html",
            context={**form_context, "error": "兩次輸入的密碼不一致。"},
            status_code=400,
        )

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
        register_teacher(db, register_data, proof_file)
    except EmailAlreadyRegisteredError as error:
        error_message = str(error)
    except InvalidProofFileError as error:
        error_message = str(error)
    except (ValidationError, ValueError):
        error_message = "註冊資料格式不正確，請重新檢查。"
    else:
        return RedirectResponse("/login?registered=teacher", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="register_teacher.html",
        context={**form_context, "error": error_message},
        status_code=400,
    )


@router.get("/register/teacher/application", response_class=HTMLResponse)
def teacher_application_page(request: Request, db: Session = Depends(get_db)):
    """Google 註冊老師後，補填申請資料。"""
    user = get_session_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user.role != "teacher":
        return RedirectResponse("/", status_code=303)

    application = get_application_by_user_id(db, user.id)
    if application is not None:
        return RedirectResponse("/teacher", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="register_teacher_application.html",
        context={"user": user, "error": None},
    )


@router.post("/register/teacher/application", response_class=HTMLResponse)
def submit_teacher_application_page(
    request: Request,
    teaching_subjects: str = Form(...),
    teaching_experience: str = Form(...),
    bio: str = Form(...),
    proof_file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    """送出 Google 老師的申請資料。"""
    user = get_session_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user.role != "teacher":
        return RedirectResponse("/", status_code=303)

    try:
        form_data = TeacherApplicationForm(
            teaching_subjects=teaching_subjects,
            teaching_experience=teaching_experience,
            bio=bio,
        )
        submit_teacher_application(db, user, form_data, proof_file)
    except TeacherApplicationExistsError:
        return RedirectResponse("/teacher", status_code=303)
    except InvalidProofFileError as error:
        error_message = str(error)
    except (ValidationError, ValueError):
        error_message = "申請資料格式不正確，請重新檢查。"
    else:
        return RedirectResponse("/teacher", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="register_teacher_application.html",
        context={"user": user, "error": error_message},
        status_code=400,
    )


@router.get("/auth/google")
def start_google_register(
    request: Request,
    role: str = "student",
    intent: str = "register",
):
    """開始 Google 驗證。註冊要帶 role；登入用 intent=login。"""
    if intent not in ("register", "login"):
        intent = "register"
    if intent == "register" and role not in ("student", "teacher"):
        return RedirectResponse("/register", status_code=303)

    if get_google_settings() is None:
        return templates.TemplateResponse(
            request=request,
            name="google_not_configured.html",
            context={"role": role if role in ("student", "teacher") else "student"},
        )

    state = secrets.token_urlsafe(16)
    request.session["google_oauth_state"] = state
    request.session["google_register_role"] = role
    request.session["google_intent"] = intent
    try:
        return RedirectResponse(build_google_auth_url(state), status_code=303)
    except GoogleAuthNotConfiguredError:
        return templates.TemplateResponse(
            request=request,
            name="google_not_configured.html",
            context={"role": role if role in ("student", "teacher") else "student"},
        )


@router.get("/auth/google/callback")
def google_callback(
    request: Request,
    db: Session = Depends(get_db),
    code: str | None = None,
    state: str | None = None,
):
    """Google 回來後建立或登入帳號。老師仍需填申請資料。"""
    saved_state = request.session.get("google_oauth_state")
    intended_role = request.session.get("google_register_role", "student")
    google_intent = request.session.get("google_intent", "register")
    request.session.pop("google_oauth_state", None)
    request.session.pop("google_register_role", None)
    request.session.pop("google_intent", None)

    if not code or not state or state != saved_state:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Google 驗證失敗，請再試一次。", "registered": None},
            status_code=400,
        )

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
    except EmailAlreadyRegisteredError as error:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": str(error), "registered": None},
            status_code=409,
        )
    except (GoogleAuthError, GoogleAuthNotConfiguredError) as error:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": str(error), "registered": None},
            status_code=400,
        )

    request.session.clear()
    request.session["user_id"] = str(user.id)

    if user.role == "teacher":
        application = get_application_by_user_id(db, user.id)
        if application is None:
            return RedirectResponse("/register/teacher/application", status_code=303)
    return redirect_user_home(user)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    """顯示登入表單。"""
    registered = request.query_params.get("registered")
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
            context={"error": "請輸入正確的 Email 格式。", "registered": None},
            status_code=400,
        )

    user = authenticate_user(db, email, password)

    if user is None:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Email 或密碼錯誤。", "registered": None},
            status_code=401,
        )

    if user.is_active is False and user.role != "teacher":
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "此帳號目前無法登入。", "registered": None},
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
    sex: str = Form(...),
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
            sex=sex,
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
    """老師測試頁；依申請狀態顯示等待、駁回或工作區。"""
    user = get_session_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user.role == "admin":
        return RedirectResponse("/admin/teacher-applications", status_code=303)
    if user.role != "teacher":
        return RedirectResponse("/student", status_code=303)

    destination = teacher_status_template(user, db)
    if isinstance(destination, RedirectResponse):
        return destination

    application = get_application_by_user_id(db, user.id)
    return templates.TemplateResponse(
        request=request,
        name=destination,
        context={"user": user, "application": application},
    )


@router.get("/student", response_class=HTMLResponse)
def student_page(request: Request, db: Session = Depends(get_db)):
    """學生測試頁。"""
    user = get_session_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user.role == "admin":
        return RedirectResponse("/admin/teacher-applications", status_code=303)
    if user.role != "student":
        return RedirectResponse("/teacher", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="student_dashboard.html",
        context={"user": user},
    )
