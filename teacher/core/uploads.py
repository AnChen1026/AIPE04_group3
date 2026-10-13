from pathlib import Path
UPLOAD_ROOT = Path("uploads")
MATERIAL_UPLOAD_DIR = UPLOAD_ROOT / "materials"
REFERENCE_UPLOAD_DIR = UPLOAD_ROOT / "references"
MATERIAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
REFERENCE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
