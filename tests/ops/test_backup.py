import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

from scripts.ops.backup import backup, verify_bundle
from scripts.ops.common import OpsError


@pytest.fixture
def settings(tmp_path):
    return SimpleNamespace(
        backup_root=tmp_path / "backups",
        state_dir=tmp_path / "state",
        source_id="test-source",
        values={"keep": 2},
    )


class Database:
    @contextmanager
    def snapshot(self):
        yield (
            "snapshot",
            {
                "row_counts": {"courses": 426},
                "references": ["storage://teaching-files/midi/song.mid"],
                "revision": "016_storage_cleanup",
            },
        )

    def dump(self, target, snapshot):
        target.write_bytes(b"PGDMP-test")


class Objects:
    def buckets(self):
        return [
            {"id": name, "public": False}
            for name in ("teaching-files", "profile-images", "teacher-proofs")
        ]

    def inventory(self, bucket):
        return (
            {
                "midi/song.mid": {
                    "id": "one",
                    "updated_at": "2026-10-28T00:00:00Z",
                    "metadata": {"eTag": "v1", "size": 4},
                }
            }
            if bucket == "teaching-files"
            else {}
        )

    def download(self, bucket, key, target):
        import hashlib

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"MThd")
        return {"bytes": 4, "sha256": hashlib.sha256(b"MThd").hexdigest()}

    def close(self):
        pass


def test_atomic_complete_backup_and_hash_verification(settings):
    result = backup(settings, postgres=Database(), storage=Objects())
    data = verify_bundle(result)
    assert data["status"] == "complete"
    assert data["database"]["row_counts"]["courses"] == 426
    assert data["objects"][0]["bytes"] == 4
    (result / "objects/teaching-files/midi/song.mid").write_bytes(b"bad!")
    with pytest.raises(OpsError, match="checksum"):
        verify_bundle(result)


def test_failed_copy_never_prunes_success(settings):
    first = backup(settings, postgres=Database(), storage=Objects())

    class Offline(Objects):
        def download(self, *args):
            raise RuntimeError("contains-secret-password")

        def inventory(self, bucket):
            result = super().inventory(bucket)
            for item in result.values():
                item["metadata"]["eTag"] = "changed"
            return result

    with pytest.raises(RuntimeError):
        backup(settings, postgres=Database(), storage=Offline())
    assert first.exists()
    assert (
        len([p for p in settings.backup_root.iterdir() if not p.name.startswith(".")])
        == 1
    )


def test_incremental_reuse_checks_version_and_checksum(settings):
    backup(settings, postgres=Database(), storage=Objects())

    class Unchanged(Objects):
        def download(self, *args):
            raise AssertionError("unchanged object should be reused")

    second = backup(settings, postgres=Database(), storage=Unchanged())
    assert verify_bundle(second)["transfer_bytes"] == len(b"PGDMP-test")


def test_retention_only_removes_managed_same_source(settings):
    manual = settings.backup_root / "manual"
    manual.mkdir(parents=True)
    (manual / "important").write_text("keep")
    foreign = settings.backup_root / "20200101T000000Z-aaaaaaaa"
    foreign.mkdir()
    (foreign / "manifest.json").write_text(
        json.dumps(
            {
                "managed_by": "aipe04-backup-v1",
                "source_id": "other",
                "status": "complete",
            }
        )
    )
    for _ in range(3):
        backup(settings, postgres=Database(), storage=Objects())
    assert manual.exists() and foreign.exists()
    managed = [
        p
        for p in settings.backup_root.iterdir()
        if p.is_dir()
        and (p / "manifest.json").exists()
        and json.loads((p / "manifest.json").read_text()).get("source_id")
        == "test-source"
    ]
    assert len(managed) == 2


def test_missing_snapshot_reference_fails_without_publishing(settings):
    class Missing(Objects):
        def inventory(self, bucket):
            return {}

        def download(self, *args):
            raise FileNotFoundError("removed during backup")

    with pytest.raises(FileNotFoundError):
        backup(settings, postgres=Database(), storage=Missing())
    assert not any(p.name.startswith("2026") for p in settings.backup_root.iterdir())


def test_same_size_changed_remote_etag_is_downloaded(settings):
    backup(settings, postgres=Database(), storage=Objects())
    seen = []

    class Changed(Objects):
        def inventory(self, bucket):
            result = super().inventory(bucket)
            for item in result.values():
                item["metadata"]["eTag"] = "different-content"
            return result

        def download(self, bucket, key, target):
            import hashlib

            seen.append(key)
            target.write_bytes(b"next")
            return {"bytes": 4, "sha256": hashlib.sha256(b"next").hexdigest()}

    result = backup(settings, postgres=Database(), storage=Changed())
    assert seen == ["midi/song.mid"]
    assert (result / "objects/teaching-files/midi/song.mid").read_bytes() == b"next"


def test_incomplete_remote_metadata_always_downloads(settings):
    backup(settings, postgres=Database(), storage=Objects())
    seen = []

    class Unversioned(Objects):
        def inventory(self, bucket):
            result = super().inventory(bucket)
            for item in result.values():
                item.pop("updated_at")
            return result

        def download(self, *args):
            seen.append(True)
            return super().download(*args)

    backup(settings, postgres=Database(), storage=Unversioned())
    assert seen == [True]
