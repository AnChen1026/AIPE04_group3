from fastapi import FastAPI
import uvicorn
from starlette.middleware.sessions import SessionMiddleware

from backend.core.config import get_session_secret_key
from backend.core.database import SessionLocal
from backend.routers.admin import router as admin_router
from backend.routers.auth import router as auth_router
from backend.services.admin import seed_admin_if_needed

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=get_session_secret_key(),
    same_site="lax",
    https_only=False,
)

app.include_router(auth_router)
app.include_router(admin_router)


@app.on_event("startup")
def on_startup():
    """本機測試：若 .env 有管理員帳密就建立 admin 帳號。"""
    db = SessionLocal()
    try:
        seed_admin_if_needed(db)
    finally:
        db.close()


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
