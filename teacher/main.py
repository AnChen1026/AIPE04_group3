import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from backend.core.database import engine
from backend.models.base import Base
from backend.models.user import User  # Register shared user table
from backend.routers.auth import router as auth_router
from teacher import models  # Register all teacher tables on shared Base
from teacher.services import teacher_sync  # Register User -> Teacher profile event
from teacher.routers import base, teacher, students, bindings, courses, inquiries, lessons, materials, practice, chat, quizzes

app = FastAPI(title="鋼琴教學管理與課程推廣平台 - 教師端", version="1.0.0")
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET_KEY", "change-this-secret-key-in-production"), same_site="lax", https_only=False)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.include_router(auth_router)
for module in (base, teacher, students, bindings, courses, inquiries, lessons, materials, practice, chat, quizzes):
    app.include_router(module.router)

# Preserve original development behavior. Production should use Alembic migrations.
Base.metadata.create_all(bind=engine)
