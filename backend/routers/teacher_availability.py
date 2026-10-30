"""老師的可上課時段：在課表上新增、移動、刪除，或取消預約。"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.teacher import get_current_teacher
from backend.models.teacher import TeacherDB
from backend.schemas.student import AvailabilitySlotIn, TeacherAvailabilitySlotResponse
from backend.services.availability import create_slot, delete_slot, list_teacher_slots, move_slot, release_slot
from backend.services.student import StudentBusinessError

router = APIRouter()


def _slot_response(db: Session, teacher_id: uuid.UUID, slot_id: uuid.UUID) -> dict:
    return next(row for row in list_teacher_slots(db, teacher_id) if row["id"] == slot_id)


@router.get("/teacher/availability", response_model=list[TeacherAvailabilitySlotResponse])
def get_my_slots(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    return list_teacher_slots(db, teacher.user_id)


@router.post("/teacher/availability", response_model=TeacherAvailabilitySlotResponse)
def add_slot(
    data: AvailabilitySlotIn,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """重疊到其他時段或已排的課回 409。"""
    try:
        slot = create_slot(db, teacher.user_id, data.starts_at, data.ends_at)
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    return _slot_response(db, teacher.user_id, slot.id)


@router.patch("/teacher/availability/{slot_id}", response_model=TeacherAvailabilitySlotResponse)
def update_slot(
    slot_id: uuid.UUID,
    data: AvailabilitySlotIn,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """只有還沒人預約的時段可以移動。"""
    try:
        slot = move_slot(db, teacher.user_id, slot_id, data.starts_at, data.ends_at)
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    return _slot_response(db, teacher.user_id, slot.id)


@router.delete("/teacher/availability/{slot_id}", status_code=204)
def remove_slot(
    slot_id: uuid.UUID,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    try:
        delete_slot(db, teacher.user_id, slot_id)
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    return Response(status_code=204)


@router.post("/teacher/availability/{slot_id}/release", response_model=TeacherAvailabilitySlotResponse)
def cancel_booking(
    slot_id: uuid.UUID,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """取消預約：待確認的約課退回、已排的課取消，時段回到可預約。"""
    try:
        slot = release_slot(db, teacher.user_id, slot_id)
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    return _slot_response(db, teacher.user_id, slot.id)
