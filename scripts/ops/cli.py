"""python -m scripts.ops.cli --config .env.ops.json COMMAND"""

import argparse
import json
import os
from pathlib import Path

from scripts.ops.common import (
    OpsError,
    atomic_json,
    error_details,
    locked,
    read_json,
    utcnow,
)
from scripts.ops.config import Settings


def run_monitor(settings):
    from scripts.ops.monitor import inspect, update_alerts
    from scripts.ops.notify import flush_outbox

    with locked(settings.state_dir / "monitor.lock"):
        report = inspect(settings)
        state = read_json(settings.state_dir / "alert-state.json", {})
        new_state, events = update_alerts(
            report, state, utcnow(), settings.values["alert_cooldown_hours"]
        )
        pending = read_json(settings.state_dir / "notification-outbox.json", [])
        # At least once: persist new delivery work before advancing dedup state.
        atomic_json(settings.state_dir / "notification-outbox.json", pending + events)
        atomic_json(settings.state_dir / "alert-state.json", new_state)
        report["active_alerts"] = new_state["active"]
        report["new_events"] = events
        report["notification"] = flush_outbox(settings)
        atomic_json(settings.state_dir / "latest-report.json", report)
        return report


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path(".env.ops.json"))
    parser.add_argument(
        "command",
        choices=[
            "backup",
            "verify",
            "restore-check",
            "monitor",
            "notify-test",
            "notify-flush",
            "install-schedule",
            "uninstall-schedule",
        ],
    )
    parser.add_argument("--bundle", type=Path)
    args = parser.parse_args()
    settings = None
    try:
        settings = Settings.load(args.config)
        if args.command == "backup":
            from scripts.ops.backup import backup

            path = backup(settings)
            result = {"status": "success", "bundle": str(path)}
        elif args.command in {"verify", "restore-check"}:
            from scripts.ops.backup import managed, verify_bundle

            bundles = managed(settings)
            bundle = args.bundle or (bundles[0][0] if bundles else None)
            if bundle is None:
                raise OpsError("no_backup_available")
            if args.command == "verify":
                manifest = verify_bundle(bundle)
                result = {
                    "status": "success",
                    "objects": len(manifest["objects"]),
                    "bundle": str(bundle),
                }
            else:
                from scripts.ops.restore import restore_check

                result = restore_check(settings, bundle)
        elif args.command == "monitor":
            result = run_monitor(settings)
        elif args.command == "notify-test":
            from scripts.ops.notify import deliver

            deliver(
                settings,
                [
                    {
                        "level": "test",
                        "code": "gmail_connection_test",
                        "observed_at": utcnow().isoformat(),
                        "details": {
                            "message": "這是使用者要求的連線測試，不是事故告警。"
                        },
                    }
                ],
            )
            result = {"status": "success", "message": "Gmail test delivered"}
        elif args.command == "notify-flush":
            from scripts.ops.notify import flush_outbox

            with locked(settings.state_dir / "monitor.lock"):
                result = flush_outbox(settings)
        else:
            from scripts.ops.schedule import install, uninstall

            result = (
                install(settings, args.config)
                if args.command == "install-schedule"
                else uninstall(settings)
            )
        if args.command == "monitor":
            print(
                json.dumps(
                    {
                        "status": "alert" if result["active_alerts"] else "healthy",
                        "active_alerts": list(result["active_alerts"]),
                        "notification": result["notification"],
                    },
                    ensure_ascii=False,
                )
            )
            return (
                1
                if result["active_alerts"]
                or result["notification"]["status"]
                in {"failed", "authorization_required"}
                else 0
            )
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except Exception as error:  # noqa: BLE001 - never print raw upstream errors/secrets
        if isinstance(error, OpsError) and str(error) == "already_running":
            print(json.dumps({"status": "skipped", "reason": "already_running"}))
            return 0
        result = {
            "status": "failed",
            "operation": args.command,
            "observed_at": utcnow().isoformat(),
            "error": error_details(error),
        }
        if settings:
            if args.command == "backup":
                atomic_json(
                    settings.state_dir / "backup-status.json",
                    result
                    | {
                        "source_id": settings.source_id,
                        "finished_at": result["observed_at"],
                    },
                )
            atomic_json(settings.state_dir / (args.command + "-failure.json"), result)
        print(json.dumps(result, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
