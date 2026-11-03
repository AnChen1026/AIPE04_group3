"""Google 註冊／登入。沒有設定 Client ID 時不啟用。"""

from urllib.parse import urlencode
import json
import urllib.error
import urllib.request

from sqlalchemy.orm import Session

from backend.core.config import read_env_value
from backend.models.auth_identity import AuthIdentity
from backend.models.user import User
from backend.repositories.auth_identity import add_identity, get_identity
from backend.repositories.user import add_user, get_user_by_email
from backend.services.user import EmailAlreadyRegisteredError

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleAuthNotConfiguredError(RuntimeError):
    """還沒設定 Google 登入環境變數。"""


class GoogleAuthError(ValueError):
    """Google 驗證失敗。"""


def get_google_settings() -> dict[str, str] | None:
    """讀取 Google OAuth 設定；缺一項就回傳 None。"""
    client_id = read_env_value("GOOGLE_CLIENT_ID")
    client_secret = read_env_value("GOOGLE_CLIENT_SECRET")
    redirect_uri = read_env_value("GOOGLE_REDIRECT_URI")
    if client_id is None or client_secret is None or redirect_uri is None:
        return None
    return {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
    }


def build_google_auth_url(state: str) -> str:
    """產生導向 Google 同意畫面的網址。"""
    settings = get_google_settings()
    if settings is None:
        raise GoogleAuthNotConfiguredError("尚未設定 Google 登入。")

    query = urlencode(
        {
            "client_id": settings["client_id"],
            "redirect_uri": settings["redirect_uri"],
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "online",
            "prompt": "select_account",
        }
    )
    return f"{GOOGLE_AUTH_URL}?{query}"


def fetch_google_profile(code: str) -> dict[str, str]:
    """用授權碼向 Google 換使用者 Email 與姓名。"""
    settings = get_google_settings()
    if settings is None:
        raise GoogleAuthNotConfiguredError("尚未設定 Google 登入。")

    token_body = urlencode(
        {
            "code": code,
            "client_id": settings["client_id"],
            "client_secret": settings["client_secret"],
            "redirect_uri": settings["redirect_uri"],
            "grant_type": "authorization_code",
        }
    ).encode("utf-8")
    token_request = urllib.request.Request(
        GOOGLE_TOKEN_URL,
        data=token_body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(token_request, timeout=15) as token_response:
            token_data = json.loads(token_response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError) as error:
        raise GoogleAuthError("Google 驗證失敗，請再試一次。") from error

    access_token = token_data.get("access_token")
    if not access_token:
        raise GoogleAuthError("Google 驗證失敗，請再試一次。")

    userinfo_request = urllib.request.Request(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        with urllib.request.urlopen(userinfo_request, timeout=15) as userinfo_response:
            profile = json.loads(userinfo_response.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError) as error:
        raise GoogleAuthError("無法取得 Google 帳號資料。") from error

    google_id = str(profile.get("id") or "").strip()
    email = str(profile.get("email") or "").strip().lower()
    name = str(profile.get("name") or email.split("@")[0] or "Google 使用者").strip()
    if not google_id or not email:
        raise GoogleAuthError("Google 帳號缺少 Email，無法註冊。")

    return {"google_id": google_id, "email": email, "name": name}


def login_or_register_google_user(
    db: Session,
    google_id: str,
    email: str,
    name: str,
    intended_role: str,
    create_if_missing: bool = True,
) -> User:
    """依 Google 身份登入；第一次且允許註冊時，依選擇的學生／老師建立帳號。"""
    identity = get_identity(db, "google", google_id)
    if identity is not None:
        user = identity.user
        if user is None:
            user = db.get(User, identity.user_id)
        if user is None:
            raise GoogleAuthError("找不到對應的帳號。")
        return user

    existing_user = get_user_by_email(db, email)
    if existing_user is not None:
        raise EmailAlreadyRegisteredError("此 Email 已經註冊，請改用原本的登入方式。")

    if create_if_missing is False:
        raise GoogleAuthError("這個 Google 帳號還沒註冊，請先選擇學生或老師身份。")

    if intended_role not in ("student", "teacher"):
        raise GoogleAuthError("請先選擇要註冊學生或老師。")

    user = User(
        email=email,
        password_hash=None,
        auth_provider="google",
        name=name[:100],
        phone_number=None,
        birthdate=None,
        sex=None,
        role=intended_role,
        is_active=intended_role == "student",
    )
    add_user(db, user)
    db.flush()
    add_identity(
        db,
        AuthIdentity(
            user_id=user.id,
            provider="google",
            provider_subject=google_id,
        ),
    )

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    # 新學生收到管理員的歡迎訊息；老師要等審核通過才送
    if user.role == "student":
        from backend.services.support import send_welcome

        send_welcome(db, user)
    return user
