#!/usr/bin/env python3
"""Synchronize the frozen H4 render review with verified minute evidence.

TEST ONLY. The immutable base review was authored while wave-2 minute data was still
unavailable. Update only the two review-history lines whose premise changed; all
editorial conclusions, scores, and approval state remain untouched.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DATE = "2026-08-10"
OLD_REQUIRED = "Scene 8で分足未取得を明示し、8:30 ET直後の価格反応を断定しない。"
NEW_REQUIRED = "Scene 8で8:30 ETの実分足を明示し、初動の時系列整合と因果証明を分ける。"
OLD_APPLIED = "2 wave後も分足未取得であることをScene 8へ残し、official-time-plus-closeだけを採用した。"
NEW_APPLIED = "成功したwave 2の検証済み1分足をScene 8へ反映し、QQQ・SOXX・NVIDIAの上向きとMCHPのほぼ横ばいを示したうえで、1分足だけでは因果を証明しない境界を残した。"


class RenderReviewTimingError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RenderReviewTimingError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RenderReviewTimingError(f"JSON root must be object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temp = path.with_name(f".{path.name}.h4-review-timing.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def replace_exact(items: Any, old: str, new: str, label: str) -> None:
    if not isinstance(items, list):
        raise RenderReviewTimingError(f"render review {label} must be an array")
    matches = [index for index, item in enumerate(items) if item == old]
    if matches != [1]:
        raise RenderReviewTimingError(
            f"render review {label} stale line drift: expected index 1, got {matches}"
        )
    items[1] = new


def sync(*, repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    path = root / f"render-specs/{DATE}/render_spec.json"
    render = load_json(path)
    if render.get("episode", {}).get("targetDate") != DATE:
        raise RenderReviewTimingError("render targetDate drift")
    review = render.get("review")
    if not isinstance(review, dict):
        raise RenderReviewTimingError("render review missing")

    replace_exact(review.get("requiredChanges"), OLD_REQUIRED, NEW_REQUIRED, "requiredChanges")
    replace_exact(review.get("changesApplied"), OLD_APPLIED, NEW_APPLIED, "changesApplied")

    serialized = json.dumps(review, ensure_ascii=False, sort_keys=True)
    if "分足未取得" in serialized:
        raise RenderReviewTimingError("stale minute-unavailable review semantics remain")

    digest = write_json(path, render)
    return {
        "status": "pass",
        "episode_date": DATE,
        "render_authoring_sha256": digest,
        "required_change": NEW_REQUIRED,
        "change_applied": NEW_APPLIED,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = sync(repo_root=args.repo_root.resolve())
    except RenderReviewTimingError as exc:
        print(json.dumps({"status": "fail", "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2

    text = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        output = args.output
        if not output.is_absolute():
            output = args.repo_root.resolve() / output
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
