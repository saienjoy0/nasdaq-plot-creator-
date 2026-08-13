from __future__ import annotations

import json
from pathlib import Path

import pytest
import visual_director_bridge as bridge

DATE = "2099-01-02"


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def catalog(single: bool = False) -> dict:
    candidates = [
        {"visualBeatId": "vb-01-01", "candidateId": "vc-01"},
    ]
    if not single:
        candidates.append(
            {"visualBeatId": "vb-01-01", "candidateId": "vc-02"}
        )
    return {
        "contractVersion": "1.0.0",
        "episodeDate": DATE,
        "sourceRenderSpecSha256": "a" * 64,
        "candidates": candidates,
    }


def test_missing_phase1_recent_context_is_explicit_not_available(tmp_path: Path) -> None:
    path = tmp_path / "recent_visual_pattern_context.json"
    value = bridge._ensure_phase1_recent_context(path, date=DATE)
    assert value["status"] == "not-available"
    assert value["approvedEpisodes"] == []
    assert json.loads(path.read_text(encoding="utf-8")) == value


def test_multiple_legal_candidates_require_real_strongest_alternative(tmp_path: Path) -> None:
    path = tmp_path / "selection.json"
    write_json(
        path,
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "round": 1,
            "selections": [
                {
                    "visualBeatId": "vb-01-01",
                    "selectedCandidateId": "vc-01",
                    "strongestAlternativeCandidateId": None,
                    "whySelected": "reason",
                    "whyNotAlternative": "",
                }
            ],
        },
    )
    with pytest.raises(bridge.VisualDirectorBridgeError, match="strongest alternative"):
        bridge._validate_editorial_selection(
            path=path,
            date=DATE,
            catalog=catalog(),
        )


def test_single_legal_candidate_does_not_invent_alternative(tmp_path: Path) -> None:
    path = tmp_path / "selection.json"
    write_json(
        path,
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "round": 1,
            "selections": [
                {
                    "visualBeatId": "vb-01-01",
                    "selectedCandidateId": "vc-01",
                    "strongestAlternativeCandidateId": None,
                    "whySelected": "only legal candidate",
                    "whyNotAlternative": "",
                }
            ],
        },
    )
    selection, plan = bridge._validate_editorial_selection(
        path=path,
        date=DATE,
        catalog=catalog(single=True),
    )
    assert selection["selections"][0]["strongestAlternativeCandidateId"] is None
    assert plan["selections"] == [
        {"visualBeatId": "vb-01-01", "candidateId": "vc-01"}
    ]


def test_legacy_authored_only_helper_is_not_a_production_default() -> None:
    assert not hasattr(bridge, "_ensure_template_policy_hints")
    assert bridge.BRIDGE_CONTRACT_VERSION == "visual-intelligence-bridge/1.2.0"
