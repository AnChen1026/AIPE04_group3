from pathlib import Path
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.core.uploads import MATERIAL_UPLOAD_DIR
from backend.dependencies.teacher import get_current_teacher
from backend.models.material import MaterialDB
from backend.models.teacher import TeacherDB

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

        teacher_id=teacher.user_id,

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
            MaterialDB.teacher_id == teacher.user_id
        )
        .all()
    )
