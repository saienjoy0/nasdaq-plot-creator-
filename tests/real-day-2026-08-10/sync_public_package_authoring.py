#!/usr/bin/env python3
"""Synchronize H4 public episode-package metadata with verified successful wave 2.

TEST ONLY. Story/scene narration is authored and validated separately. This helper
updates the surrounding package metadata (overview, uncertainty, source usage,
implementation notes, and concise 04 review summary) so the final package cannot
carry the superseded 'minute data unavailable' state after Research and Story have
already been re-authored from verified minute evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

DATE = "2026-08-10"
STALE_TOKENS = (
    "分足欠損",
    "分足未取得",
    "分足反応は未確認",
    "8:30 ET直後分足は取得できない",
    "未取得の分足線",
    "historical minute data未取得",
    "2 wave後も分足未取得",
    "Scene 8で分足未取得を明示",
)


class PublicPackageSyncError(ValueError):
    pass


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicPackageSyncError(f"cannot read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise PublicPackageSyncError(f"JSON root must be object: {path}")
    return value


def replace_line(lines: list[str], prefix: str, replacement: str) -> None:
    matches = [index for index, line in enumerate(lines) if line.startswith(prefix)]
    if len(matches) != 1:
        raise PublicPackageSyncError(
            f"expected exactly one line starting {prefix!r}; found {len(matches)}"
        )
    lines[matches[0]] = replacement


def replace_exact(lines: list[str], old: str, new: str) -> None:
    matches = [index for index, line in enumerate(lines) if line == old]
    if len(matches) != 1:
        raise PublicPackageSyncError(
            f"expected exactly one legacy line {old!r}; found {len(matches)}"
        )
    lines[matches[0]] = new


def sync(*, repo_root: Path) -> dict[str, Any]:
    root = repo_root.resolve()
    package_path = root / f"episodes/{DATE}/episode_package_public_{DATE}.md"
    dossier_path = root / f"research/{DATE}/causal_research_dossier_{DATE}.json"
    result_path = root / f"research/{DATE}/research_acquisition_result_w02.json"

    if not package_path.is_file():
        raise PublicPackageSyncError(f"public package missing: {package_path}")
    dossier = load_json(dossier_path)
    result = load_json(result_path)
    if result.get("status") != "success" or result.get("wave") != 2:
        raise PublicPackageSyncError("verified wave 2 result is not successful")
    result_rows = {
        item.get("requestId"): item
        for item in result.get("results", [])
        if isinstance(item, dict) and isinstance(item.get("requestId"), str)
    }
    for request_id in ("RA-W2-001", "RA-W2-002", "RA-W2-003", "RA-W2-004"):
        if result_rows.get(request_id, {}).get("recordCount") != 1000:
            raise PublicPackageSyncError(f"verified 1000-bar result missing: {request_id}")
    if result_rows.get("RA-W2-005", {}).get("recordCount") != 1:
        raise PublicPackageSyncError("verified Microchip IR result missing")

    handoff = dossier.get("editorial_handoff")
    if not isinstance(handoff, dict) or not isinstance(handoff.get("causal_spine"), str):
        raise PublicPackageSyncError("dossier editorial_handoff.causal_spine missing")

    lines = package_path.read_text(encoding="utf-8").splitlines()

    replace_line(
        lines,
        "- ストーリーの背骨：",
        f"- ストーリーの背骨：{handoff['causal_spine']}。",
    )
    replace_line(
        lines,
        "- 重要な反対材料：",
        "- 重要な反対材料：雇用減は景気減速リスクでもある。 / AMD -1.21%、Alphabet -0.96%でテック全面高ではない。 / 原油・利回り低下と好決算も同日に存在した。 / 8:30 ETの1分足は時系列整合の証拠であって因果証明ではなく、MCHPは同じ発表分ではほぼ横ばい。",
    )
    replace_line(
        lines,
        "- 相殺・反対材料：",
        "- 相殺・反対材料：雇用減そのものが示す成長不安 / AMD -1.21% / Alphabet -0.96% / 1分足だけでは因果を証明しない / MCHPは同じ発表分でほぼ横ばい",
    )

    # Scene 1 package-level uncertainty appears exactly once before Scene 2.
    replace_exact(
        lines,
        "- 不確実性：分足反応は未確認",
        "- 不確実性：8:30 ETのQQQ・SOXX・NVIDIA初動は上向きと確認したが、1分足だけで終日上昇の因果や寄与度は証明しない",
    )

    replace_line(
        lines,
        "8月7日のNasdaq Compositeは1.30%上昇、SOXXは2.02%高でした。",
        "8月7日のNasdaq Compositeは1.30%上昇、SOXXは2.02%高でした。一方、7月の米非農業部門雇用者数は市場予想+8万人に対して-2.3万人。動画ではExpected / Actual / Gap、利上げ観測の後退、Microchip好決算による半導体の増幅、AMD・Alphabetの逆行に加え、8:30 ETのQQQ・SOXX・NVIDIAの初動上昇とMCHPの違いまで確認します。ただし1分足は因果そのものの証明ではありません。本動画はニュース解説であり、個別銘柄の売買を勧めるものではありません。",
    )

    replace_line(
        lines,
        "- Timeline：",
        "- Timeline：Scene 8は検証済み1分足を使用。8:30 ETの発表分でQQQ・SOXX・NVIDIAが上向き、MCHPはほぼ横ばいだった事実を時系列証拠として使い、1分足だけで因果を断定しない。",
    )
    replace_line(
        lines,
        "- 実装時に変更禁止：",
        "- 実装時に変更禁止：雇用悪化そのものと利上げ観測後退の分離、Microchipを増幅要因へ限定、AMD/Alphabet逆行、QQQ・SOXX・NVIDIAの発表分上昇、MCHPの同一分ほぼ横ばい、1分足は因果証明ではないという境界。",
    )
    replace_line(
        lines,
        "- source-001｜",
        "- source-001｜朝のNASDAQカフェ source collector / Longbridge｜NASDAQ Cafe Source Pack 2026-08-10｜daily-inputs/2026-08-10/daily_source_package_2026-08-10.md｜用途：Nasdaq Composite、SOXX、MCHP、NVDA、AMD、Alphabet、Microsoftの終値と騰落率 / follow-up取得前のBroad Research入力",
    )
    replace_line(
        lines,
        "- source-005｜",
        "- source-005｜NASDAQ Cafe Collector / Longbridge｜Research Acquisition Result Wave 2 — verified 1-minute series｜research/2026-08-10/research_acquisition_result_w02.json｜用途：QQQ、SOXX、MCHP、NVDAの検証済み1分足（各1000本） / 8:30 ET発表分の初動比較 / Microchip IR取得成功",
    )
    replace_line(
        lines,
        "- 必須修正と反映結果：",
        "- 必須修正と反映結果：Scene 4で雇用悪化と利上げ観測後退を分離。Scene 8で8:30 ETのQQQ・SOXX・NVIDIA初動上昇とMCHPのほぼ横ばいを確認し、1分足は因果証明ではない境界を維持した。",
    )

    text = "\n".join(lines) + "\n"
    stale = [token for token in STALE_TOKENS if token in text]
    if stale:
        raise PublicPackageSyncError(
            f"superseded minute-unavailable metadata remains in public package: {stale}"
        )
    required = (
        "719.16",
        "720.23",
        "541.06",
        "542.40",
        "219.95",
        "220.31",
        "79.58",
        "79.56",
        "1分足は因果証明ではない",
    )
    missing = [token for token in required if token not in text]
    if missing:
        raise PublicPackageSyncError(
            f"verified timing metadata missing from public package: {missing}"
        )

    temp = package_path.with_name(f".{package_path.name}.h4-public.tmp")
    temp.write_text(text, encoding="utf-8")
    temp.replace(package_path)
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "status": "pass",
        "episode_date": DATE,
        "public_package": package_path.relative_to(root).as_posix(),
        "public_package_sha256": digest,
        "wave2_status": result["status"],
        "causal_spine": handoff["causal_spine"],
        "stale_token_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = sync(repo_root=args.repo_root.resolve())
    except PublicPackageSyncError as exc:
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
