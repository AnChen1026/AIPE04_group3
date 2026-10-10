from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.core.database import get_db
from backend.dependencies import get_current_user, require_roles 
from backend.schemas.student import StudentProfileSchema, StudentProfileUpdate, InquiryCreate, InquiryResponse, EnrollmentResponse,LessonSessionResponse, ChangeRequestCreate, ChangeRequestResponse
from backend.schemas.student import AssignmentResponse, SubmissionCreate, SubmissionHistoryResponse
from backend.repositories.student import StudentRepository
import uuid


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
        
    inquiry = StudentRepository.create_inquiry(
        db=db,
        student_id=profile.id,
        course_id=payload.course_id,
        message=payload.message,
        client_request_id=payload.client_request_id,
        session_id=payload.recommendation_session_id
    )
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
    """【課務申請】學生發起約課、請假或調課申請（自帶樂樂鎖版本與去重機制）"""
    profile = StudentRepository.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="學生資料異常")

    # 1. 安全邊界驗證：確保該 enrollment_id 確實屬於目前操作的學生，防止越權橫向滲透
    enrollment = StudentRepository.get_enrollment_by_id_and_student(db, payload.enrollment_id, profile.id)
    if not enrollment:
        raise HTTPException(status_code=403, detail="您沒有操作該修課班級的權限。")
    if enrollment.status != "active":
        raise HTTPException(status_code=400, detail="該修課關係目前非有效狀態，無法發起申請。")

    # 2. 針對請假與調課，驗證目標 session 存在性
    session = None
    if payload.request_type in ("leave", "reschedule"):
        if not payload.session_id:
            raise HTTPException(status_code=400, detail="請假或調課必須指定目標課堂 ID (session_id)。")
        session = StudentRepository.get_session_by_id(db, payload.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="找不到欲調整的目標課堂。")
        if session.status != "scheduled":
            raise HTTPException(status_code=400, detail="該堂課已結束或已取消，無法再發起異動。")

    # 3. 呼叫帶有去重防連點機制的商業處理層
    change_request = StudentRepository.create_change_request(
        db=db,
        user_id=current_user.id,
        enrollment=enrollment,
        session=session,
        request_type=payload.request_type,
        proposed_payload=payload.proposed_payload,
        reason=payload.reason,
        client_request_id=payload.client_request_id
    )
    
    return change_request


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
    """【錄音送出】學生確認上傳並發起音訊分析與 LLM 評分任務（自帶去重防護機制）"""
    profile = StudentRepository.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="學生資料異常")

    # 1. 越權防線（Horizontal Privilege Escalation Protection）
    # 強制驗證該 assignment_id 確實隸屬於當前學生名下的修課班級，防止惡意橫向破解跨學生作業提交
    assignment = StudentRepository.get_assignment_by_id_and_student(db, assignment_id, profile.id)
    if not assignment:
        raise HTTPException(status_code=403, detail="您沒有權限提交此份作業。")
    if assignment.status != "published":
        raise HTTPException(status_code=400, detail="此作業目前未開放繳交。")

    # 2. 建立提交紀錄並在同筆交易內預留空的 Evaluation 快照（防假 0 分）
    submission = StudentRepository.create_submission(
        db=db,
        assignment_id=assignment.id,
        student_id=profile.id,
        audio_file_id=payload.audio_file_id,
        duration_seconds=payload.duration_seconds,
        client_submission_id=payload.client_submission_id
    )

    # 3. 這裡成功持久化 pending 狀態，後續會由 background worker 異步撈走處理
    return submission


@router.get("/assignments/{assignment_id}/submissions", response_model=list[SubmissionHistoryResponse])
def get_my_submission_history(
    assignment_id: uuid.UUID,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """【評分與歷史】學生針對特定作業，查看自己多次錄音提交的 AI 分數（音高／節奏）與 LLM 導師回饋"""
    profile = StudentRepository.get_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="學生資料異常")

    # 強制檢查作業歸屬
    assignment = StudentRepository.get_assignment_by_id_and_student(db, assignment_id, profile.id)
    if not assignment:
        raise HTTPException(status_code=403, detail="您沒有查看此份作業歷史紀錄的權限。")

    return StudentRepository.get_submission_history_with_evaluation(db, assignment.id, profile.id)
