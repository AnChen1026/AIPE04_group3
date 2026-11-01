"""Candidate ranking never invents a course or trusts invalid vectors."""


def test_semantic_ranking_keeps_candidates_and_moves_closest_first():
    from backend.services.ai_semantic import rank_candidates

    candidates = [
        ("one", {"score": [0.0, 1.0]}),
        ("two", {"score": [1.0, 0.0]}),
        ("no-index", None),
    ]
    result = rank_candidates(candidates, [1.0, 0.0])
    assert [row[0] for row in result] == ["two", "one", "no-index"]


def test_invalid_or_mismatched_vectors_preserve_candidate_as_unindexed():
    from backend.services.ai_semantic import rank_candidates

    candidates = [
        ("valid", {"score": [1.0, 0.0]}),
        ("bad", {"score": [float("nan"), 0.0]}),
        ("mismatch", {"score": [1.0]}),
    ]
    result = rank_candidates(candidates, [1.0, 0.0])
    assert [row[0] for row in result] == ["valid", "bad", "mismatch"]
