from types import SimpleNamespace

from scripts.ops import restore


def test_restore_only_uses_network_isolated_disposable_target(monkeypatch, tmp_path):
    calls = []
    manifest = {
        "source_id": "one",
        "database": {
            "row_counts": {"courses": 426},
            "references": [],
            "revision": "016_storage_cleanup",
        },
        "objects": [],
    }
    monkeypatch.setattr(restore, "verify_bundle", lambda p: manifest)

    def execute(args, timeout=180):
        calls.append(args)
        if "psql" in args:
            statement = args[-1]
            if "json_build_object" in statement:
                return '{"courses":426}'
            if "json_agg" in statement:
                return "[]"
            return '"016_storage_cleanup"'
        return ""

    monkeypatch.setattr(restore, "execute", execute)
    monkeypatch.setattr(
        restore.subprocess, "run", lambda *a, **kw: SimpleNamespace(returncode=0)
    )
    config = SimpleNamespace(
        source_id="one", docker="/docker", state_dir=tmp_path / "state"
    )
    result = restore.restore_check(config, tmp_path)
    run = calls[0]
    assert run[run.index("--network") + 1] == "none"
    assert "-p" not in run and "--publish" not in run
    assert not any("DATABASE_URL" in arg or "PGPASSWORD" in arg for arg in run)
    assert result["tables_verified"] == 1
