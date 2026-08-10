#!/usr/bin/env python3
"""Synchronize stale public-package timing prose for the frozen H4 fixture.

TEST ONLY. The immutable base fixture predates the successful wave-2 minute evidence.
Scene 8 authoring is already corrected elsewhere; this helper updates only the stale
summary/publishing/production-note prose that would otherwise be parsed back into the
final episode package and reintroduce the old `minute data unavailable` conclusion.
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


REPLACEMENTS: dict[str, str] = {
    "- ストーリーの背骨：雇用予想+8万人→実際-2.3万人→利上げ観測後退→大型テックへの金利逆風緩和→Microchip好決算と原油・利回り低下が増幅→NASDAQ +1.30%、ただし個別差と分足欠損を残す。":
        "- ストーリーの背骨：雇用予想+8万人→実際-2.3万人→利上げ観測後退→8:30 ETにQQQ・SOXX・NVIDIAが上向き→大型テックへの金利逆風緩和→Microchip好決算と原油・利回り低下が増幅→NASDAQ +1.30%、ただし1分足は因果証明ではなく個別差を残す。",
    "- 重要な反対材料：雇用減は景気減速リスクでもある。 / AMD -1.21%、Alphabet -0.96%でテック全面高ではない。 / 原油・利回り低下と好決算も同日に存在した。 / QQQ/SOXX/MCHP/NVDAの8:30 ET直後分足は取得できない。":
        "- 重要な反対材料：雇用減は景気減速リスクでもある。 / AMD -1.21%、Alphabet -0.96%でテック全面高ではない。 / 原油・利回り低下と好決算も同日に存在した。 / 8:30 ETの1分足はQQQ・SOXX・NVIDIAで上向いたが、1分足だけでは雇用統計が原因と証明できず、MCHPは同じ1分ではほぼ横ばいだった。",
    "- 相殺・反対材料：雇用減そのものが示す成長不安 / AMD -1.21% / Alphabet -0.96% / 分足未取得":
        "- 相殺・反対材料：雇用減そのものが示す成長不安 / AMD -1.21% / Alphabet -0.96% / MCHPは8:30 ETの同じ1分ではほぼ横ばい",
    "- 不確実性：分足反応は未確認":
        "- 不確実性：8:30 ETの初動は後段で確認するが、1分足だけでは因果は証明できない",
    "8月7日のNasdaq Compositeは1.30%上昇、SOXXは2.02%高でした。一方、7月の米非農業部門雇用者数は市場予想+8万人に対して-2.3万人。動画ではExpected / Actual / Gap、利上げ観測の後退、Microchip好決算による半導体の増幅、AMD・Alphabetの逆行、分足未取得という留保まで分けて確認します。本動画はニュース解説であり、個別銘柄の売買を勧めるものではありません。":
        "8月7日のNasdaq Compositeは1.30%上昇、SOXXは2.02%高でした。一方、7月の米非農業部門雇用者数は市場予想+8万人に対して-2.3万人。動画ではExpected / Actual / Gap、利上げ観測の後退、Microchip好決算による半導体の増幅、AMD・Alphabetの逆行に加え、8:30 ETのQQQ・SOXX・NVDAの初動とMCHPの個別差まで確認します。1分足は時系列整合の証拠であり、原因そのものの証明ではありません。本動画はニュース解説であり、個別銘柄の売買を勧めるものではありません。",
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
)


def sync(*, repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    path = root / f"episodes/{DATE}/episode_package_public_{DATE}.md"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PublicTimingAuthoringError(f"cannot read {path}: {exc}") from exc

    applied: list[str] = []
    for old, new in REPLACEMENTS.items():
        if old not in text:
            raise PublicTimingAuthoringError(f"expected stale public-package text missing: {old}")
        text = text.replace(old, new, 1)
        applied.append(old)

    leftovers = [marker for marker in STALE_MARKERS if marker in text]
    if leftovers:
        raise PublicTimingAuthoringError(f"stale minute-unavailable semantics remain: {leftovers}")

    temp = path.with_name(f".{path.name}.h4-timing.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(path)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "status": "pass",
        "episode_date": DATE,
        "replacement_count": len(applied),
        "episode_package_public_sha256": digest,
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
