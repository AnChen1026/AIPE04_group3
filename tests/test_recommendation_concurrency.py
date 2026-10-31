"""Concurrent updates must not overwrite another turn in the same session."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.database import engine
from backend.models.student import RecommendationSession


def test_concurrent_turn_is_rejected_without_overwriting_state():
    from backend.services.recommendation import RecommendationConflict, answer_recommendation

    owner = '0' * 64
    with Session(engine) as setup:
        row = RecommendationSession(owner_hash=owner, messages=[], criteria={}, asked_fields=[], question_count=0,
            status='asking', result_message='', expires_at=datetime.now(timezone.utc) + timedelta(hours=1))
        setup.add(row);setup.commit();identifier=row.id
    try:
        with Session(engine) as first, Session(engine) as second:
            first.scalar(select(RecommendationSession).where(RecommendationSession.id == identifier).with_for_update())
            with pytest.raises(RecommendationConflict):
                answer_recommendation(second, owner, identifier, '我想上線上課')
            first.rollback()
    finally:
        with Session(engine) as cleanup:
            row=cleanup.get(RecommendationSession,identifier)
            if row:cleanup.delete(row);cleanup.commit()
