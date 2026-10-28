"""Private artifacts, locking and secret-safe failures."""

import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path


class OpsError(Exception):
    """A stable public error code, never an upstream exception or credential."""


def utcnow():
    return datetime.now(UTC)


def private_dir(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.chmod(0o700)
    return path


def atomic_json(path, value):
    path = Path(path)
    private_dir(path.parent)
    fd, name = tempfile.mkstemp(prefix=".write-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as output:
            json.dump(value, output, ensure_ascii=False, indent=2)
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return default


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


@contextmanager
def locked(path):
    private_dir(Path(path).parent)
    fd = os.open(path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise OpsError("already_running") from None
        yield
    finally:
        os.close(fd)


def error_details(error):
    result = {"type": type(error).__name__}
    if isinstance(error, OpsError):
        result["code"] = str(error)
    response = getattr(error, "response", None)
    if response is not None:
        result["http_status"] = response.status_code
    return result
