"""首頁推薦 API（F02）。

規格見 docs/智慧課程推薦系統流程設計.md 與 PRD F02：
- 訪客不用登入，用自己的話描述想學的內容。
- 整次對談最多追問兩題；問了還是不清楚就保留「不確定」。
- 只推薦已發布的鋼琴課；未知條件不視為符合；沒有符合時直說。

"""

import hashlib
import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.database import get_db
from backend.models.student import RecommendationItem as StoredRecommendationItem
from backend.models.student import RecommendationSession
from backend.services.ai_model_planner import AIPlannerUnclear, AIPlannerUnavailable, is_configured
from backend.services.ai_rate_limit import RateLimiter
from backend.services.recommendation import (
    RecommendationConflict,
    RecommendationNotFound,
    answer_recommendation,
    read_recommendation,
    recommendation_items,
    start_recommendation,
)

router = APIRouter(prefix="/api/recommendations", tags=["首頁推薦"])
ai_limiter = RateLimiter()


def _limit_ai(owner):
    if is_configured() and not ai_limiter.allow(owner):
        raise HTTPException(status_code=429, detail="找課請求太頻繁，請稍後再試。", headers={"Retry-After": "60"})


class RecommendationMessage(BaseModel):
    """訪客說的話：第一次的描述，或回答追問。"""

    message: str = Field(min_length=1, max_length=1000)

    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("請輸入找課需求。")
        return value.strip()


class RecommendedCourse(BaseModel):
    id: str
    title: str
    teacher_name: str
    level: str | None = None
    style: str | None = None
    delivery_mode: str | None = None
    region: str | None = None
    price_per_lesson: int | None = None
    time_slots: str | None = None
    description: str | None = None
    image_url: str | None = None
    teacher_photo_url: str | None = None


class RecommendationItem(BaseModel):
    course: RecommendedCourse
    matched: list[str]
    """符合訪客條件的項目，例如「流行」「入門」。"""
    unknown: list[str]
    """課程沒填、無法確認的項目，例如「價格（老師未填）」。"""
    reason: str


class RecommendationResponse(BaseModel):
    session_id: uuid.UUID
    status: str
    """asking：還在追問；done：已給結果；unsupported：不是鋼琴。"""
    question: str | None
    """status 為 asking 時要問訪客的題目。"""
    questions_asked: int
    """已經問了幾題，最多 2。"""
    criteria: dict
    """整理出的條件：目標風格、找課程度、上課方式、地區、預算、時段。不知道的保持 null。"""
    message: str
    results: list[RecommendationItem]


def _owner_hash(request: Request) -> str:
    owner = request.session.get("recommendation_owner")
    if not owner:
        owner = secrets.token_urlsafe(32)
        request.session["recommendation_owner"] = owner
    return hashlib.sha256(owner.encode()).hexdigest()


def _response(db: Session, row: RecommendationSession) -> RecommendationResponse:
    items = recommendation_items(db, row)
    expected_count = db.scalar(select(func.count()).select_from(StoredRecommendationItem).where(StoredRecommendationItem.session_id == row.id)) or 0
    message = row.result_message
    if len(items) < expected_count:
        message = "部分課程已更新或下架，請重新搜尋。"
    return RecommendationResponse(
        session_id=row.id,
        status=row.status,
        question=row.question,
        questions_asked=row.question_count,
        criteria={**{key: value for key, value in row.criteria.items() if not key.startswith("_")}, **({"learning_goal": row.criteria["_semantic_query"]} if row.criteria.get("_semantic_query") else {})},
        message=message,
        results=items,
    )


@router.post("", response_model=RecommendationResponse)
def start(data: RecommendationMessage, request: Request, db: Session = Depends(get_db)):
    """訪客第一次描述需求。body：RecommendationMessage。回傳追問或推薦結果。"""
    try:
        owner = _owner_hash(request)
        _limit_ai(owner)
        return _response(db, start_recommendation(db, owner, data.message))
    except AIPlannerUnavailable:
        raise HTTPException(status_code=503, detail="AI 找課暫時無法使用，請稍後再試。") from None
    except AIPlannerUnclear:
        db.rollback()
        raise HTTPException(status_code=422, detail="我還無法確認你的條件，請換個方式說明。") from None


@router.post("/{session_id}/answer", response_model=RecommendationResponse)
def answer(
    session_id: uuid.UUID,
    data: RecommendationMessage,
    request: Request,
    db: Session = Depends(get_db),
):
    """回答追問。body：RecommendationMessage。整次最多兩題，回答完就給結果。"""
    try:
        owner = _owner_hash(request)
        _limit_ai(owner)
        row = answer_recommendation(db, owner, session_id, data.message)
    except RecommendationNotFound:
        raise HTTPException(status_code=404, detail="找不到這次找課對談，請重新開始。") from None
    except RecommendationConflict:
        raise HTTPException(status_code=409, detail="上一則訊息仍在處理，請稍後重試。") from None
    except AIPlannerUnavailable:
        raise HTTPException(status_code=503, detail="AI 找課暫時無法使用，請稍後再試。") from None
    except AIPlannerUnclear:
        db.rollback()
        raise HTTPException(status_code=422, detail="我還無法確認你的條件，請換個方式說明。") from None
    return _response(db, row)


@router.get("/{session_id}", response_model=RecommendationResponse)
def read(session_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    """讀取這次推薦目前的狀態。只有開始它的同一個瀏覽器讀得到。"""
    try:
        row = read_recommendation(db, _owner_hash(request), session_id)
    except RecommendationNotFound:
        raise HTTPException(status_code=404, detail="找不到這次找課對談，請重新開始。") from None
    return _response(db, row)
