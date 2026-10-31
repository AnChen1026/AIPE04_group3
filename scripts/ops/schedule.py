"""Current-user launchd jobs with code isolated from Git branch changes."""

import os
import plistlib
import subprocess
import sys
from pathlib import Path

from scripts.ops import runtime as runtime_install
from scripts.ops.common import OpsError, private_dir, utcnow

LABELS = {"backup": "com.aipe04.group3.backup", "monitor": "com.aipe04.group3.monitor"}


def plist(settings, config_path, command, python=None, runtime=None):
    root = Path(runtime) if runtime else Path(__file__).resolve().parents[2]
    log = settings.state_dir / ("launchd-" + command + ".log")
    value = {
        "Label": LABELS[command],
        "ProgramArguments": [
            str(python or sys.executable),
            "-m",
            "scripts.ops.cli",
            "--config",
            str(Path(config_path).resolve()),
            command,
        ],
        "WorkingDirectory": str(root),
        "EnvironmentVariables": {
            "PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin",
            "PYTHONUNBUFFERED": "1",
        },
        "RunAtLoad": False,
        "ProcessType": "Background",
        "StandardOutPath": str(log),
        "StandardErrorPath": str(log),
    }
    if command == "backup":
        value["StartCalendarInterval"] = {"Hour": 9, "Minute": 0}
    else:
        value["StartInterval"] = 3600
    return value


def loaded(domain, label):
    result = subprocess.run(
        ["/bin/launchctl", "print", domain + "/" + label],
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        return True
    if b"Could not find service" in result.stderr:
        return False
    raise OpsError("launch_agent_status_unknown")


def owned(value, config_path=None):
    args = value.get("ProgramArguments", [])
    cwd = Path(value.get("WorkingDirectory", "/")).resolve()
    repo = Path(__file__).resolve().parents[2]
    if args[1:3] != ["-m", "scripts.ops.cli"] or not (
        cwd == repo or cwd.is_relative_to(runtime_install.base() / "versions")
    ):
        return False
    if config_path is not None:
        if "--config" not in args:
            return False
        index = args.index("--config") + 1
        if index >= len(args) or args[index] != str(Path(config_path).resolve()):
            return False
    return True


def stop(domain, label, path):
    if loaded(domain, label):
        subprocess.run(
            ["/bin/launchctl", "bootout", domain, str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        if loaded(domain, label):
            raise OpsError("launch_agent_still_loaded")


def install(settings, config_path):
    if sys.platform != "darwin":
        raise OpsError("launchd_requires_macos")
    if not os.path.realpath("/etc/localtime").endswith("/Asia/Taipei"):
        raise OpsError("mac_timezone_must_be_Asia_Taipei")
    directory = Path.home() / "Library/LaunchAgents"
    directory.mkdir(parents=True, exist_ok=True)
    domain = "gui/" + str(os.getuid())
    for label in LABELS.values():
        path = directory / (label + ".plist")
        if path.exists() and not owned(plistlib.loads(path.read_bytes()), config_path):
            raise OpsError("existing_launch_agent_conflict")
        if not path.exists() and loaded(domain, label):
            raise OpsError("existing_launch_agent_conflict")
    python, code = runtime_install.prepare()
    installed = []
    for command, label in LABELS.items():
        target = directory / (label + ".plist")
        value = plist(settings, config_path, command, python, code)
        if target.exists() and plistlib.loads(target.read_bytes()) != value:
            copies = private_dir(settings.state_dir / "schedule-backups")
            (
                copies / (utcnow().strftime("%Y%m%dT%H%M%SZ-") + label + ".plist")
            ).write_bytes(target.read_bytes())
            stop(domain, label, target)
        target.write_bytes(plistlib.dumps(value))
        target.chmod(0o600)
        log = settings.state_dir / ("launchd-" + command + ".log")
        log.touch(mode=0o600, exist_ok=True)
        log.chmod(0o600)
        if not loaded(domain, label):
            result = subprocess.run(
                ["/bin/launchctl", "bootstrap", domain, str(target)],
                capture_output=True,
                check=False,
            )
            if result.returncode or not loaded(domain, label):
                raise OpsError("launch_agent_bootstrap_failed")
        installed.append(label)
    return {
        "status": "installed",
        "labels": installed,
        "timezone": "Asia/Taipei",
        "backup": "09:00 daily",
        "monitor": "every 3600 seconds",
        "runtime": str(code),
    }


def uninstall(settings):
    domain = "gui/" + str(os.getuid())
    for label in LABELS.values():
        path = Path.home() / "Library/LaunchAgents" / (label + ".plist")
        if not path.exists():
            if loaded(domain, label):
                raise OpsError("launch_agent_definition_missing")
            continue
        if not owned(plistlib.loads(path.read_bytes())):
            raise OpsError("launch_agent_not_owned")
        stop(domain, label, path)
        path.unlink()
    return {"status": "uninstalled", "backups_preserved": True}
