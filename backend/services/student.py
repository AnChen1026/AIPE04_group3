"""學生接洽、綁定、課表與練習的規則。"""

import hashlib
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.student import (
    BindingCode,
    ChangeRequest,
    ConversationMessage,
    Course,
    CourseBinding,
    InquiryConversation,
    LessonSession,
    PracticeFeedback,
    PracticeRecording,
    ReferenceMidi,
)
from backend.models.user import User
from backend.repositories.student import StudentRepository
from backend.services.chat_hub import chat_hub, message_event

UPLOAD_DIR = Path("uploads")


class StudentBusinessError(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def _commit(db: Session) -> None:
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise


def list_home_course_rows(db: Session) -> list[dict]:
    """首頁依課程類型分成橫向列，只顯示已發布課程。"""
    rows = db.execute(
        select(Course, User.name)
        .join(User, User.id == Course.teacher_id)
        .where(Course.status == "published")
        .order_by(Course.title)
    ).all()
    grouped: dict[str, list[dict]] = {}
    style_order: list[str] = []
    for course, teacher_name in rows:
        style = course.style or "其他鋼琴"
        if style not in grouped:
            grouped[style] = []
            style_order.append(style)
        grouped[style].append(
            {
                "id": course.id,
                "title": course.title,
                "region": course.region or "地區未填",
                "teacher_name": teacher_name,
            }
        )
    preferred = ["古典鋼琴", "流行鋼琴", "爵士鋼琴"]
    style_order.sort(key=lambda name: preferred.index(name) if name in preferred else len(preferred))
    return [{"style": style, "courses": grouped[style]} for style in style_order]


def list_published_courses(db: Session) -> list[Course]:
    return StudentRepository.list_published_courses(db)


def start_conversation(db: Session, student: User, course_id: uuid.UUID) -> InquiryConversation:
    """學生對已發布課程按洽詢，建立或打開同一段對話。"""
    course = StudentRepository.get_course(db, course_id)
    if course is None or course.status != "published":
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "這門課尚未發布，不能洽詢。")
    if course.teacher_id == student.id:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "不能洽詢自己的課程。")

    existing = StudentRepository.get_conversation_for_student_course(db, student.id, course.id)
    if existing is not None:
        return existing

    conversation = InquiryConversation(
        student_id=student.id,
        teacher_id=course.teacher_id,
        course_id=course.id,
    )
    db.add(conversation)
    _commit(db)
    db.refresh(conversation)
    return conversation


def student_can_read_conversation(conversation: InquiryConversation, student: User) -> bool:
    return conversation.student_id == student.id


def add_message(
    db: Session,
    conversation: InquiryConversation,
    sender: User,
    body: str,
    client_message_id: str | None = None,
) -> ConversationMessage:
    text = body.strip()
    if text == "":
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "訊息不能是空白。")
    if sender.id not in (conversation.student_id, conversation.teacher_id):
        raise StudentBusinessError(status.HTTP_403_FORBIDDEN, "不能在這段對話發言。")

    client_id = (client_message_id or "").strip() or None
    if client_id is not None and len(client_id) > 64:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "訊息編號太長。")
    if client_id is not None:
        existing = StudentRepository.get_message_by_client_id(db, conversation.id, client_id)
        if existing is not None:
            chat_hub.publish(conversation.id, message_event(existing))
            return existing

    message = ConversationMessage(
        conversation_id=conversation.id,
        sender_id=sender.id,
        client_message_id=client_id,
        body=text,
    )
    db.add(message)
    try:
        _commit(db)
    except IntegrityError:
        db.rollback()
        if client_id is None:
            raise
        existing = StudentRepository.get_message_by_client_id(db, conversation.id, client_id)
        if existing is None:
            raise
        chat_hub.publish(conversation.id, message_event(existing))
        return existing
    db.refresh(message)
    chat_hub.publish(conversation.id, message_event(message))
    return message


def mark_conversation_read(db: Session, conversation_id: uuid.UUID, reader_id: uuid.UUID) -> None:
    messages = StudentRepository.list_messages(db, conversation_id)
    now = datetime.now(timezone.utc)
    changed = False
    for message in messages:
        if message.sender_id != reader_id and message.read_at is None:
            message.read_at = now
            changed = True
    if changed:
        _commit(db)


def redeem_binding_code(db: Session, student: User, conversation: InquiryConversation, code: str) -> CourseBinding:
    """綁定碼只讓這位學生進入這門課。"""
    binding_code = StudentRepository.get_binding_code(db, code.strip())
    if binding_code is None or binding_code.used_at is not None:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "綁定碼不能使用。")
    if binding_code.student_id != student.id or binding_code.course_id != conversation.course_id:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "這組綁定碼不能進入這門課。")
    if binding_code.conversation_id != conversation.id:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "這組綁定碼不屬於這段對話。")

    binding = StudentRepository.get_binding(db, student.id, conversation.course_id)
    now = datetime.now(timezone.utc)
    if binding is None:
        binding = CourseBinding(
            student_id=student.id,
            teacher_id=conversation.teacher_id,
            course_id=conversation.course_id,
            status="bound",
            bound_at=now,
        )
        db.add(binding)
    else:
        binding.status = "bound"
        binding.bound_at = now
        binding.unbound_at = None
    binding_code.used_at = now
    _commit(db)
    db.refresh(binding)
    return binding


def require_bound(db: Session, student_id: uuid.UUID, course_id: uuid.UUID) -> Course:
    course = StudentRepository.get_course(db, course_id)
    if course is None:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這門課。")
    if not StudentRepository.is_bound(db, student_id, course_id):
        raise StudentBusinessError(status.HTTP_403_FORBIDDEN, "綁定前不能使用課表、錄音或練習回饋。")
    return course


def create_change_request(
    db: Session,
    student: User,
    course_id: uuid.UUID,
    request_type: str,
    session_id: uuid.UUID | None,
    proposed_starts_at: datetime | None,
    proposed_ends_at: datetime | None,
    reason: str | None,
) -> ChangeRequest:
    course = require_bound(db, student.id, course_id)
    if request_type not in ("booking", "leave", "reschedule"):
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "申請種類不正確。")
    if request_type in ("leave", "reschedule"):
        if session_id is None:
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "請假或調課要指定原本的課堂。")
        lesson = StudentRepository.get_session(db, session_id)
        if lesson is None or lesson.student_id != student.id or lesson.course_id != course.id:
            raise StudentBusinessError(status.HTTP_403_FORBIDDEN, "不能對這堂課提出申請。")
    if request_type in ("booking", "reschedule"):
        if proposed_starts_at is None or proposed_ends_at is None or proposed_ends_at <= proposed_starts_at:
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "請填開始和結束時間，結束要晚於開始。")

    change_request = ChangeRequest(
        course_id=course.id,
        teacher_id=course.teacher_id,
        student_id=student.id,
        session_id=session_id,
        request_type=request_type,
        proposed_starts_at=proposed_starts_at,
        proposed_ends_at=proposed_ends_at,
        reason=reason,
        status="pending",
    )
    db.add(change_request)
    _commit(db)
    db.refresh(change_request)
    return change_request


def save_recording(
    db: Session,
    student: User,
    course_id: uuid.UUID,
    filename: str,
    content: bytes,
) -> PracticeRecording:
    course = require_bound(db, student.id, course_id)
    suffix = Path(filename).suffix.lower()
    if suffix not in (".wav", ".webm", ".mp3", ".m4a", ".ogg"):
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "請上傳音檔，或用網頁錄音。")
    if len(content) == 0:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "音檔是空的。")

    recording_id = uuid.uuid4()
    folder = UPLOAD_DIR / "practice" / str(student.id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{recording_id}{suffix}"
    path.write_bytes(content)

    recording = PracticeRecording(
        id=recording_id,
        course_id=course.id,
        teacher_id=course.teacher_id,
        student_id=student.id,
        file_path=str(path),
        status="pending",
    )
    feedback = PracticeFeedback(
        recording_id=recording_id,
        course_id=course.id,
        teacher_id=course.teacher_id,
        student_id=student.id,
        status="pending",
    )
    db.add(recording)
    db.add(feedback)
    _commit(db)
    db.refresh(recording)
    return recording


def create_course(
    db: Session,
    teacher: User,
    title: str,
    level: str | None,
    style: str | None,
    delivery_mode: str | None,
    region: str | None,
    price_per_lesson: int | None,
    time_slots: str | None,
    publish: bool,
    midi_name: str | None,
    midi_content: bytes | None,
) -> Course:
    if title.strip() == "":
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "課程名稱不能是空白。")

    midi_file_path: Path | None = None
    midi_storage_key: str | None = None
    midi_original_name: str | None = None
    midi_sha256: str | None = None
    midi_size: int | None = None
    if midi_name is not None:
        suffix = Path(midi_name).suffix.lower()
        if suffix not in (".mid", ".midi"):
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "參考檔必須是 MIDI（.mid 或 .midi）。")
        if not midi_content:
            raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "參考 MIDI 檔是空的。")

        midi_original_name = midi_name.replace("\\", "/").rsplit("/", 1)[-1][-255:]
        midi_sha256 = hashlib.sha256(midi_content).hexdigest()
        midi_size = len(midi_content)
        folder = UPLOAD_DIR / "midi" / str(teacher.id)
        folder.mkdir(parents=True, exist_ok=True)
        midi_file_path = folder / f"{uuid.uuid4()}{suffix}"
        midi_file_path.write_bytes(midi_content)
        midi_storage_key = str(midi_file_path)
    elif midi_content:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "參考 MIDI 缺少檔名。")

    course = Course(
        id=uuid.uuid4(),
        teacher_id=teacher.id,
        title=title.strip(),
        level=level or None,
        style=style or None,
        delivery_mode=delivery_mode or None,
        region=region or None,
        price_per_lesson=price_per_lesson,
        time_slots=time_slots or None,
        status="published" if publish else "draft",
        reference_midi_path=midi_storage_key,
    )
    db.add(course)
    if midi_storage_key is not None:
        db.add(
            ReferenceMidi(
                course_id=course.id,
                teacher_id=teacher.id,
                storage_key=midi_storage_key,
                original_filename=midi_original_name,
                content_sha256=midi_sha256,
                file_size_bytes=midi_size,
            )
        )
    try:
        _commit(db)
    except Exception:
        if midi_file_path is not None:
            midi_file_path.unlink(missing_ok=True)
        raise
    db.refresh(course)
    return course


def issue_binding_code(db: Session, teacher: User, conversation_id: uuid.UUID) -> BindingCode:
    conversation = StudentRepository.get_conversation(db, conversation_id)
    if conversation is None or conversation.teacher_id != teacher.id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這段接洽對話。")

    code = secrets.token_hex(4).upper()
    binding_code = BindingCode(
        code=code,
        student_id=conversation.student_id,
        teacher_id=teacher.id,
        course_id=conversation.course_id,
        conversation_id=conversation.id,
    )
    db.add(binding_code)
    message = ConversationMessage(
        conversation_id=conversation.id,
        sender_id=teacher.id,
        body=f"綁定碼：{code}",
    )
    db.add(message)
    _commit(db)
    db.refresh(binding_code)
    db.refresh(message)
    chat_hub.publish(conversation.id, message_event(message))
    return binding_code


def decide_change_request(db: Session, teacher: User, request_id: uuid.UUID, approve: bool) -> ChangeRequest:
    change_request = StudentRepository.get_change_request(db, request_id)
    if change_request is None or change_request.teacher_id != teacher.id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到這筆課務申請。")
    if change_request.status != "pending":
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "這筆申請已經處理過。")
    if not StudentRepository.is_bound(db, change_request.student_id, change_request.course_id):
        raise StudentBusinessError(status.HTTP_403_FORBIDDEN, "學生尚未綁定這門課。")

    if not approve:
        change_request.status = "rejected"
        _commit(db)
        db.refresh(change_request)
        return change_request

    if change_request.request_type == "leave":
        lesson = StudentRepository.get_session(db, change_request.session_id)
        if lesson is None:
            raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到原本的課堂。")
        lesson.status = "cancelled"
    else:
        ignore_id = change_request.session_id if change_request.request_type == "reschedule" else None
        taken = StudentRepository.slot_is_taken(
            db,
            change_request.teacher_id,
            change_request.student_id,
            change_request.proposed_starts_at,
            change_request.proposed_ends_at,
            ignore_id,
        )
        if taken:
            change_request.status = "rejected"
            _commit(db)
            db.refresh(change_request)
            raise StudentBusinessError(status.HTTP_409_CONFLICT, "時段已被占用，正式課表沒有改變。")
        if change_request.request_type == "booking":
            db.add(
                LessonSession(
                    course_id=change_request.course_id,
                    teacher_id=change_request.teacher_id,
                    student_id=change_request.student_id,
                    starts_at=change_request.proposed_starts_at,
                    ends_at=change_request.proposed_ends_at,
                    status="scheduled",
                )
            )
        else:
            lesson = StudentRepository.get_session(db, change_request.session_id)
            if lesson is None:
                raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到原本的課堂。")
            lesson.starts_at = change_request.proposed_starts_at
            lesson.ends_at = change_request.proposed_ends_at

    change_request.status = "approved"
    _commit(db)
    db.refresh(change_request)
    return change_request


def unbind_student(db: Session, teacher: User, course_id: uuid.UUID, student_id: uuid.UUID) -> CourseBinding:
    course = StudentRepository.get_course(db, course_id)
    if course is None or course.teacher_id != teacher.id:
        raise StudentBusinessError(status.HTTP_404_NOT_FOUND, "找不到你的課程。")
    binding = StudentRepository.get_binding(db, student_id, course_id)
    if binding is None or binding.status != "bound":
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "這位學生目前沒有綁定這門課。")
    binding.status = "unbound"
    binding.unbound_at = datetime.now(timezone.utc)
    _commit(db)
    db.refresh(binding)
    return binding
