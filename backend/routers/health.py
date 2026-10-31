import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.core.database import get_db

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """給 Docker healthcheck 與監測工具呼叫。資料庫連不上就回 503，讓外部知道服務不正常。"""
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        logger.exception("健康檢查：資料庫連不上")
        return JSONResponse(status_code=503, content={"status": "error", "database": "error"})
    return {"status": "ok", "database": "ok"}
