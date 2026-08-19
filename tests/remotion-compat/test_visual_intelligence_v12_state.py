#!/usr/bin/env python3
"""Unit acceptance for v1.2 state ordering and semantic hard-gate preservation."""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import run_daily_production_v12 as v12  # noqa: E402
import run_daily_renderer_closure_v12 as closure_v12  # noqa: E402
import visual_source_checkpoint_v12  # noqa: E402


class FakeDailyProductionError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class FakeModule:
    DailyProductionError = FakeDailyProductionError
    ERROR_CODES = {
        "stale": "E_STALE_INPUT",
        "episode": "E_EPISODE_NOT_FINAL",
        "package": "E_PACKAGE_MISMATCH",
        "render": "E_RENDER_SPEC_INVALID",
        "date": "E_DATE_MISMATCH",
        "inquisition": "E_INQUISITION_UNRESOLVED",
    }

    @staticmethod
    def load_json(path: Path, label: str):
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise FakeDailyProductionError("E_STALE_INPUT", f"{label} must be object")
        return value

    @staticmethod
    def sha256_file(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def expect_error(code: str, fn) -> None:
    try:
        fn()
    except FakeDailyProductionError as exc:
        if exc.code != code:
            raise AssertionError(f"expected {code}, got {exc.code}: {exc}") from exc
    else:
        raise AssertionError(f"expected {code}")


def test_post_pass_b_visual_source_authoring_is_preserved() -> None:
    date = "2099-03-04"
    with tempfile.TemporaryDirectory(prefix="nasdaq-v12-source-authoring-") as temp:
        root = Path(temp)
        work = root / "working" / date
        vi = work / "visual-intelligence"
        write(
            vi / "visual_requirements.json",
            {
                "contractVersion": "1.0.0",
                "episodeDate": date,
                "intent": {"beats": []},
                "provisionalDirection": {"requirements": []},
            },
        )
        intent_path = write(
            work / "visual_source_intents.json",
            {
                "contractVersion": "1.0.0",
                "episodeDate": date,
                "intents": [{"intentId": "chatgpt-authored-source-plan"}],
            },
        )
        selection_path = write(
            work / "visual_source_selection.json",
            {
                "contractVersion": "1.0.0",
                "episodeDate": date,
                "selectedPath": "primary",
            },
        )
        expected_intents = intent_path.read_bytes()
        expected_selection = selection_path.read_bytes()
        result = visual_source_checkpoint_v12.materialize(
            work=work,
            date=date,
            projected={
                "visualSourceIntents": [],
                "visualSourceSelection": {
                    "contractVersion": "1.0.0",
                    "episodeDate": date,
                    "selectedPath": "fallback",
                },
            },
        )
        if result != "preserved":
            raise AssertionError("sealed Visual Source checkpoint was not preserved")
        if intent_path.read_bytes() != expected_intents:
            raise AssertionError("sealed Visual Source intents changed")
        if selection_path.read_bytes() != expected_selection:
            raise AssertionError("sealed Visual Source selection changed")


def test_pre_pass_b_materialization_remains_authoritative() -> None:
    date = "2099-03-05"
    with tempfile.TemporaryDirectory(prefix="nasdaq-v12-source-seed-") as temp:
        root = Path(temp)
        work = root / "working" / date
        result = visual_source_checkpoint_v12.materialize(
            work=work,
            date=date,
            projected={
                "visualSourceIntents": [{"intentId": "pre-pass-b-seed"}],
                "visualSourceSelection": None,
            },
        )
        if result != "seeded":
            raise AssertionError("pre-Requirements Visual Source was not seeded")
        value = json.loads((work / "visual_source_intents.json").read_text(encoding="utf-8"))
        if value.get("intents") != [{"intentId": "pre-pass-b-seed"}]:
            raise AssertionError("pre-Requirements Visual Source seed drifted")


def test_semantic_pause_carries_required_action() -> None:
    pause = closure_v12.VisualIntelligenceDecisionRequired(
        "selection needed",
        required_action="AUTHOR_VISUAL_SOURCE_SELECTION",
    )
    if pause.required_action != "AUTHOR_VISUAL_SOURCE_SELECTION":
        raise AssertionError("semantic pause lost required action")
    if pause.include_candidate_catalog:
        raise AssertionError("pre-asset semantic pause must not claim Candidate Catalog exists")


def main() -> int:
    expected_prefix = [
        "research_inputs_bound",
        "causal_dossier_valid",
        "editorial_snapshot_valid",
        "visual_requirements_planned",
        "assets_resolved",
        "visual_intelligence_valid",
        "episode_package_final",
        "memory_usage_valid",
    ]
    if v12.VI_STATES[1:9] != expected_prefix:
        raise AssertionError(f"v1.2 state order drifted: {v12.VI_STATES[1:9]}")

    test_post_pass_b_visual_source_authoring_is_preserved()
    test_pre_pass_b_materialization_remains_authoritative()
    test_semantic_pause_carries_required_action()

    module = FakeModule()
    date = "2099-03-03"
    with tempfile.TemporaryDirectory(prefix="nasdaq-v12-state-") as temp:
        root = Path(temp)
        work = root / "working" / date
        vi = work / "visual-intelligence"
        snapshot = write(
            vi / "editorial_snapshot.json",
            {"contractVersion": "1.0.0", "episodeDate": date},
        )
        snapshot_sha = module.sha256_file(snapshot)

        # The current-v1.2 editorial snapshot gate is intentionally semantic-frozen.
        # Prove that the old snapshot-only fixture now fails closed, then provide the
        # explicit synthetic Acceptance / Freeze / WS-4 lineage required by production.
        expect_error(
            "E_STALE_INPUT",
            lambda: v12._validate_vi_transition(
                module=module,
                workspace=root,
                date=date,
                new_state="editorial_snapshot_valid",
                evidence_paths=[snapshot],
            ),
        )

        acceptance = write(
            root / "verification" / date / "editorial_semantic_acceptance.json",
            {"status": "PASS", "episodeDate": date},
        )
        authoring_sha = "a" * 64
        projection = write(
            work / "story-engine" / "story_projection_report.json",
            {
                "status": "pass",
                "episode_date": date,
                "source_daily_authoring_sha256": authoring_sha,
            },
        )
        freeze_path = write(
            root / "semantic-freezes" / f"{date}.json",
            {"contractVersion": "1.2.0", "episodeDate": date},
        )
        acceptance_sha = module.sha256_file(acceptance)

        class AcceptanceModule:
            @staticmethod
            def verify_acceptance(*args, **kwargs):
                return {"status": "PASS", "episodeDate": date}

        class FreezeModule:
            @staticmethod
            def verify_manifest(*args, **kwargs):
                return {
                    "contractVersion": "1.2.0",
                    "episodeDate": date,
                    "editorialSemanticAcceptance": {"sha256": acceptance_sha},
                    "canonicalAuthoring": {"sha256": authoring_sha},
                }

        original_loader = v12.current_mechanisms.load_external_module

        def semantic_loader(name, path):
            if path.name == "validate_editorial_semantic_boundary.py":
                return AcceptanceModule
            if path.name == "chatgpt_semantic_freeze.py":
                return FreezeModule
            return original_loader(name, path)

        v12.current_mechanisms.load_external_module = semantic_loader
        try:
            v12._validate_vi_transition(
                module=module,
                workspace=root,
                date=date,
                new_state="editorial_snapshot_valid",
                evidence_paths=[snapshot, acceptance, projection, freeze_path],
            )
        finally:
            v12.current_mechanisms.load_external_module = original_loader

        requirements = write(
            vi / "visual_requirements.json",
            {
                "contractVersion": "1.0.0",
                "bridgeContractVersion": "visual-intelligence-bridge/1.2.0",
                "episodeDate": date,
                "editorialSnapshotSha256": snapshot_sha,
                "intent": {"beats": []},
                "provisionalDirection": {"requirements": []},
            },
        )
        requirements_report = write(
            vi / "visual_requirements_validation.json",
            {
                "status": "PASS",
                "episodeDate": date,
                "beatCount": 0,
                "editorialSnapshotSha256": snapshot_sha,
            },
        )
        v12._validate_vi_transition(
            module=module,
            workspace=root,
            date=date,
            new_state="visual_requirements_planned",
            evidence_paths=[requirements, requirements_report],
        )

        package = write(
            vi / "visual_intelligence_package.json",
            {
                "contractVersion": "1.0.0",
                "bridgeContractVersion": "visual-intelligence-bridge/1.2.0",
                "episodeDate": date,
                "inputs": {"editorialSnapshotSha256": snapshot_sha},
                "final": {"status": "PASS"},
            },
        )
        validation = write(
            vi / "visual_intelligence_validation.json",
            {
                "status": "PASS",
                "episodeDate": date,
                "packageSha256": module.sha256_file(package),
            },
        )
        v12._validate_vi_transition(
            module=module,
            workspace=root,
            date=date,
            new_state="visual_intelligence_valid",
            evidence_paths=[package, validation],
        )

        write(snapshot, {"contractVersion": "1.0.0", "episodeDate": date, "storyRevision": 2})
        expect_error(
            "E_STALE_INPUT",
            lambda: v12._validate_vi_transition(
                module=module,
                workspace=root,
                date=date,
                new_state="visual_requirements_planned",
                evidence_paths=[requirements, requirements_report],
            ),
        )
        expect_error(
            "E_STALE_INPUT",
            lambda: v12._validate_vi_transition(
                module=module,
                workspace=root,
                date=date,
                new_state="visual_intelligence_valid",
                evidence_paths=[package, validation],
            ),
        )

        # Recreate a matching snapshot for the Story-final hard-gate check.
        write(snapshot, {"contractVersion": "1.0.0", "episodeDate": date})
        story_acceptance = write(
            work / "story-engine" / "story_engine_acceptance.json",
            {"status": "pass"},
        )
        episode_package = write(
            root / "episodes" / date / f"episode_package_{date}.md",
            "# synthetic\n",
        )
        story_projection = write(
            work / "story-engine" / "story_projection_report.json",
            {"episode_date": date, "status": "pass"},
        )
        pre_tts = write(
            root / "verification" / date / "pre_tts_visual_gate.json",
            {"episodeDate": date, "status": "PASS", "violations": []},
        )

        class StoryAcceptanceValidator:
            @staticmethod
            def validate_acceptance(*args, **kwargs):
                return {"status": "pass", "errors": []}

        original_loader = v12.current_mechanisms.load_external_module
        v12.current_mechanisms.load_external_module = lambda *args, **kwargs: StoryAcceptanceValidator
        try:
            v12._validate_story_final_gate(
                module=module,
                workspace=root,
                date=date,
                evidence_paths=[story_acceptance, episode_package, story_projection, pre_tts],
            )
            write(
                pre_tts,
                {"episodeDate": date, "status": "PASS", "violations": ["synthetic"]},
            )
            expect_error(
                "E_RENDER_SPEC_INVALID",
                lambda: v12._validate_story_final_gate(
                    module=module,
                    workspace=root,
                    date=date,
                    evidence_paths=[story_acceptance, episode_package, story_projection, pre_tts],
                ),
            )
        finally:
            v12.current_mechanisms.load_external_module = original_loader

    print("visual intelligence v1.2 state tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
