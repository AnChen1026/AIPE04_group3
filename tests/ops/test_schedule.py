from pathlib import Path
from types import SimpleNamespace

from scripts.ops.schedule import plist


def test_schedule_contains_paths_but_no_credentials(tmp_path):
    settings = SimpleNamespace(state_dir=tmp_path / "state")
    backup = plist(settings, tmp_path / ".env.ops.json", "backup", python="/python")
    monitor = plist(settings, tmp_path / ".env.ops.json", "monitor", python="/python")
    assert backup["StartCalendarInterval"] == {"Hour": 9, "Minute": 0}
    assert monitor["StartInterval"] == 3600
    assert (
        "password" not in str(backup).lower()
        and "supabase_secret" not in str(backup).lower()
    )
    assert Path(backup["WorkingDirectory"]).name == "AIPE04_group3"


def test_failed_uninstall_preserves_definition(tmp_path, monkeypatch):
    import plistlib

    import pytest

    from scripts.ops import schedule
    from scripts.ops.common import OpsError

    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    folder = tmp_path / "Library/LaunchAgents"
    folder.mkdir(parents=True)
    target = folder / (schedule.LABELS["backup"] + ".plist")
    settings = SimpleNamespace(state_dir=tmp_path / "state")
    target.write_bytes(
        plistlib.dumps(schedule.plist(settings, tmp_path / ".env.ops.json", "backup"))
    )
    monkeypatch.setattr(
        schedule.subprocess,
        "run",
        lambda *a, **kw: SimpleNamespace(returncode=0, stderr=b""),
    )
    with pytest.raises(OpsError, match="still_loaded"):
        schedule.uninstall(settings)
    assert target.exists()
