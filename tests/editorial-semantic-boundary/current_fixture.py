from __future__ import annotations

import copy
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

DATE = "2099-01-07"
MARKET_DATE = "2099-01-06"
CUTOFF = "2099-01-07T06:00:00-05:00"
ROLES = [
    "direction_and_conclusion", "contradiction", "confirmed_facts", "expected_actual_gap",
    "global_context", "market_reaction", "entity_divergence", "validation_points", "fixed_closing",
]
STORY_ROLES = ["hook", "question", "setup", "explanation", "context", "test", "comparison", "verification", "closing"]


def canonical_projection_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha(path: Path) -> str:
    return sha_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def file_ref(root: Path, path: Path) -> dict[str, str]:
    return {"path": path.relative_to(root).as_posix(), "sha256": sha(path)}


def current_grammar_id(visual_template: str) -> str:
    """Resolve synthetic Current grammar from the existing compatibility contract.

    This intentionally mirrors Renderer makeCurrentVisualGrammarFixture(): the fixture never
    owns a second grammar literal and takes the first allowed grammar for its visual template.
    """
    contract_path = Path(__file__).resolve().parents[2] / "contracts/visual_grammar_renderer_compatibility.json"
    value = json.loads(contract_path.read_text(encoding="utf-8"))
    for item in value.get("templates", []):
        if not isinstance(item, dict) or item.get("visualTemplateId") != visual_template:
            continue
        allowed = item.get("allowedGrammarIds")
        if isinstance(allowed, list) and allowed and all(isinstance(grammar_id, str) and grammar_id for grammar_id in allowed):
            return allowed[0]
    raise ValueError(f"Current visual template is absent from compatibility contract: {visual_template}")


def install_runtime(source_root: Path, root: Path) -> None:
    """Copy only current contracts/validators used by the synthetic E2E."""
    copies = [
        "contracts/chatgpt_daily_authoring_v2.schema.json",
        "contracts/editorial_semantic_acceptance.schema.json",
        "contracts/chatgpt_semantic_freeze.schema.json",
        "contracts/canon_manifest.schema.json",
        "contracts/visual_grammar_renderer_compatibility.json",
        "skills/nasdaq-cafe-causal-research/contracts",
        "skills/nasdaq-cafe-causal-research/validators/validate_causal_research_dossier.py",
        "skills/nasdaq-cafe-editorial-memory/contracts",
        "skills/nasdaq-cafe-story-plan/contracts",
        "skills/nasdaq-cafe-story-plan/validators/validate_story_plan.py",
        "skills/nasdaq-cafe-story-authoring/contracts",
        "skills/nasdaq-cafe-entertainment-critic/contracts",
        "scripts/build_research_input_manifest.py",
        "scripts/editorial_memory_retrieval.py",
        "scripts/temporal_evidence.py",
        "scripts/story-engine/validate_story_engine_bundle.py",
        "scripts/canon_manifest.py",
        "scripts/materialize_causal_research.py",
        "scripts/validate_editorial_semantic_boundary.py",
        "scripts/chatgpt_semantic_freeze.py",
    ]
    for rel in copies:
        src = source_root / rel
        dst = root / rel
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)


def make_canon(root: Path) -> None:
    docs = []
    for number, name in (
        ("01", "01_fox_character_bible.md"),
        ("02", "02_editorial_bible.md"),
        ("03", "03_episode_production_spec.md"),
        ("04", "04_entertainment_inquisitor.md"),
    ):
        path = root / "source-of-truth" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        data = f"synthetic canon {number}\n".encode()
        path.write_bytes(data)
        docs.append({
            "id": number,
            "logicalPath": f"source-of-truth/{name}",
            "sha256": sha_bytes(data),
            "rawBytes": len(data),
            "storage": {
                "mode": "direct" if number in {"01", "02"} else "gzip+base64-concatenated",
                "parts": [f"source-of-truth/{name}"] if number in {"01", "02"} else [],
            },
        })
    import base64, gzip
    for item in docs[2:]:
        logical = root / item["logicalPath"]
        encoded = base64.b64encode(gzip.compress(logical.read_bytes())).decode("ascii")
        part_rel = item["logicalPath"] + ".gz.b64"
        part = root / part_rel
        part.write_text(encoded, encoding="ascii")
        item["storage"] = {"mode": "gzip+base64-concatenated", "parts": [part_rel]}
    write_json(root / "source-of-truth/canon_manifest.json", {
        "contractVersion": "1.0.0", "authority": "nasdaq-cafe-semantic-canon", "documents": docs,
    })


def query_plan() -> dict[str, Any]:
    return {
        "contract_version": "1.0.0", "episode_date": DATE,
        "lead_candidates": ["synthetic lead"], "entities": [], "topics": ["AI"], "technologies": [],
        "policies": [], "indicators": ["NASDAQ"], "relations": [],
        "time_window": {"from": None, "to": MARKET_DATE}, "comparison_questions": ["what changed"],
        "limits": {"max_threads": 0, "max_claims": 0, "max_episodes": 0, "max_lessons": 0, "max_characters": 1000},
    }


def retrieval_report(query_rel: str) -> dict[str, Any]:
    return {
        "contract_version": "1.0.0", "episode_date": DATE, "query_plan_path": query_rel,
        "selected": [], "rejected": [],
        "limits": {"max_threads": 0, "max_claims": 0, "max_episodes": 0, "max_lessons": 0, "max_characters": 1000},
        "usage": {"threads": 0, "claims": 0, "episodes": 0, "lessons": 0, "characters": 0},
        "diversity": {"distinct_episode_ids": [], "distinct_thread_ids": [], "duplicate_groups_removed": 0},
        "warnings": [],
    }


def research_manifest(root: Path, daily: Path, query: Path, context: Path, report: Path) -> dict[str, Any]:
    return {
        "contract_version": "1.0.0", "episode_date": DATE,
        "session": {"market_date": MARKET_DATE, "timezone": "America/New_York", "information_cutoff": CUTOFF},
        "inputs": {
            "daily_source_package": file_ref(root, daily), "memory_query_plan": file_ref(root, query),
            "memory_context": file_ref(root, context), "memory_retrieval_report": file_ref(root, report),
        },
        "memory_intake": {"current_revalidation_required": [], "historical_context_only": [], "procedural": [], "not_selected": []},
        "validation": {"status": "pass", "errors": [], "warnings": []},
    }


def evidence(eid: str, claim: str) -> dict[str, Any]:
    return {
        "evidence_id": eid, "claim": claim, "evidence_class": "fact", "source_tier": "tier_1",
        "source_title": f"Source {eid}", "source_issuer_or_publisher": "Synthetic IR",
        "source_reference": f"synthetic://{eid}", "event_timestamp": None, "publication_timestamp": None,
        "timezone": None, "directness": "direct", "independence_group": eid,
        "confidence": "high", "limitations": "synthetic contract fixture",
    }


def dossier(root: Path, manifest: Path, daily: Path) -> dict[str, Any]:
    return {
        "contract_version": "0.3.0", "episode_date": DATE,
        "session": {"market_date": MARKET_DATE, "timezone": "America/New_York", "information_cutoff": CUTOFF},
        "input_provenance": [{"path_or_reference": daily.relative_to(root).as_posix(), "role": "daily_input", "version_or_hash": sha(daily)}],
        "research_input_manifest": file_ref(root, manifest),
        "contradictions": [{"id": "CON-01", "statement": "好材料なのに指数反応は限定的だった", "rank": 1, "selection_reason": "中心矛盾"}],
        "research_questions": [{"id": "Q-01", "perspective": "timeline", "question": "なぜ反応が限定的か", "status": "answered", "answer_summary": "複数要因", "evidence_ids": ["E-001", "E-002", "E-003"]}],
        "evidence": [evidence("E-001", "会社材料は強かった"), evidence("E-002", "NASDAQは小幅高だった"), evidence("E-003", "反対材料が残った")],
        "memory_revalidation": [],
        "expected_actual_gap": {
            "expected": {"status": "confirmed", "basis_class": "official_consensus", "statement": "市場予想", "evidence_ids": ["E-001"]},
            "actual": {"statement": "実績は予想を上回った", "evidence_ids": ["E-001"]},
            "gap": {"statement": "上振れ", "market_meaning": "好材料だが指数全体への波及は限定", "confidence": "medium"},
        },
        "timeline": [{"id": "T-01", "timestamp_or_window": "16:00", "timezone": "America/New_York", "event": "発表", "precision": "minute", "evidence_ids": ["E-001"]}],
        "causal_edges": [{"id": "EDGE-01", "from_node": "company", "to_node": "nasdaq", "mechanism": "支援材料", "evidence_ids": ["E-002"], "timing_alignment": "partial", "confidence": "medium", "strongest_alternative": "macro", "editorially_required": True, "scope": "nasdaq_wide"}],
        "factor_roles": {"primary_candidate": "company", "amplifiers": [], "offsetting": ["counter"], "unresolved": []},
        "alternative_hypotheses": [{"id": "ALT-01", "hypothesis": "マクロが相殺", "supporting_evidence_ids": ["E-003"], "weakening_evidence_ids": ["E-002"], "status": "credible"}],
        "contrary_evidence": [{"statement": "反対材料", "evidence_ids": ["E-003"], "effect_on_confidence": "material"}],
        "editorial_handoff": {
            "provisional_lead": "synthetic lead", "central_hypothesis": "強い会社材料と相殺要因の綱引き", "confidence": "medium",
            "company_direct_material": ["E-001"], "nasdaq_wide_material": ["E-002"],
            "causal_spine": "会社材料→支援→相殺→限定反応", "headline_beyond_discovery": "強い材料だけではNASDAQ全体を説明できない",
            "exclude_from_narration": [], "unresolved_questions": [], "next_validation_points": [], "memory_differences": [],
        },
        "validation": {"status": "pass", "errors": [], "warnings": []},
        "carryover_results": [],
        "cross_market_assessment": {"materiality": "not_material", "rationale": "今回は非主要", "evidence_ids": [], "alternatives": []},
        "validation_candidates": [], "visual_evidence_needs": [],
    }


def story_plan(dossier_ref: dict[str, str]) -> dict[str, Any]:
    angles = []
    for index, question in enumerate(("なぜ好材料だけで上がらない？", "何が相殺した？", "指数を見る軸は何？"), 1):
        angles.append({
            "id": f"angle-{index:02d}", "angle_type": "contradiction" if index == 1 else "comparison",
            "central_question": question,
            "story_spine": "会社材料→支援→相殺→限定反応" if index == 1 else f"別角度{index}",
            "opening_promise": "矛盾の正体を確認する" if index == 1 else f"約束{index}",
            "midpoint_turn_claim": "反対材料まで見ると説明が変わる" if index == 1 else f"転換{index}",
            "closing_reframe": "強い個別材料とNASDAQ全体の原因は分けて見る" if index == 1 else f"結論{index}",
            "causality_scope": "nasdaq_support", "confidence": "medium",
            "evidence_ids": ["E-001", "E-002"], "counterevidence_ids": ["E-003"],
            "risk": "単純化", "why_distinct": f"異なる問い{index}",
        })
    scenes = []
    for index in range(1, 10):
        if index == 9:
            before, meaning, after, cont, ev, conn = "理解済み", "", "理解済み", "", [], "closing"
        else:
            before = f"理解{index-1}"
            meaning = f"新しい意味{index}"
            after = f"理解{index}が深まる"
            cont = "次の確認が必要" if index <= 7 else ""
            ev = [["E-001"], ["E-003"], ["E-001"], ["E-001", "E-002"], ["E-002"], ["E-002"], ["E-003"], ["E-001", "E-002", "E-003"]][index-1]
            conn = ["opening", "but", "therefore", "therefore", "contrast", "therefore", "contrast", "callback"][index-1]
        scenes.append({
            "scene_id": f"scene-{index:02d}", "formal_role": ROLES[index-1], "story_role": STORY_ROLES[index-1],
            "viewer_belief_before": before, "new_evidence_ids": ev, "new_meaning": meaning,
            "viewer_belief_after": after, "continuation_reason": cont, "connector": conn,
        })
    return {
        "contract_version": "1.2.0", "episode_date": DATE, "created_at": CUTOFF, "producer": "chatgpt",
        "causal_dossier": dossier_ref, "central_contradiction_id": "CON-01", "central_contradiction": "好材料なのに指数反応は限定的だった",
        "central_question": angles[0]["central_question"], "headline_beyond_discovery": "強い材料だけではNASDAQ全体を説明できない",
        "naive_explanations": [{"id": "naive-01", "explanation": "好材料なら全部上がる", "status": "weakened", "evidence_ids": ["E-003"], "why": "反対材料がある"}],
        "angle_candidates": angles, "selected_angle_id": "angle-01", "story_spine": angles[0]["story_spine"],
        "opening_promise": angles[0]["opening_promise"],
        "midpoint_turn": {"scene_id": "scene-04", "claim": angles[0]["midpoint_turn_claim"], "evidence_ids": ["E-001", "E-002"], "what_changes": "個別材料だけから複合要因へ"},
        "closing_reframe": {"scene_id": "scene-08", "text": angles[0]["closing_reframe"]},
        "open_loops": [{"id": "loop-01", "open_scene": "scene-01", "question": "なぜ限定反応？", "promised_evidence_ids": ["E-003"], "close_scene": "scene-08", "resolution": "相殺要因を確認"}],
        "scenes": scenes,
        "temporal_usage": {"carryover_results": [], "cross_market": {"mode": "internal_only", "scene_id": None, "visual_need_ids": []}, "validation_obligations": []},
    }


def story_script(plan: dict[str, Any], plan_ref: dict[str, str], dossier_ref: dict[str, str]) -> dict[str, Any]:
    scenes = []
    for index, (role, planned) in enumerate(zip(ROLES, plan["scenes"], strict=True), 1):
        if index == 9:
            parts = [
                "僕からは以上、朝のNASDAQカフェでした。",
                "いってらっしゃい。おやすみなさい。",
            ]
            claims = []
        else:
            parts = [
                f"僕はScene {index}で市場を確認します。",
                "ここから市場の意味を確認します。",
            ]
            evid_for_claim = list(planned["new_evidence_ids"])
            claim_evidence = ["E-002"] if "E-002" in evid_for_claim else [evid_for_claim[0]]
            claims = [{
                "claim_id": f"claim-{index:02d}", "statement": f"Scene {index}の主張", "claim_type": "fact",
                "evidence_ids": claim_evidence, "confidence": "medium",
                "scope": "nasdaq_support" if "E-002" in claim_evidence else "company",
            }]
        evid = list(planned["new_evidence_ids"])
        scenes.append({
            "scene_id": f"scene-{index:02d}", "formal_role": role, "narration": "\n\n".join(parts),
            "connection_to_previous": planned["connector"],
            "evidence_ids": evid, "causal_claims": claims,
        })
    return {
        "contract_version": "1.0.0", "episode_date": DATE, "producer": "chatgpt",
        "story_plan": plan_ref, "causal_dossier": dossier_ref, "scenes": scenes,
        "retained_counterevidence_ids": ["E-003"], "unresolved_points": [],
    }


def creative_review() -> dict[str, Any]:
    checks = []
    for index in range(1, 9):
        checks.append({
            "scene_id": f"scene-{index:02d}", "mode": "close" if index == 8 else "continue",
            "payoff_delivered": True, "belief_changed": True,
            "continuation_reason_natural": None if index == 8 else True,
            "closure_effective": True if index == 8 else None,
            "opening_promise_recovered": True if index == 8 else None,
            "procedural_language_dominant": False,
        })
    return {
        "contract_version": "1.1.0", "episode_date": DATE, "round": 1, "reviewer": "editorial_critic",
        "scores": {"opening": 5, "progression": 5, "discovery": 5, "clarity": 5, "fox_voice": 5, "late_payoff": 5},
        "total_score": 30, "scene_checks": checks, "findings": [], "immediate_failures": [], "verdict": "pass",
    }


def production(script: dict[str, Any]) -> dict[str, Any]:
    scenes = []
    for index, scripted in enumerate(script["scenes"], 1):
        parts = scripted["narration"].split("\n\n")
        if len(parts) != 2 or any(not part for part in parts):
            raise ValueError(f"scene-{index:02d}: synthetic Current narration must contain exactly two paragraphs")
        chunks = [{"text": part, "expression": "分析"} for part in parts]
        beats = []
        for beat_index in (1, 2):
            visual_template = "opening-contradiction"
            beats.append({
                "primaryFunction": "Explain", "screenState": f"scene-{index:02d}-state-{beat_index}",
                "visualMode": "text-focus", "visualTemplate": visual_template, "contentType": "text",
                "screenQuestion": f"Scene {index} question {beat_index}", "primaryElement": f"Scene {index} element",
                "viewerTexts": [f"Scene {index} text {beat_index}"], "changeCue": "next",
                "grammarId": current_grammar_id(visual_template), "transitionRole": "continuation", "evidenceSourceIds": scripted["evidence_ids"],
                "metrics": [], "nodes": [], "edges": [],
            })
        scenes.append({
            "sceneRole": ROLES[index-1], "formalName": f"Scene {index}", "purpose": f"purpose {index}",
            "causalScope": "multiple", "performanceIntent": "落ち着いて確認", "evidenceSourceIds": scripted["evidence_ids"],
            "uncertainty": "synthetic", "timelineBasis": "synthetic", "expectedBasisType": "official_consensus",
            "visualMode": "text-focus", "initialExpression": "分析", "headline": f"Scene {index}",
            "supportingTexts": [f"support {index}"], "sourceLabel": "Synthetic", "chunks": chunks, "beats": beats,
        })
    return {
        "episodeType": "single-news",
        "sources": [{
            "sourceId": "source-001",
            "title": "Synthetic Current source",
            "publisher": "Synthetic IR",
            "sourceType": "official",
            "reference": "synthetic://source-001",
            "publishedAt": None,
            "accessedAt": CUTOFF,
            "usedFor": ["synthetic Current machinery qualification"],
            "narrationAttribution": "Synthetic IR",
        }],
        "pronunciations": [], "corrections": [], "visualSourceIntents": [], "visualSourceSelection": None,
        "financialBindings": [], "scenes": scenes,
    }


def canonical_authoring(root: Path, dossier_path: Path) -> dict[str, Any]:
    dossier_ref = file_ref(root, dossier_path)
    plan = story_plan(dossier_ref)
    plan_ref = {"path": f"working/{DATE}/story-engine/story_plan.json", "sha256": sha_bytes(canonical_projection_bytes(plan))}
    script = story_script(plan, plan_ref, dossier_ref)
    return {
        "contractVersion": "2.0.0", "episodeDate": DATE, "marketDate": MARKET_DATE, "informationCutoff": CUTOFF,
        "durationMode": "standard", "shortenedReason": None,
        "causalDossier": {**dossier_ref, "validation": {"path": f"research/{DATE}/causal_dossier_validation.json", "sha256": "0" * 64}},
        "storyPlan": plan, "storyScript": script, "creativeReview": creative_review(),
        "publishing": {"titleCandidates": ["Synthetic title"], "thumbnailTextCandidates": ["Synthetic thumb"], "description": "Synthetic description"},
        "production": production(script),
    }
