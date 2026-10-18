"""Fixtures for destructive Alembic tests on an isolated PostgreSQL database."""

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
        pytest.skip("未設定 TEST_DATABASE_URL；略過破壞性的 Migration 測試。")

    url = make_url(raw_url)
    if not url.drivername.startswith("postgresql"):
        raise pytest.UsageError("TEST_DATABASE_URL 必須使用 PostgreSQL。")
    if not url.database or not url.database.endswith("_test"):
        raise pytest.UsageError("拒絕清理非測試資料庫；資料庫名稱必須以 _test 結尾。")
    return raw_url


@pytest.fixture
def migration_database(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[Config, Engine]]:
    database_url = _guard_test_database_url(os.environ.get("TEST_DATABASE_URL"))
    monkeypatch.setenv("DATABASE_URL", database_url)

    engine = create_engine(database_url)
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.exec_driver_sql("DROP SCHEMA public CASCADE")
        connection.exec_driver_sql("CREATE SCHEMA public")

    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(REPO_ROOT / "alembic"))
    try:
        yield config, engine
    finally:
        # Migration 測試會刻意升降版本；離開時恢復最新版，避免同一輪 pytest
        # 後面的 API 測試接到殘缺資料表。
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.exec_driver_sql("DROP SCHEMA public CASCADE")
            connection.exec_driver_sql("CREATE SCHEMA public")
        command.upgrade(config, "head")
        engine.dispose()
