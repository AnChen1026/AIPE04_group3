"""可上課時段的規則。

老師在課表上開放時段；已綁定這位老師任一門課的學生點選後送出約課，時段先保留給他，
老師完成約課才排進正式課表。老師和學生私下約好時，老師也可以直接把時段排給學生。
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.student import AvailabilitySlot, ChangeRequest, Course, LessonSession
from backend.models.user import User
from backend.repositories.student import StudentRepository
from backend.services.student import StudentBusinessError, _commit, reopen_slot, require_bound

# 排課的最小單位。老師可能要換地點，例如 18:00-19:00 下一堂 19:15-20:15
SLOT_MINUTES = 15
# 學生新約一堂課可以選的長度；調課沿用原本那堂的長度
BOOKING_MINUTES = (60, 90)


def _on_grid(value: datetime) -> bool:
    return value.minute % SLOT_MINUTES == 0 and value.second == 0 and value.microsecond == 0


def _check_grid(*values: datetime) -> None:
    if not all(_on_grid(value) for value in values):
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "時間要以 15 分鐘為單位。")


def _check_times(starts_at: datetime, ends_at: datetime) -> None:
    if ends_at <= starts_at:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "結束時間要晚於開始時間。")
    _check_grid(starts_at, ends_at)
    if starts_at <= datetime.now(timezone.utc):
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "不能開放已經過去的時間。")


def _overlapping_slot(
    db: Session,
    teacher_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
    ignore_slot_id: uuid.UUID | None = None,
) -> AvailabilitySlot | None:
    query = select(AvailabilitySlot).where(
        AvailabilitySlot.teacher_id == teacher_id,
        AvailabilitySlot.starts_at < ends_at,
        AvailabilitySlot.ends_at > starts_at,
    )
    if ignore_slot_id is not None:
        query = query.where(AvailabilitySlot.id != ignore_slot_id)
    return db.scalar(query)


def _check_free(
    db: Session,
    teacher_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
    ignore_slot_id: uuid.UUID | None = None,
) -> None:
    """同一位老師的時段不能互相重疊，也不能蓋到已排的課。"""
    if _overlapping_slot(db, teacher_id, starts_at, ends_at, ignore_slot_id) is not None:
        raise StudentBusinessError(status.HTTP_409_CONFLICT, "這段時間和其他可上課時段重疊。")
    lesson = db.scalar(
        select(LessonSession).where(
            LessonSession.teacher_id == teacher_id,
            LessonSession.status == "scheduled",
            LessonSession.starts_at < ends_at,
            LessonSession.ends_at > starts_at,
        )
    )
    if lesson is not None:
        raise StudentBusinessError(status.HTTP_409_CONFLICT, "這段時間已經有課。")


def _own_slot(db: Session, teacher_id: uuid.UUID, slot_id: uuid.UUID, lock: bool = False) -> AvailabilitySlot:
    query = select(AvailabilitySlot).where(AvailabilitySlot.id == slot_id)
    if lock:
        query = query.with_for_update()
    slot = db.scalar(query)
    if slot is None or slot.teacher_id != teacher_id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這個時段。")
    return slot


def _carve(db: Session, slot: AvailabilitySlot, starts_at: datetime, ends_at: datetime) -> AvailabilitySlot:
    """把開放時段切成要用的那段；前後剩下的另外留成可預約。原本這筆就是要用的那段。"""
    for piece_start, piece_end in ((slot.starts_at, starts_at), (ends_at, slot.ends_at)):
        if piece_start < piece_end:
            db.add(
                AvailabilitySlot(
                    teacher_id=slot.teacher_id,
                    starts_at=piece_start,
                    ends_at=piece_end,
                    status="open",
                    from_weekly=slot.from_weekly,
                )
            )
    slot.starts_at = starts_at
    slot.ends_at = ends_at
    db.flush()
    return slot


def time_conflict(
    db: Session,
    teacher_id: uuid.UUID,
    student_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
    ignore_session_id: uuid.UUID | None = None,
) -> str | None:
    """老師要把課排在這段時間時的衝突原因。開放時段會讓位，不算衝突。"""
    if StudentRepository.slot_is_taken(db, teacher_id, student_id, starts_at, ends_at, ignore_session_id):
        return "這段時間老師或學生已經有課"
    held = db.scalar(
        select(AvailabilitySlot.id).where(
            AvailabilitySlot.teacher_id == teacher_id,
            AvailabilitySlot.status == "held",
            AvailabilitySlot.starts_at < ends_at,
            AvailabilitySlot.ends_at > starts_at,
        )
    )
    return "這段時間有學生的預約還在等老師確認" if held else None


def take_open_time(db: Session, teacher_id: uuid.UUID, starts_at: datetime, ends_at: datetime) -> AvailabilitySlot | None:
    """課排在開放時段上時，時段讓出這段時間。完整落在一個時段內時，回傳切出來的那段。"""
    overlapping = db.scalars(
        select(AvailabilitySlot)
        .where(
            AvailabilitySlot.teacher_id == teacher_id,
            AvailabilitySlot.status == "open",
            AvailabilitySlot.starts_at < ends_at,
            AvailabilitySlot.ends_at > starts_at,
        )
        .with_for_update()
    ).all()
    taken = None
    for slot in overlapping:
        if slot.starts_at <= starts_at and slot.ends_at >= ends_at:
            taken = _carve(db, slot, starts_at, ends_at)
        elif slot.starts_at < starts_at:
            slot.ends_at = starts_at
        elif slot.ends_at > ends_at:
            slot.starts_at = ends_at
        else:
            db.delete(slot)
    db.flush()
    return taken


def mark_booked(slot: AvailabilitySlot | None, lesson: LessonSession) -> None:
    if slot is None:
        return
    slot.status = "booked"
    slot.student_id = lesson.student_id
    slot.course_id = lesson.course_id
    slot.lesson_id = lesson.id


def _pending_request(db: Session, slot_id: uuid.UUID) -> ChangeRequest | None:
    return db.scalar(
        select(ChangeRequest).where(
            ChangeRequest.availability_slot_id == slot_id,
            ChangeRequest.status == "pending",
        )
    )


def list_teacher_slots(db: Session, teacher_id: uuid.UUID) -> list[dict]:
    """老師自己的全部時段，連同預約的學生、課程與待處理的約課。"""
    slots = list(
        db.scalars(
            select(AvailabilitySlot)
            .where(AvailabilitySlot.teacher_id == teacher_id)
            .order_by(AvailabilitySlot.starts_at)
        )
    )
    student_names = dict(
        db.execute(select(User.id, User.name).where(User.id.in_({slot.student_id for slot in slots if slot.student_id})))
        .all()
    )
    course_titles = dict(
        db.execute(select(Course.id, Course.title).where(Course.id.in_({slot.course_id for slot in slots if slot.course_id})))
        .all()
    )
    requests = dict(
        db.execute(
            select(ChangeRequest.availability_slot_id, ChangeRequest.id).where(
                ChangeRequest.availability_slot_id.in_([slot.id for slot in slots if slot.status == "held"]),
                ChangeRequest.status == "pending",
            )
        )
        .all()
    )
    return [
        {
            "id": slot.id,
            "starts_at": slot.starts_at,
            "ends_at": slot.ends_at,
            "status": slot.status,
            "student_id": slot.student_id,
            "student_name": student_names.get(slot.student_id),
            "course_id": slot.course_id,
            "course_title": course_titles.get(slot.course_id),
            "lesson_id": slot.lesson_id,
            "change_request_id": requests.get(slot.id),
        }
        for slot in slots
    ]


def create_slot(db: Session, teacher_id: uuid.UUID, starts_at: datetime, ends_at: datetime) -> AvailabilitySlot:
    _check_times(starts_at, ends_at)
    _check_free(db, teacher_id, starts_at, ends_at)
    slot = AvailabilitySlot(teacher_id=teacher_id, starts_at=starts_at, ends_at=ends_at, status="open")
    db.add(slot)
    _commit(db)
    db.refresh(slot)
    return slot


def move_slot(
    db: Session, teacher_id: uuid.UUID, slot_id: uuid.UUID, starts_at: datetime, ends_at: datetime
) -> AvailabilitySlot:
    slot = _own_slot(db, teacher_id, slot_id, lock=True)
    if slot.status != "open":
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "已有學生預約的時段不能移動，請先取消預約。")
    _check_times(starts_at, ends_at)
    _check_free(db, teacher_id, starts_at, ends_at, ignore_slot_id=slot.id)
    slot.starts_at = starts_at
    slot.ends_at = ends_at
    _commit(db)
    db.refresh(slot)
    return slot


def delete_slot(db: Session, teacher_id: uuid.UUID, slot_id: uuid.UUID) -> None:
    """刪掉時段。學生點選、還在等老師的約課會一起退回。"""
    slot = _own_slot(db, teacher_id, slot_id, lock=True)
    if slot.status == "booked":
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "已排進課表的時段請先取消預約。")
    pending = _pending_request(db, slot.id)
    if pending is not None:
        pending.status = "rejected"
        pending.availability_slot_id = None
    db.delete(slot)
    _commit(db)


def release_slot(db: Session, teacher_id: uuid.UUID, slot_id: uuid.UUID) -> AvailabilitySlot:
    """取消預約：待確認的約課退回；已排的課取消。時段回到可預約。"""
    slot = _own_slot(db, teacher_id, slot_id, lock=True)
    if slot.status == "open":
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "這個時段還沒有人預約。")
    pending = _pending_request(db, slot.id)
    if pending is not None:
        pending.status = "rejected"
    if slot.lesson_id is not None:
        lesson = db.get(LessonSession, slot.lesson_id)
        if lesson is not None:
            lesson.status = "cancelled"
    reopen_slot(db, slot)
    _commit(db)
    db.refresh(slot)
    return slot


def list_open_slots(db: Session, student: User, course_id: uuid.UUID) -> list[AvailabilitySlot]:
    """已綁定的學生看這門課老師還沒被預約、尚未開始的時段。"""
    course = require_bound(db, student.id, course_id)
    return list(
        db.scalars(
            select(AvailabilitySlot)
            .where(
                AvailabilitySlot.teacher_id == course.teacher_id,
                AvailabilitySlot.status == "open",
                AvailabilitySlot.starts_at > datetime.now(timezone.utc),
            )
            .order_by(AvailabilitySlot.starts_at)
        )
    )


def _hold_part_of_slot(
    db: Session,
    student: User,
    course: Course,
    slot_id: uuid.UUID,
    starts_at: datetime | None,
    minutes: int | None,
    ignore_session_id: uuid.UUID | None = None,
) -> AvailabilitySlot:
    """從開放時段切出學生選的那段並保留給他。

    鎖住這筆時段再判斷：兩人同時按，後到的會等前一筆交易結束，看到的就不是 open。
    """
    slot = db.scalar(select(AvailabilitySlot).where(AvailabilitySlot.id == slot_id).with_for_update())
    if slot is None or slot.teacher_id != course.teacher_id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這個時段。")
    if slot.status != "open":
        raise StudentBusinessError(status.HTTP_409_CONFLICT, "這個時段剛被其他同學預約了。")
    starts_at = starts_at or slot.starts_at
    if minutes is None:
        minutes = min(BOOKING_MINUTES[0], int((slot.ends_at - starts_at).total_seconds() // 60))
    ends_at = starts_at + timedelta(minutes=minutes)
    if not _on_grid(starts_at):
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "時間要以 15 分鐘為單位。")
    if starts_at < slot.starts_at or ends_at > slot.ends_at:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "這段時間超出老師開放的時段。")
    if starts_at <= datetime.now(timezone.utc):
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "這個時段已經過去了。")
    if StudentRepository.slot_is_taken(db, course.teacher_id, student.id, starts_at, ends_at, ignore_session_id):
        raise StudentBusinessError(status.HTTP_409_CONFLICT, "你這段時間已經有課。")
    _carve(db, slot, starts_at, ends_at)
    slot.status = "held"
    slot.student_id = student.id
    slot.course_id = course.id
    return slot


def book_slot(
    db: Session,
    student: User,
    course_id: uuid.UUID,
    slot_id: uuid.UUID,
    starts_at: datetime | None = None,
    minutes: int | None = None,
    reason: str | None = None,
) -> ChangeRequest:
    """學生在開放時段內選開始時間與長度：送出約課並先保留這段，老師完成約課才排進正式課表。"""
    course = require_bound(db, student.id, course_id)
    if minutes is not None and minutes not in BOOKING_MINUTES:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "上課長度只能選 60 或 90 分鐘。")
    slot = _hold_part_of_slot(db, student, course, slot_id, starts_at, minutes)
    change_request = ChangeRequest(
        course_id=course.id,
        teacher_id=course.teacher_id,
        student_id=student.id,
        availability_slot_id=slot.id,
        request_type="booking",
        proposed_starts_at=slot.starts_at,
        proposed_ends_at=slot.ends_at,
        reason=reason,
        status="pending",
    )
    db.add(change_request)
    _commit(db)
    db.refresh(change_request)
    return change_request


def reschedule_to_slot(
    db: Session,
    student: User,
    course_id: uuid.UUID,
    session_id: uuid.UUID,
    slot_id: uuid.UUID,
    starts_at: datetime,
    reason: str | None = None,
) -> ChangeRequest:
    """調課只能選老師開放的時段，長度沿用原本那堂。老師同意前原本的課不變，新時段先保留。"""
    course = require_bound(db, student.id, course_id)
    lesson = StudentRepository.get_session(db, session_id)
    if lesson is None or lesson.student_id != student.id or lesson.course_id != course.id:
        raise StudentBusinessError(status.HTTP_403_FORBIDDEN, "不能對這堂課提出申請。")
    if lesson.status != "scheduled" or lesson.starts_at <= datetime.now(timezone.utc):
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "這堂課已經不能調課。")
    pending = db.scalar(
        select(ChangeRequest.id).where(ChangeRequest.session_id == lesson.id, ChangeRequest.status == "pending")
    )
    if pending is not None:
        raise StudentBusinessError(status.HTTP_409_CONFLICT, "這堂課已經有申請在等老師確認。")
    minutes = int((lesson.ends_at - lesson.starts_at).total_seconds() // 60)
    slot = _hold_part_of_slot(db, student, course, slot_id, starts_at, minutes, ignore_session_id=lesson.id)
    change_request = ChangeRequest(
        course_id=course.id,
        teacher_id=course.teacher_id,
        student_id=student.id,
        session_id=lesson.id,
        availability_slot_id=slot.id,
        request_type="reschedule",
        proposed_starts_at=slot.starts_at,
        proposed_ends_at=slot.ends_at,
        reason=reason,
        status="pending",
    )
    db.add(change_request)
    _commit(db)
    db.refresh(change_request)
    return change_request


def create_teacher_lesson(
    db: Session,
    teacher_id: uuid.UUID,
    student_id: uuid.UUID,
    course_id: uuid.UUID,
    starts_at: datetime,
    ends_at: datetime,
    slot_id: uuid.UUID | None = None,
) -> LessonSession:
    """老師和學生約好了，直接排進正式課表。課的時間由老師決定，蓋到的開放時段會讓出來。"""
    course = StudentRepository.get_course(db, course_id)
    if course is None or course.teacher_id != teacher_id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到你的課程。")
    if not StudentRepository.is_bound(db, student_id, course_id):
        raise StudentBusinessError(status.HTTP_403_FORBIDDEN, "學生尚未綁定這門課。")
    if ends_at <= starts_at:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "結束時間要晚於開始時間。")
    _check_grid(starts_at, ends_at)

    if slot_id is not None:
        slot = _own_slot(db, teacher_id, slot_id, lock=True)
        if slot.status != "open":
            raise StudentBusinessError(status.HTTP_409_CONFLICT, "這個時段已經有人預約。")
    conflict = time_conflict(db, teacher_id, student_id, starts_at, ends_at)
    if conflict is not None:
        raise StudentBusinessError(status.HTTP_409_CONFLICT, f"{conflict}。")

    lesson = LessonSession(
        course_id=course.id,
        teacher_id=teacher_id,
        student_id=student_id,
        starts_at=starts_at,
        ends_at=ends_at,
        status="scheduled",
    )
    db.add(lesson)
    db.flush()
    mark_booked(take_open_time(db, teacher_id, starts_at, ends_at), lesson)
    _commit(db)
    db.refresh(lesson)
    return lesson


def cancel_teacher_lesson(db: Session, teacher_id: uuid.UUID, lesson_id: uuid.UUID) -> LessonSession:
    """老師取消一堂課；它若來自可上課時段，時段回到可預約。"""
    lesson = StudentRepository.get_session(db, lesson_id)
    if lesson is None or lesson.teacher_id != teacher_id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這堂課。")
    if lesson.status != "scheduled":
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "這堂課已經取消了。")
    lesson.status = "cancelled"
    slot = db.scalar(select(AvailabilitySlot).where(AvailabilitySlot.lesson_id == lesson.id))
    if slot is not None:
        reopen_slot(db, slot)
    _commit(db)
    db.refresh(lesson)
    return lesson
