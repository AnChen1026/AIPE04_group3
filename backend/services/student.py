import uuid
from fastapi import status
from sqlalchemy.orm import Session

from backend.models.student import CourseInquiry, ChangeRequest, PracticeSubmission
from backend.schemas.student import InquiryCreate, ChangeRequestCreate, SubmissionCreate
from backend.repositories.student import StudentRepository

class StudentBusinessError(Exception):
    """
    自定義學生端商業邏輯異常類別
    讓 API 路由與網頁 SSR View 能精準捕捉並回傳對應的 HTTP 狀態碼與錯誤訊息。
    """
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


def process_student_inquiry(db: Session, student_id: uuid.UUID, payload: InquiryCreate) -> CourseInquiry:
    """處理學生發起站內課程洽詢的商業邏輯。"""
    inquiry = StudentRepository.create_inquiry(
        db=db,
        student_id=student_id,
        course_id=payload.course_id,
        message=payload.message,
        client_request_id=payload.client_request_id,
        session_id=payload.recommendation_session_id
    )
    return inquiry


def process_student_change_request(
    db: Session, 
    user_id: uuid.UUID, 
    student_id: uuid.UUID, 
    payload: ChangeRequestCreate
) -> ChangeRequest:
    """
    處理學生發起課務異動（約課/請假/調課）的核心業務邏輯
    死守防禦防線：強制校驗橫向越權權限，並納入樂觀鎖版本校驗。
    """
    # 1. 橫向越權防禦：驗證該修課紀錄是否確實屬於當前登入的學生
    enrollment = StudentRepository.get_enrollment_by_id_and_student(db, payload.enrollment_id, student_id)
    if not enrollment:
        raise StudentBusinessError(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="安全防禦：該修課紀錄不存在，或不屬於您本人，拒絕發起異動。"
        )
        
    # 2. 針對請假與調課，強制進行原課堂與樂觀鎖版本校驗
    session = None
    if payload.request_type in ("leave", "reschedule"):
        if not payload.session_id:
            raise StudentBusinessError(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不合規的請求：請假或調課申請必須指定原本的課堂時段。"
            )
        
        session = StudentRepository.get_session_by_id(db, payload.session_id)
        if not session:
            raise StudentBusinessError(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="找不到您指定的原課堂資料。"
            )
            
        # 樂觀鎖（Optimistic Locking）機制防衝突
        if session.version and payload.proposed_payload.get("expected_version"):
            if session.version != payload.proposed_payload["expected_version"]:
                raise StudentBusinessError(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="該堂課的時間已被異動，請重新整理個人課表頁面後再試。"
                )

    # 3. 交付 Repository 層執行全局去重並落實雙方審核初始化
    return StudentRepository.create_change_request(
        db=db,
        user_id=user_id,
        enrollment=enrollment,
        session=session,
        request_type=payload.request_type,
        proposed_payload=payload.proposed_payload,
        reason=payload.reason,
        client_request_id=payload.client_request_id
    )


def process_student_submission(
    db: Session, 
    student_id: uuid.UUID, 
    assignment_id: uuid.UUID, 
    payload: SubmissionCreate
) -> PracticeSubmission:
    """
    處理學生練習作業錄音提交的核心業務邏輯
    死守防禦防線：嚴防橫向越權提交非本人作業，串接去重防連點機制，分數預設為 NULL。
    """
    # 1. 橫向越權防禦：安全校驗該指派作業是否確實存在，且屬於當前學生的班級
    assignment = StudentRepository.get_assignment_by_id_and_student(db, assignment_id, student_id)
    if not assignment:
        raise StudentBusinessError(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="安全防禦：該指定作業不存在，或不屬於您的修課班級，拒絕上傳錄音。"
        )

    # 2. 呼叫自帶 client_submission_id 冪等性檢查的 Repository 函數
    # 完美落實音訊分析尚未完成前，評分欄位一律維持 NULL、API 絕不盲目顯示 0 分的鐵律
    submission = StudentRepository.create_submission(
        db=db,
        assignment_id=assignment.id,
        student_id=student_id,
        audio_file_id=payload.audio_file_id,
        duration_seconds=payload.duration_seconds,
        client_submission_id=payload.client_submission_id
    )
    
    return submission
