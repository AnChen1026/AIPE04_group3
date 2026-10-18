"""首頁推薦 API 端口（F02）。網址與資料格式先定好，實作由負責首頁推薦的組員完成。

規格見 docs/智慧課程推薦系統流程設計.md 與 PRD F02：
- 訪客不用登入，用自己的話描述想學的內容。
- 整次對談最多追問兩題；問了還是不清楚就保留「不確定」。
- 只推薦已發布的鋼琴課；未知條件不視為符合；沒有符合時直說。

目前三個端口都回 501，前端可以先依這裡的格式串接。
"""

import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/recommendations", tags=["首頁推薦"])

NOT_READY = "首頁推薦還在開發中。"


class RecommendationMessage(BaseModel):
    """訪客說的話：第一次的描述，或回答追問。"""

    message: str


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


@router.post("", response_model=RecommendationResponse)
def start(data: RecommendationMessage):
    """訪客第一次描述需求。body：RecommendationMessage。回傳追問或推薦結果。"""
    raise HTTPException(status_code=501, detail=NOT_READY)


@router.post("/{session_id}/answer", response_model=RecommendationResponse)
def answer(session_id: uuid.UUID, data: RecommendationMessage):
    """回答追問。body：RecommendationMessage。整次最多兩題，回答完就給結果。"""
    raise HTTPException(status_code=501, detail=NOT_READY)


@router.get("/{session_id}", response_model=RecommendationResponse)
def read(session_id: uuid.UUID):
    """讀取這次推薦目前的狀態。只有開始它的同一個瀏覽器讀得到。"""
    raise HTTPException(status_code=501, detail=NOT_READY)
