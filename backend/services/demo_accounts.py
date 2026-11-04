"""測試環境建立一組已綁定的老師、學生帳號，附上課程、對話與約課紀錄，讓大家登入就有東西可看。"""

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import read_env_value
from backend.core.security import hash_password
from backend.models.student import AvailabilitySlot, LessonSession
from backend.models.teacher_application import TeacherApplication
from backend.models.user import User
from backend.repositories.user import add_user, get_user_by_email
from backend.services.availability import book_slot
from backend.services.course import create_course
from backend.services.student import _bind_student, _commit, add_message, create_change_request, start_conversation
from backend.services.studio import save_studio
from backend.services.support import send_welcome
from backend.services.weekly_schedule import TAIPEI, _at, create_recurring, replace_weekly

logger = logging.getLogger(__name__)

# 星期用 Python 的算法：0 是週一
TEACHER_WEEKLY = [(1, 14 * 60, 18 * 60), (3, 14 * 60, 18 * 60), (5, 10 * 60, 13 * 60)]
LESSON_WEEKDAY, LESSON_START, LESSON_END = 5, 10 * 60, 11 * 60
PAST_LESSON_WEEKS = 3

MESSAGES = [
    ("student", "老師好，我想學流行鋼琴，可以從零開始嗎？"),
    ("teacher", "可以喔！我們先從和弦和簡單的伴奏開始，每週六早上上一堂。"),
    ("student", "好的，那我先約週六十點。"),
    ("teacher", "沒問題，已經幫你排好固定課了。練習錄音記得上傳，我會看回饋。"),
]


def seed_demo_accounts_if_needed(db: Session) -> None:
    """若 .env 有 demo 老師、學生帳密，且兩個 Email 都還沒註冊，就建立整組 demo 資料。"""
    teacher_email = read_env_value("DEMO_TEACHER_EMAIL")
    teacher_password = read_env_value("DEMO_TEACHER_PASSWORD")
    student_email = read_env_value("DEMO_STUDENT_EMAIL")
    student_password = read_env_value("DEMO_STUDENT_PASSWORD")
    if None in (teacher_email, teacher_password, student_email, student_password):
        return

    teacher_email = teacher_email.strip().lower()
    student_email = student_email.strip().lower()
    # 建過就不動，大家在 demo 帳號裡改的東西不會被重建蓋掉
    if get_user_by_email(db, teacher_email) or get_user_by_email(db, student_email):
        return

    try:
        _create_demo(db, teacher_email, teacher_password, student_email, student_password)
    except Exception:
        db.rollback()
        logger.exception("demo 帳號沒有建立完成")


def _create_demo(db: Session, teacher_email: str, teacher_password: str, student_email: str, student_password: str) -> None:
    teacher = User(
        email=teacher_email,
        password_hash=hash_password(teacher_password),
        auth_provider="password",
        name="王小琴",
        role="teacher",
        is_active=True,
    )
    student = User(
        email=student_email,
        password_hash=hash_password(student_password),
        auth_provider="password",
        name="林小明",
        role="student",
        is_active=True,
    )
    add_user(db, teacher)
    add_user(db, student)
    db.flush()
    db.add(
        TeacherApplication(
            user_id=teacher.id,
            teaching_subjects="流行鋼琴、古典鋼琴",
            teaching_experience="教學 8 年",
            bio="demo 老師帳號",
            status="approved",
        )
    )
    _commit(db)
    send_welcome(db, teacher)
    send_welcome(db, student)

    save_studio(db, teacher.id, {"name": "小琴鋼琴工作室", "owner_name": teacher.name, "city": "台北市", "district": "大安區"})
    course = create_course(
        db,
        teacher.id,
        {
            "title": "流行鋼琴入門",
            "status": "published",
            "level": "入門",
            "style": "流行",
            "delivery_mode": "online",
            "price_per_lesson": 1200,
            "time_slots": "週二、週四下午，週六上午",
            "description": "從和弦與伴奏開始，學會自彈自唱喜歡的流行歌。",
        },
    )

    conversation = start_conversation(db, student, course.id)
    now = datetime.now(timezone.utc)
    _bind_student(db, student, course, now - timedelta(weeks=PAST_LESSON_WEEKS + 1))
    _commit(db)
    for sender, body in MESSAGES:
        add_message(db, conversation, teacher if sender == "teacher" else student, body)

    replace_weekly(db, teacher.id, TEACHER_WEEKLY)
    create_recurring(db, teacher.id, student.id, course.id, LESSON_WEEKDAY, LESSON_START, LESSON_END)
    _add_past_lessons(db, teacher, student, course.id)

    upcoming = db.scalars(
        select(LessonSession)
        .where(LessonSession.student_id == student.id, LessonSession.starts_at > now)
        .order_by(LessonSession.starts_at)
    ).all()
    if len(upcoming) > 1:
        create_change_request(db, student, course.id, "leave", upcoming[1].id, "那週要出國，想請假一次。")

    open_slot = db.scalar(
        select(AvailabilitySlot)
        .where(AvailabilitySlot.teacher_id == teacher.id, AvailabilitySlot.status == "open")
        .order_by(AvailabilitySlot.starts_at)
    )
    if open_slot is not None:
        book_slot(db, student, course.id, open_slot.id, minutes=60, reason="想加一堂練習考試曲目。")


def _add_past_lessons(db: Session, teacher: User, student: User, course_id) -> None:
    """固定課只會往後排，前幾週上過的課直接補進去，課表才看得到歷史紀錄。"""
    today = datetime.now(TAIPEI).date()
    last_lesson_day = today - timedelta(days=(today.weekday() - LESSON_WEEKDAY) % 7 or 7)
    for week in range(PAST_LESSON_WEEKS):
        day = last_lesson_day - timedelta(weeks=week)
        db.add(
            LessonSession(
                course_id=course_id,
                teacher_id=teacher.id,
                student_id=student.id,
                starts_at=_at(day, LESSON_START),
                ends_at=_at(day, LESSON_END),
                status="scheduled",
            )
        )
    _commit(db)
