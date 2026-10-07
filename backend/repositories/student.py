import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.models.student import StudentProfile, CourseInquiry, Enrollment

def get_student_profile_by_user_id(db: Session, user_id: uuid.UUID) -> StudentProfile | None:
    """透過 users.id 取得學生的 Profile。"""
    return db.scalar(select(StudentProfile).where(StudentProfile.user_id == user_id))

def check_inquiry_duplicate(db: Session, client_request_id: uuid.UUID) -> bool:
    """檢查洽詢去重鍵是否已存在。"""
    return db.scalar(select(CourseInquiry).where(CourseInquiry.client_request_id == client_request_id)) is not None

def save_inquiry(db: Session, inquiry: CourseInquiry) -> None:
    """儲存洽詢紀錄。"""
    db.add(inquiry)

def get_student_active_enrollment(db: Session, student_id: uuid.UUID, course_id: uuid.UUID) -> Enrollment | None:
    """檢查學生在該課程是否擁有 active 的正式修課關係。"""
    statement = select(Enrollment).where(
        Enrollment.student_id == student_id,
        Enrollment.course_id == course_id,
        Enrollment.status == "active"
    )
    return db.scalar(statement)
