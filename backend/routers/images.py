"""公開的老師照片與課程圖片。只給已發布課程與已核准老師的圖，其他一律 404。"""

import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.uploads import resolve_stored_path
from backend.models.student import Course
from backend.models.teacher import TeacherDB
from backend.models.user import User

router = APIRouter(prefix="/api/images", tags=["圖片"])

CACHE = {"Cache-Control": "public, max-age=300"}


def _send(path: str | None):
    if not path:
        raise HTTPException(status_code=404, detail="沒有圖片。")
    file = resolve_stored_path(path)
    if not file.is_file():
        raise HTTPException(status_code=404, detail="沒有圖片。")
    return FileResponse(file, headers=CACHE)


@router.get("/courses/{course_id}")
def course_image(course_id: uuid.UUID, db: Session = Depends(get_db)):
    course = db.get(Course, course_id)
    # 老師自己編輯草稿時也要看得到圖，所以草稿也給；封存的課不給
    if course is None or course.status == "archived":
        raise HTTPException(status_code=404, detail="沒有圖片。")
    return _send(course.image_path)


@router.get("/teachers/{user_id}")
def teacher_photo(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None or user.role != "teacher" or user.is_active is not True:
        raise HTTPException(status_code=404, detail="沒有圖片。")
    profile = db.query(TeacherDB).filter(TeacherDB.user_id == user_id).first()
    return _send(profile.photo_path if profile else None)
