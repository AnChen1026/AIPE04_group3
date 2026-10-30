from types import SimpleNamespace

from scripts.ops.postgres import Postgres


def test_dump_credentials_never_appear_in_process_arguments(tmp_path, monkeypatch):
    calls = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        if kwargs.get("capture_output") or isinstance(kwargs.get("stdout"), int):
            return SimpleNamespace(returncode=0, stdout=b"dump table list")
        kwargs["stdout"].write(b"PGDMP-test")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("scripts.ops.postgres.subprocess.run", run)
    config = SimpleNamespace(
        docker="/docker",
        pg={
            "password": "unit-test-secret",
            "sslrootcert": "/ca.crt",
            "host": "db.example",
            "port": 5432,
            "user": "app",
            "dbname": "postgres",
        },
    )
    Postgres(config).dump(tmp_path / "database.dump", "snapshot-id")
    assert "unit-test-secret" not in str([args for args, _ in calls])
    assert calls[0][1]["env"]["PGPASSWORD"] == "unit-test-secret"
    assert "--snapshot=snapshot-id" in calls[0][0]
