from backend.core.storage import cleanup_files
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.common import get_current_user
from backend.dependencies.teacher import get_current_teacher
from backend.models.teacher import TeacherDB
from backend.models.user import User
from backend.schemas.teacher import TeacherIn, TeacherProfileResponse
from backend.services.images import MAX_IMAGE_BYTES, save_image
from backend.services.student import StudentBusinessError
from backend.services.teacher_profile import PROFILE_FIELDS, RESPONSE_FIELDS, account_of, gender_of, profile_complete
from backend.services.teacher_sync import _ensure_teacher_profile

router = APIRouter()


def profile_response(teacher: TeacherDB, user: User | None) -> TeacherProfileResponse:
    return TeacherProfileResponse(
        id=str(teacher.id),
        user_id=str(teacher.user_id),
        name=user.name if user else teacher.name,
        # 只看帳號性別；以前個人資料另外存的「不透露」不再顯示
        gender=gender_of(user) or "",
        status=teacher.status,
        photo_url=f"/api/images/teachers/{teacher.user_id}" if teacher.photo_path else None,
        profile_complete=profile_complete(teacher, user),
        email=user.email if user else None,
        sex=user.sex if user else None,
        phone_number=user.phone_number if user else None,
        birthdate=user.birthdate if user else None,
        **{field: getattr(teacher, field) for field in RESPONSE_FIELDS},
    )


@router.get("/teacher/me", response_model=TeacherProfileResponse)
def get_my_teacher(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    return profile_response(teacher, account_of(db, teacher))


@router.post("/teacher/profile", response_model=TeacherProfileResponse)
def save_teacher_profile(
    data: TeacherIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """建立或更新老師個人資料，帳號的姓名、性別、手機、生日一起存（同一個交易）。照片以外都必填，欄位檢查在 TeacherIn。"""
    if user.role != "teacher":
        raise HTTPException(status_code=403, detail="只有教師可以建立教師資料")

    teacher = db.query(TeacherDB).filter(TeacherDB.user_id == user.id).first()
    if teacher is None:
        teacher = TeacherDB(id=uuid.uuid4(), user_id=user.id)
        db.add(teacher)

    user.name = data.name
    user.sex = data.sex
    user.phone_number = data.phone_number
    user.birthdate = data.birthdate
    teacher.name = data.name
    # 學生看到的性別就是帳號性別
    teacher.gender = gender_of(user)
    for field in PROFILE_FIELDS:
        setattr(teacher, field, getattr(data, field))
    # 審核狀態只看帳號是否核准，不讓前端自己決定
    teacher.status = "active" if user.is_active else "pending"
    db.commit()
    db.refresh(teacher)
    return profile_response(teacher, user)


@router.post("/teacher/photo", response_model=TeacherProfileResponse)
def upload_teacher_photo(
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """上傳或更換老師照片。沒有上傳時，首頁與課程頁用預設圖。"""
    try:
        storage_key = save_image(photo.file.read(MAX_IMAGE_BYTES + 1), "teachers")
        teacher.photo_path = storage_key
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    try:
        db.commit()
    except Exception:
        db.rollback()
        cleanup_files([storage_key])
        raise
    db.refresh(teacher)
    return profile_response(teacher, account_of(db, teacher))

@router.get("/teacher/auth-status")
def teacher_auth_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    teacher = (
        db.query(TeacherDB)
        .filter(
            TeacherDB.user_id == user.id
        )
        .first()
    )

    # 舊的已核准教師帳號也在這裡補建 profile。
    if user.role == "teacher" and user.is_active and teacher is None:
        teacher = _ensure_teacher_profile(db, user)
        db.commit()
        db.refresh(teacher)

    return {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "has_teacher_profile":
            teacher is not None,
        "teacher_id":
            teacher.id if teacher else None,
        "teacher_profile_status":
            teacher.status if teacher else None,
    }
