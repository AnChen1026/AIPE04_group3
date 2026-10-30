"""公開的老師照片與課程圖片。只給已發布課程與已核准老師的圖，其他一律 404。"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from backend.core.storage import file_response
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.common import get_session_user
from backend.models.teacher_application import TeacherApplication
from backend.models.student import Course
from backend.models.teacher import TeacherDB
from backend.models.user import User

router = APIRouter(prefix="/api/images", tags=["圖片"])

CACHE = {"Cache-Control": "public, max-age=300"}


def _send(path: str | None, cache: bool = True):
    if not path:
        raise HTTPException(status_code=404, detail="沒有圖片。")
    return file_response(path, headers=CACHE if cache else {"Cache-Control": "no-store"})


@router.get("/courses/{course_id}")
def course_image(course_id: uuid.UUID, db: Session = Depends(get_db), viewer: User | None = Depends(get_session_user)):
    course = db.get(Course, course_id)
    # 草稿只給已登入的擁有者；公開狀態才允許公共快取。
    if course is None or course.status == "archived":
        raise HTTPException(status_code=404, detail="沒有圖片。")
    if course.status != "published" and (viewer is None or not viewer.is_active or viewer.id != course.teacher_id):
        raise HTTPException(status_code=404, detail="沒有圖片。")
    return _send(course.image_path, cache=course.status == "published")


@router.get("/teachers/{user_id}")
def teacher_photo(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None or user.role != "teacher" or user.is_active is not True:
        raise HTTPException(status_code=404, detail="沒有圖片。")
    approved = db.query(TeacherApplication).filter(TeacherApplication.user_id == user_id, TeacherApplication.status == "approved").first()
    if approved is None:
        raise HTTPException(status_code=404, detail="沒有圖片。")
    profile = db.query(TeacherDB).filter(TeacherDB.user_id == user_id).first()
    return _send(profile.photo_path if profile else None)
