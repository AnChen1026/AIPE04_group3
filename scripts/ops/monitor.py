"""Independent readonly probes and stateful alert transitions."""

from datetime import datetime, timedelta

import httpx
import psycopg

from scripts.ops.backup import managed
from scripts.ops.common import error_details, read_json, utcnow
from scripts.ops.storage import Storage


def probe_database(settings):
    with psycopg.connect(**settings.pg, autocommit=True) as db:
        db.execute("BEGIN READ ONLY")
        try:
            size = db.execute("SELECT pg_database_size(current_database())").fetchone()[
                0
            ]
            cleanup = db.execute(
                "SELECT count(*) FROM public.storage_cleanup_jobs"
            ).fetchone()[0]
            stuck = db.execute(
                "SELECT count(*) FROM public.practice_recordings WHERE status IN ('pending','processing') AND submitted_at < now()-interval '15 minutes'"
            ).fetchone()[0]
            total, failed = db.execute(
                "SELECT count(*),count(*) FILTER (WHERE status='failed') FROM public.practice_recordings WHERE submitted_at>=now()-interval '24 hours'"
            ).fetchone()
            return {
                "bytes": size,
                "cleanup_jobs": cleanup,
                "stuck_analysis": stuck,
                "recent_recordings": total,
                "failed_recordings": failed,
            }
        finally:
            db.execute("ROLLBACK")


def probe_storage(settings):
    storage = Storage(settings)
    try:
        size = count = 0
        names = []
        for bucket in storage.buckets():
            names.append(bucket["id"])
            for item in storage.inventory(bucket["id"]).values():
                actual = (item.get("metadata") or {}).get("size")
                if not isinstance(actual, int) or actual < 0:
                    raise ValueError("missing_size_metadata")
                size += actual
                count += 1
        return {"bytes": size, "objects": count, "buckets": names}
    finally:
        storage.close()


def probe_health(settings):
    response = httpx.get(
        settings.values["site_url"].rstrip("/") + "/health",
        timeout=90,
        follow_redirects=False,
    )
    response.raise_for_status()
    return {
        "status": "ok" if response.json() == {"status": "ok"} else "unexpected_response"
    }


def inspect(settings, now=None, probes=None):
    now = now or utcnow()
    probes = probes or {
        "database": probe_database,
        "storage": probe_storage,
        "health": probe_health,
    }
    observations = {}
    conditions = {}

    def condition(code, level, **details):
        conditions[code] = {"level": level, "details": details}

    for name, probe in probes.items():
        try:
            observations[name] = {"status": "ok", "value": probe(settings)}
            condition(name + "_probe", "ok")
        except Exception as error:  # noqa: BLE001 - one failing probe must not suppress the others
            observations[name] = {"status": "unknown", "error": error_details(error)}
            condition(name + "_probe", "critical", error=error_details(error))
    for name, budget_name in [
        ("database", "database_budget_bytes"),
        ("storage", "storage_budget_bytes"),
    ]:
        observation = observations.get(name, {"status": "unknown"})
        if observation["status"] != "ok":
            condition(name + "_capacity", "unknown")
            continue
        used = observation["value"]["bytes"]
        budget = settings.values[budget_name]
        percent = 100 * used / budget
        level = (
            "critical"
            if percent >= settings.values["critical_pct"]
            else "warning"
            if percent >= settings.values["warning_pct"]
            else "ok"
        )
        condition(
            name + "_capacity",
            level,
            bytes=used,
            budget_bytes=budget,
            percent=round(percent, 2),
        )
    database = observations.get("database", {})
    if database.get("status") == "ok":
        values = database["value"]
        condition(
            "file_cleanup_backlog",
            "warning" if values["cleanup_jobs"] else "ok",
            count=values["cleanup_jobs"],
        )
        condition(
            "analysis_stuck",
            "warning" if values["stuck_analysis"] else "ok",
            count=values["stuck_analysis"],
        )
        total, failed = values["recent_recordings"], values["failed_recordings"]
        rate = 100 * failed / total if total else 0
        level = (
            "critical"
            if total >= 5 and rate >= 50
            else "warning"
            if total >= 5 and rate >= 20
            else "ok"
        )
        condition(
            "analysis_failures",
            level,
            total=total,
            failed=failed,
            percent=round(rate, 2),
        )
    else:
        for code in ("file_cleanup_backlog", "analysis_stuck", "analysis_failures"):
            condition(code, "unknown")
    health = observations.get("health", {})
    if health.get("status") == "ok":
        condition(
            "website_response",
            "ok" if health["value"]["status"] == "ok" else "critical",
        )
    else:
        condition("website_response", "unknown")
    try:
        bundles = managed(settings)
        if bundles:
            newest, manifest = bundles[0]
            finished = datetime.fromisoformat(manifest["completed_at"])
            age = (now - finished).total_seconds() / 3600
            condition(
                "backup_age",
                "critical"
                if age > 2 * settings.values["max_backup_age_hours"]
                else "warning"
                if age > settings.values["max_backup_age_hours"]
                else "ok",
                hours=round(age, 2),
                bundle=newest.name,
            )
        else:
            condition("backup_age", "critical", reason="no_successful_backup")
        last = read_json(settings.state_dir / "backup-status.json", {})
        condition(
            "backup_last_run",
            "critical"
            if last.get("source_id") == settings.source_id
            and last.get("status") == "failed"
            else "ok",
        )
        condition("backup_probe", "ok")
    except Exception as error:  # noqa: BLE001 - preserve unknown backup state
        observations["backup"] = {"status": "unknown", "error": error_details(error)}
        condition("backup_probe", "critical", error=error_details(error))
        condition("backup_age", "unknown")
        condition("backup_last_run", "unknown")
    return {
        "source_id": settings.source_id,
        "observed_at": now.isoformat(),
        "observations": observations,
        "conditions": conditions,
    }


def update_alerts(report, state, now, cooldown_hours=24):
    active = {key: dict(value) for key, value in state.get("active", {}).items()}
    events = []
    rank = {"ok": 0, "warning": 1, "critical": 2}
    for code, condition in report["conditions"].items():
        level = condition["level"]
        old = active.get(code)
        if level == "unknown":
            continue  # Unknown is never evidence of recovery.
        if level == "ok":
            if old:
                events.append(
                    {
                        "code": code,
                        "level": "resolved",
                        "observed_at": now.isoformat(),
                        "details": condition["details"],
                    }
                )
                active.pop(code)
            continue
        last = datetime.fromisoformat(old["last_emitted"]) if old else None
        emit = (
            old is None
            or rank[level] > rank[old["level"]]
            or now - last >= timedelta(hours=cooldown_hours)
        )
        active[code] = {
            "level": level,
            "first_seen": old["first_seen"] if old else now.isoformat(),
            "last_seen": now.isoformat(),
            "last_emitted": now.isoformat() if emit else old["last_emitted"],
        }
        if emit:
            events.append(
                {
                    "code": code,
                    "level": level,
                    "observed_at": now.isoformat(),
                    "details": condition["details"],
                }
            )
    return {"version": 1, "source_id": report["source_id"], "active": active}, events
