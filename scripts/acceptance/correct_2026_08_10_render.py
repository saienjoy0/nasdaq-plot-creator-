#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

SCENE8_CHUNK1 = (
    '最後に、時系列まで確認します。8時30分ETの発表の1分前から発表分へ、NASDAQの代理として見るQQQは'
    '719.16から720.23、SOXXは541.06から542.40、NVIDIAは219.95から220.31へ上向きました。'
    'だから、弱い雇用から利上げ観測後退、そしてテック買いという市場解釈は、引けだけでなく発表時刻の初動とも整合します。'
    'ただし、1分足は原因そのものを証明しません。MCHPは同じ1分で79.58から79.56とほぼ横ばいでした。'
    'Microchipの大幅高は会社固有材料を別の増幅要因として分ける方が自然です。'
)
SCENE8_CHUNK2 = (
    '僕の結論は中程度の確信で、雇用下振れから利上げリスク低下が主役候補。'
    'Microchip好決算と原油・利回り低下が増幅要因。成長不安と個別の下落銘柄が反対材料です。'
    '悪材料が消えた夜ではなく、どの採点表が優先されたかが変わった夜でした。'
)
PUBLISHING_DESCRIPTION = (
    '8月7日のNasdaq Compositeは1.30%上昇、SOXXは2.02%高でした。一方、7月の米非農業部門雇用者数は'
    '市場予想+8万人に対して-2.3万人。動画ではExpected / Actual / Gap、利上げ観測の後退、Microchip好決算による'
    '半導体の増幅、AMD・Alphabetの逆行、8:30 ETの1分足初動と因果上の限界まで分けて確認します。'
    '本動画はニュース解説であり、個別銘柄の売買を勧めるものではありません。'
)


def cue_start(text: str, size: int = 42) -> str:
    return text[:size]


def cue_end(text: str, size: int = 48) -> str:
    return text[-size:]


def main() -> int:
    path = Path('render-specs/2026-08-10/render_spec.json')
    doc = json.loads(path.read_text(encoding='utf-8'))
    episode = doc.get('episode', {})
    if episode.get('targetDate') != '2026-08-10':
        raise SystemExit('render targetDate drift')
    scenes = doc.get('scenes', [])
    if len(scenes) != 9:
        raise SystemExit('render scene count drift')

    episode['shortenedReason'] = (
        '雇用統計、金利観測、半導体増幅、反対材料、8:30 ETの初動までを9シーンで完結でき、'
        '追加ニュースや未検証の因果で水増ししないため。'
    )

    expected_scopes = {2: ('macro', 'nasdaq'), 3: ('macro', 'nasdaq'), 5: ('global', 'multiple')}
    for scene_number, (old, new) in expected_scopes.items():
        scene = scenes[scene_number - 1]
        if scene.get('sceneNumber') != scene_number:
            raise SystemExit(f'Scene {scene_number} numbering drift')
        if scene.get('causalScope') not in (old, new):
            raise SystemExit(f'Scene {scene_number} causalScope drift: {scene.get("causalScope")}')
        scene['causalScope'] = new

    scenes[0]['uncertainty'] = '8:30 ETの初動は確認済み。ただし1分足だけで因果や寄与度は確定しない'

    scene3_followup = scenes[2]['visualBeats'][1]
    beat_id = scene3_followup.get('visualBeatId') or scene3_followup.get('beatId')
    if beat_id not in {'scene-03-beat-002', 'vb-03-02'} or scene3_followup.get('visualMode') != 'text-focus':
        raise SystemExit(f'unexpected Scene 3 follow-up Beat shape: {beat_id!r}')
    if scene3_followup.get('objectIds') not in (['scene-03-card-002'], []):
        raise SystemExit(f'Scene 3 follow-up objectIds drift: {scene3_followup.get("objectIds")}')
    scene3_followup['objectIds'] = []

    for scene in scenes:
        for beat in scene.get('visualBeats', []):
            template = beat.get('visualTemplate')
            grammar = beat.get('visualGrammar', {})
            current_id = beat.get('visualBeatId') or beat.get('beatId')
            if template == 'text-focus':
                if current_id in {'scene-02-beat-002', 'scene-03-beat-002', 'vb-02-02', 'vb-03-02'}:
                    beat['visualTemplate'] = 'evidence-boundary'
                    beat.setdefault('templateConfig', {})['variant'] = 'confirmed-vs-unconfirmed'
                    if isinstance(grammar, dict):
                        grammar['grammarId'] = 'evidence'
                    if 'visualGrammarId' in beat:
                        beat['visualGrammarId'] = 'evidence'
                else:
                    if isinstance(grammar, dict):
                        grammar['grammarId'] = 'bridge-text'
            elif template == 'expected-actual-gap-flow':
                if isinstance(grammar, dict):
                    grammar['grammarId'] = 'gap'
            elif template == 'market-pulse-grid':
                if isinstance(grammar, dict):
                    grammar['grammarId'] = 'evidence'

    scene8 = scenes[7]
    if scene8.get('sceneNumber') != 8:
        raise SystemExit('Scene 8 numbering drift')
    chunks = scene8.get('narrationChunks', [])
    if len(chunks) != 2:
        raise SystemExit(f'expected two Scene 8 narration chunks, got {len(chunks)}')
    for chunk, text in zip(chunks, (SCENE8_CHUNK1, SCENE8_CHUNK2)):
        chunk['speechText'] = text
        chunk['captionText'] = text

    scene8['purpose'] = '発表時刻の初動を確認しつつ、1分足を因果証明へ拡大しない結論の境界を示す'
    scene8['performanceIntent'] = '時系列の確認は明確に、因果の限界は一段落として切り分ける'
    scene8['uncertainty'] = 'QQQ・SOXX・NVIDIAの初動は発表時刻と整合するが、1分足だけでは因果や寄与度を証明しない。MCHPは同じ発表分ではほぼ横ばい。'
    scene8['supportingTexts'] = ['初動：QQQ / SOXX / NVDA ↑', 'MCHP：発表分ほぼ横ばい', '1分足 ≠ 因果証明']
    scene8['sourceLabel'] = 'BLS / Reuters / 検証済み1分足'
    scene8['timelineBasis'] = 'BLS 8:30 ET発表・主要報道・Longbridge 1分Kline'

    cards = {card.get('cardId'): card for card in scene8.get('cards', [])}
    card1 = cards.get('scene-08-card-001')
    card2 = cards.get('scene-08-card-002')
    if not card1 or not card2:
        raise SystemExit('Scene 8 expected verification cards are missing')
    card1['title'] = '発表時刻の初動'
    card1['lines'] = [
        {'label': 'QQQ', 'tone': 'neutral', 'value': '719.16 → 720.23'},
        {'label': 'SOXX', 'tone': 'neutral', 'value': '541.06 → 542.40'},
        {'label': 'MCHP', 'tone': 'neutral', 'value': '79.58 → 79.56'},
    ]
    card2['title'] = '言わないこと'
    card2['lines'] = [
        {'label': '1', 'tone': 'neutral', 'value': '1分足だけで因果確定'},
        {'label': '2', 'tone': 'neutral', 'value': 'MCHPも同時反応した'},
    ]

    beats = scene8.get('visualBeats', [])
    if len(beats) != 2:
        raise SystemExit(f'expected two Scene 8 visual beats, got {len(beats)}')
    beat1, beat2 = beats
    beat1['changeCue'] = 'QQQ 719.16 → 720.23'
    beat1['primaryElement'] = '発表時刻の1分足初動'
    beat1['screenQuestion'] = '8:30 ETの発表分で何が動いたか'
    beat1['viewerTexts'] = ['QQQ 719.16→720.23', 'SOXX 541.06→542.40', 'MCHP 79.58→79.56']
    beat1.setdefault('templateConfig', {})['dataBasis'] = 'Longbridge verified 1m Kline history / minute-close'
    beat1['narrationStartCue'] = cue_start(SCENE8_CHUNK1)
    beat1['narrationEndCue'] = cue_end(SCENE8_CHUNK1)

    beat2['changeCue'] = '1分足 ≠ 因果証明'
    beat2['primaryElement'] = '時系列整合と因果の境界'
    beat2['screenQuestion'] = '確認した初動をどこまで因果へ使えるか'
    beat2['viewerTexts'] = ['1分足だけで因果確定しない', 'MCHPは同じ分でほぼ横ばい']
    beat2.setdefault('templateConfig', {})['dataBasis'] = '1分足の時系列整合 + 反対材料'
    beat2['narrationStartCue'] = cue_start(SCENE8_CHUNK2)
    beat2['narrationEndCue'] = cue_end(SCENE8_CHUNK2)

    source001_seen = False
    source005_seen = False
    for source in doc.get('sources', []):
        if source.get('sourceId') == 'source-001':
            source['usedFor'] = ['Nasdaq Composite、SOXX、MCHP、NVDA、AMD、Alphabet、Microsoftの終値と騰落率']
            source001_seen = True
        elif source.get('sourceId') == 'source-005':
            source['title'] = 'Research Acquisition Result Wave 2 — verified 1-minute series'
            source['usedFor'] = ['QQQ・SOXX・MCHP・NVDAの2026-08-07検証済み1分足と発表時刻の初動確認']
            source['narrationAttribution'] = '検証済み追加取得結果'
            source005_seen = True
    if not source001_seen:
        raise SystemExit('source-001 missing')
    if not source005_seen:
        raise SystemExit('source-005 missing')

    publishing = doc.get('publishing')
    if not isinstance(publishing, dict):
        raise SystemExit('publishing block missing')
    publishing['description'] = PUBLISHING_DESCRIPTION

    editorial = doc.get('editorial')
    if not isinstance(editorial, dict):
        raise SystemExit('editorial block missing')
    editorial['counterEvidence'] = [
        '雇用減は景気減速リスクでもある。',
        'AMD -1.21%、Alphabet -0.96%でテック全面高ではない。',
        '原油・利回り低下と好決算も同日に存在した。',
        '8:30 ETの1分足はQQQ・SOXX・NVIDIAで上向いたが、1分足だけでは因果や寄与度を証明しない。MCHPは同じ発表分でほぼ横ばい。',
    ]
    editorial['offsettingFactors'] = [
        '雇用減そのものが示す成長不安',
        'AMD -1.21%',
        'Alphabet -0.96%',
        'MCHPは8:30 ET発表分ほぼ横ばい',
        '1分足だけで因果証明しない',
    ]
    editorial['storySpine'] = (
        '雇用予想+8万人→実際-2.3万人→利上げ観測後退→8:30 ETにQQQ・SOXX・NVIDIAが上向き→'
        '大型テックへの金利逆風緩和→Microchip好決算と原油・利回り低下が増幅→NASDAQ +1.30%、'
        'ただし1分足は因果証明ではなく個別差を残す。'
    )
    editorial['timelineBasis'] = (
        'BLSの8:30 ET公式発表、Reutersの利上げ観測報道、Longbridgeの検証済み1分Kline、'
        '8月7日通常取引終値。1分足は発表時刻との整合確認に使い、因果の単独証明には使わない。'
    )

    review = doc.get('review')
    if not isinstance(review, dict):
        raise SystemExit('review block missing')
    review['changesApplied'] = [
        '『悪い雇用だから株高』ではなく『追加利上げリスク低下』と明示した。',
        'Scene 8に検証済み1分足の初動を反映し、1分足だけでは因果を証明しない境界とMCHPの個別差を残した。',
        'MicrochipをNASDAQ主因ではなく半導体増幅要因へ限定した。',
    ]
    review['requiredChanges'] = [
        'Scene 4で弱い雇用そのものと利上げ観測後退を分離する。',
        'Scene 8で検証済み1分足の初動を示し、1分足だけで因果を断定せず、MCHPの個別差を反対材料として残す。',
    ]

    serialized = json.dumps(doc, ensure_ascii=False, sort_keys=True)
    stale_terms = [
        '分足未取得', '分足は未取得', '分足欠損', '8:30 ET直後分足は取得できない',
        '分足反応は未確認', '分足取得制約', '2回の追加取得でも得られず',
    ]
    found_stale = [term for term in stale_terms if term in serialized]
    if found_stale:
        raise SystemExit(f'stale wave2 failure metadata remains in render: {found_stale}')

    text = json.dumps(doc, ensure_ascii=False, indent=2, sort_keys=True) + '\n'
    actual = hashlib.sha256(text.encode('utf-8')).hexdigest()
    path.write_text(text, encoding='utf-8')
    print(f'PASS corrected render with verified wave2 timing {actual}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
