#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

DATE = '2026-08-10'
TERMINAL_REUSE_LABEL = '主因候補：利上げ観測後退'
NEW_STORY_SPINE = (
    '雇用予想+8万人→実際-2.3万人→利上げ観測後退→8:30 ETにQQQ・SOXX・NVIDIAが上向き→'
    '大型テックへの金利逆風緩和→Microchip好決算と原油・利回り低下が増幅→NASDAQ +1.30%、'
    'ただし1分足は因果証明ではなく個別差を残す。'
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def build_scene8(scene: dict) -> str:
    lines = [
        f"## B8. Scene 8｜{scene['formalName']}",
        '',
        f"- 目的：{scene['purpose']}",
        '- 目安時間：執筆目安のみ。実測はTTS後',
        f"- 因果の対象：{scene['causalScope']}",
        f"- 狐の演技意図：{scene['performanceIntent']}",
        f"- 狐の表情：{scene['initialExpression']}",
        '- 表情切り替え：Visual Beatに合わせて既存表情だけを使用',
        f"- 画面モード：{scene['visualMode']}",
        f"- Headline：{scene['headline']}",
        '- 前後の接続文：最後に発表時刻の初動と因果の限界を確認して、結論の境界を引きます。',
        '',
        '### Visual Beats',
        '',
    ]

    for beat in scene['visualBeats']:
        grammar = beat['visualGrammar']
        lines.extend([
            f"- **{beat['beatId']}**",
            f"  - 開始合図：{beat['narrationStartCue']}",
            f"  - 終了合図：{beat['narrationEndCue']}",
            f"  - 変化合図：{beat['changeCue']}",
            f"  - 主要視覚機能：{beat['primaryFunction']}",
            f"  - 画面状態：{beat['screenState']}",
            f"  - Visual Grammar：{grammar['grammarId']} / {grammar['transitionRole']}",
            f"  - Visual Template ID：{beat['visualTemplate']}",
            f"  - Template Variant：{beat.get('templateConfig', {}).get('variant', 'default')}",
            f"  - 入力構造：{' / '.join(beat['viewerTexts'])}",
            f"  - 画面の問い：{beat['screenQuestion']}",
            f"  - 主要要素：{beat['primaryElement']}",
            f"  - 視聴者向けテキスト：{' / '.join(beat['viewerTexts'])}",
            '  - 使用アセットID：not-required',
            f"  - アセット状態：{beat['assetState']}",
            '  - 表示後の復帰先：該当なし',
            '  - Primary / Approved Fallback：not-required',
            '  - selected_path：not-required',
            f"  - 根拠ID：{', '.join(beat['evidenceSourceIds'])}",
            '',
        ])

    narration = ''.join(chunk['speechText'] for chunk in scene['narrationChunks'])
    lines.extend([
        '### 完成ナレーション',
        '',
        narration,
        '',
        f"- ナレーションで示す出典主体・媒体：{scene['sourceLabel']}",
        f"- 大テロップ：{scene['headline']}",
        f"- 補助テロップ：{' / '.join(scene['supportingTexts'])}",
        '- 使用する数字：8:30 ET、QQQ 719.16→720.23、SOXX 541.06→542.40、NVIDIA 219.95→220.31、MCHP 79.58→79.56',
        f"- 画面で見せる内容：{' / '.join(scene['supportingTexts'])}",
        f"- 根拠：{scene['sourceLabel']}",
        f"- 不確実性：{scene['uncertainty']}",
        '',
    ])
    return '\n'.join(lines)


def main() -> int:
    render_path = Path(f'render-specs/{DATE}/render_spec.json')
    public_path = Path(f'episodes/{DATE}/episode_package_public_{DATE}.md')
    render = json.loads(render_path.read_text(encoding='utf-8'))
    scenes = render.get('scenes', [])
    if len(scenes) != 9 or scenes[7].get('sceneNumber') != 8:
        raise SystemExit('render Scene 8 shape drift')
    scene8 = scenes[7]

    existing_support = list(scene8.get('supportingTexts', []))
    scene8['supportingTexts'] = [TERMINAL_REUSE_LABEL] + [
        value for value in existing_support if value != TERMINAL_REUSE_LABEL
    ]
    render_text = json.dumps(render, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    render_path.write_text(render_text, encoding='utf-8')

    text = public_path.read_text(encoding='utf-8')
    match = re.search(r'(?ms)^## B8\. Scene 8.*?(?=^## B9\.)', text)
    if match is None:
        raise SystemExit('public package Scene 8 section not found')
    text = text[:match.start()] + build_scene8(scene8) + text[match.end():]

    replacements = {
        'ストーリーの背骨：雇用予想+8万人→実際-2.3万人→利上げ観測後退→大型テックへの金利逆風緩和→Microchip好決算と原油・利回り低下が増幅→NASDAQ +1.30%、ただし個別差と分足欠損を残す。':
            f'ストーリーの背骨：{NEW_STORY_SPINE}',
        '不確実性：分足反応は未確認':
            '不確実性：8:30 ETの初動は確認済み。ただし1分足だけで因果や寄与度は確定しない',
        'QQQ/SOXX/MCHP/NVDAの8:30 ET直後分足は取得できない。':
            '8:30 ETの検証済み1分足ではQQQ・SOXX・NVIDIAが上向き、MCHPはほぼ横ばい。1分足だけでは因果を証明しない。',
        '相殺・反対材料：雇用減そのものが示す成長不安 / AMD -1.21% / Alphabet -0.96% / 分足未取得':
            '相殺・反対材料：雇用減そのものが示す成長不安 / AMD -1.21% / Alphabet -0.96% / MCHPは8:30 ET発表分ほぼ横ばい / 1分足だけで因果証明しない',
        '動画ではExpected / Actual / Gap、利上げ観測の後退、Microchip好決算による半導体の増幅、AMD・Alphabetの逆行、分足未取得という留保まで分けて確認します。':
            '動画ではExpected / Actual / Gap、利上げ観測の後退、Microchip好決算による半導体の増幅、AMD・Alphabetの逆行、8:30 ETの1分足初動と因果上の限界まで分けて確認します。',
        '- Timeline：`official-time-plus-close`。8:30 ETの公式発表時刻と引けの終値だけを使い、未取得の分足線は作らない。':
            '- Timeline：BLS 8:30 ETの公式発表時刻、検証済み1分足初動、引けの終値を分けて使用。1分足だけで因果は確定しない。',
        '- 実装時に変更禁止：雇用悪化そのものと利上げ観測後退の分離、Microchipを増幅要因へ限定、AMD/Alphabet逆行、2 wave後も分足未取得という留保。':
            '- 実装時に変更禁止：雇用悪化そのものと利上げ観測後退の分離、Microchipを増幅要因へ限定、AMD/Alphabet逆行、1分足は因果証明ではないこと、MCHPは同じ発表分でほぼ横ばいという反対材料。',
        '- source-001｜朝のNASDAQカフェ source collector / Longbridge｜NASDAQ Cafe Source Pack 2026-08-10｜daily-inputs/2026-08-10/daily_source_package_2026-08-10.md｜用途：Nasdaq Composite、SOXX、MCHP、NVDA、AMD、Alphabet、Microsoftの終値と騰落率 / 分足取得制約':
            '- source-001｜朝のNASDAQカフェ source collector / Longbridge｜NASDAQ Cafe Source Pack 2026-08-10｜daily-inputs/2026-08-10/daily_source_package_2026-08-10.md｜用途：Nasdaq Composite、SOXX、MCHP、NVDA、AMD、Alphabet、Microsoftの終値と騰落率',
        '- source-005｜NASDAQ Cafe Collector / Longbridge｜Research Acquisition Result Wave 2｜research/2026-08-10/research_acquisition_result_w02.json｜用途：QQQ、SOXX、MCHP、NVDAのhistorical minute data未取得':
            '- source-005｜NASDAQ Cafe Collector / Longbridge｜Research Acquisition Result Wave 2 — verified 1-minute series｜research/2026-08-10/research_acquisition_result_w02.json｜用途：QQQ、SOXX、MCHP、NVDAの2026-08-07検証済み1分足と8:30 ET初動確認',
        '- 必須修正と反映結果：Scene 4で雇用悪化と利上げ観測後退を分離。Scene 8で分足未取得を明示し、8:30 ET直後の値動きを断定しない。':
            '- 必須修正と反映結果：Scene 4で雇用悪化と利上げ観測後退を分離。Scene 8で検証済み1分足の初動を追加し、1分足だけでは因果を証明しない境界とMCHPの個別差を維持。',
    }
    for old, new in replacements.items():
        if old not in text:
            raise SystemExit(f'expected stale public-package text not found: {old}')
        text = text.replace(old, new)

    stale = (
        '対象日のminute dataは取得できませんでした',
        '8:30 ET直後の分足は未確認',
        '分足未取得',
        '未取得の分足',
        '分足欠損',
        '分足反応は未確認',
        '分足取得制約',
        '2回の追加取得でも得られず',
    )
    found_stale = [value for value in stale if value in text]
    if found_stale:
        raise SystemExit(f'stale wave2 failure text remains: {found_stale}')

    required: list[str] = list(scene8['supportingTexts'])
    for chunk in scene8['narrationChunks']:
        required.extend([chunk['speechText'], chunk['captionText']])
    for beat in scene8['visualBeats']:
        required.extend([
            beat['narrationStartCue'], beat['narrationEndCue'], beat['screenQuestion'],
            beat['primaryElement'], beat['changeCue'], *beat['viewerTexts'],
        ])
    missing = [value for value in required if value not in text]
    if missing:
        raise SystemExit(f'public package still misses final render strings: {missing}')

    public_path.write_text(text, encoding='utf-8')
    print(
        'PASS synchronized episode public package with verified wave2 timing '
        f'public_sha256={sha256_text(text)} render_sha256={sha256_text(render_text)}'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
