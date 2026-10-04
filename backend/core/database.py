# 建立 PostgreSQL 連線與 Session。

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.core.config import get_database_url

database_url = get_database_url()

engine = create_engine(
    database_url,
    echo=False,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    """每次請求拿一個 Session，用完後關掉。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
