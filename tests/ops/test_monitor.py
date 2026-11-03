from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from scripts.ops.monitor import inspect, update_alerts

NOW = datetime(2026, 10, 28, tzinfo=UTC)


def report(level):
    return {
        "source_id": "one",
        "conditions": {"database_capacity": {"level": level, "details": {}}},
    }


def test_dedup_escalation_unknown_and_recovery():
    state, events = update_alerts(report("warning"), {}, NOW)
    assert len(events) == 1
    state, events = update_alerts(report("warning"), state, NOW + timedelta(hours=1))
    assert events == []
    state, events = update_alerts(report("critical"), state, NOW + timedelta(hours=2))
    assert events[0]["level"] == "critical"
    state, events = update_alerts(report("unknown"), state, NOW + timedelta(hours=3))
    assert state["active"]["database_capacity"]["level"] == "critical" and events == []
    state, events = update_alerts(report("ok"), state, NOW + timedelta(hours=4))
    assert events[0]["level"] == "resolved" and state["active"] == {}


def test_probe_failure_does_not_report_zero_capacity_or_leak_secret(tmp_path):
    settings = SimpleNamespace(
        source_id="one",
        backup_root=tmp_path / "none",
        state_dir=tmp_path / "state",
        values={
            "database_budget_bytes": 100,
            "storage_budget_bytes": 100,
            "warning_pct": 70,
            "critical_pct": 85,
            "max_backup_age_hours": 36,
        },
    )

    def offline(_):
        raise RuntimeError("postgres://password-secret@host")

    probes = {
        "database": offline,
        "storage": lambda s: {"bytes": 80},
        "health": lambda s: {"status": "ok"},
    }
    result = inspect(settings, NOW, probes)
    assert result["conditions"]["database_capacity"]["level"] == "unknown"
    assert result["conditions"]["storage_capacity"]["level"] == "warning"
    assert result["conditions"]["database_probe"]["level"] == "critical"
    assert "password-secret" not in str(result)
