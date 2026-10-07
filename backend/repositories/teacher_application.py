"""TeacherApplication 的資料庫存取。"""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from backend.models.teacher_application import TeacherApplication


def get_application_by_user_id(
    db: Session,
    user_id: uuid.UUID,
) -> TeacherApplication | None:
    """依使用者查詢老師申請。"""
    statement = select(TeacherApplication).where(TeacherApplication.user_id == user_id)
    return db.scalar(statement)


def get_application_by_id(
    db: Session,
    application_id: uuid.UUID,
) -> TeacherApplication | None:
    """依申請 ID 查詢，並帶出對應使用者。"""
    statement = (
        select(TeacherApplication)
        .options(joinedload(TeacherApplication.user))
        .where(TeacherApplication.id == application_id)
    )
    return db.scalar(statement)


def list_applications(db: Session) -> list[TeacherApplication]:
    """列出全部老師申請，新的在上面。"""
    statement = (
        select(TeacherApplication)
        .options(joinedload(TeacherApplication.user))
        .order_by(TeacherApplication.created_at.desc())
    )
    return list(db.scalars(statement).unique())


def add_application(db: Session, application: TeacherApplication) -> None:
    """把老師申請加入目前的資料庫交易。"""
    db.add(application)
