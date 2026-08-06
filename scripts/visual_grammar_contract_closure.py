#!/usr/bin/env python3
"""Verify Final Episode Contract Visual Grammar against a render_spec 2.4.0.

The check is deterministic and compares explicit Beat IDs. It never infers a
Grammar or Template from scene number, narration, metrics, or renderer output.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class VisualGrammarClosureError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise VisualGrammarClosureError(f"file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise VisualGrammarClosureError(
            f"invalid JSON at {path}:{exc.lineno}:{exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(value, dict):
        raise VisualGrammarClosureError(f"JSON root must be an object: {path}")
    return value


def final_contract_grammar_map(
    final_contract: dict[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:
    if final_contract.get("contractVersion") != "1.1.0":
        raise VisualGrammarClosureError("Final Episode Contract must be 1.1.0")
    if final_contract.get("visualGrammarContractVersion") != "1.0.0":
        raise VisualGrammarClosureError(
            "Final Episode Contract visualGrammarContractVersion must be 1.0.0"
        )
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for scene in final_contract.get("scenes", []):
        scene_id = scene.get("sceneId")
        for beat in scene.get("visualBeats", []):
            beat_id = beat.get("visualBeatId")
            grammar = beat.get("visualGrammar")
            key = (scene_id, beat_id)
            if key in result:
                raise VisualGrammarClosureError(f"duplicate Final Contract Beat: {key}")
            if not isinstance(grammar, dict):
                raise VisualGrammarClosureError(
                    f"Final Contract Beat {key} is missing visualGrammar"
                )
            result[key] = grammar
    return result


def render_spec_grammar_map(
    render_spec: dict[str, Any],
) -> dict[tuple[str, str], dict[str, Any]]:
    if render_spec.get("schemaVersion") != "2.4.0":
        raise VisualGrammarClosureError("render_spec must be 2.4.0")
    root = render_spec.get("visualGrammarContract")
    if not isinstance(root, dict) or root.get("contractVersion") != "1.0.0":
        raise VisualGrammarClosureError(
            "render_spec visualGrammarContract 1.0.0 is required"
        )
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for scene in render_spec.get("scenes", []):
        scene_id = scene.get("sceneId")
        for beat in scene.get("visualBeats", []):
            beat_id = beat.get("beatId")
            key = (scene_id, beat_id)
            if key in result:
                raise VisualGrammarClosureError(f"duplicate render_spec Beat: {key}")
            result[key] = {
                "contractVersion": "1.0.0",
                "grammarId": beat.get("visualGrammarId"),
                "transitionRole": beat.get("transitionRole"),
                "returnTargetBeatId": beat.get("returnTargetBeatId"),
            }
    return result


def validate_final_contract_against_render(
    final_contract: dict[str, Any], render_spec: dict[str, Any]
) -> dict[str, Any]:
    final_map = final_contract_grammar_map(final_contract)
    render_map = render_spec_grammar_map(render_spec)
    if set(final_map) != set(render_map):
        raise VisualGrammarClosureError(
            "Visual Beat set mismatch: "
            f"missing_in_render={sorted(set(final_map) - set(render_map))} "
            f"extra_in_render={sorted(set(render_map) - set(final_map))}"
        )
    mismatches: list[str] = []
    for key in sorted(final_map):
        expected = final_map[key]
        actual = render_map[key]
        if expected != actual:
            mismatches.append(f"{key}: final={expected!r} render={actual!r}")
    if mismatches:
        raise VisualGrammarClosureError(
            "Final Episode Contract and render_spec Visual Grammar mismatch:\n"
            + "\n".join(mismatches)
        )
    episode_date = final_contract.get("episodeDate")
    render_date = render_spec.get("episode", {}).get("id")
    if episode_date != render_date:
        raise VisualGrammarClosureError(
            f"episode date mismatch: final={episode_date!r} render={render_date!r}"
        )
    return {
        "status": "PASS",
        "finalEpisodeContractVersion": "1.1.0",
        "visualGrammarContractVersion": "1.0.0",
        "renderSpecVersion": "2.4.0",
        "episodeDate": episode_date,
        "visualBeatCount": len(final_map),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--final-episode-contract", type=Path, required=True)
    parser.add_argument("--render-spec", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = validate_final_contract_against_render(
            load_json(args.final_episode_contract), load_json(args.render_spec)
        )
    except VisualGrammarClosureError as exc:
        print(
            json.dumps(
                {"status": "FAIL", "errors": str(exc).splitlines()},
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
