"""Import the fictional AICourseFinder catalog into local/staging only.
Stable UUIDs and insert-only behavior preserve existing data on reruns.
"""

import argparse
import json
import uuid
from pathlib import Path

from sqlalchemy import insert, select

from backend.models.student import Course
from backend.models.teacher import TeacherDB
from backend.models.teacher_application import TeacherApplication
from backend.models.user import User
from backend.services.course import check_course_fields

namespace = uuid.uuid5(uuid.NAMESPACE_URL, "aipe04/local/aicourse-demo-import/v1")


def identity(kind, key):
    return uuid.uuid5(namespace, kind + ":" + key)


levels = {
    "intro": "入門",
    "beginner": "初階",
    "intermediate": "中階",
    "advanced": "進階",
}
slots = {
    "weekday_day": "平日白天",
    "weekday_evening": "平日晚上",
    "weekend_morning": "週末上午",
    "weekend_afternoon": "週末下午",
    "weekend_evening": "週末晚上",
}
goals = {
    "classical": "古典",
    "pop": "流行",
    "accompaniment": "伴奏",
    "exam": "檢定",
    "interest": "興趣",
}


def import_demo(db, source):
    if any(not r.get("is_demo") for r in source["teachers"] + source["courses"]):
        raise ValueError("Only fictional demo records are allowed")
    for group in ("teachers", "courses"):
        ids = [r["id"] for r in source[group]]
        if len(set(ids)) != len(ids):
            raise ValueError("Duplicate source IDs")
    teachers = {t["id"]: t for t in source["teachers"]}
    for c in source["courses"]:
        key = c["public_teacher_id"] or c["teacher_id"]
        if key not in teachers:
            teachers[key] = {
                "id": key,
                "display_name": c["teacher_name"],
                "biography": c["teaching_profile"],
                "teaching_style": "",
                "specialties": c["goals"],
                "years_experience": None,
            }
    created = {"users": 0, "profiles": 0, "applications": 0, "courses": 0}
    for key, t in teachers.items():
        uid = identity("teacher", key)
        existing = db.get(User, uid)
        if existing is not None and (
            existing.email != f"aicourse-{uid.hex}@example.invalid"
            or existing.name != t["display_name"]
            or existing.role != "teacher"
            or existing.password_hash is not None
        ):
            raise ValueError("Demo user ID collision; nothing should be committed")
        if existing is None:
            db.execute(
                insert(User).values(
                    id=uid,
                    email=f"aicourse-{uid.hex}@example.invalid",
                    name=t["display_name"],
                    role="teacher",
                    is_active=True,
                    auth_provider="password",
                    password_hash=None,
                )
            )
            created["users"] += 1
    db.flush()
    for key, t in teachers.items():
        uid = identity("teacher", key)
        if db.scalar(select(TeacherDB).where(TeacherDB.user_id == uid)) is None:
            db.add(
                TeacherDB(
                    id=identity("profile", key),
                    user_id=uid,
                    name=t["display_name"],
                    gender="未提供",
                    seniority=t["years_experience"],
                    expertise="、".join(goals.get(g, g) for g in t["specialties"]),
                    short_intros=("[虛構測試資料] " + t["biography"])[:200],
                    teaching_method=t["teaching_style"][:255],
                    status="active",
                )
            )
            created["profiles"] += 1
        if (
            db.scalar(
                select(TeacherApplication).where(TeacherApplication.user_id == uid)
            )
            is None
        ):
            db.add(
                TeacherApplication(
                    id=identity("application", key),
                    user_id=uid,
                    teaching_subjects="鋼琴",
                    teaching_experience="舊 AICourseFinder 虛構測試資料，非真實資格。",
                    bio=t["biography"],
                    status="approved",
                    review_note="本機假資料搬移，非真實老師審核。",
                )
            )
            created["applications"] += 1
    db.flush()
    for c in source["courses"]:
        if c["instrument"] != "piano" or not c["is_demo"]:
            raise ValueError("Unexpected non-demo or non-piano record")
        cid = identity("course", c["id"])
        existing = db.get(Course, cid)
        if existing is not None:
            if (
                existing.teacher_id
                != identity("teacher", c["public_teacher_id"] or c["teacher_id"])
                or existing.title != c["title"]
                or not (existing.description or "").startswith(
                    "[虛構測試資料・AICourseFinder]"
                )
            ):
                raise ValueError(
                    "Demo course ID collision; nothing should be committed"
                )
            continue
        key = c["public_teacher_id"] or c["teacher_id"]
        mode = {"online": "online", "onsite": "in_person", "hybrid": None}[
            c["delivery_mode"]
        ]
        desc = "\n".join(
            filter(
                None,
                [
                    "[虛構測試資料・AICourseFinder]",
                    c["description"],
                    c["teaching_profile"],
                    f"對象：{ {'adult': '成人', 'child': '兒童'}.get(c['audience'], c['audience']) }；每堂 {c['duration_minutes']} 分鐘。",
                    "上課方式：線上／實體皆可。"
                    if c["delivery_mode"] == "hybrid"
                    else "",
                    f"原示範工作室：{c['studio_name']}；來源課程：{c['id']}。",
                    "原型有效期限："
                    + c["valid_until"]
                    + "（僅保留來源紀錄，本機測試持續顯示）。",
                ],
            )
        )
        fields = check_course_fields(
            {
                "title": c["title"],
                "level": levels[c["level"]],
                "style": "、".join(goals[g] for g in c["goals"]),
                "delivery_mode": mode,
                "region": c["area"],
                "price_per_lesson": c["price_amount"],
                "time_slots": "、".join(slots[s] for s in c["slots"]),
                "status": c["status"],
                "description": desc,
            }
        )
        db.add(Course(id=cid, teacher_id=identity("teacher", key), **fields))
        created["courses"] += 1
    db.flush()
    return created


def main():
    from sqlalchemy.engine import make_url

    from backend.core.config import get_database_url, read_env_value
    from backend.core.database import SessionLocal

    parser = argparse.ArgumentParser(
        description="Insert fictional catalog; dry-run by default"
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm-database")
    args = parser.parse_args()
    env = read_env_value("APP_ENV") or "local"
    url = make_url(get_database_url())
    if env not in {"local", "staging"}:
        parser.error("Demo imports are limited to local/staging")
    if url.host not in {"localhost", "127.0.0.1", "postgres"} and env != "staging":
        parser.error("Remote imports require APP_ENV=staging")
    if args.apply and args.confirm_database != url.database:
        parser.error("--apply requires --confirm-database matching target database")
    source = json.loads((Path(__file__).parent / "data/aicourse-demo.json").read_text())
    with SessionLocal() as db:
        try:
            # Serialize repeated imports without affecting normal website writes.
            from sqlalchemy import text

            db.execute(text("SELECT pg_advisory_xact_lock(426226)"))
            counts = import_demo(db, source)
            if args.apply:
                db.commit()
            else:
                db.rollback()
        except Exception:
            db.rollback()
            raise
    print(
        json.dumps(
            {"mode": "apply" if args.apply else "dry-run", "created": counts},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
