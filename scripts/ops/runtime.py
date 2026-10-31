"""Install versioned maintenance code outside the working Git checkout."""

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

from scripts.ops.common import OpsError, private_dir


def base():
    return Path.home() / "Library/Application Support/AIPE04Ops"


def prepare():
    source = Path(__file__).resolve().parent
    files = sorted([*source.glob("*.py"), source / "requirements.txt"])
    version = hashlib.sha256(
        b"".join(p.name.encode() + p.read_bytes() for p in files)
    ).hexdigest()[:16]
    root = private_dir(base())
    version_root = root / "versions" / version
    if not version_root.exists():
        package = private_dir(version_root / "scripts/ops")
        (version_root / "scripts/__init__.py").write_text("")
        for file in files:
            shutil.copyfile(file, package / file.name)
    environment = root / "venv"
    python = environment / "bin/python"
    if not python.exists():
        result = subprocess.run(
            [sys._base_executable, "-m", "venv", str(environment)],
            capture_output=True,
            check=False,
            timeout=120,
        )
        if result.returncode:
            raise OpsError("ops_environment_creation_failed")
    requirements = source / "requirements.txt"
    checksum = hashlib.sha256(requirements.read_bytes()).hexdigest()
    stamp = root / "requirements.sha256"
    if not stamp.exists() or stamp.read_text() != checksum:
        result = subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "-r",
                str(requirements),
            ],
            capture_output=True,
            check=False,
            timeout=600,
        )
        if result.returncode:
            raise OpsError("ops_dependency_install_failed")
        stamp.write_text(checksum)
    return python, version_root
