"""老師註冊申請與管理員審核。"""

from datetime import datetime, timezone
from pathlib import Path
import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from backend.core.security import hash_password
from backend.models.teacher_application import TeacherApplication
from backend.models.user import User
from backend.repositories.teacher_application import (
    add_application,
    get_application_by_user_id,
)
from backend.repositories.user import add_user, get_user_by_email
from backend.schemas.user import (
    TeacherApplicationForm,
    TeacherApplicationResponse,
    TeacherRegister,
    UserBrief,
)
from backend.services.user import EmailAlreadyRegisteredError

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROOF_DIR = PROJECT_ROOT / "uploads" / "teacher_proofs"
ALLOWED_PROOF_SUFFIXES = {".pdf", ".jpg", ".jpeg", ".png"}


class TeacherApplicationExistsError(ValueError):
    """這位老師已經送過申請。"""


class InvalidProofFileError(ValueError):
    """證明文件格式不正確。"""


def save_proof_file(proof_file: UploadFile | None) -> tuple[str | None, str | None]:
    """有上傳檔案才存到 uploads；沒有附件就回傳 None。"""
    if proof_file is None:
        return None, None

    original_name = Path(proof_file.filename or "").name
    if original_name == "":
        return None, None

    suffix = Path(original_name).suffix.lower()
    if suffix not in ALLOWED_PROOF_SUFFIXES:
        raise InvalidProofFileError("證明文件只接受 PDF、JPG 或 PNG。")

    file_bytes = proof_file.file.read()
    if not file_bytes:
        return None, None

    PROOF_DIR.mkdir(parents=True, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    stored_path = PROOF_DIR / stored_name
    stored_path.write_bytes(file_bytes)

    relative_path = f"teacher_proofs/{stored_name}"
    return relative_path, original_name


def register_teacher(
    db: Session,
    register_data: TeacherRegister,
    proof_file: UploadFile | None,
) -> User:
    """建立老師帳號與 pending 申請，帳號先不啟用。"""
    normalized_email = str(register_data.email).strip().lower()
    existing_user = get_user_by_email(db, normalized_email)
    if existing_user is not None:
        raise EmailAlreadyRegisteredError("此 Email 已經註冊。")

    relative_path, original_name = save_proof_file(proof_file)

    user = User(
        email=normalized_email,
        password_hash=hash_password(register_data.password),
        auth_provider="password",
        name=register_data.name,
        phone_number=register_data.phone_number,
        birthdate=register_data.birthdate,
        sex=register_data.sex,
        role="teacher",
        is_active=False,
    )
    add_user(db, user)
    db.flush()

    application = TeacherApplication(
        user_id=user.id,
        teaching_subjects=register_data.teaching_subjects,
        teaching_experience=register_data.teaching_experience,
        bio=register_data.bio,
        proof_file_path=relative_path,
        proof_file_name=original_name,
        status="pending",
    )
    add_application(db, application)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(user)
    return user


def submit_teacher_application(
    db: Session,
    user: User,
    form_data: TeacherApplicationForm,
    proof_file: UploadFile | None,
) -> TeacherApplication:
    """Google 註冊後補送老師申請資料。"""
    existing = get_application_by_user_id(db, user.id)
    if existing is not None:
        raise TeacherApplicationExistsError("老師申請資料已經送出。")

    relative_path, original_name = save_proof_file(proof_file)
    application = TeacherApplication(
        user_id=user.id,
        teaching_subjects=form_data.teaching_subjects,
        teaching_experience=form_data.teaching_experience,
        bio=form_data.bio,
        proof_file_path=relative_path,
        proof_file_name=original_name,
        status="pending",
    )
    add_application(db, application)
    user.role = "teacher"
    user.is_active = False

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(application)
    return application


def approve_teacher_application(
    db: Session,
    application: TeacherApplication,
    admin: User,
) -> TeacherApplication:
    """管理員核准後，正式啟用老師帳號。"""
    application.status = "approved"
    application.reviewed_at = datetime.now(timezone.utc)
    application.reviewed_by = admin.id
    application.user.role = "teacher"
    application.user.is_active = True

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(application)
    return application


def reject_teacher_application(
    db: Session,
    application: TeacherApplication,
    admin: User,
) -> TeacherApplication:
    """管理員駁回後，維持 rejected，不能使用老師功能。"""
    application.status = "rejected"
    application.reviewed_at = datetime.now(timezone.utc)
    application.reviewed_by = admin.id
    application.user.role = "teacher"
    application.user.is_active = False

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(application)
    return application


def build_application_response(application: TeacherApplication) -> TeacherApplicationResponse:
    """把老師申請轉成前端 JSON。"""
    return TeacherApplicationResponse(
        id=application.id,
        teaching_subjects=application.teaching_subjects,
        teaching_experience=application.teaching_experience,
        bio=application.bio,
        proof_file_name=application.proof_file_name,
        has_proof=application.proof_file_path is not None,
        status=application.status,
        created_at=application.created_at,
        user=UserBrief.model_validate(application.user),
    )
