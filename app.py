from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from backend.core.config import get_session_secret_key
from backend.core.database import SessionLocal, engine
from backend.models.base import Base
from backend.routers.admin import router as admin_router
from backend.routers.auth import router as auth_router
from backend.routers.student import router as student_router
from backend.routers.student_views import router as student_views_router
from backend.routers.teacher_bindings import router as teacher_bindings_router
from backend.routers.teacher_chat import router as teacher_chat_router
from backend.routers.teacher_courses import router as teacher_courses_router
from backend.routers.teacher_dashboard import router as teacher_dashboard_router
from backend.routers.teacher_inquiries import router as teacher_inquiries_router
from backend.routers.teacher_learning import router as teacher_learning_router
from backend.routers.teacher_lessons import router as teacher_lessons_router
from backend.routers.teacher_materials import router as teacher_materials_router
from backend.routers.teacher_practice import router as teacher_practice_router
from backend.routers.teacher_profile import router as teacher_profile_router
from backend.routers.teacher_quizzes import router as teacher_quizzes_router
from backend.routers.teacher_students import router as teacher_students_router
from backend.services.admin import seed_admin_if_needed
from backend.services import teacher_sync  # 註冊老師資料同步，讓老師登入時補上 teacher_profiles

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=get_session_secret_key(),
    same_site="lax",
    https_only=False,
)

app.include_router(auth_router)
app.include_router(admin_router)
app.include_router(student_router)
app.include_router(student_views_router)
app.include_router(teacher_learning_router)
# 老師端左側選單在 /test。先掛 auth 的首頁，老師端的 GET / 不會蓋掉現有首頁。
for teacher_module in (
    teacher_dashboard_router,
    teacher_profile_router,
    teacher_students_router,
    teacher_bindings_router,
    teacher_courses_router,
    teacher_inquiries_router,
    teacher_lessons_router,
    teacher_materials_router,
    teacher_practice_router,
    teacher_chat_router,
    teacher_quizzes_router,
):
    app.include_router(teacher_module)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """本機測試：若 .env 有管理員帳密就建立 admin 帳號。"""
    # 只補老師端還沒有的表，不會改掉學生端已經用 Alembic 建好的表。
    Base.metadata.create_all(bind=engine)
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
