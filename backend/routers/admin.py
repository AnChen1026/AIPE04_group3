"""管理員審核老師註冊申請、查看師生名單的 API。"""

from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.common import get_current_admin
from backend.models.user import User
from backend.repositories.teacher_application import (
    get_application_by_id,
    list_applications,
)
from backend.repositories.user import list_users_by_role
from backend.schemas.user import TeacherApplicationResponse, UserResponse
from backend.services.teacher import (
    approve_teacher_application,
    build_application_response,
    reject_teacher_application,
)
from backend.services.user import build_user_response

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
UPLOAD_DIR = BASE_DIR / "uploads"


@router.get(
    "/api/admin/teacher-applications",
    response_model=list[TeacherApplicationResponse],
)
def api_teacher_application_list(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """JSON：全部老師申請。"""
    return [build_application_response(item) for item in list_applications(db)]


@router.post(
    "/api/admin/teacher-applications/{application_id}/approve",
    response_model=TeacherApplicationResponse,
)
def api_approve_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """JSON：核准老師申請。"""
    application = get_application_by_id(db, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="找不到這筆申請。")
    approve_teacher_application(db, application, admin)
    return build_application_response(application)


@router.post(
    "/api/admin/teacher-applications/{application_id}/reject",
    response_model=TeacherApplicationResponse,
)
def api_reject_application(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """JSON：駁回老師申請。"""
    application = get_application_by_id(db, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="找不到這筆申請。")
    reject_teacher_application(db, application, admin)
    return build_application_response(application)


@router.get("/api/admin/teacher-applications/{application_id}/proof")
def api_download_proof(
    application_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """JSON：下載證明文件。"""
    application = get_application_by_id(db, application_id)
    if application is None or application.proof_file_path is None:
        raise HTTPException(status_code=404, detail="找不到證明文件。")

    file_path = UPLOAD_DIR / application.proof_file_path
    if file_path.exists() is False:
        raise HTTPException(status_code=404, detail="找不到證明文件。")

    return FileResponse(
        path=file_path,
        filename=application.proof_file_name or "proof",
    )


@router.get("/api/admin/teachers", response_model=list[UserResponse])
def api_teacher_list(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """JSON：全部老師帳號，含審核狀態。"""
    return [build_user_response(db, user) for user in list_users_by_role(db, "teacher")]


@router.get("/api/admin/students", response_model=list[UserResponse])
def api_student_list(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    """JSON：全部學生帳號。"""
    return [build_user_response(db, user) for user in list_users_by_role(db, "student")]
