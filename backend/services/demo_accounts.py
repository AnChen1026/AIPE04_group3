"""測試環境建立一組已綁定的老師、學生帳號，附上課程、對話與約課紀錄，讓大家登入就有東西可看。"""

import io
import logging
import wave
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.config import read_env_value
from backend.core.security import hash_password
from backend.models.student import AvailabilitySlot, LessonSession, PracticeFeedback
from backend.models.teacher_application import TeacherApplication
from backend.models.user import User
from backend.repositories.user import add_user, get_user_by_email
from backend.services.assignment import create_assignment, quiz_questions, submit_quiz_attempt
from backend.services.availability import book_slot
from backend.services.course import create_course
from backend.services.student import (
    _bind_student,
    _commit,
    add_message,
    create_change_request,
    save_recording,
    start_conversation,
)
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

# 演奏作業：C 大調音階上下行，參考 MIDI 和錄音都由程式產生
SCALE_NOTES = [60, 62, 64, 65, 67, 65, 64, 62, 60]
SCALE_BPM = 90
# 音高滿分 70、節奏滿分 30。兩次錄音，看得出進步
RECORDING_FEEDBACK = [
    (14, 48.0, 18.0, "音大多彈對了，第 4、5 個音偶爾按錯；節奏後半段越彈越快，先跟著節拍器慢慢彈。"),
    (5, 61.0, 24.0, "比上次穩定很多，音幾乎都正確。下行時第 7 個音還是稍微搶拍，再練幾次就會更順。"),
]

QUIZ_QUESTIONS = [
    {
        "type": "single",
        "difficulty": "easy",
        "topic": "拍子",
        "question": "在 4/4 拍裡，一個四分音符是幾拍？",
        "options": ["半拍", "一拍", "兩拍", "四拍"],
        "answers": [1],
        "hint": "4/4 拍的分母代表以哪一種音符當一拍。",
        "explanation": "4/4 拍以四分音符為一拍，所以四分音符是一拍。",
    },
    {
        "type": "single",
        "difficulty": "easy",
        "topic": "音名",
        "question": "鋼琴上兩個黑鍵左邊的白鍵是哪一個音？",
        "options": ["C", "D", "E", "F"],
        "answers": [0],
        "hint": "從兩個黑鍵那一組找起。",
        "explanation": "兩個黑鍵左邊的白鍵是 C，也就是 Do。",
    },
    {
        "type": "truefalse",
        "difficulty": "medium",
        "topic": "音階",
        "question": "C 大調音階沒有任何升降記號。",
        "options": ["是", "否"],
        "answers": [0],
        "hint": "想想 C 大調在鋼琴上只用到哪些鍵。",
        "explanation": "C 大調只用白鍵，沒有升降記號。",
    },
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

    _add_assignments(db, teacher, student, course.id)


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


def _add_assignments(db: Session, teacher: User, student: User, course_id) -> None:
    """一份交過兩次錄音的演奏作業、一份作答過一次的題庫作業。"""
    now = datetime.now(timezone.utc)
    performance = create_assignment(
        db,
        teacher.id,
        course_id,
        student.id,
        "performance",
        "C 大調音階上下行",
        "右手 1-2-3-1-2-3-4-5 指法，每個音一樣大聲。",
        now + timedelta(days=5),
        ("c-major-scale.mid", _scale_midi()),
        [],
        practice_bpm=SCALE_BPM,
    )
    # 錄音直接寫入回饋，不跑評分：啟動時不想等音訊分析和 AI
    for days_ago, pitch_score, rhythm_score, text in RECORDING_FEEDBACK:
        recording = save_recording(
            db, student, course_id, "practice.wav", _scale_wav(), assignment=performance, metronome_bpm=SCALE_BPM
        )
        feedback = db.scalar(select(PracticeFeedback).where(PracticeFeedback.recording_id == recording.id))
        recording.submitted_at = now - timedelta(days=days_ago)
        feedback.pitch_score = pitch_score
        feedback.rhythm_score = rhythm_score
        feedback.feedback_text = text
        recording.status = feedback.status = "completed"
        _commit(db)

    quiz = create_assignment(
        db,
        teacher.id,
        course_id,
        student.id,
        "quiz",
        "樂理小測驗：拍子與音名",
        None,
        now + timedelta(days=7),
        None,
        [],
        questions=QUIZ_QUESTIONS,
    )
    questions = quiz_questions(db, quiz.id)
    answers = {item.id: item.answers for item in questions}
    # 第一題故意答錯，學生和老師都看得到錯題
    first = questions[0]
    answers[first.id] = [(first.answers[0] + 1) % len(first.options)]
    submit_quiz_attempt(db, student.id, quiz.id, answers)


def _scale_midi() -> bytes:
    import pretty_midi

    midi = pretty_midi.PrettyMIDI(initial_tempo=SCALE_BPM)
    piano = pretty_midi.Instrument(program=0)
    beat = 60 / SCALE_BPM
    for index, pitch in enumerate(SCALE_NOTES):
        piano.notes.append(pretty_midi.Note(velocity=80, pitch=pitch, start=index * beat, end=(index + 0.9) * beat))
    midi.instruments.append(piano)
    buffer = io.BytesIO()
    midi.write(buffer)
    return buffer.getvalue()


def _scale_wav() -> bytes:
    """用正弦波彈出同一段音階，當作學生的錄音。"""
    import numpy as np

    rate = 22050
    beat = 60 / SCALE_BPM
    tone_time = np.arange(int(rate * beat * 0.9)) / rate
    parts = []
    for pitch in SCALE_NOTES:
        frequency = 440 * 2 ** ((pitch - 69) / 12)
        parts.append(np.sin(2 * np.pi * frequency * tone_time) * np.exp(-3 * tone_time))
        parts.append(np.zeros(int(rate * beat * 0.1)))
    samples = (np.concatenate(parts) * 0.5 * 32767).astype(np.int16)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(rate)
        audio.writeframes(samples.tobytes())
    return buffer.getvalue()
