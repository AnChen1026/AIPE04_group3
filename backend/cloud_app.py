"""Same-origin production entry point; local backend.main remains API-only."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.staticfiles import StaticFiles

from backend.core.config import read_env_value
from backend.main import app as api


class VueFiles(StaticFiles):
    async def get_response(self, path, scope):
        try:
            response = await super().get_response(path, scope)
            if response.status_code != 404:
                return response
        except StarletteHTTPException as error:
            if error.status_code != 404:
                raise
        # Never turn unknown API requests/assets into a successful HTML response.
        first = "" if path in {"", ".", "/"} else path.split("/")[0]
        allowed = {
            "",
            "courses",
            "login",
            "signup",
            "forgot-password",
            "student",
            "teacher",
            "admin",
            "search",
        }
        target = (Path(self.directory) / path).resolve()
        if first not in allowed or not target.is_relative_to(
            Path(self.directory).resolve()
        ):
            raise HTTPException(404)
        return FileResponse(
            Path(self.directory) / "index.html", headers={"Cache-Control": "no-cache"}
        )


def create_app(frontend_dir: Path | None = None):
    @asynccontextmanager
    async def lifespan(app):
        async with api.router.lifespan_context(api):
            yield

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.mount("/backend", api)
    directory = frontend_dir or Path(
        read_env_value("FRONTEND_DIST") or "/app/frontend/dist"
    )
    app.mount("/", VueFiles(directory=directory, check_dir=False))
    return app


app = create_app()
