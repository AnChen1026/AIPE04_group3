"""Rebuild changed public course embeddings with a local/approved model gateway.

Defaults to dry-run. Writes require --apply and matching --confirm-database.
"""

import argparse
import os

from sqlalchemy import select
from sqlalchemy.engine import make_url

from backend.core.config import get_database_url
from backend.core.database import SessionLocal
from backend.models.course_embedding import CourseEmbedding
from backend.models.student import Course
from backend.services.ai_semantic import course_hash, course_text, embed_texts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-database", default="")
    args = parser.parse_args()
    version = os.environ.get("AI_COURSE_EMBEDDING_VERSION", "")
    if not version:
        parser.error("AI_COURSE_EMBEDDING_VERSION is required")
    target = make_url(get_database_url()).database
    if args.apply and (not target or args.confirm_database != target):
        parser.error("--confirm-database must match the target database name")
    with SessionLocal() as db:
        courses = db.scalars(
            select(Course).where(Course.status == "published").order_by(Course.id)
        ).all()
        existing = {row.course_id: row for row in db.scalars(select(CourseEmbedding))}
        todo = [
            c
            for c in courses
            if c.id not in existing
            or existing[c.id].model_version != version
            or existing[c.id].content_hash != course_hash(c)
        ]
        if not args.apply:
            print(f"published={len(courses)} pending={len(todo)} mode=dry-run")
            return
        for start in range(0, len(todo), 4):
            batch = todo[start : start + 4]
            vectors = embed_texts([course_text(course) for course in batch])
            if vectors is None:
                db.rollback()
                raise RuntimeError("embedding_gateway_unavailable")
            for course, vector in zip(batch, vectors, strict=True):
                row = existing.get(course.id)
                if row is None:
                    row = CourseEmbedding(course_id=course.id)
                    db.add(row)
                row.model_version = version
                row.content_hash = course_hash(course)
                row.embedding = vector
            # Short transactions let a failed or interrupted run resume safely.
            db.commit()
            if (start + len(batch)) % 40 == 0 or start + len(batch) == len(todo):
                print(f"indexed={start + len(batch)}/{len(todo)}", flush=True)
        print(f"published={len(courses)} indexed={len(todo)} mode=apply")


if __name__ == "__main__":
    main()
