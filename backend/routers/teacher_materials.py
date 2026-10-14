from datetime import datetime, date
from pathlib import Path
from uuid import UUID as UUIDType
import uuid
from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.models.user import User
from backend.dependencies.common import get_current_user
from backend.models import *
from backend.schemas import *
from backend.dependencies.teacher import get_current_teacher
from backend.services.teacher_sync import _ensure_teacher_profile
from backend.core.uploads import MATERIAL_UPLOAD_DIR

router = APIRouter()

@router.post("/teacher/materials/upload")
async def upload_material(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="沒有檔案",
        )

    # -----------------------------------------------------
    # 建立唯一檔名
    # -----------------------------------------------------

    extension = Path(file.filename).suffix

    saved_filename = (
        f"{uuid.uuid4()}{extension}"
    )

    file_path = (
        MATERIAL_UPLOAD_DIR /
        saved_filename
    )

    # -----------------------------------------------------
    # 儲存檔案
    # -----------------------------------------------------

    contents = await file.read()

    with open(
        file_path,
        "wb",
    ) as f:
        f.write(contents)

    # -----------------------------------------------------
    # 建立 DB
    # -----------------------------------------------------

    material = MaterialDB(
        id=uuid.uuid4(),

        teacher_id=teacher.id,

        filename=file.filename,

        file_type=file.content_type,

        file_path=str(file_path),
    )

    db.add(material)
    db.commit()
    db.refresh(material)

    return {
        "message": "教材上傳成功",
        "material_id": material.id,
        "filename": file.filename,
        "file_path": str(file_path),
    }

@router.get("/teacher/materials")
def get_my_materials(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    return (
        db.query(MaterialDB)
        .filter(
            MaterialDB.teacher_id == teacher.id
        )
        .all()
    )

@router.get("/teachers/{teacher_id}/materials")
def get_materials(
    teacher_id: UUIDType,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):

    if teacher.id != teacher_id:
        raise HTTPException(
            status_code=403,
            detail="不能查看其他教師的教材",
        )

    return (
        db.query(MaterialDB)
        .filter(
            MaterialDB.teacher_id == teacher.id
        )
        .all()
    )

