from fastapi import FastAPI
import uvicorn
from starlette.middleware.sessions import SessionMiddleware

from backend.core.config import get_session_secret_key
from backend.routers.auth import router as auth_router

app = FastAPI()

app.add_middleware(
    SessionMiddleware,
    secret_key=get_session_secret_key(),
    same_site="lax",
    https_only=False,
)

app.include_router(auth_router)

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )