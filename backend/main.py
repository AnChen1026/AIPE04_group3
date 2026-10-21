from fastapi import FastAPI
import uvicorn
import sys
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

# Ensure the project root is importable when this module is started from the
# backend directory, so imports such as ``backend.core.config`` resolve.
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.config import get_session_secret_key
from core.database import SessionLocal
from routers.admin import router as admin_router
from routers.health import router as health_router
from routers.images import router as images_router
from routers.public_courses import router as public_courses_router
from routers.recommendations import router as recommendations_router
from routers.auth import router as auth_router
from routers.student import router as student_router
from routers.chat_ws import router as chat_ws_router
from routers.teacher_chat import router as teacher_chat_router
from routers.teacher_courses import router as teacher_courses_router
from routers.teacher_inquiries import router as teacher_inquiries_router
from routers.teacher_lessons import router as teacher_lessons_router
from routers.teacher_materials import router as teacher_materials_router
from routers.teacher_practice import router as teacher_practice_router
from routers.teacher_profile import router as teacher_profile_router
from routers.teacher_quizzes import router as teacher_quizzes_router
from routers.teacher_students import router as teacher_students_router
from services.admin import seed_admin_if_needed
from services import teacher_sync  # 註冊老師資料同步，讓老師登入時補上 teacher_profiles

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=get_session_secret_key(),
    same_site="lax",
    https_only=False,
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(public_courses_router)
app.include_router(images_router)
app.include_router(recommendations_router)
app.include_router(admin_router)
app.include_router(student_router)
app.include_router(chat_ws_router)
# 老師端 API
for teacher_module in (
    teacher_profile_router,
    teacher_students_router,
    teacher_chat_router,
    teacher_courses_router,
    teacher_inquiries_router,
    teacher_lessons_router,
    teacher_materials_router,
    teacher_practice_router,
    teacher_quizzes_router,
):
    app.include_router(teacher_module)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",       # 這是 Docker 前端 Nginx 的網址
        "http://127.0.0.1",
        "http://localhost:5173",  # 本機 Vite 開發環境（可選）
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """本機測試：若 .env 有管理員帳密就建立 admin 帳號。資料表一律用 alembic upgrade head 建立。"""
    db = SessionLocal()
    try:
        seed_admin_if_needed(db)
    finally:
        db.close()


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
