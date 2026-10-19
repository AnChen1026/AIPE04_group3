"""訪客讀取已發布課程。不需要登入。"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.schemas.student import PublishedCourseResponse
from backend.services.student import list_public_published_courses

router = APIRouter(prefix="/api/courses", tags=["課程"])


@router.get("", response_model=list[PublishedCourseResponse])
def published_courses(db: Session = Depends(get_db)):
    return list_public_published_courses(db)
