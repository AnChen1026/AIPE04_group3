"""AuthIdentity 的資料庫存取。"""

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.models.auth_identity import AuthIdentity


def get_identity(db: Session, provider: str, provider_subject: str) -> AuthIdentity | None:
    """依 Google 等外部身份查詢。"""
    statement = (
        select(AuthIdentity)
        .options(joinedload(AuthIdentity.user))
        .where(
            AuthIdentity.provider == provider,
            AuthIdentity.provider_subject == provider_subject,
        )
    )
    return db.scalar(statement)


def add_identity(db: Session, identity: AuthIdentity) -> None:
    """把外部登入身份加入目前的資料庫交易。"""
    db.add(identity)
