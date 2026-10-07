import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.dependencies import get_current_student
from backend.models.user import User

from backend.schemas.student import InquiryCreate, InquiryResponse, SubmissionAsyncResponse
import backend.repositories.student as student_repo
import backend.services.student as student_service

router = APIRouter(
    prefix="/api/student",
    tags=["學生工作區"],
)

def heavy_ai_audio_task(submission_id: uuid.UUID):
    """【AI核心異步任務】背景執行：音訊事件辨識 -> MIDI 對齊 -> 規則評分 -> LLM 生成。"""
    # 這裡將對接未來待指派的 AI/音訊辨識服務，不阻塞主執行緒
    print(f"背景非阻塞任務啟動：正在處理提交案 {submission_id} 的音訊辨識與評分流程...")
    pass


@router.post("/inquiries", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def create_inquiry(
    payload: InquiryCreate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_student)
):
    """學生發起站內洽詢"""
    # 1. 拿登入者的 user_id 去找 student_profile.id
    profile = student_repo.get_student_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="找不到您的學生設定檔。")
    
    # 2. 呼叫服務層處理交易
    try:
        inquiry = student_service.process_student_inquiry(db, student_id=profile.id, payload=payload)
        # 轉換為前端需要的 Response
        return InquiryResponse(
            id=inquiry.id,
            course_id=inquiry.course_id,
            student_id=inquiry.student_id,
            message=inquiry.message,
            reply_text=inquiry.teacher_response,
            status=inquiry.status,
            created_at=inquiry.created_at
        )
    except student_service.DuplicateRequestError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/assignments/{assignment_id}/submissions", response_model=SubmissionAsyncResponse, status_code=status.HTTP_202_ACCEPTED)
async def submit_assignment(
    assignment_id: uuid.UUID,
    background_tasks: BackgroundTasks, # FastAPI 內建背景任務
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_student)
):
    """
    【核心功能】學生上傳錄音作業。
    行為：快速保存紀錄、回傳 202 處理中狀態、並以非阻塞方式將音訊分析丟到背景執行。
    """
    profile = student_repo.get_student_profile_by_user_id(db, current_user.id)
    if not profile:
        raise HTTPException(status_code=404, detail="找不到您的學生設定檔。")

    # 實作防線：此處應調用作業查詢，確保該作業確實是指派給該 profile.id 的
    
    # 生成本次提交的唯一識別碼 (ID 共用原則)
    submission_id = uuid.uuid4()
    
    # TODO: 這裡實作將 audio_file 儲存到 files 表與實體儲存區 (files 表)
    # new_file = save_to_files_table(db, audio_file)
    # new_submission = create_submission_record(db, id=submission_id, status="processing")

    # 【核心規格：快速回饋】將沉重的音訊辨識與 LLM 流程塞入背景任務，立馬回傳 202 釋放前端
    background_tasks.add_task(heavy_ai_audio_task, submission_id)

    return SubmissionAsyncResponse(
        submission_id=submission_id,
        assignment_id=assignment_id,
        status="processing",
        message="音訊錄音上傳成功，後台已啟動快速辨識評分流程，請稍後刷新查看。"
    )
