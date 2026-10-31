"""Private file storage. Authorization stays in the calling service/router.

Local paths remain compatible with existing uploads. Cloud references contain
only an allowlisted bucket and key, never a user-supplied URL or credentials.
"""

import mimetypes
import tempfile
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from urllib.parse import quote, urlsplit

import httpx
from fastapi import HTTPException
from fastapi.responses import FileResponse

from backend.core import uploads
from backend.core.config import read_env_value

BUCKETS = {"teaching-files", "profile-images", "teacher-proofs"}
client_factory = httpx.Client


def _parts(value: str):
    if value.startswith("storage://"):
        parsed = urlsplit(value)
        if parsed.netloc not in BUCKETS or parsed.query or parsed.fragment:
            raise ValueError("Invalid storage reference")
        key = parsed.path.lstrip("/")
        _check_key(key)
        return parsed.netloc, key
    return None


def _check_key(key: str):
    if (
        not key
        or "\\" in key
        or "%" in key
        or ":" in key
        or "\x00" in key
        or key.startswith("/")
    ):
        raise ValueError("Invalid storage key")
    if any(p in ("", ".", "..") for p in key.split("/")):
        raise ValueError("Invalid storage key")


def _local_path(value: str) -> Path:
    root = (uploads.PROJECT_ROOT / "uploads").resolve()
    path = Path(value)
    path = path if path.is_absolute() else uploads.PROJECT_ROOT / path
    path = path.resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError("File must be inside uploads")
    return path


def _connection():
    url = (read_env_value("SUPABASE_URL") or "").rstrip("/")
    key = read_env_value("SUPABASE_SECRET_KEY")
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.path
        or parsed.query
        or parsed.fragment
        or parsed.username
    ):
        raise RuntimeError("SUPABASE_URL must be an HTTPS origin")
    if not key:
        raise RuntimeError("SUPABASE_SECRET_KEY is required")
    # New secret keys use apikey; legacy service_role JWTs also support Bearer.
    headers = {"apikey": key}
    if key.count(".") == 2:
        headers["Authorization"] = "Bearer " + key
    return url + "/storage/v1", headers


def _object_url(bucket, key):
    return "/object/" + bucket + "/" + quote(key, safe="/")


def save_file(path: Path, content: bytes, content_type: str | None = None) -> str:
    path = _local_path(str(path))
    backend = read_env_value("STORAGE_BACKEND") or "local"
    if backend == "local":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return uploads.stored_path(path)
    if backend != "supabase":
        raise RuntimeError("Unknown STORAGE_BACKEND")
    key = path.relative_to(uploads.PROJECT_ROOT / "uploads").as_posix()
    _check_key(key)
    bucket = (
        "profile-images"
        if key.startswith("images/")
        else "teacher-proofs"
        if key.startswith("teacher_proofs/")
        else "teaching-files"
    )
    base, headers = _connection()
    headers["Content-Type"] = (
        content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    )
    headers["x-upsert"] = "false"
    try:
        with client_factory(timeout=60) as client:
            response = client.post(
                base + _object_url(bucket, key), headers=headers, content=content
            )
            response.raise_for_status()
    except httpx.HTTPError:
        raise HTTPException(503, "檔案儲存暫時無法使用，請稍後再試。") from None
    return f"storage://{bucket}/{key}"


@contextmanager
def local_file(value: str):
    parts = _parts(value)
    if parts is None:
        path = _local_path(value)
        if not path.is_file():
            raise HTTPException(404, "找不到檔案。")
        yield path
        return
    bucket, key = parts
    base, headers = _connection()
    with tempfile.TemporaryDirectory(prefix="aipe04-download-") as folder:
        path = Path(folder) / PurePosixPath(key).name
        try:
            with (
                client_factory(timeout=60) as client,
                client.stream(
                    "GET",
                    base
                    + "/object/authenticated/"
                    + bucket
                    + "/"
                    + quote(key, safe="/"),
                    headers=headers,
                ) as response,
            ):
                if response.status_code == 404:
                    raise HTTPException(404, "找不到檔案。")
                if response.status_code == 400:
                    response.read()
                    try:
                        missing = str(response.json().get("statusCode")) == "404"
                    except ValueError:
                        missing = False
                    if missing:
                        raise HTTPException(404, "找不到檔案。")
                response.raise_for_status()
                with path.open("wb") as output:
                    for chunk in response.iter_bytes(65536):
                        output.write(chunk)
        except httpx.HTTPError:
            raise HTTPException(503, "檔案下載暫時無法使用，請稍後再試。") from None
        yield path


class StoredFileResponse(FileResponse):
    def __init__(self, path, context, **kwargs):
        super().__init__(path, **kwargs)
        self.storage_context = context

    async def __call__(self, scope, receive, send):
        try:
            await super().__call__(scope, receive, send)
        finally:
            self.storage_context.__exit__(None, None, None)


def file_response(value: str, **kwargs):
    context = local_file(value)
    path = context.__enter__()
    headers = {"Cache-Control": "no-store", **kwargs.pop("headers", {})}
    try:
        return StoredFileResponse(path, context, headers=headers, **kwargs)
    except BaseException:
        context.__exit__(None, None, None)
        raise


def delete_file(value: str):
    parts = _parts(value)
    if parts is None:
        _local_path(value).unlink(missing_ok=True)
        return
    bucket, key = parts
    base, headers = _connection()
    with client_factory(timeout=30) as client:
        response = client.request(
            "DELETE",
            base + "/object/" + bucket,
            headers=headers,
            json={"prefixes": [key]},
        )
        response.raise_for_status()


def cleanup_files(values):
    """Best effort deletion; persist failed keys for an explicit retry command."""
    for value in filter(None, values):
        try:
            delete_file(value)
        except Exception:  # noqa: BLE001 - persist/retry failures from either storage adapter
            from backend.core.database import SessionLocal
            from backend.models.storage_cleanup import StorageCleanup

            with SessionLocal.begin() as db:
                db.add(StorageCleanup(storage_key=value))
