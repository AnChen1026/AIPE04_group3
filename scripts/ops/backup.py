"""Atomic, independently verifiable bundles with conservative retention."""

import os
import re
import shutil
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from scripts.ops.common import (
    OpsError,
    atomic_json,
    locked,
    private_dir,
    read_json,
    sha256,
    utcnow,
)
from scripts.ops.config import BUCKETS
from scripts.ops.postgres import Postgres
from scripts.ops.storage import Storage, fingerprint, safe_key

MANAGER = "aipe04-backup-v1"
NAME = re.compile(r"^\d{8}T\d{6}Z-[a-f0-9]{8}$")


def member(root, relative):
    safe_key(relative)
    path = Path(root) / relative
    if path.is_symlink() or not path.resolve().is_relative_to(Path(root).resolve()):
        raise OpsError("unsafe_backup_member")
    return path


def managed(settings):
    if not settings.backup_root.exists():
        return []
    result = []
    for path in settings.backup_root.iterdir():
        if path.is_symlink() or not path.is_dir() or not NAME.fullmatch(path.name):
            continue
        try:
            data = read_json(path / "manifest.json")
        except (ValueError, OSError):
            continue
        if (
            isinstance(data, dict)
            and data.get("managed_by") == MANAGER
            and data.get("version") == 1
            and data.get("source_id") == settings.source_id
            and data.get("status") == "complete"
            and isinstance(data.get("completed_at"), str)
        ):
            result.append((path, data))
    return sorted(
        result, key=lambda pair: (pair[1]["completed_at"], pair[0].name), reverse=True
    )


def verify_bundle(root):
    root = Path(root)
    data = read_json(root / "manifest.json")
    if (
        not isinstance(data, dict)
        or data.get("managed_by") != MANAGER
        or data.get("version") != 1
        or data.get("status") != "complete"
    ):
        raise OpsError("invalid_backup_manifest")
    entries = [data["database"]] + data["objects"]
    refs = set()
    seen = set()
    for entry in entries:
        path = member(root, entry["path"])
        if entry["path"] in seen:
            raise OpsError("duplicate_backup_member")
        seen.add(entry["path"])
        if (
            not path.is_file()
            or path.stat().st_size != entry["bytes"]
            or sha256(path) != entry["sha256"]
        ):
            raise OpsError("backup_checksum_mismatch")
        if "bucket" in entry:
            safe_key(entry["bucket"])
            safe_key(entry["key"])
            if entry["path"] != "objects/" + entry["bucket"] + "/" + entry["key"]:
                raise OpsError("invalid_object_path")
            refs.add("storage://" + entry["bucket"] + "/" + entry["key"])
    if not set(data["database"]["references"]).issubset(refs):
        raise OpsError("backup_missing_referenced_object")
    return data


def prune(settings):
    removed = []
    for path, _ in managed(settings)[settings.values["keep"] :]:
        shutil.rmtree(path)
        removed.append(path.name)
    return removed


def backup(settings, postgres=None, storage=None):
    postgres = postgres or Postgres(settings)
    storage = storage or Storage(settings)
    private_dir(settings.backup_root)
    with locked(settings.state_dir / "backup.lock"):
        name = utcnow().strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]
        partial = private_dir(settings.backup_root / (".partial-" + name))
        started = utcnow().isoformat()
        previous = managed(settings)
        prior_root, prior_data = previous[0] if previous else (None, {"objects": []})
        cache = {(item["bucket"], item["key"]): item for item in prior_data["objects"]}
        transfer = 0
        try:
            with postgres.snapshot() as (snapshot, metadata):
                target = partial / "database.dump"
                postgres.dump(target, snapshot)
                database = metadata | {
                    "path": "database.dump",
                    "bytes": target.stat().st_size,
                    "sha256": sha256(target),
                }
                transfer += database["bytes"]
            buckets = {bucket["id"]: bucket for bucket in storage.buckets()}
            objects = []
            required = {bucket: set() for bucket in BUCKETS}
            for ref in database["references"]:
                url = urlsplit(ref)
                if (
                    url.scheme != "storage"
                    or url.netloc not in BUCKETS
                    or url.query
                    or url.fragment
                    or not url.path.startswith("/")
                ):
                    raise OpsError("unsupported_database_file_reference")
                required[url.netloc].add(safe_key(url.path[1:]))
            for bucket in BUCKETS:
                if bucket not in buckets or buckets[bucket].get("public") is not False:
                    raise OpsError("required_private_bucket_missing")
                inventory = storage.inventory(bucket)
                for key in sorted(set(inventory) | required[bucket]):
                    safe_key(key)
                    path = "objects/" + bucket + "/" + key
                    target = member(partial, path)
                    private_dir(target.parent)
                    version = fingerprint(inventory.get(key, {}))
                    old = cache.get((bucket, key))
                    copied = False
                    if (
                        old
                        and version is not None
                        and old.get("remote_version") == version
                    ):
                        source = member(prior_root, old["path"])
                        if (
                            source.is_file()
                            and source.stat().st_size == old["bytes"]
                            and sha256(source) == old["sha256"]
                        ):
                            try:
                                os.link(source, target)
                            except OSError:
                                shutil.copyfile(source, target)
                            target.chmod(0o600)
                            info = {"bytes": old["bytes"], "sha256": old["sha256"]}
                            copied = True
                    if not copied:
                        info = storage.download(bucket, key, target)
                        transfer += info["bytes"]
                    expected_size = (inventory.get(key, {}).get("metadata") or {}).get(
                        "size"
                    )
                    if expected_size is not None and info["bytes"] != expected_size:
                        raise OpsError("object_size_changed_during_backup")
                    objects.append(
                        {
                            "bucket": bucket,
                            "key": key,
                            "path": path,
                            "remote_version": version,
                            **info,
                        }
                    )
            manifest = {
                "managed_by": MANAGER,
                "version": 1,
                "status": "complete",
                "source_id": settings.source_id,
                "started_at": started,
                "completed_at": utcnow().isoformat(),
                "database": database,
                "objects": objects,
                "transfer_bytes": transfer,
            }
            atomic_json(partial / "manifest.json", manifest)
            verify_bundle(partial)
            final = settings.backup_root / name
            partial.rename(final)
            # Publish success before retention; a pruning error never invalidates the backup.
            atomic_json(
                settings.state_dir / "backup-status.json",
                {
                    "status": "success",
                    "source_id": settings.source_id,
                    "finished_at": manifest["completed_at"],
                    "bundle": name,
                    "transfer_bytes": transfer,
                },
            )
            try:
                prune(settings)
            except OSError:
                atomic_json(
                    settings.state_dir / "retention-status.json",
                    {"status": "failed", "finished_at": utcnow().isoformat()},
                )
            return final
        except BaseException:
            shutil.rmtree(
                partial, ignore_errors=True
            )  # Only this invocation's unpublished directory.
            raise
        finally:
            storage.close()
