"""老師照片與課程圖片。只收真的 JPG、PNG、WebP，最大 5 MB。"""

import uuid

from fastapi import status

from backend.core.uploads import UPLOAD_ROOT, stored_path
from backend.services.student import StudentBusinessError

MAX_IMAGE_BYTES = 5 * 1024 * 1024
IMAGE_DIR = UPLOAD_ROOT / "images"

# 檔頭判斷實際格式，不只看副檔名
SIGNATURES = (
    (b"\xff\xd8\xff", ".jpg"),
    (b"\x89PNG\r\n\x1a\n", ".png"),
)


def image_suffix(content: bytes) -> str | None:
    for signature, suffix in SIGNATURES:
        if content.startswith(signature):
            return suffix
    if content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        return ".webp"
    return None


def save_image(content: bytes, folder: str) -> str:
    """存檔後回傳寫進資料庫的路徑。舊圖不刪，換圖時資料庫只改指向新檔。"""
    if len(content) == 0:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "圖片是空的。")
    if len(content) > MAX_IMAGE_BYTES:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "圖片最大 5 MB。")
    suffix = image_suffix(content)
    if suffix is None:
        raise StudentBusinessError(status.HTTP_400_BAD_REQUEST, "請上傳 JPG、PNG 或 WebP 圖片。")

    target = IMAGE_DIR / folder
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{uuid.uuid4()}{suffix}"
    path.write_bytes(content)
    return stored_path(path)
