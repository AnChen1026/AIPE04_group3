"""老師的可上課時段：在課表上新增、移動、刪除，或取消預約。"""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies.teacher import get_current_teacher
from backend.models.teacher import TeacherDB
from backend.schemas.student import (
    AvailabilitySlotIn,
    RecurringLessonIn,
    RecurringLessonResponse,
    RecurringLessonResult,
    RecurringLessonStopIn,
    RecurringLessonUpdateIn,
    TeacherAvailabilitySlotResponse,
    WeeklyAvailabilityIn,
    WeeklyWindow,
)
from backend.services.availability import create_slot, delete_slot, list_teacher_slots, move_slot, release_slot
from backend.services.student import StudentBusinessError
from backend.services.weekly_schedule import (
    create_recurring,
    extend_teacher_schedule,
    list_recurring,
    list_weekly,
    replace_weekly,
    stop_recurring,
    update_recurring,
)

router = APIRouter()


def _slot_response(db: Session, teacher_id: uuid.UUID, slot_id: uuid.UUID) -> dict:
    return next(row for row in list_teacher_slots(db, teacher_id) if row["id"] == slot_id)


@router.get("/teacher/availability", response_model=list[TeacherAvailabilitySlotResponse])
def get_my_slots(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    extend_teacher_schedule(db, teacher.user_id)
    return list_teacher_slots(db, teacher.user_id)


@router.get("/teacher/availability/weekly", response_model=list[WeeklyWindow])
def get_weekly_availability(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    return list_weekly(db, teacher.user_id)


@router.put("/teacher/availability/weekly", response_model=list[WeeklyWindow])
def set_weekly_availability(
    data: WeeklyAvailabilityIn,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """整份換掉。還沒人預約的固定時段重算，往後維持 8 週；已排的課和待確認的預約不動。"""
    windows = [(item.weekday, item.start_minute, item.end_minute) for item in data.windows]
    try:
        return replace_weekly(db, teacher.user_id, windows)
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/teacher/recurring-lessons", response_model=list[RecurringLessonResponse])
def get_recurring_lessons(
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    return list_recurring(db, teacher.user_id)


@router.post("/teacher/recurring-lessons", response_model=RecurringLessonResult)
def add_recurring_lesson(
    data: RecurringLessonIn,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """學生的固定上課時間。和別的課衝突的那幾週跳過並列在 skipped；和其他固定時間重疊回 409。"""
    try:
        return create_recurring(
            db, teacher.user_id, data.student_id, data.course_id, data.weekday, data.start_minute, data.end_minute
        )
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.patch("/teacher/recurring-lessons/{rule_id}", response_model=RecurringLessonResult)
def change_recurring_lesson(
    rule_id: uuid.UUID,
    data: RecurringLessonUpdateIn,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """已排的課只有老師勾選的才一起移動，其他的保留。"""
    try:
        return update_recurring(
            db, teacher.user_id, rule_id, data.weekday, data.start_minute, data.end_minute, data.move_lesson_ids
        )
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.post("/teacher/recurring-lessons/{rule_id}/stop", status_code=204)
def stop_recurring_lesson(
    rule_id: uuid.UUID,
    data: RecurringLessonStopIn,
    db: Session = Depends(get_db),
    teacher: TeacherDB = Depends(get_current_teacher),
):
    """停用後不再排課。已排的課只取消老師勾選的，其他的保留。"""
    try:
        stop_recurring(db, teacher.user_id, rule_id, data.cancel_lesson_ids)
    except StudentBusinessError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail) from error
    return Response(status_code=204)


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
