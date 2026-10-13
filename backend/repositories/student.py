"""讀寫學生找課、綁定、課表與練習資料。"""

import uuid
from datetime import datetime

from sqlalchemy import or_, select
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
)
from backend.models.user import User


class StudentRepository:
    @staticmethod
    def get_course(db: Session, course_id: uuid.UUID) -> Course | None:
        return db.get(Course, course_id)

    @staticmethod
    def list_published_courses(db: Session) -> list[Course]:
        return list(
            db.scalars(
                select(Course).where(Course.status == "published").order_by(Course.created_at.desc())
            ).all()
        )

    @staticmethod
    def list_teacher_courses(db: Session, teacher_id: uuid.UUID) -> list[Course]:
        return list(
            db.scalars(
                select(Course).where(Course.teacher_id == teacher_id).order_by(Course.created_at.desc())
            ).all()
        )

    @staticmethod
    def get_conversation(db: Session, conversation_id: uuid.UUID) -> InquiryConversation | None:
        return db.get(InquiryConversation, conversation_id)

    @staticmethod
    def get_conversation_for_student_course(
        db: Session, student_id: uuid.UUID, course_id: uuid.UUID
    ) -> InquiryConversation | None:
        return db.scalar(
            select(InquiryConversation).where(
                InquiryConversation.student_id == student_id,
                InquiryConversation.course_id == course_id,
            )
        )

    @staticmethod
    def list_student_conversations(db: Session, student_id: uuid.UUID) -> list[InquiryConversation]:
        return list(
            db.scalars(
                select(InquiryConversation)
                .where(InquiryConversation.student_id == student_id)
                .order_by(InquiryConversation.created_at.desc())
            ).all()
        )

    @staticmethod
    def list_teacher_conversations(db: Session, teacher_id: uuid.UUID) -> list[InquiryConversation]:
        return list(
            db.scalars(
                select(InquiryConversation)
                .where(InquiryConversation.teacher_id == teacher_id)
                .order_by(InquiryConversation.created_at.desc())
            ).all()
        )

    @staticmethod
    def list_messages(db: Session, conversation_id: uuid.UUID) -> list[ConversationMessage]:
        return list(
            db.scalars(
                select(ConversationMessage)
                .where(ConversationMessage.conversation_id == conversation_id)
                .order_by(ConversationMessage.created_at.asc())
            ).all()
        )

    @staticmethod
    def unread_count(db: Session, conversation_id: uuid.UUID, reader_id: uuid.UUID) -> int:
        messages = db.scalars(
            select(ConversationMessage).where(
                ConversationMessage.conversation_id == conversation_id,
                ConversationMessage.sender_id != reader_id,
                ConversationMessage.read_at.is_(None),
            )
        ).all()
        return len(messages)

    @staticmethod
    def get_binding(db: Session, student_id: uuid.UUID, course_id: uuid.UUID) -> CourseBinding | None:
        return db.scalar(
            select(CourseBinding).where(
                CourseBinding.student_id == student_id,
                CourseBinding.course_id == course_id,
            )
        )

    @staticmethod
    def is_bound(db: Session, student_id: uuid.UUID, course_id: uuid.UUID) -> bool:
        binding = StudentRepository.get_binding(db, student_id, course_id)
        return binding is not None and binding.status == "bound"

    @staticmethod
    def get_binding_code(db: Session, code: str) -> BindingCode | None:
        return db.scalar(select(BindingCode).where(BindingCode.code == code))

    @staticmethod
    def list_schedule(db: Session, student_id: uuid.UUID, course_id: uuid.UUID) -> list[LessonSession]:
        return list(
            db.scalars(
                select(LessonSession)
                .where(
                    LessonSession.student_id == student_id,
                    LessonSession.course_id == course_id,
                    LessonSession.status == "scheduled",
                )
                .order_by(LessonSession.starts_at.asc())
            ).all()
        )

    @staticmethod
    def get_session(db: Session, session_id: uuid.UUID) -> LessonSession | None:
        return db.get(LessonSession, session_id)

    @staticmethod
    def slot_is_taken(
        db: Session,
        teacher_id: uuid.UUID,
        student_id: uuid.UUID,
        starts_at: datetime,
        ends_at: datetime,
        ignore_session_id: uuid.UUID | None = None,
    ) -> bool:
        query = select(LessonSession).where(
            LessonSession.status == "scheduled",
            LessonSession.starts_at < ends_at,
            LessonSession.ends_at > starts_at,
            or_(LessonSession.teacher_id == teacher_id, LessonSession.student_id == student_id),
        )
        if ignore_session_id is not None:
            query = query.where(LessonSession.id != ignore_session_id)
        return db.scalar(query) is not None

    @staticmethod
    def list_change_requests_for_student(db: Session, student_id: uuid.UUID, course_id: uuid.UUID) -> list[ChangeRequest]:
        return list(
            db.scalars(
                select(ChangeRequest)
                .where(ChangeRequest.student_id == student_id, ChangeRequest.course_id == course_id)
                .order_by(ChangeRequest.created_at.desc())
            ).all()
        )

    @staticmethod
    def list_pending_requests_for_teacher(db: Session, teacher_id: uuid.UUID) -> list[ChangeRequest]:
        return list(
            db.scalars(
                select(ChangeRequest)
                .where(ChangeRequest.teacher_id == teacher_id, ChangeRequest.status == "pending")
                .order_by(ChangeRequest.created_at.asc())
            ).all()
        )

    @staticmethod
    def get_change_request(db: Session, request_id: uuid.UUID) -> ChangeRequest | None:
        return db.get(ChangeRequest, request_id)

    @staticmethod
    def list_recordings(db: Session, student_id: uuid.UUID, course_id: uuid.UUID) -> list[PracticeRecording]:
        return list(
            db.scalars(
                select(PracticeRecording)
                .where(PracticeRecording.student_id == student_id, PracticeRecording.course_id == course_id)
                .order_by(PracticeRecording.submitted_at.desc())
            ).all()
        )

    @staticmethod
    def get_recording(db: Session, recording_id: uuid.UUID) -> PracticeRecording | None:
        return db.get(PracticeRecording, recording_id)

    @staticmethod
    def get_feedback(db: Session, recording_id: uuid.UUID) -> PracticeFeedback | None:
        return db.scalar(select(PracticeFeedback).where(PracticeFeedback.recording_id == recording_id))

    @staticmethod
    def get_user(db: Session, user_id: uuid.UUID) -> User | None:
        return db.get(User, user_id)
