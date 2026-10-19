"""上傳檔案的位置。一律放在專案根目錄的 uploads/，不跟著啟動時所在的資料夾跑。"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_ROOT = PROJECT_ROOT / "uploads"
MATERIAL_UPLOAD_DIR = UPLOAD_ROOT / "materials"
PRACTICE_UPLOAD_DIR = UPLOAD_ROOT / "practice"
MIDI_UPLOAD_DIR = UPLOAD_ROOT / "midi"
MATERIAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def stored_path(path: Path) -> str:
    """寫進資料庫的路徑：相對於專案根目錄，例如 uploads/practice/...。"""
    return path.relative_to(PROJECT_ROOT).as_posix()


def resolve_stored_path(value: str) -> Path:
    """把資料庫裡的路徑轉回實際檔案位置。舊資料存的是相對路徑，也用專案根目錄去找。"""
    path = Path(value)
    return path if path.is_absolute() else PROJECT_ROOT / path
