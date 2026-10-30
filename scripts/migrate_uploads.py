"""Copy referenced local uploads to private Storage, verify, then update keys.

Run against the TARGET staging database with access to the source upload tree.
Existing local files are never deleted. Copied objects are content addressed,
so a rolled-back run can safely reuse verified copies on the next attempt.
"""

import argparse
import hashlib
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.engine import make_url

from backend.core import storage, uploads
from backend.core.config import get_database_url, read_env_value
from backend.core.database import SessionLocal
from backend.models.teacher_application import TeacherApplication
from backend.services.storage_files import FILE_FIELDS as FIELDS


def plan(db, source_root):
    root = (source_root / "uploads").resolve()
    references = []
    for model, field in FIELDS:
        for row in db.scalars(select(model).where(getattr(model, field).is_not(None))):
            value = getattr(row, field)
            if value.startswith("storage://"):
                storage._parts(value)
                continue
            if model is TeacherApplication and not value.startswith(("uploads/", "/")):
                value = "uploads/" + value
            if Path(value).is_absolute():
                # Explicitly supplied source root is the only permitted absolute tree.
                path = Path(value).resolve()
            else:
                path = (source_root / value).resolve()
            if not path.is_relative_to(root) or not path.is_file():
                raise ValueError(
                    f"Missing or unsafe local file in {model.__tablename__}.{field}; no DB changes"
                )
            references.append((row, field, path))
    return references


def migrate(db, references, source_root=None):
    source_root = source_root or uploads.PROJECT_ROOT
    mapping = {}
    for row, field, path in references:
        if path not in mapping:
            content = path.read_bytes()
            digest = hashlib.sha256(content).hexdigest()
            # Classify by DB field, not by a user-provided filename.
            category = (
                "images"
                if field in {"image_path", "photo_path"}
                else "teacher_proofs"
                if field == "proof_file_path"
                else "materials"
            )
            bucket = (
                "profile-images"
                if category == "images"
                else "teacher-proofs"
                if category == "teacher_proofs"
                else "teaching-files"
            )
            source_id = hashlib.sha256(
                path.relative_to(source_root / "uploads").as_posix().encode()
            ).hexdigest()
            key = f"{category}/migrated/{source_id}-{digest}{path.suffix.lower()}"
            value = f"storage://{bucket}/{key}"
            try:
                with storage.local_file(value) as downloaded:
                    if hashlib.sha256(downloaded.read_bytes()).hexdigest() != digest:
                        raise ValueError(
                            "Existing content-addressed object does not match"
                        )
            except HTTPException as error:
                if error.status_code != 404:
                    raise
                actual = storage.save_file(
                    uploads.PROJECT_ROOT / "uploads" / key, content
                )
                if actual != value:
                    raise ValueError("Migration requires supabase backend")
                with storage.local_file(value) as downloaded:
                    if hashlib.sha256(downloaded.read_bytes()).hexdigest() != digest:
                        raise ValueError("Uploaded object hash mismatch")
            mapping[path] = value
        setattr(row, field, mapping[path])
    db.flush()
    return len(mapping)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=uploads.PROJECT_ROOT)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-database")
    args = parser.parse_args()
    if (
        read_env_value("APP_ENV") != "staging"
        or read_env_value("STORAGE_BACKEND") != "supabase"
    ):
        parser.error("Use staging DB with STORAGE_BACKEND=supabase")
    if args.apply and args.confirm_database != make_url(get_database_url()).database:
        parser.error("--apply requires --confirm-database matching target")
    with SessionLocal() as db:
        try:
            references = plan(db, args.source_root.resolve())
            unique = len({path for _, _, path in references})
            if args.apply:
                migrate(db, references, args.source_root.resolve())
                db.commit()
            else:
                db.rollback()
            print(
                {
                    "mode": "apply" if args.apply else "dry-run",
                    "references": len(references),
                    "files": unique,
                }
            )
        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    main()
