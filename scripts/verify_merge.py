#!/usr/bin/env python3
"""用隔離測試資料庫執行合併前檢查。"""

from __future__ import annotations

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]


def read_env_file() -> dict[str, str]:
    values: dict[str, str] = {}
    path = ROOT / ".env"
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def find_python() -> Path:
    candidates = (
        ROOT / ".venv" / "bin" / "python",
        ROOT / ".venv" / "Scripts" / "python.exe",
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return Path(sys.executable)


def test_database_name(raw_url: str) -> str:
    parsed = urlparse(raw_url)
    name = parsed.path.removeprefix("/")
    if not parsed.scheme.startswith("postgresql"):
        fail("TEST_DATABASE_URL 必須是 PostgreSQL 連線字串。")
    if not name.endswith("_test") or not re.fullmatch(r"[A-Za-z0-9_]+", name):
        fail("為保護正式資料，測試資料庫名稱必須以 _test 結尾。")
    return name


def fail(message: str) -> None:
    print(f"\n驗證停止：{message}", file=sys.stderr)
    raise SystemExit(1)


def run(title: str, command: list[str], env: dict[str, str], cwd: Path = ROOT) -> None:
    print(f"\n=== {title} ===")
    result = subprocess.run(command, cwd=cwd, env=env, check=False)
    if result.returncode:
        fail(f"「{title}」未通過，請先處理上方訊息。")


def ensure_test_database(python: Path, env: dict[str, str], database_name: str) -> None:
    worker = """
import os
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

url = make_url(os.environ["TEST_DATABASE_URL"])
database_name = os.environ["AIPE04_TEST_DATABASE_NAME"]
admin_url = url.set(database="postgres")
engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
with engine.connect() as connection:
    exists = connection.execute(
        text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": database_name}
    ).scalar()
    if not exists:
        connection.exec_driver_sql(f'CREATE DATABASE "{database_name}"')
engine.dispose()
"""
    worker_env = dict(env)
    worker_env["AIPE04_TEST_DATABASE_NAME"] = database_name
    run("準備隔離測試資料庫", [str(python), "-c", worker], worker_env)


def main() -> None:
    if "--help" in sys.argv or "-h" in sys.argv:
        print("用法：python scripts/verify_merge.py\n執行後端、Migration 與 Vue 合併前檢查。")
        return

    file_env = read_env_file()
    test_url = os.environ.get("TEST_DATABASE_URL") or file_env.get("TEST_DATABASE_URL")
    if not test_url:
        fail("找不到 TEST_DATABASE_URL。請先把 .env.example 複製成 .env。")
    database_name = test_database_name(test_url)

    python = find_python()
    if not python.exists():
        fail("找不到 Python，請先依 README 建立 .venv。")

    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not npm:
        fail("找不到 npm，請先安裝 README 指定的 Node.js。")
    if not (ROOT / "frontend" / "node_modules").exists():
        fail("前端套件尚未安裝，請先在 frontend 執行 npm install。")

    env = dict(os.environ)
    env.update({key: value for key, value in file_env.items() if key not in env})
    env["TEST_DATABASE_URL"] = test_url
    env["DATABASE_URL"] = test_url
    env.setdefault("SESSION_SECRET_KEY", "local-merge-verification-only")

    ensure_test_database(python, env, database_name)
    run("升級測試資料庫", [str(python), "-m", "alembic", "upgrade", "head"], env)
    run("後端與 Migration 測試", [str(python), "-m", "pytest", "-q"], env)
    run("確認 Model 與 Migration 同步", [str(python), "-m", "alembic", "check"], env)
    run("Vue 程式檢查", [npm, "run", "lint-check"], env, ROOT / "frontend")
    run("Vue 型別檢查", [npm, "run", "type-check"], env, ROOT / "frontend")
    run("建立 Vue 正式版", [npm, "run", "build-only"], env, ROOT / "frontend")

    print("\n全部驗證通過：可以進行手動驗收與 Pull Request Review。")


if __name__ == "__main__":
    main()
