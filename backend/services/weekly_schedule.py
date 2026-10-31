"""每週固定時間：老師的可上課時間、學生的固定上課時間。

兩者都是規則，實際的時段與課堂一律往後維持 8 週。規則記下已經產生到哪一天，
往後補的時候只補新的日子，所以老師刪掉的單一時段、學生請假的那堂不會被補回來。
"""

import uuid
from collections.abc import Iterator
from datetime import date, datetime, time, timedelta, timezone

from fastapi import status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from backend.models.student import (
    AvailabilitySlot,
    ChangeRequest,
    Course,
    LessonSession,
    RecurringLesson,
    WeeklyAvailability,
)
from backend.models.user import User
from backend.repositories.student import StudentRepository
from backend.services.availability import SLOT_MINUTES, mark_booked, take_open_time, time_conflict
from backend.services.student import StudentBusinessError, _commit, reopen_slot

# 台灣沒有日光節約，規則裡的幾點幾分固定用 UTC+8 換算
TAIPEI = timezone(timedelta(hours=8))
HORIZON_DAYS = 56


def _today() -> date:
    return datetime.now(TAIPEI).date()


def _horizon() -> date:
    return _today() + timedelta(days=HORIZON_DAYS)


def _at(day: date, minute: int) -> datetime:
    return datetime.combine(day, time(0), TAIPEI) + timedelta(minutes=minute)


def _days_on(weekday: int, first: date, last: date) -> Iterator[date]:
    day = first + timedelta(days=(weekday - first.weekday()) % 7)
    while day <= last:
        yield day
        day += timedelta(days=7)


def _check_rule_time(weekday: int, start_minute: int, end_minute: int) -> None:
    if not 0 <= weekday <= 6:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "星期不正確。")
    if not 0 <= start_minute < end_minute <= 1440:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "結束時間要晚於開始時間。")
    if start_minute % SLOT_MINUTES or end_minute % SLOT_MINUTES:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "時間要以 15 分鐘為單位。")


def _fill_weekly(db: Session, rule: WeeklyAvailability, first: date, last: date) -> None:
    """把規則展開成可預約時段，已有時段或課的部分讓開。"""
    now = datetime.now(timezone.utc)
    for day in _days_on(rule.weekday, first, last):
        starts_at, ends_at = _at(day, rule.start_minute), _at(day, rule.end_minute)
        if starts_at <= now:
            continue
        slots = db.execute(
            select(AvailabilitySlot.starts_at, AvailabilitySlot.ends_at).where(
                AvailabilitySlot.teacher_id == rule.teacher_id,
                AvailabilitySlot.starts_at < ends_at,
                AvailabilitySlot.ends_at > starts_at,
            )
        ).all()
        lessons = db.execute(
            select(LessonSession.starts_at, LessonSession.ends_at).where(
                LessonSession.teacher_id == rule.teacher_id,
                LessonSession.status == "scheduled",
                LessonSession.starts_at < ends_at,
                LessonSession.ends_at > starts_at,
            )
        ).all()
        cursor = starts_at
        for busy_start, busy_end in sorted([*slots, *lessons]):
            if busy_start > cursor:
                db.add(_open_slot(rule.teacher_id, cursor, busy_start))
            cursor = max(cursor, busy_end)
        if cursor < ends_at:
            db.add(_open_slot(rule.teacher_id, cursor, ends_at))
        db.flush()


def _open_slot(teacher_id: uuid.UUID, starts_at: datetime, ends_at: datetime) -> AvailabilitySlot:
    return AvailabilitySlot(teacher_id=teacher_id, starts_at=starts_at, ends_at=ends_at, status="open", from_weekly=True)


def _fill_recurring(db: Session, rule: RecurringLesson, first: date, last: date) -> tuple[int, list[dict]]:
    """把固定上課時間排成課。和別的課衝突的那一週跳過，回傳排了幾堂、跳過哪幾週。"""
    now = datetime.now(timezone.utc)
    created = 0
    skipped = []
    for day in _days_on(rule.weekday, first, last):
        starts_at, ends_at = _at(day, rule.start_minute), _at(day, rule.end_minute)
        if starts_at <= now:
            continue
        reason = time_conflict(db, rule.teacher_id, rule.student_id, starts_at, ends_at)
        if reason is not None:
            skipped.append({"starts_at": starts_at, "ends_at": ends_at, "reason": reason})
            continue
        lesson = LessonSession(
            course_id=rule.course_id,
            teacher_id=rule.teacher_id,
            student_id=rule.student_id,
            starts_at=starts_at,
            ends_at=ends_at,
            status="scheduled",
            recurring_lesson_id=rule.id,
        )
        db.add(lesson)
        db.flush()
        mark_booked(take_open_time(db, rule.teacher_id, starts_at, ends_at), lesson)
        created += 1
    return created, skipped


def extend_teacher_schedule(db: Session, teacher_id: uuid.UUID) -> None:
    """看課表時補到往後 8 週。今天補過就不會再寫資料庫；解除綁定的學生不再排課。"""
    horizon = _horizon()
    first = _today()
    changed = False
    for rule in db.scalars(
        select(WeeklyAvailability)
        .where(WeeklyAvailability.teacher_id == teacher_id, WeeklyAvailability.generated_through < horizon)
        .with_for_update()
    ):
        _fill_weekly(db, rule, max(first, rule.generated_through + timedelta(days=1)), horizon)
        rule.generated_through = horizon
        changed = True
    for rule in db.scalars(
        select(RecurringLesson)
        .where(RecurringLesson.teacher_id == teacher_id, RecurringLesson.generated_through < horizon)
        .with_for_update()
    ):
        if not StudentRepository.is_bound(db, rule.student_id, rule.course_id):
            continue
        _fill_recurring(db, rule, max(first, rule.generated_through + timedelta(days=1)), horizon)
        rule.generated_through = horizon
        changed = True
    if changed:
        _commit(db)


def list_weekly(db: Session, teacher_id: uuid.UUID) -> list[WeeklyAvailability]:
    return list(
        db.scalars(
            select(WeeklyAvailability)
            .where(WeeklyAvailability.teacher_id == teacher_id)
            .order_by(WeeklyAvailability.weekday, WeeklyAvailability.start_minute)
        )
    )


def replace_weekly(db: Session, teacher_id: uuid.UUID, windows: list[tuple[int, int, int]]) -> list[WeeklyAvailability]:
    """換掉每週可上課時間：還沒人預約的固定時段重算，已排的課和待確認的預約不動。"""
    ordered = sorted(windows)
    for weekday, start_minute, end_minute in ordered:
        _check_rule_time(weekday, start_minute, end_minute)
    for before, after in zip(ordered, ordered[1:]):
        if before[0] == after[0] and after[1] < before[2]:
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "同一天的時間不能重疊。")

    db.execute(delete(WeeklyAvailability).where(WeeklyAvailability.teacher_id == teacher_id))
    db.execute(
        delete(AvailabilitySlot).where(
            AvailabilitySlot.teacher_id == teacher_id,
            AvailabilitySlot.status == "open",
            AvailabilitySlot.from_weekly.is_(True),
            AvailabilitySlot.starts_at > datetime.now(timezone.utc),
        )
    )
    horizon = _horizon()
    for weekday, start_minute, end_minute in ordered:
        rule = WeeklyAvailability(
            teacher_id=teacher_id,
            weekday=weekday,
            start_minute=start_minute,
            end_minute=end_minute,
            generated_through=horizon,
        )
        db.add(rule)
        db.flush()
        _fill_weekly(db, rule, _today(), horizon)
    _commit(db)
    return list_weekly(db, teacher_id)


def _future_lessons(db: Session, rule_id: uuid.UUID) -> list[LessonSession]:
    return list(
        db.scalars(
            select(LessonSession)
            .where(
                LessonSession.recurring_lesson_id == rule_id,
                LessonSession.status == "scheduled",
                LessonSession.starts_at > datetime.now(timezone.utc),
            )
            .order_by(LessonSession.starts_at)
        )
    )


def _recurring_row(db: Session, rule: RecurringLesson) -> dict:
    student = db.get(User, rule.student_id)
    course = db.get(Course, rule.course_id)
    return {
        "id": rule.id,
        "student_id": rule.student_id,
        "student_name": student.name if student else "學生",
        "course_id": rule.course_id,
        "course_title": course.title if course else "課程",
        "weekday": rule.weekday,
        "start_minute": rule.start_minute,
        "end_minute": rule.end_minute,
        "future_lessons": _future_lessons(db, rule.id),
    }


def list_recurring(db: Session, teacher_id: uuid.UUID) -> list[dict]:
    rules = db.scalars(
        select(RecurringLesson)
        .where(RecurringLesson.teacher_id == teacher_id)
        .order_by(RecurringLesson.weekday, RecurringLesson.start_minute)
    )
    return [_recurring_row(db, rule) for rule in rules]


def _own_rule(db: Session, teacher_id: uuid.UUID, rule_id: uuid.UUID) -> RecurringLesson:
    rule = db.get(RecurringLesson, rule_id)
    if rule is None or rule.teacher_id != teacher_id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這個固定上課時間。")
    return rule


def _check_rule_overlap(
    db: Session,
    teacher_id: uuid.UUID,
    student_id: uuid.UUID,
    weekday: int,
    start_minute: int,
    end_minute: int,
    ignore_rule_id: uuid.UUID | None = None,
) -> None:
    """兩個固定時間重疊的話每週都會撞，直接擋下來，不是跳過某一週能解決的。"""
    query = select(RecurringLesson).where(
        (RecurringLesson.teacher_id == teacher_id) | (RecurringLesson.student_id == student_id),
        RecurringLesson.weekday == weekday,
        RecurringLesson.start_minute < end_minute,
        RecurringLesson.end_minute > start_minute,
    )
    if ignore_rule_id is not None:
        query = query.where(RecurringLesson.id != ignore_rule_id)
    if db.scalars(query).first() is not None:
        raise StudentBusinessError(status.HTTP_409_CONFLICT, "這段時間和其他固定上課時間重疊。")


def create_recurring(
    db: Session,
    teacher_id: uuid.UUID,
    student_id: uuid.UUID,
    course_id: uuid.UUID,
    weekday: int,
    start_minute: int,
    end_minute: int,
) -> dict:
    course = StudentRepository.get_course(db, course_id)
    if course is None or course.teacher_id != teacher_id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到你的課程。")
    if not StudentRepository.is_bound(db, student_id, course_id):
        raise StudentBusinessError(status.HTTP_403_FORBIDDEN, "學生尚未綁定這門課。")
    _check_rule_time(weekday, start_minute, end_minute)
    _check_rule_overlap(db, teacher_id, student_id, weekday, start_minute, end_minute)

    horizon = _horizon()
    rule = RecurringLesson(
        teacher_id=teacher_id,
        student_id=student_id,
        course_id=course_id,
        weekday=weekday,
        start_minute=start_minute,
        end_minute=end_minute,
        generated_through=horizon,
    )
    db.add(rule)
    db.flush()
    created, skipped = _fill_recurring(db, rule, _today(), horizon)
    _commit(db)
    return {"rule": _recurring_row(db, rule), "created": created, "skipped": skipped}


def _withdraw_pending_requests(db: Session, lesson_id: uuid.UUID) -> None:
    """這堂課被老師改動了，學生還在等的請假、調課就不再有意義。"""
    pending = db.scalars(
        select(ChangeRequest).where(ChangeRequest.session_id == lesson_id, ChangeRequest.status == "pending")
    )
    for change_request in pending:
        change_request.status = "rejected"
        slot = db.get(AvailabilitySlot, change_request.availability_slot_id) if change_request.availability_slot_id else None
        if slot is not None:
            reopen_slot(db, slot)


def _chosen_lessons(db: Session, rule_id: uuid.UUID, lesson_ids: list[uuid.UUID]) -> list[LessonSession]:
    wanted = set(lesson_ids)
    return [lesson for lesson in _future_lessons(db, rule_id) if lesson.id in wanted]


def update_recurring(
    db: Session,
    teacher_id: uuid.UUID,
    rule_id: uuid.UUID,
    weekday: int,
    start_minute: int,
    end_minute: int,
    move_lesson_ids: list[uuid.UUID],
) -> dict:
    """改固定時間。已排的課只有老師勾選的才移到同一週的新時間，其他的保留；之後補的週用新時間。"""
    rule = _own_rule(db, teacher_id, rule_id)
    _check_rule_time(weekday, start_minute, end_minute)
    _check_rule_overlap(db, teacher_id, rule.student_id, weekday, start_minute, end_minute, ignore_rule_id=rule.id)
    rule.weekday = weekday
    rule.start_minute = start_minute
    rule.end_minute = end_minute

    now = datetime.now(timezone.utc)
    moved = 0
    skipped = []
    for lesson in _chosen_lessons(db, rule.id, move_lesson_ids):
        local_day = lesson.starts_at.astimezone(TAIPEI).date()
        day = local_day + timedelta(days=weekday - local_day.weekday())
        starts_at, ends_at = _at(day, start_minute), _at(day, end_minute)
        reason = "已經過去的時間" if starts_at <= now else None
        reason = reason or time_conflict(db, teacher_id, rule.student_id, starts_at, ends_at, ignore_session_id=lesson.id)
        if reason is not None:
            skipped.append({"starts_at": starts_at, "ends_at": ends_at, "reason": reason})
            continue
        _withdraw_pending_requests(db, lesson.id)
        old_slot = db.scalar(select(AvailabilitySlot).where(AvailabilitySlot.lesson_id == lesson.id))
        if old_slot is not None:
            reopen_slot(db, old_slot)
        lesson.starts_at = starts_at
        lesson.ends_at = ends_at
        db.flush()
        mark_booked(take_open_time(db, teacher_id, starts_at, ends_at), lesson)
        moved += 1
    _commit(db)
    return {"rule": _recurring_row(db, rule), "created": moved, "skipped": skipped}


def stop_recurring(db: Session, teacher_id: uuid.UUID, rule_id: uuid.UUID, cancel_lesson_ids: list[uuid.UUID]) -> None:
    """停用固定時間，之後不再排課。已排的課只取消老師勾選的，其他的保留。"""
    rule = _own_rule(db, teacher_id, rule_id)
    for lesson in _chosen_lessons(db, rule.id, cancel_lesson_ids):
        _withdraw_pending_requests(db, lesson.id)
        lesson.status = "cancelled"
        slot = db.scalar(select(AvailabilitySlot).where(AvailabilitySlot.lesson_id == lesson.id))
        if slot is not None:
            reopen_slot(db, slot)
    db.delete(rule)
    _commit(db)
