import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies import get_current_user, require_roles 
from backend.schemas.student import (
    StudentProfileSchema, StudentProfileUpdate, InquiryCreate, InquiryResponse, 
    EnrollmentResponse, LessonSessionResponse, ChangeRequestCreate, ChangeRequestResponse,
    AssignmentResponse, SubmissionCreate, SubmissionHistoryResponse
)
from backend.repositories.student import StudentRepository


from backend.services.student import (
    process_student_inquiry, 
    process_student_change_request, 
    process_student_submission, 
    StudentBusinessError
)

router = APIRouter(
    prefix="/api/student",
    tags=["Student 學生端功能"],
    dependencies=[Depends(get_current_user), Depends(require_roles("student"))] # 限制必須是學生身份
)

@router.get("/me", response_model=StudentProfileSchema)
def get_my_profile(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """取得當前登入學生的 Profile 資訊"""
    profile = StudentRepository.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="找不到該學生的 Profile 資料，請確認註冊流程是否正確。")
    return profile

@router.patch("/me", response_model=StudentProfileSchema)
def update_my_profile(payload: StudentProfileUpdate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """更新學生的自我程度與備註"""
    profile = StudentRepository.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="找不到學生 Profile")
    return StudentRepository.update_profile(db, profile, payload.current_level, payload.notes)

@router.post("/inquiries", response_model=InquiryResponse)
def create_course_inquiry(payload: InquiryCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """學生對公開課程發起站內洽詢"""
    profile = StudentRepository.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="學生資料異常")
        
    # 完美呼叫原本就規劃在 services/student.py 的找課洽詢處理邏輯
    inquiry = process_student_inquiry(db=db, student_id=profile.id, payload=payload)
    return inquiry

@router.get("/inquiries", response_model=list[InquiryResponse])
def get_my_inquiries(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """學生查看自己過去所有的洽詢紀錄"""
    profile = StudentRepository.get_profile_by_user_id(db, current_user.id)
    return StudentRepository.get_student_inquiries(db, profile.id)

@router.get("/enrollments", response_model=list[EnrollmentResponse])
def get_my_enrollments(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """學生查看自己目前所有的修課班級 (Active/Paused 等)"""
    profile = StudentRepository.get_profile_by_user_id(db, current_user.id)
    return StudentRepository.get_student_enrollments(db, profile.id)


# ======================================================================
# 學生課表查詢與請假調課異動申請 API 端點

@router.get("/schedule", response_model=list[LessonSessionResponse])
def get_my_schedule(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """【課表功能】取得當前登入學生的個人課表曆資訊"""
    profile = StudentRepository.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="學生資料異常")
    return StudentRepository.get_student_schedule(db, profile.id)


@router.post("/change-requests", response_model=ChangeRequestResponse, status_code=201)
def apply_for_lesson_change(
    payload: ChangeRequestCreate, 
    current_user=Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    """【課務申請】學生發起約課、請假或調課申請"""
    profile = StudentRepository.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="學生資料異常")

    try:
        return process_student_change_request(db, current_user.id, profile.id, payload)
    except StudentBusinessError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/change-requests", response_model=list[ChangeRequestResponse])
def get_my_change_requests(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """【異動歷史】學生查詢自己所有的請假、調課申請審核紀錄與狀態"""
    profile = StudentRepository.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="學生資料異常")
    return StudentRepository.get_student_change_requests(db, profile.id)


# ======================================================================
# 學生練習作業列表、錄音確認提交、評分歷史狀態查詢 API 端點

@router.get("/assignments", response_model=list[AssignmentResponse])
def list_my_practice_assignments(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """【作業清單】學生查看目前所有被指派且已發布（published）的鋼琴練習作業"""
    profile = StudentRepository.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="學生資料異常")
    return StudentRepository.get_student_assignments(db, profile.id)


@router.post("/assignments/{assignment_id}/submissions", response_model=SubmissionHistoryResponse, status_code=201)
def submit_lesson_recording(
    assignment_id: uuid.UUID,
    payload: SubmissionCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """【錄音送出】學生確認上傳並發起音訊分析與 LLM 評分任務"""
    profile = StudentRepository.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="學生資料異常")

    try:
        return process_student_submission(db, profile.id, assignment_id, payload)
    except StudentBusinessError as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)


@router.get("/assignments/{assignment_id}/submissions", response_model=list[SubmissionHistoryResponse])
def get_my_submission_history(
    assignment_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """【評分與歷史】學生針對特定作業，查看自己多次錄音提交的 AI 分數與 LLM 導師回饋"""
    profile = StudentRepository.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="學生資料異常")

    assignment = StudentRepository.get_assignment_by_id_and_student(db, assignment_id, profile.id)
    if not assignment:
        raise HTTPException(status_code=403, detail="您沒有查看此份作業歷史紀錄的權限。")

    return StudentRepository.get_submission_history_with_evaluation(db, assignment.id, profile.id)
