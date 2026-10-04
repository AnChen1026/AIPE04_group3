# 讀取專案設定。
# 資料庫連線字串放在環境變數或專案根目錄的 .env，不要寫死在程式裡。

from pathlib import Path
import os


def read_env_value(name):
    """先看系統環境變數，再看 .env。找不到就回傳 None。"""
    value = os.environ.get(name)
    if value:
        return value.strip()

    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists() is False:
        return None

    for line in env_path.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if text.startswith("#"):
            continue
        if "=" not in text:
            continue

        key_name, key_value = text.split("=", 1)
        if key_name.strip() == name:
            cleaned = key_value.strip().strip('"').strip("'")
            if cleaned:
                return cleaned

    return None


def get_database_url():
    """取得 PostgreSQL 連線字串。"""
    database_url = read_env_value("DATABASE_URL")
    if database_url is None:
        raise RuntimeError(
            "沒有設定 DATABASE_URL，請在專案根目錄 .env 寫入連線字串。"
        )
    return database_url


def get_session_secret_key():
    """取得簽署登入 Session Cookie 的密鑰。"""
    secret_key = read_env_value("SESSION_SECRET_KEY")
    if secret_key is None:
        raise RuntimeError(
            "沒有設定 SESSION_SECRET_KEY，請在專案根目錄 .env 設定隨機密鑰。"
        )
    return secret_key
