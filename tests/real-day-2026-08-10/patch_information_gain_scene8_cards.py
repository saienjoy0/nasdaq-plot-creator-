#!/usr/bin/env python3
"""Give revised H5 Scene 8 explicit verification cards required by Renderer 2.4.

H5-only acceptance helper. It adds no evidence and changes no narration or causal
meaning. It converts already-authored Scene 8 viewer text into explicit card objects
so the official renderer can draw verification-matrix / verification-checklist.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

DATE = "2026-08-10"
RESERVED_PREFIX = "scene-08-h5-"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be object: {path}")
    return value


def dump(path: Path, value: dict[str, Any]) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def card(card_id: str, title: str, value: str, tone: str) -> dict[str, Any]:
    return {
        "cardId": card_id,
        "role": None,
        "title": title,
        "lines": [{"label": title, "value": value, "tone": tone}],
    }


def apply(root: Path) -> dict[str, Any]:
    render_path = root / f"render-specs/{DATE}/render_spec.json"
    render = load(render_path)
    scene = next(row for row in render.get("scenes", []) if row.get("sceneNumber") == 8)
    beats = scene.get("visualBeats", [])
    if len(beats) < 2:
        raise SystemExit("Scene 8 requires two revised verification Beats")
    first, second = beats[:2]
    if first.get("visualTemplate") != "verification-matrix":
        raise SystemExit("Scene 8 Beat 1 must already be verification-matrix")
    if second.get("visualTemplate") != "verification-checklist":
        raise SystemExit("Scene 8 Beat 2 must already be verification-checklist")

    first_ids = [
        "scene-08-h5-strengthen-macro",
        "scene-08-h5-strengthen-reaction",
        "scene-08-h5-weaken-boundary",
        "scene-08-h5-weaken-counter",
    ]
    second_ids = [
        "scene-08-h5-path-macro",
        "scene-08-h5-path-company",
        "scene-08-h5-summary-amplifier",
        "scene-08-h5-summary-conclusion",
    ]
    rows = [
        card(first_ids[0], "強める1", "雇用下振れ→利上げ観測後退", "positive"),
        card(first_ids[1], "強める2", "QQQ・SOXX・NVIDIA初動↑", "positive"),
        card(first_ids[2], "弱める1", "1分足だけでは因果証明できない", "warning"),
        card(first_ids[3], "弱める2", "成長不安・AMD/Alphabet下落", "warning"),
        card(second_ids[0], "経路1", "雇用→利上げ観測後退", "positive"),
        card(second_ids[1], "経路2", "Microchip決算は別エンジン", "neutral"),
        card(second_ids[2], "まとめ1", "原油・利回り低下は増幅", "neutral"),
        card(second_ids[3], "まとめ2", "違う理由の上昇が同じ方向へ重なった", "emphasis"),
    ]
    scene["cards"] = [
        row for row in scene.get("cards", [])
        if not str(row.get("cardId", "")).startswith(RESERVED_PREFIX)
    ] + rows

    first["objectIds"] = first_ids
    first["sequencePolicy"] = "object-order-fallback"
    first["templateConfig"]["laneLabels"] = ["強める", "弱める"]

    second["objectIds"] = second_ids
    second["sequencePolicy"] = "object-order-fallback"
    # The current renderer maps verification-checklist through the same two-lane
    # surface. These labels keep the intended checklist semantics explicit.
    second["templateConfig"]["laneLabels"] = ["経路", "まとめ"]

    dump(render_path, render)
    return {
        "status": "pass",
        "episodeDate": DATE,
        "scene8Beat1CardIds": first_ids,
        "scene8Beat2CardIds": second_ids,
        "newEvidenceAdded": False,
        "narrationChanged": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = apply(args.repo_root.resolve())
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
