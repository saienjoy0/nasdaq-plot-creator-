#!/usr/bin/env python3
"""Validate the editorial Visual Grammar 1.0.0 contract.

The validator checks explicit Beat-level editorial decisions. It never chooses a
Visual Grammar from a scene number, text, metric sign, or item count. Structural
integrity is a hard failure. Editorial variety and preferred visual composition are
machine-readable warnings for ChatGPT/editorial review and never block production.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

EXPECTED_GRAMMARS = {
    "contradiction", "entity", "evidence", "gap", "causal", "reaction",
    "comparison", "verification", "analogy", "assembly", "bridge-text",
}
EXPECTED_TRANSITIONS = {"continuation", "major-shift", "return", "closing"}


class VisualGrammarError(ValueError):
    """Raised when Visual Grammar declarations are invalid."""


@dataclass(frozen=True)
class BeatRef:
    scene_index: int
    scene_id: str
    beat_index: int
    beat_id: str
    grammar_id: str
    transition_role: str
    return_target_beat_id: str | None

    @property
    def path(self) -> str:
        return f"$.scenes[{self.scene_index}].visualBeats[{self.beat_index}]"


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VisualGrammarError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise VisualGrammarError(
            f"invalid JSON at {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise VisualGrammarError(f"JSON root must be an object: {path}")
    return value


def _json_path(error: Any) -> str:
    path = "$"
    for part in error.path:
        path += f"[{part}]" if isinstance(part, int) else f".{part}"
    return path


def validate_registry(registry: dict[str, Any], schema: dict[str, Any]) -> None:
    errors = sorted(
        Draft202012Validator(schema).iter_errors(registry),
        key=lambda error: list(error.path),
    )
    if errors:
        raise VisualGrammarError(
            "\n".join(f"{_json_path(error)}: {error.message}" for error in errors)
        )

    grammar_ids = [item["grammarId"] for item in registry["grammars"]]
    if len(grammar_ids) != len(set(grammar_ids)):
        raise VisualGrammarError("$.grammars: grammarId values must be unique")
    if set(grammar_ids) != EXPECTED_GRAMMARS:
        raise VisualGrammarError(
            "$.grammars: grammar set mismatch: "
            f"missing={sorted(EXPECTED_GRAMMARS - set(grammar_ids))} "
            f"extra={sorted(set(grammar_ids) - EXPECTED_GRAMMARS)}"
        )
    transitions = set(registry["transitionRoles"])
    if transitions != EXPECTED_TRANSITIONS:
        raise VisualGrammarError(
            "$.transitionRoles: transition set mismatch: "
            f"missing={sorted(EXPECTED_TRANSITIONS - transitions)} "
            f"extra={sorted(transitions - EXPECTED_TRANSITIONS)}"
        )
    counted = {grammar["grammarId"]: grammar["counted"] for grammar in registry["grammars"]}
    if counted["assembly"] or counted["bridge-text"]:
        raise VisualGrammarError(
            "assembly and bridge-text must not count toward Scene 1-8 diversity"
        )
    if any(
        not counted[grammar_id]
        for grammar_id in EXPECTED_GRAMMARS - {"assembly", "bridge-text"}
    ):
        raise VisualGrammarError(
            "all analytical grammars must count toward Scene 1-8 diversity"
        )


def _finding(
    findings: list[dict[str, str]], code: str, path: str, message: str
) -> None:
    findings.append({"code": code, "path": path, "message": message})


def _violation(
    violations: list[dict[str, str]], code: str, path: str, message: str
) -> None:
    _finding(violations, code, path, message)


def _warning(
    warnings: list[dict[str, str]], code: str, path: str, message: str
) -> None:
    _finding(warnings, code, path, message)


def _collect_beats(
    episode: dict[str, Any], violations: list[dict[str, str]]
) -> list[BeatRef]:
    scenes = episode.get("scenes")
    if not isinstance(scenes, list):
        _violation(
            violations, "VG_SCENES_INVALID", "$.scenes", "scenes must be an array"
        )
        return []

    beats: list[BeatRef] = []
    seen_scene_ids: set[str] = set()
    seen_beat_ids: set[str] = set()
    for scene_index, scene in enumerate(scenes):
        scene_path = f"$.scenes[{scene_index}]"
        if not isinstance(scene, dict):
            _violation(
                violations, "VG_SCENE_INVALID", scene_path, "scene must be an object"
            )
            continue
        scene_id = scene.get("sceneId")
        expected_scene_id = f"scene-{scene_index + 1:02d}"
        if scene_id != expected_scene_id:
            _violation(
                violations,
                "VG_SCENE_ORDER_INVALID",
                f"{scene_path}.sceneId",
                f"expected {expected_scene_id}",
            )
        if scene_id in seen_scene_ids:
            _violation(
                violations,
                "VG_SCENE_DUPLICATE",
                f"{scene_path}.sceneId",
                f"duplicate sceneId: {scene_id}",
            )
        seen_scene_ids.add(str(scene_id))
        visual_beats = scene.get("visualBeats")
        if not isinstance(visual_beats, list) or not visual_beats:
            _violation(
                violations,
                "VG_BEATS_INVALID",
                f"{scene_path}.visualBeats",
                "visualBeats must be a non-empty array",
            )
            continue
        for beat_index, beat in enumerate(visual_beats):
            beat_path = f"{scene_path}.visualBeats[{beat_index}]"
            if not isinstance(beat, dict):
                _violation(
                    violations, "VG_BEAT_INVALID", beat_path, "beat must be an object"
                )
                continue
            beat_id = beat.get("visualBeatId")
            if not isinstance(beat_id, str) or not beat_id:
                _violation(
                    violations,
                    "VG_BEAT_ID_INVALID",
                    f"{beat_path}.visualBeatId",
                    "visualBeatId is required",
                )
                continue
            if beat_id in seen_beat_ids:
                _violation(
                    violations,
                    "VG_BEAT_ID_DUPLICATE",
                    f"{beat_path}.visualBeatId",
                    f"duplicate visualBeatId: {beat_id}",
                )
            seen_beat_ids.add(beat_id)
            visual_grammar = beat.get("visualGrammar")
            if not isinstance(visual_grammar, dict):
                _violation(
                    violations,
                    "VG_DECLARATION_MISSING",
                    f"{beat_path}.visualGrammar",
                    "visualGrammar is required for every Beat",
                )
                continue
            contract_version = visual_grammar.get("contractVersion")
            grammar_id = visual_grammar.get("grammarId")
            transition_role = visual_grammar.get("transitionRole")
            return_target = visual_grammar.get("returnTargetBeatId")
            if contract_version != "1.0.0":
                _violation(
                    violations,
                    "VG_VERSION_MISMATCH",
                    f"{beat_path}.visualGrammar.contractVersion",
                    "must equal 1.0.0",
                )
            if grammar_id not in EXPECTED_GRAMMARS:
                _violation(
                    violations,
                    "VG_UNKNOWN_GRAMMAR",
                    f"{beat_path}.visualGrammar.grammarId",
                    f"unknown grammarId: {grammar_id}",
                )
                continue
            if transition_role not in EXPECTED_TRANSITIONS:
                _violation(
                    violations,
                    "VG_UNKNOWN_TRANSITION",
                    f"{beat_path}.visualGrammar.transitionRole",
                    f"unknown transitionRole: {transition_role}",
                )
                continue
            if transition_role == "return":
                if not isinstance(return_target, str) or not return_target:
                    _violation(
                        violations,
                        "VG_RETURN_TARGET_MISSING",
                        f"{beat_path}.visualGrammar.returnTargetBeatId",
                        "return requires returnTargetBeatId",
                    )
            elif return_target is not None:
                _violation(
                    violations,
                    "VG_RETURN_TARGET_UNEXPECTED",
                    f"{beat_path}.visualGrammar.returnTargetBeatId",
                    "only return may declare returnTargetBeatId",
                )
            beats.append(
                BeatRef(
                    scene_index,
                    str(scene_id),
                    beat_index,
                    beat_id,
                    grammar_id,
                    transition_role,
                    return_target,
                )
            )
    return beats


def validate_episode(
    episode: dict[str, Any], registry: dict[str, Any]
) -> dict[str, Any]:
    violations: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    if episode.get("visualGrammarContractVersion") != "1.0.0":
        _violation(
            violations,
            "VG_ROOT_VERSION_MISMATCH",
            "$.visualGrammarContractVersion",
            "must equal 1.0.0",
        )
    episode_date = episode.get("episodeDate")
    if not isinstance(episode_date, str):
        _violation(
            violations,
            "VG_EPISODE_DATE_MISSING",
            "$.episodeDate",
            "episodeDate is required",
        )
        episode_date = "0000-00-00"

    beats = _collect_beats(episode, violations)
    by_id = {beat.beat_id: beat for beat in beats}
    for beat in beats:
        if beat.transition_role == "return" and beat.return_target_beat_id not in by_id:
            _violation(
                violations,
                "VG_RETURN_TARGET_UNKNOWN",
                f"{beat.path}.visualGrammar.returnTargetBeatId",
                f"unknown Beat: {beat.return_target_beat_id}",
            )

    scene_1_8 = [beat for beat in beats if 0 <= beat.scene_index <= 7]
    front = [beat for beat in beats if 0 <= beat.scene_index <= 3]
    back = [beat for beat in beats if 4 <= beat.scene_index <= 7]
    counted_map = {
        grammar["grammarId"]: grammar["counted"] for grammar in registry["grammars"]
    }
    counted = {beat.grammar_id for beat in scene_1_8 if counted_map[beat.grammar_id]}
    front_counted = {beat.grammar_id for beat in front if counted_map[beat.grammar_id]}
    back_counted = {beat.grammar_id for beat in back if counted_map[beat.grammar_id]}

    if len(counted) < 6:
        _warning(
            warnings,
            "VG_GRAMMAR_COUNT_TOO_LOW",
            "$.scenes[0:8]",
            f"editorial target is at least 6 counted grammars; found={len(counted)}",
        )
    if len(front_counted) < 3:
        _warning(
            warnings,
            "VG_FRONT_HALF_GRAMMAR_COUNT_TOO_LOW",
            "$.scenes[0:4]",
            f"editorial target is at least 3 counted grammars; found={len(front_counted)}",
        )
    if len(back_counted) < 3:
        _warning(
            warnings,
            "VG_BACK_HALF_GRAMMAR_COUNT_TOO_LOW",
            "$.scenes[4:8]",
            f"editorial target is at least 3 counted grammars; found={len(back_counted)}",
        )

    major = [beat for beat in scene_1_8 if beat.transition_role == "major-shift"]
    front_major = [beat for beat in front if beat.transition_role == "major-shift"]
    back_major = [beat for beat in back if beat.transition_role == "major-shift"]
    if len(major) < 4:
        _warning(
            warnings,
            "VG_MAJOR_SHIFT_COUNT_TOO_LOW",
            "$.scenes[0:8]",
            f"editorial target is at least 4 major shifts; found={len(major)}",
        )
    if not front_major:
        _warning(
            warnings,
            "VG_FRONT_HALF_MAJOR_SHIFT_MISSING",
            "$.scenes[0:4]",
            "editorial target is at least one major shift",
        )
    if not back_major:
        _warning(
            warnings,
            "VG_BACK_HALF_MAJOR_SHIFT_MISSING",
            "$.scenes[4:8]",
            "editorial target is at least one major shift",
        )

    bridge_beats = [beat for beat in beats if beat.grammar_id == "bridge-text"]
    if len(bridge_beats) > 2:
        _warning(
            warnings,
            "VG_BRIDGE_TEXT_OVERUSED",
            "$.scenes",
            f"editorial target is at most 2 bridge-text beats; found={len(bridge_beats)}",
        )
    ordered = sorted(beats, key=lambda beat: (beat.scene_index, beat.beat_index))
    for previous, current in zip(ordered, ordered[1:]):
        if previous.grammar_id == current.grammar_id == "bridge-text":
            _warning(
                warnings,
                "VG_BRIDGE_TEXT_CONSECUTIVE",
                current.path,
                "consecutive bridge-text beats reduce visual progression",
            )

    grammar_by_scene: dict[int, set[str]] = {}
    for beat in beats:
        grammar_by_scene.setdefault(beat.scene_index + 1, set()).add(beat.grammar_id)
    preferred_scene_grammar = {
        1: "contradiction",
        6: "reaction",
        7: "comparison",
        8: "verification",
        9: "assembly",
    }
    for scene_number, grammar_id in preferred_scene_grammar.items():
        if grammar_id not in grammar_by_scene.get(scene_number, set()):
            _warning(
                warnings,
                "VG_REQUIRED_SCENE_GRAMMAR_MISSING",
                f"$.scenes[{scene_number - 1}]",
                f"editorial preference: Scene {scene_number} uses {grammar_id}",
            )
    if (
        "causal" not in grammar_by_scene.get(5, set())
        and not episode.get("scene5CausalExceptionReason")
    ):
        _warning(
            warnings,
            "VG_SCENE5_CAUSAL_MISSING",
            "$.scenes[4]",
            "editorial preference: Scene 5 uses causal or records an exception reason",
        )
    expected_confirmed = episode.get("expectedConfirmed")
    if expected_confirmed is True and "gap" not in grammar_by_scene.get(4, set()):
        _warning(
            warnings,
            "VG_SCENE4_GAP_MISSING",
            "$.scenes[3]",
            "editorial preference: Expected-confirmed episodes visualize the gap in Scene 4",
        )

    violations.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    warnings.sort(key=lambda item: (item["path"], item["code"], item["message"]))
    return {
        "reportVersion": "1.0.0",
        "visualGrammarContractVersion": "1.0.0",
        "status": "PASS" if not violations else "FAIL",
        "episodeDate": episode_date,
        "beatCount": len(beats),
        "scene1To8BeatCount": len(scene_1_8),
        "semanticGrammarCount": len(counted),
        "frontHalfGrammarCount": len(front_counted),
        "backHalfGrammarCount": len(back_counted),
        "majorShiftCount": len(major),
        "frontHalfMajorShiftCount": len(front_major),
        "backHalfMajorShiftCount": len(back_major),
        "bridgeTextBeatCount": len(bridge_beats),
        "violations": violations,
        "warnings": warnings,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("episode_contract", type=Path)
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("contracts/visual_grammar_semantics.json"),
    )
    parser.add_argument(
        "--registry-schema",
        type=Path,
        default=Path("contracts/visual_grammar_semantics.schema.json"),
    )
    parser.add_argument(
        "--report-schema",
        type=Path,
        default=Path("contracts/visual_grammar_structural_report.schema.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        registry = load_json(args.registry)
        validate_registry(registry, load_json(args.registry_schema))
        report = validate_episode(load_json(args.episode_contract), registry)
        report_errors = sorted(
            Draft202012Validator(load_json(args.report_schema)).iter_errors(report),
            key=lambda error: list(error.path),
        )
        if report_errors:
            raise VisualGrammarError(
                "\n".join(
                    f"{_json_path(error)}: {error.message}" for error in report_errors
                )
            )
    except VisualGrammarError as exc:
        print(
            json.dumps(
                {"status": "FAIL", "errors": str(exc).splitlines()},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
