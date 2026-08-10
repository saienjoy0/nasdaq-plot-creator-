#!/usr/bin/env python3
"""Synchronize stale public/render timing prose for the frozen H4 fixture.

TEST ONLY. The immutable base fixture predates the successful wave-2 minute evidence.
This helper updates only prose/metadata whose factual premise changed after verified
minute evidence arrived. It does not change the selected story, causal confidence,
review scores, or scene narration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DATE = "2026-08-10"


class PublicTimingAuthoringError(ValueError):
    pass


NEW_STORY_SPINE = (
    "雇用予想+8万人→実際-2.3万人→利上げ観測後退→8:30 ETにQQQ・SOXX・NVIDIAが上向き→"
    "大型テックへの金利逆風緩和→Microchip好決算と原油・利回り低下が増幅→NASDAQ +1.30%、"
    "ただし1分足は因果証明ではなく個別差を残す。"
)
NEW_COUNTEREVIDENCE = (
    "8:30 ETの1分足はQQQ・SOXX・NVIDIAで上向いたが、1分足だけでは雇用統計が原因と証明できず、"
    "MCHPは同じ1分ではほぼ横ばいだった。"
)
NEW_OFFSETTING = "MCHPは8:30 ETの同じ1分ではほぼ横ばい"
NEW_TIMELINE_BASIS = (
    "BLSの8:30 ET公式発表、Reutersの利上げ観測報道、QQQ・SOXX・NVDA・MCHPの検証済み1分足、"
    "8月7日通常取引終値。1分足は時系列整合の証拠であり、因果証明には使わない。"
)
NEW_DESCRIPTION = (
    "8月7日のNasdaq Compositeは1.30%上昇、SOXXは2.02%高でした。一方、7月の米非農業部門雇用者数は"
    "市場予想+8万人に対して-2.3万人。動画ではExpected / Actual / Gap、利上げ観測の後退、Microchip好決算による"
    "半導体の増幅、AMD・Alphabetの逆行に加え、8:30 ETのQQQ・SOXX・NVDAの初動とMCHPの個別差まで確認します。"
    "1分足は時系列整合の証拠であり、原因そのものの証明ではありません。本動画はニュース解説であり、個別銘柄の"
    "売買を勧めるものではありません。"
)
NEW_SCENE1_UNCERTAINTY = "8:30 ETの初動は後段で確認するが、1分足だけでは因果は証明できない"
NEW_SHORTENED_REASON = "雇用統計、金利観測、半導体増幅、反対材料、8:30 ETの初動まで9シーンで完結できるため。"
NEW_REVIEW_REQUIRED = "Scene 8で8:30 ETの実分足を明示し、初動の時系列整合と因果証明を分ける。"
NEW_REVIEW_APPLIED = (
    "成功したwave 2の検証済み1分足をScene 8へ反映し、QQQ・SOXX・NVIDIAの上向きとMCHPのほぼ横ばいを示したうえで、"
    "1分足だけでは因果を証明しない境界を残した。"
)

PUBLIC_REPLACEMENTS: dict[str, str] = {
    "- ストーリーの背骨：雇用予想+8万人→実際-2.3万人→利上げ観測後退→大型テックへの金利逆風緩和→Microchip好決算と原油・利回り低下が増幅→NASDAQ +1.30%、ただし個別差と分足欠損を残す。":
        f"- ストーリーの背骨：{NEW_STORY_SPINE}",
    "- 重要な反対材料：雇用減は景気減速リスクでもある。 / AMD -1.21%、Alphabet -0.96%でテック全面高ではない。 / 原油・利回り低下と好決算も同日に存在した。 / QQQ/SOXX/MCHP/NVDAの8:30 ET直後分足は取得できない。":
        f"- 重要な反対材料：雇用減は景気減速リスクでもある。 / AMD -1.21%、Alphabet -0.96%でテック全面高ではない。 / 原油・利回り低下と好決算も同日に存在した。 / {NEW_COUNTEREVIDENCE}",
    "- 相殺・反対材料：雇用減そのものが示す成長不安 / AMD -1.21% / Alphabet -0.96% / 分足未取得":
        f"- 相殺・反対材料：雇用減そのものが示す成長不安 / AMD -1.21% / Alphabet -0.96% / {NEW_OFFSETTING}",
    "- 不確実性：分足反応は未確認":
        f"- 不確実性：{NEW_SCENE1_UNCERTAINTY}",
    "8月7日のNasdaq Compositeは1.30%上昇、SOXXは2.02%高でした。一方、7月の米非農業部門雇用者数は市場予想+8万人に対して-2.3万人。動画ではExpected / Actual / Gap、利上げ観測の後退、Microchip好決算による半導体の増幅、AMD・Alphabetの逆行、分足未取得という留保まで分けて確認します。本動画はニュース解説であり、個別銘柄の売買を勧めるものではありません。":
        NEW_DESCRIPTION,
    "- Timeline：`official-time-plus-close`。8:30 ETの公式発表時刻と引けの終値だけを使い、未取得の分足線は作らない。":
        "- Timeline：`verified-series-plus-official-time-plus-close`。8:30 ETの公式発表時刻、QQQ・SOXX・NVDA・MCHPの検証済み1分足、引けの終値を使う。1分足は因果証明には使わない。",
    "- 実装時に変更禁止：雇用悪化そのものと利上げ観測後退の分離、Microchipを増幅要因へ限定、AMD/Alphabet逆行、2 wave後も分足未取得という留保。":
        "- 実装時に変更禁止：雇用悪化そのものと利上げ観測後退の分離、Microchipを増幅要因へ限定、AMD/Alphabet逆行、1分足は時系列整合の証拠であり因果証明ではないという留保。",
    "- source-001｜朝のNASDAQカフェ source collector / Longbridge｜NASDAQ Cafe Source Pack 2026-08-10｜daily-inputs/2026-08-10/daily_source_package_2026-08-10.md｜用途：Nasdaq Composite、SOXX、MCHP、NVDA、AMD、Alphabet、Microsoftの終値と騰落率 / 分足取得制約":
        "- source-001｜朝のNASDAQカフェ source collector / Longbridge｜NASDAQ Cafe Source Pack 2026-08-10｜daily-inputs/2026-08-10/daily_source_package_2026-08-10.md｜用途：Nasdaq Composite、SOXX、MCHP、NVDA、AMD、Alphabet、Microsoftの終値と騰落率",
    "- source-005｜NASDAQ Cafe Collector / Longbridge｜Research Acquisition Result Wave 2｜research/2026-08-10/research_acquisition_result_w02.json｜用途：QQQ、SOXX、MCHP、NVDAのhistorical minute data未取得":
        "- source-005｜NASDAQ Cafe Collector / Longbridge｜Research Acquisition Result Wave 2｜research/2026-08-10/research_acquisition_result_w02.json｜用途：QQQ、SOXX、MCHP、NVDAの検証済み1分足と8:30 ET初動比較",
    "- 必須修正と反映結果：Scene 4で雇用悪化と利上げ観測後退を分離。Scene 8で分足未取得を明示し、8:30 ET直後の値動きを断定しない。":
        "- 必須修正と反映結果：Scene 4で雇用悪化と利上げ観測後退を分離。Scene 8で8:30 ETの実分足を明示し、QQQ・SOXX・NVDAの上向きとMCHPのほぼ横ばいを分け、1分足だけで因果を断定しない。",
}

STALE_MARKERS = (
    "分足未取得",
    "分足欠損",
    "8:30 ET直後分足は取得できない",
    "分足反応は未確認",
    "未取得の分足線",
    "historical minute data未取得",
    "分足は未取得",
    "分足は2回の追加取得でも得られず",
    "分足取得制約",
)


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicTimingAuthoringError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PublicTimingAuthoringError(f"JSON root must be object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    temp = path.with_name(f".{path.name}.h4-timing.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sync_public(path: Path) -> tuple[str, int]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PublicTimingAuthoringError(f"cannot read {path}: {exc}") from exc
    applied = 0
    for old, new in PUBLIC_REPLACEMENTS.items():
        if old not in text:
            raise PublicTimingAuthoringError(f"expected stale public-package text missing: {old}")
        text = text.replace(old, new, 1)
        applied += 1
    leftovers = [marker for marker in STALE_MARKERS if marker in text]
    if leftovers:
        raise PublicTimingAuthoringError(f"stale public minute-unavailable semantics remain: {leftovers}")
    temp = path.with_name(f".{path.name}.h4-timing.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)
    return hashlib.sha256(text.encode("utf-8")).hexdigest(), applied


def replace_review_line(items: Any, old: str, new: str, label: str) -> None:
    if not isinstance(items, list):
        raise PublicTimingAuthoringError(f"render review {label} must be an array")
    matches = [index for index, item in enumerate(items) if item == old]
    if matches != [1]:
        raise PublicTimingAuthoringError(
            f"render review {label} stale line drift: expected index 1, got {matches}"
        )
    items[1] = new


def sync_render(path: Path) -> str:
    render = load_json(path)
    if render.get("episode", {}).get("targetDate") != DATE:
        raise PublicTimingAuthoringError("render targetDate drift")

    editorial = render.get("editorial")
    episode = render.get("episode")
    publishing = render.get("publishing")
    review = render.get("review")
    scenes = render.get("scenes")
    sources = render.get("sources")
    if not all(isinstance(item, dict) for item in (editorial, episode, publishing, review)):
        raise PublicTimingAuthoringError("render editorial/episode/publishing/review contract drift")
    if not isinstance(scenes, list) or len(scenes) != 9 or not isinstance(sources, list):
        raise PublicTimingAuthoringError("render scenes/sources contract drift")

    counter = editorial.get("counterEvidence")
    offsetting = editorial.get("offsettingFactors")
    if not isinstance(counter, list) or len(counter) < 4 or not isinstance(offsetting, list) or len(offsetting) < 4:
        raise PublicTimingAuthoringError("render editorial counterevidence shape drift")
    counter[3] = NEW_COUNTEREVIDENCE
    offsetting[3] = NEW_OFFSETTING
    editorial["storySpine"] = NEW_STORY_SPINE
    editorial["timelineBasis"] = NEW_TIMELINE_BASIS
    episode["shortenedReason"] = NEW_SHORTENED_REASON
    publishing["description"] = NEW_DESCRIPTION

    scene1 = scenes[0]
    if not isinstance(scene1, dict) or scene1.get("sceneId") != "scene-01":
        raise PublicTimingAuthoringError("render Scene 1 identity drift")
    scene1["uncertainty"] = NEW_SCENE1_UNCERTAINTY

    source_by_id = {
        item.get("sourceId"): item
        for item in sources
        if isinstance(item, dict) and isinstance(item.get("sourceId"), str)
    }
    source1 = source_by_id.get("source-001")
    source5 = source_by_id.get("source-005")
    if not isinstance(source1, dict) or not isinstance(source5, dict):
        raise PublicTimingAuthoringError("render source-001/source-005 missing")
    source1["usedFor"] = ["Nasdaq Composite、SOXX、MCHP、NVDA、AMD、Alphabet、Microsoftの終値と騰落率"]
    source5["usedFor"] = ["QQQ、SOXX、MCHP、NVDAの検証済み1分足と8:30 ET初動比較"]

    replace_review_line(
        review.get("requiredChanges"),
        "Scene 8で分足未取得を明示し、8:30 ET直後の価格反応を断定しない。",
        NEW_REVIEW_REQUIRED,
        "requiredChanges",
    )
    replace_review_line(
        review.get("changesApplied"),
        "2 wave後も分足未取得であることをScene 8へ残し、official-time-plus-closeだけを採用した。",
        NEW_REVIEW_APPLIED,
        "changesApplied",
    )

    serialized = json.dumps(render, ensure_ascii=False, sort_keys=True)
    leftovers = [marker for marker in STALE_MARKERS if marker in serialized]
    if leftovers:
        raise PublicTimingAuthoringError(f"stale render minute-unavailable semantics remain: {leftovers}")
    return write_json(path, render)


def sync(*, repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    public_path = root / f"episodes/{DATE}/episode_package_public_{DATE}.md"
    render_path = root / f"render-specs/{DATE}/render_spec.json"
    public_digest, replacement_count = sync_public(public_path)
    render_digest = sync_render(render_path)
    return {
        "status": "pass",
        "episode_date": DATE,
        "replacement_count": replacement_count,
        "episode_package_public_sha256": public_digest,
        "render_authoring_sha256": render_digest,
        "stale_markers_remaining": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = sync(repo_root=args.repo_root.resolve())
    except PublicTimingAuthoringError as exc:
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
