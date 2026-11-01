"""Refine can attach only verbatim evidence to its own candidate."""

from backend.services.ai_refine import refine_evidence


def test_refine_keeps_each_quote_with_its_own_course():
    candidates = [
        {"id": "a", "description": "適合初學者，循序練習"},
        {"id": "b", "description": "教授電影配樂與和弦"},
    ]
    calls = []

    def choose(query, candidate, prior):
        calls.append((candidate["id"], list(prior)))
        return {
            "items": [
                *prior,
                {
                    "course_id": candidate["id"],
                    "quote": "適合初學者" if candidate["id"] == "a" else "教授電影配樂",
                },
            ]
        }

    result = refine_evidence("電影配樂", candidates, choose)
    assert result == [
        {"course_id": "a", "quote": "適合初學者"},
        {"course_id": "b", "quote": "教授電影配樂"},
    ]
    assert calls[1][1] == [{"course_id": "a", "quote": "適合初學者"}]


def test_refine_rejects_fabricated_and_cross_course_quotes():
    candidates = [{"id": "a", "description": "教授電影配樂"}]
    assert (
        refine_evidence(
            "電影",
            candidates,
            lambda *args: {"items": [{"course_id": "other", "quote": "教授電影配樂"}]},
        )
        == []
    )
    assert (
        refine_evidence(
            "電影",
            candidates,
            lambda *args: {"items": [{"course_id": "a", "quote": "保證耐心"}]},
        )
        == []
    )


def test_refine_can_revise_prior_evidence_but_not_cross_sources():
    candidates = [
        {"id": "a", "description": "入門練習，也可學流行"},
        {"id": "b", "description": "專教電影配樂"},
    ]

    def choose(query, candidate, prior):
        if candidate["id"] == "a":
            return {"items": [{"course_id": "a", "quote": "入門練習"}]}
        return {
            "items": [
                {"course_id": "a", "quote": "也可學流行"},
                {"course_id": "b", "quote": "專教電影配樂"},
            ]
        }

    assert refine_evidence("電影配樂", candidates, choose) == [
        {"course_id": "a", "quote": "也可學流行"},
        {"course_id": "b", "quote": "專教電影配樂"},
    ]


def test_direct_evidence_rejects_wrong_course_and_nonverbatim_quotes():
    from backend.services.ai_refine import direct_evidence

    candidates = [{'id':'a','description':'電影配樂入門'}, {'id':'b','description':'爵士基礎'}]
    model_output = {'items':[
        {'course_id':'a','quote':'爵士基礎'},
        {'course_id':'b','quote':'不存在'},
        {'course_id':'a','quote':'電影配樂'},
        {'course_id':'unknown','quote':'電影配樂'},
    ]}
    assert direct_evidence(candidates, model_output) == [{'course_id':'a','quote':'電影配樂'}]
