"""工作室資料：老師自己建立與修改，編號由系統產生、建立後不變。"""

import secrets
import uuid

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.studio import Studio
from backend.services.student import StudentBusinessError

MAX_INTRO_LENGTH = 1000
TEXT_FIELDS = {"name": 100, "owner_name": 100, "city": 100, "district": 100}


def get_studio(db: Session, teacher_id: uuid.UUID) -> Studio | None:
    return db.scalar(select(Studio).where(Studio.teacher_id == teacher_id))


def _new_code(db: Session) -> str:
    # 「ST」加 6 位數字，例如 ST482913
    while True:
        code = f"ST{secrets.randbelow(1_000_000):06d}"
        if db.scalar(select(Studio.id).where(Studio.code == code)) is None:
            return code


def _clean(fields: dict) -> dict:
    cleaned = {}
    for key, limit in TEXT_FIELDS.items():
        value = (fields.get(key) or "").strip()
        if len(value) > limit:
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"欄位太長，最多 {limit} 個字。")
        cleaned[key] = value or None
    intro = (fields.get("intro") or "").strip()
    if len(intro) > MAX_INTRO_LENGTH:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, f"工作室介紹最多 {MAX_INTRO_LENGTH} 個字。")
    cleaned["intro"] = intro or None
    if not cleaned["name"]:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "請填寫工作室名稱。")
    if not cleaned["owner_name"]:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "請填寫工作室擁有者。")
    return cleaned


def save_studio(db: Session, teacher_id: uuid.UUID, fields: dict) -> Studio:
    """第一次儲存時建立工作室並產生編號，之後只更新老師填的欄位。"""
    cleaned = _clean(fields)
    studio = get_studio(db, teacher_id)
    if studio is None:
        studio = Studio(teacher_id=teacher_id, code=_new_code(db), **cleaned)
        db.add(studio)
    else:
        for key, value in cleaned.items():
            setattr(studio, key, value)
    db.commit()
    db.refresh(studio)
    return studio
