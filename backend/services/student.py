from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import uuid

from backend.models.student import CourseInquiry
from backend.schemas.student import InquiryCreate
import backend.repositories.student as student_repo

class DuplicateRequestError(ValueError):
    """防止重複送出的客製化異常錯誤。"""

def process_student_inquiry(db: Session, student_id: uuid.UUID, payload: InquiryCreate) -> CourseInquiry:
    """處理學生發起站內洽詢的商業邏輯（含去重防禦與交易控制）。"""
    
    # 1. 檢查防手抖去重鍵
    if student_repo.check_inquiry_duplicate(db, payload.client_request_id):
        raise DuplicateRequestError("此筆洽詢已在處理中，請勿重複點擊發送。")

    # 2. 轉換為實體 Model
    new_inquiry = CourseInquiry(
        student_id=student_id,
        course_id=payload.course_id,
        message=payload.inquiry_text,
        client_request_id=payload.client_request_id,
        status="new"
    )

    student_repo.save_inquiry(db, new_inquiry)

    # 3. 交易安全控制
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise DuplicateRequestError("資料衝突，該筆請求已被處理過。")
    except Exception:
        db.rollback()
        raise

    db.refresh(new_inquiry)
    return new_inquiry
