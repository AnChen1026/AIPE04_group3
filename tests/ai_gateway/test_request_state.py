"""Conversation state can only change with evidence from the current turn."""

import pytest


def test_unquoted_model_change_does_not_override_confirmed_budget():
    from backend.services.ai_request_state import InvalidPlan, apply_changes

    old = {"max_price": 1200, "delivery_mode": "online"}
    with pytest.raises(InvalidPlan):
        apply_changes(
            old,
            "想學電影配樂",
            [{"field": "max_price", "value": 1500, "quote": "1500元"}],
        )
    assert old == {"max_price": 1200, "delivery_mode": "online"}


def test_confirmed_budget_change_keeps_unmentioned_mode():
    from backend.services.ai_request_state import apply_changes

    old = {"max_price": 1200, "delivery_mode": "online"}
    updated = apply_changes(
        old,
        "預算改成1500元以下，其他不變",
        [{"field": "max_price", "value": 1500, "quote": "1500元以下"}],
    )
    assert updated == {"max_price": 1500, "delivery_mode": "online"}
    assert old["max_price"] == 1200


def test_one_unsupported_change_rejects_all_changes():
    from backend.services.ai_request_state import InvalidPlan, apply_changes

    old = {"max_price": 1200, "delivery_mode": "online"}
    with pytest.raises(InvalidPlan):
        apply_changes(
            old,
            "1500元以下，不要實體",
            [
                {"field": "max_price", "value": 1500, "quote": "1500元以下"},
                {"field": "delivery_mode", "value": "in_person", "quote": "不要實體"},
            ],
        )
    assert old == {"max_price": 1200, "delivery_mode": "online"}


def test_explicit_cancel_removes_only_budget():
    from backend.services.ai_request_state import apply_changes

    current = {"max_price": 1200, "delivery_mode": "online"}
    result = apply_changes(
        current,
        "預算不限，其他不變",
        [{"field": "max_price", "value": None, "quote": "預算不限"}],
    )
    assert result == {"max_price": None, "delivery_mode": "online"}


def test_negated_cancel_cannot_remove_budget():
    from backend.services.ai_request_state import InvalidPlan, apply_changes

    with pytest.raises(InvalidPlan):
        apply_changes(
            {"max_price": 1200},
            "預算不是不限",
            [{"field": "max_price", "value": None, "quote": "預算不是不限"}],
        )


@pytest.mark.parametrize(
    "message,quote",
    [
        ("不要線上上課", "線上"),
        ("如果線上課有折扣再說", "線上"),
        ("我的朋友想上線上課", "線上"),
        ("不想要線上，但是線上也許可以", "線上"),
    ],
)
def test_cannot_infer_positive_hard_filter_from_negated_or_hypothetical_text(
    message, quote
):
    from backend.services.ai_request_state import InvalidPlan, apply_changes

    with pytest.raises(InvalidPlan):
        apply_changes(
            {}, message, [{"field": "delivery_mode", "value": "online", "quote": quote}]
        )


@pytest.mark.parametrize('message', [
    '我不喜歡線上上課', '我不能線上上課', '我拒絕線上上課',
    '我無法線上上課', '我的朋友想要線上上課', '如果天氣不好，線上上課',
])
def test_model_proposal_does_not_turn_negative_or_hypothetical_into_hard_mode(message):
    from backend.services.ai_request_state import InvalidPlan, apply_changes

    with pytest.raises(InvalidPlan):
        apply_changes({}, message, [{'field':'delivery_mode','value':'online','quote':'線上'}])


@pytest.mark.parametrize('message', ['預算不限不行', '預算不限是不對的', '預算不限只是舉例', '預算不限嗎？', '預算不限，這不是真的'])
def test_budget_cannot_be_cleared_from_nonaffirmative_context(message):
    from backend.services.ai_request_state import InvalidPlan, apply_changes
    with pytest.raises(InvalidPlan):
        apply_changes({'max_price':1200}, message, [{'field':'max_price','value':None,'quote':'預算不限'}])


@pytest.mark.parametrize('message', ['台北市不行', '台北市不適合', '台北市已取消'])
def test_location_negation_cannot_become_positive_filter(message):
    from backend.services.ai_request_state import InvalidPlan, apply_changes
    with pytest.raises(InvalidPlan):
        apply_changes({}, message, [{'field':'region','value':'台北市','quote':'台北市'}])
