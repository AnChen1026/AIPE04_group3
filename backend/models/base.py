# SQLAlchemy 2.x 的共用 Base。
# 之後每一張表的 Model 都繼承這個 Base。

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """所有資料表 Model 的父類別。"""
