"""管理員審核老師註冊申請。"""

from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.common import get_current_admin, get_session_user
from backend.models.user import User
from backend.repositories.teacher_application import (
    get_application_by_id,
    list_applications,
)
from backend.repositories.user import list_users_by_role
from backend.schemas.user import TeacherApplicationResponse
from backend.services.teacher import (
    approve_teacher_application,
    build_application_response,
    reject_teacher_application,
)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[2]
templates = Jinja2Templates(directory=BASE_DIR / "templates")
UPLOAD_DIR = BASE_DIR / "uploads"


def require_admin(request: Request, db: Session) -> User | RedirectResponse:
    """管理員才能進入審核頁；未登入就去登入頁。"""
    user = get_session_user(request, db)
    if user is None:
        return RedirectResponse("/login", status_code=303)
    if user.role != "admin" or user.is_active is False:
        return RedirectResponse("/", status_code=303)
    return user


@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request, db: Session = Depends(get_db)):
    """管理員測試頁：查看並審核老師申請。"""
    return teacher_application_list(request, db)


@router.get("/admin/teacher-applications", response_class=HTMLResponse)
def teacher_application_list(
    request: Request,
    db: Session = Depends(get_db),
):
    """查看全部老師註冊申請。"""
    admin = require_admin(request, db)
    if isinstance(admin, RedirectResponse):
        return admin

    applications = list_applications(db)
    return templates.TemplateResponse(
        request=request,
        name="admin/teacher_applications.html",
        context={
            "user": admin,
            "applications": applications,
            "admin_section": "applications",
        },
    )


@router.get("/admin/teachers", response_class=HTMLResponse)
def teacher_list(request: Request, db: Session = Depends(get_db)):
    """顯示全部老師帳號。"""
    admin = require_admin(request, db)
    if isinstance(admin, RedirectResponse):
        return admin

    application_status = {
        item.user_id: item.status for item in list_applications(db)
    }
    return templates.TemplateResponse(
        request=request,
        name="admin/teachers.html",
        context={
            "user": admin,
            "teachers": list_users_by_role(db, "teacher"),
            "application_status": application_status,
            "admin_section": "teachers",
        },
    )


@router.get("/admin/students", response_class=HTMLResponse)
def student_list(request: Request, db: Session = Depends(get_db)):
    """顯示全部學生帳號。"""
    admin = require_admin(request, db)
    if isinstance(admin, RedirectResponse):
        return admin

    return templates.TemplateResponse(
        request=request,
        name="admin/students.html",
        context={
            "user": admin,
            "students": list_users_by_role(db, "student"),
            "admin_section": "students",
        },
    )


@router.post("/admin/teacher-applications/{application_id}/approve")
def approve_application(
    application_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
):
    """核准老師申請並啟用帳號。"""
    admin = require_admin(request, db)
    if isinstance(admin, RedirectResponse):
        return admin

    application = get_application_by_id(db, application_id)
    if application is None:
        return RedirectResponse("/admin/teacher-applications", status_code=303)
    approve_teacher_application(db, application, admin)
    return RedirectResponse("/admin/teacher-applications", status_code=303)


@router.post("/admin/teacher-applications/{application_id}/reject")
def reject_application(
    application_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
):
    """駁回老師申請，維持 rejected。"""
    admin = require_admin(request, db)
    if isinstance(admin, RedirectResponse):
        return admin

    application = get_application_by_id(db, application_id)
    if application is None:
        return RedirectResponse("/admin/teacher-applications", status_code=303)
    reject_teacher_application(db, application, admin)
    return RedirectResponse("/admin/teacher-applications", status_code=303)


@router.get("/admin/teacher-applications/{application_id}/proof")
def download_proof(
    application_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
):
    """下載老師申請的證明文件。"""
    admin = require_admin(request, db)
    if isinstance(admin, RedirectResponse):
        return admin

    application = get_application_by_id(db, application_id)
    if application is None or application.proof_file_path is None:
        return RedirectResponse("/admin/teacher-applications", status_code=303)

    file_path = UPLOAD_DIR / application.proof_file_path
    if file_path.exists() is False:
        return RedirectResponse("/admin/teacher-applications", status_code=303)

    return FileResponse(
        path=file_path,
        filename=application.proof_file_name or "proof",
    )


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
