from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid

from backend.models.student import CourseInquiry
from backend.schemas.student import InquiryCreate
from backend.repositories.student import StudentRepository

class DuplicateRequestError(ValueError):
    """防止重複送出的客製化異常錯誤。"""

def process_student_inquiry(db: Session, student_id: uuid.UUID, payload: InquiryCreate) -> CourseInquiry:
    """處理學生發起站內洽詢的商業邏輯（完美串接 StudentRepository 與最新 Schema 規格）。"""
    
    # 呼叫 StudentRepository 中自帶去重邏輯的 create_inquiry 函式
    # payload.message，完全對齊 Schema
    inquiry = StudentRepository.create_inquiry(
        db=db,
        student_id=student_id,
        course_id=payload.course_id,
        message=payload.message, # 完美對齊 schemas/student.py 欄位
        client_request_id=payload.client_request_id,
        session_id=payload.recommendation_session_id
    )
    
    # 檢查返回的資料是否已存在。如果 client_request_id 相同且非新建立，可在此拋出客製化異常
    return inquiry
