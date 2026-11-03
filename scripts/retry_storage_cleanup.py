"""Run with python -m scripts.retry_storage_cleanup after migrations."""

from sqlalchemy import select

from backend.core.database import SessionLocal
from backend.core.storage import delete_file
from backend.models.storage_cleanup import StorageCleanup
from backend.services.storage_files import is_file_referenced


def main():
    removed = failed = 0
    with SessionLocal() as db:
        # Serialize concurrent maintenance commands; each key is safe to delete twice.
        jobs = db.scalars(
            select(StorageCleanup)
            .order_by(StorageCleanup.created_at)
            .limit(100)
            .with_for_update(skip_locked=True)
        ).all()
        for job in jobs:
            if is_file_referenced(db, job.storage_key):
                db.delete(job)  # It was reused; this is no longer an orphan.
                continue
            try:
                delete_file(job.storage_key)
            except Exception:  # noqa: BLE001 - persist/retry failures from either storage adapter
                job.attempts += 1
                failed += 1
            else:
                db.delete(job)
                removed += 1
        db.commit()
    print({"removed": removed, "retry_pending": failed})


if __name__ == "__main__":
    main()
