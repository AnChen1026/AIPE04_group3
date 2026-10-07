# API 路由。放各功能的 FastAPI endpoint。
# 接收前端傳來的請求，並回傳結果。

from backend.routers.auth import router as auth_router
from backend.routers.admin import router as admin_router
from backend.routers.student import router as student_router

__all__ = ["auth_router", "admin_router", "student_router"]
