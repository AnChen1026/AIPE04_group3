from pathlib import Path
UPLOAD_ROOT = Path("uploads")
MATERIAL_UPLOAD_DIR = UPLOAD_ROOT / "materials"
MATERIAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
