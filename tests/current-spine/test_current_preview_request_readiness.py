from pathlib import Path

import current_preview_request_readiness_v12 as readiness


def test_choose_prepare_when_director_semantic_missing(tmp_path: Path):
    vi = tmp_path / "working/2026-08-17/visual-intelligence"
    vi.mkdir(parents=True)
    assert readiness.choose_phase(tmp_path, "2026-08-17") == "prepare"


def test_choose_compile_when_director_semantic_exists(tmp_path: Path):
    vi = tmp_path / "working/2026-08-17/visual-intelligence"
    vi.mkdir(parents=True)
    (vi / "visual_director_decision.semantic.json").write_text("{}\n", encoding="utf-8")
    assert readiness.choose_phase(tmp_path, "2026-08-17") == "compile"


def test_prepared_is_not_ready_and_preserves_required_action():
    state, action = readiness.classify_facade_outcome({
        "status": "PREPARED",
        "requiredAction": "AUTHOR_VISUAL_INTELLIGENCE_DECISION",
    })
    assert state == "NOT_READY"
    assert action == "AUTHOR_VISUAL_INTELLIGENCE_DECISION"


def test_review_required_maps_to_critic_action():
    state, action = readiness.classify_facade_outcome({"status": "REVIEW_REQUIRED"})
    assert state == "NOT_READY"
    assert action == "AUTHOR_VISUAL_CRITIC_REVIEW"


def test_pass_is_ready():
    state, action = readiness.classify_facade_outcome({"status": "PASS"})
    assert state == "PASS"
    assert action is None
