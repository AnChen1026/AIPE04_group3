"""The model can propose a turn but cannot silently change unquoted facts."""

from types import SimpleNamespace

import pytest


def test_model_planner_rejects_fabricated_evidence(monkeypatch):
    from backend.services.ai_model_planner import AIPlannerUnclear, plan_turn

    monkeypatch.setenv("AI_COURSE_GATEWAY_URL", "https://gateway.example")
    monkeypatch.setenv("AI_COURSE_GATEWAY_TOKEN", "k" * 48)
    monkeypatch.setattr(
        "backend.services.ai_model_planner.httpx.post",
        lambda *args, **kwargs: SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {
                "choices": [
                    {
                        "message": {
                            "content": '{"changes":[{"field":"max_price","value":1500,"quote":"1500元以下"}],"question":""}'
                        }
                    }
                ]
            },
        ),
    )
    with pytest.raises(AIPlannerUnclear):
        plan_turn("我想重新學鋼琴", {"max_price": 1200})


def test_unavailable_planner_preserves_explicit_fallback(monkeypatch):
    from backend.services.ai_model_planner import plan_turn

    monkeypatch.delenv("AI_COURSE_GATEWAY_URL", raising=False)
    assert plan_turn("我想學鋼琴", {}) is None


def test_learning_goal_is_preserved_as_preference_not_hard_style(monkeypatch):
    from backend.services.ai_model_planner import plan_turn

    monkeypatch.setenv("AI_COURSE_GATEWAY_URL", "https://gateway.example")
    monkeypatch.setenv("AI_COURSE_GATEWAY_TOKEN", "k" * 48)
    monkeypatch.setattr(
        "backend.services.ai_model_planner.httpx.post",
        lambda *args, **kwargs: SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {
                "choices": [
                    {
                        "message": {
                            "content": '{"changes":[{"field":"style","value":"電影配樂","quote":"彈電影配樂"}],"question":""}'
                        }
                    }
                ]
            },
        ),
    )
    result = plan_turn("我想彈電影配樂", {"style": None})
    assert result is not None
    assert result[0]["style"] is None
    assert result[0]["_semantic_query"] == "彈電影配樂"


def test_multiple_model_questions_are_rejected(monkeypatch):
    from backend.services.ai_model_planner import AIPlannerUnclear, plan_turn

    monkeypatch.setenv('AI_COURSE_GATEWAY_URL', 'https://gateway.example')
    monkeypatch.setenv('AI_COURSE_GATEWAY_TOKEN', 'k' * 48)
    monkeypatch.setattr('backend.services.ai_model_planner.httpx.post', lambda *args, **kwargs: SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {'choices': [{'message': {'content': '{"changes":[],"question":"程度如何？要線上嗎？"}'}}]},
    ))
    result = plan_turn('我要找鋼琴課', {})
    assert result[1] == '你最想用鋼琴彈什麼？'


def test_changing_a_soft_style_replaces_previous_semantic_goal(monkeypatch):
    from backend.services.ai_model_planner import plan_turn
    monkeypatch.setenv('AI_COURSE_GATEWAY_URL', 'https://gateway.example')
    monkeypatch.setenv('AI_COURSE_GATEWAY_TOKEN', 'k' * 48)
    monkeypatch.setattr('backend.services.ai_model_planner.httpx.post', lambda *args, **kwargs: SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: {'choices': [{'message': {'content': '{"changes":[{"field":"style","value":"爵士","quote":"爵士"}],"question":""}'}}]},
    ))
    result = plan_turn('我想改成爵士', {'style': None, '_semantic_query': '電影配樂'})
    assert result[0]['style'] is None
    assert result[0]['_semantic_query'] == '爵士'


def test_rejects_negation_of_existing_goal_instead_of_keeping_it():
    from backend.services.ai_model_planner import AIPlannerUnclear, plan_turn

    with pytest.raises(AIPlannerUnclear):
        plan_turn('我不喜歡電影配樂', {'_semantic_query': '電影配樂'})
