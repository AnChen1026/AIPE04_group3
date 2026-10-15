"""PostgreSQL integration-test fixtures with a destructive-use safety guard."""

from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url


REPO_ROOT = Path(__file__).resolve().parents[2]


def _guard_test_database_url(raw_url: str | None) -> str:
    if not raw_url:
        raise pytest.UsageError("必須設定 TEST_DATABASE_URL，且資料庫名稱要以 _test 結尾。")

    url = make_url(raw_url)
    if not url.drivername.startswith("postgresql"):
        raise pytest.UsageError("TEST_DATABASE_URL 必須使用 PostgreSQL。")
    if not url.database or not url.database.endswith("_test"):
        raise pytest.UsageError("拒絕清理非測試資料庫；資料庫名稱必須以 _test 結尾。")
    return raw_url


@pytest.fixture(scope="session")
def test_database_url() -> str:
    return _guard_test_database_url(os.environ.get("TEST_DATABASE_URL"))


@pytest.fixture
def alembic_config(test_database_url: str, monkeypatch: pytest.MonkeyPatch) -> Iterator[Config]:
    monkeypatch.setenv("DATABASE_URL", test_database_url)
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))

    # Each test gets the full real migration path from an empty database.
    command.downgrade(config, "base")
    try:
        yield config
    finally:
        command.downgrade(config, "base")


@pytest.fixture
def database_engine(test_database_url: str) -> Iterator[Engine]:
    engine = create_engine(test_database_url)
    try:
        yield engine
    finally:
        engine.dispose()
