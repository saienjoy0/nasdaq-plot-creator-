import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from temporal_evidence import (  # noqa: E402
    TemporalEvidenceError,
    project_publication_temporal,
    projected_watch_next,
    replay_open_validation_obligations,
    render_mandatory_temporal_carryover,
    validate_publication_temporal,
)


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def vo(date="2026-08-12", oid="VO-2026-08-12-01", market="Japan"):
    return {
        "obligation_id": oid,
        "source_episode_date": date,
        "hypothesis_reference": "CH-01",
        "question": "同じ評価軸が次の市場でも確認できるか",
        "observation_target": {
            "market": market,
            "instrument_group": "semiconductor",
            "metric": "session_return",
            "session": "next_completed_regular_session",
            "precision_required": "market-close",
        },
        "strengthen_condition": "同方向の弱さが確認される",
        "weaken_condition": "同方向の弱さが確認されない",
        "max_observation_sessions": 2,
        "importance": "material",
        "status": "open",
        "watch_next_display_text": f"次の{market}半導体セッションを確認",
    }


def record(date, obligations=None, results=None, watch=None):
    obligations = obligations or []
    return {
        "contract_version": "1.1.0",
        "episode_date": date,
        "watch_next": watch if watch is not None else [x["watch_next_display_text"] for x in obligations],
        "temporal_evidence": {
            "carryover_results": results or [],
            "validation_obligations": obligations,
        },
    }


def archive(root: Path, date: str, rec: dict, rev="v001", approved="approved_preview"):
    base = root / "editorial-memory" / "episodes" / date
    write_json(
        base / "index.json",
        {
            "current_revision": rev,
            "revisions": [{"revision": rev, "approval_status": approved}],
        },
    )
    rec = dict(rec)
    rec.setdefault("approval", {"status": approved, "approved_at": f"{date}T12:00:00Z"})
    write_json(base / "revisions" / rev / "publication_record.json", rec)


def test_production_gap_keeps_open_vo(tmp_path: Path):
    archive(tmp_path, "2026-08-12", record("2026-08-12", [vo()]))
    open_items = replay_open_validation_obligations(tmp_path, before_episode_date="2026-08-14")
    assert [x.obligation["obligation_id"] for x in open_items] == ["VO-2026-08-12-01"]


def test_current_revision_only(tmp_path: Path):
    base = tmp_path / "editorial-memory" / "episodes" / "2026-08-12"
    write_json(
        base / "index.json",
        {
            "current_revision": "v002",
            "revisions": [
                {"revision": "v001", "approval_status": "approved_preview"},
                {"revision": "v002", "approval_status": "approved_preview"},
            ],
        },
    )
    r1 = record("2026-08-12", [vo(oid="VO-OLD")])
    r1["approval"] = {"status": "approved_preview", "approved_at": "x"}
    r2 = record("2026-08-12", [vo(oid="VO-NEW")])
    r2["approval"] = {"status": "approved_preview", "approved_at": "x"}
    write_json(base / "revisions/v001/publication_record.json", r1)
    write_json(base / "revisions/v002/publication_record.json", r2)
    ids = [x.obligation["obligation_id"] for x in replay_open_validation_obligations(tmp_path, before_episode_date="2026-08-13")]
    assert ids == ["VO-NEW"]


def test_unapproved_revision_not_carried(tmp_path: Path):
    archive(tmp_path, "2026-08-12", record("2026-08-12", [vo()]), approved="draft")
    assert replay_open_validation_obligations(tmp_path, before_episode_date="2026-08-13") == []


def test_result_closes_obligation(tmp_path: Path):
    archive(tmp_path, "2026-08-12", record("2026-08-12", [vo()]))
    archive(
        tmp_path,
        "2026-08-13",
        record(
            "2026-08-13",
            results=[{
                "obligation_id": "VO-2026-08-12-01",
                "status": "supports",
                "current_evidence_ids": ["E-014"],
                "notes": "observed",
            }],
        ),
    )
    assert replay_open_validation_obligations(tmp_path, before_episode_date="2026-08-14") == []


def test_not_observed_keeps_open(tmp_path: Path):
    archive(tmp_path, "2026-08-12", record("2026-08-12", [vo()]))
    archive(
        tmp_path,
        "2026-08-13",
        record(
            "2026-08-13",
            results=[{
                "obligation_id": "VO-2026-08-12-01",
                "status": "not_observed",
                "current_evidence_ids": [],
                "notes": "market holiday",
            }],
        ),
    )
    assert len(replay_open_validation_obligations(tmp_path, before_episode_date="2026-08-14")) == 1


def test_one_vo_one_target_rejects_arrays(tmp_path: Path):
    bad = vo()
    bad["observation_target"]["market"] = ["Japan", "Hong Kong"]
    rec = record("2026-08-12", [bad], watch=[bad["watch_next_display_text"]])
    try:
        validate_publication_temporal(rec, tmp_path)
    except TemporalEvidenceError as exc:
        assert "1 VO = 1 target" in str(exc)
    else:
        raise AssertionError("expected TemporalEvidenceError")


def test_duplicate_semantics_must_reuse_id(tmp_path: Path):
    archive(tmp_path, "2026-08-12", record("2026-08-12", [vo()]))
    duplicate = vo(date="2026-08-13", oid="VO-2026-08-13-99")
    rec = record("2026-08-13", [duplicate])
    try:
        validate_publication_temporal(rec, tmp_path)
    except TemporalEvidenceError as exc:
        assert "duplicate VO must continue existing id" in str(exc)
    else:
        raise AssertionError("expected TemporalEvidenceError")


def test_watch_next_projection_is_structured_vo_projection(tmp_path: Path):
    item = vo()
    rec = record("2026-08-12", [item], watch=[item["watch_next_display_text"], "一般的な確認点"])
    validate_publication_temporal(rec, tmp_path)
    assert projected_watch_next(rec) == [item["watch_next_display_text"]]


def test_supports_requires_current_evidence(tmp_path: Path):
    rec = record(
        "2026-08-12",
        results=[{
            "obligation_id": "VO-X",
            "status": "supports",
            "current_evidence_ids": [],
            "notes": "bad",
        }],
    )
    try:
        validate_publication_temporal(rec, tmp_path)
    except TemporalEvidenceError as exc:
        assert "Current Evidence ID" in str(exc)
    else:
        raise AssertionError("expected TemporalEvidenceError")


def test_render_context_has_mandatory_section(tmp_path: Path):
    archive(tmp_path, "2026-08-12", record("2026-08-12", [vo()]))
    text = render_mandatory_temporal_carryover(tmp_path, episode_date="2026-08-13")
    assert "## Mandatory Temporal Carryover" in text
    assert "VO-2026-08-12-01" in text
    assert "Carry forward questions, not conclusions" in text


def test_same_id_cannot_change_semantics(tmp_path: Path):
    archive(tmp_path, "2026-08-12", record("2026-08-12", [vo()]))
    changed = vo(date="2026-08-13")
    changed["weaken_condition"] = "別の条件へ勝手に変更"
    rec = record("2026-08-13", [changed])
    try:
        validate_publication_temporal(rec, tmp_path)
    except TemporalEvidenceError as exc:
        assert "changed semantics" in str(exc)
    else:
        raise AssertionError("expected TemporalEvidenceError")


def test_expiry_requires_completed_session_count(tmp_path: Path):
    archive(tmp_path, "2026-08-12", record("2026-08-12", [vo()]))
    rec = record(
        "2026-08-13",
        results=[{
            "obligation_id": "VO-2026-08-12-01",
            "status": "expired",
            "current_evidence_ids": [],
            "notes": "bad early expiry",
        }],
    )
    try:
        validate_publication_temporal(rec, tmp_path)
    except TemporalEvidenceError as exc:
        assert "completed_observation_sessions" in str(exc)
    else:
        raise AssertionError("expected TemporalEvidenceError")


def test_expiry_cannot_happen_before_max_sessions(tmp_path: Path):
    archive(tmp_path, "2026-08-12", record("2026-08-12", [vo()]))
    rec = record(
        "2026-08-13",
        results=[{
            "obligation_id": "VO-2026-08-12-01",
            "status": "expired",
            "current_evidence_ids": [],
            "completed_observation_sessions": 1,
            "notes": "too soon",
        }],
    )
    try:
        validate_publication_temporal(rec, tmp_path)
    except TemporalEvidenceError as exc:
        assert "cannot expire before" in str(exc)
    else:
        raise AssertionError("expected TemporalEvidenceError")


def test_temporal_visual_need_requires_intent_mapping(tmp_path: Path):
    date = "2026-08-13"
    write_json(
        tmp_path / "research" / date / f"causal_research_dossier_{date}.json",
        {
            "contract_version": "0.3.0",
            "visual_evidence_needs": [{"need_id": "TVE-01"}],
        },
    )
    write_json(
        tmp_path / "working" / date / "story-engine" / "story_plan.json",
        {
            "temporal_usage": {
                "carryover_results": [],
                "cross_market": {
                    "mode": "spoken",
                    "scene_id": "scene-06",
                    "visual_need_ids": ["TVE-01"],
                },
                "validation_obligations": [],
            }
        },
    )
    from temporal_evidence import validate_temporal_visual_intents
    try:
        validate_temporal_visual_intents(
            tmp_path,
            episode_date=date,
            visual_sources={"contractVersion": "1.0.0", "intents": []},
        )
    except TemporalEvidenceError as exc:
        assert "E_TEMPORAL_VISUAL_EVIDENCE_MISSING" in str(exc)
        assert "TVE-01" in str(exc)
    else:
        raise AssertionError("expected TemporalEvidenceError")


def test_internal_only_temporal_does_not_force_visual(tmp_path: Path):
    date = "2026-08-13"
    write_json(
        tmp_path / "research" / date / f"causal_research_dossier_{date}.json",
        {"contract_version": "0.3.0", "visual_evidence_needs": [{"need_id": "TVE-01"}]},
    )
    write_json(
        tmp_path / "working" / date / "story-engine" / "story_plan.json",
        {
            "temporal_usage": {
                "carryover_results": [],
                "cross_market": {
                    "mode": "internal_only",
                    "scene_id": None,
                    "visual_need_ids": ["TVE-01"],
                },
                "validation_obligations": [],
            }
        },
    )
    from temporal_evidence import validate_temporal_visual_intents
    validate_temporal_visual_intents(
        tmp_path,
        episode_date=date,
        visual_sources={"contractVersion": "1.0.0", "intents": []},
    )


def test_spoken_temporal_visual_need_can_bind_existing_intent(tmp_path: Path):
    date = "2026-08-13"
    write_json(
        tmp_path / "research" / date / f"causal_research_dossier_{date}.json",
        {"contract_version": "0.3.0", "visual_evidence_needs": [{"need_id": "TVE-01"}]},
    )
    write_json(
        tmp_path / "working" / date / "story-engine" / "story_plan.json",
        {
            "temporal_usage": {
                "carryover_results": [],
                "cross_market": {"mode": "spoken", "scene_id": "scene-06", "visual_need_ids": ["TVE-01"]},
                "validation_obligations": [],
            }
        },
    )
    from temporal_evidence import validate_temporal_visual_intents
    validate_temporal_visual_intents(
        tmp_path,
        episode_date=date,
        visual_sources={
            "contractVersion": "1.0.0",
            "intents": [{"temporalEvidenceNeedIds": ["TVE-01"]}],
        },
    )


def test_publication_projection_uses_structured_vo_and_preserves_general_watch():
    item = vo()
    story_item = {
        **item,
        "candidate_id": "VC-01",
        "mode": "spoken",
        "scene_id": "scene-08",
        "visual_need_ids": [],
    }
    base = {
        "contract_version": "1.0.0",
        "episode_date": "2026-08-12",
        "watch_next": ["一般的な金利確認"],
    }
    dossier = {
        "contract_version": "0.3.0",
        "episode_date": "2026-08-12",
        "carryover_results": [],
    }
    story = {
        "episode_date": "2026-08-12",
        "temporal_usage": {
            "carryover_results": [],
            "cross_market": {"mode": "internal_only", "scene_id": None, "visual_need_ids": []},
            "validation_obligations": [story_item],
        },
    }
    projected = project_publication_temporal(base, dossier=dossier, story_plan=story)
    assert projected["contract_version"] == "1.1.0"
    assert projected["watch_next"] == ["一般的な金利確認", item["watch_next_display_text"]]
    assert projected["temporal_evidence"]["validation_obligations"] == [item]
    assert "candidate_id" not in projected["temporal_evidence"]["validation_obligations"][0]


def test_publication_projection_is_idempotent_for_watch_next():
    item = vo()
    story_item = {**item, "candidate_id": "VC-01", "mode": "spoken", "scene_id": "scene-08", "visual_need_ids": []}
    dossier = {"contract_version": "0.3.0", "episode_date": "2026-08-12", "carryover_results": []}
    story = {
        "episode_date": "2026-08-12",
        "temporal_usage": {
            "carryover_results": [],
            "cross_market": {"mode": "internal_only", "scene_id": None, "visual_need_ids": []},
            "validation_obligations": [story_item],
        },
    }
    first = project_publication_temporal(
        {"contract_version": "1.0.0", "episode_date": "2026-08-12", "watch_next": ["一般点"]},
        dossier=dossier,
        story_plan=story,
    )
    second = project_publication_temporal(first, dossier=dossier, story_plan=story)
    assert second["watch_next"] == first["watch_next"]
