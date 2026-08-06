# 朝のNASDAQカフェ｜Visual Grammar Overhaul 総合実装設計書

- 文書種別：二リポジトリ横断・実装正本
- 作成日：2026-08-06
- 対象（編集・契約）：`saienjoy0/nasdaq-plot-creator-`
- 対象（映像・実行）：`saienjoy0/saienjoy0-nasdaq-cafe-remotion`
- 正本参照：`01_fox_character_bible`、`02_editorial_bible`、`03_episode_production_spec v2.5.0`、`04_entertainment_inquisitor v2.5.0`
- 目標契約：Visual Grammar `1.0.0`、`render_spec 2.4.0`
- 対象外：市場因果の変更、狐の人物像変更、背景差し替え、AIによる完成動画視覚検査、final自動実行

## 0. 結論

現在の編集骨格は維持し、映像だけを次の固定経路へ移行する。

```text
編集上の問い
→ Visual Grammar ID
→ 承認済みVisual Template
→ Renderer Appearance Class
→ 固定Stage Shell
→ Shot / Motion
→ 機械検査
→ Preview
→ ユーザー目視確認
```

目的は、問いが変わると画面の物理的な見え方も変わる一方で、固定カフェ背景、狐の定位置、字幕安全領域を維持することである。ChatGPTが意味と見せ方を確定し、コードは資格判定・一致検査・描画だけを行う。Beat数だけでなく実音声時間で単調性を検査し、旧版と新版は同一台本・同一TTSでA/B比較する。AIによる代表フレーム採点や完成動画視聴は導入しない。

## 1. 絶対境界

- 01・02の市場因果、主役一本＋世界の波及型、Expected / Actual / Gap、反対材料は変更しない。
- 映像都合でScene順、ナレーション、因果範囲、確信度を変更しない。
- `visualGrammarId`は意味分類であり、原因推論に使わない。
- Scene番号、文中単語、数値の正負、項目数からGrammarやTemplateを自動決定しない。
- Rendererは`visualTemplate`で描画し、`visualGrammarId`からTemplateを選択しない。
- GitHub Actions、Codex、Remotionは台本の意味を変更しない。
- Preview目視確認前にfinalへ進まない。

## 2. 二層モデル

### 2.1 Semantic Grammar

ChatGPTがEpisode Package作成時に「このBeatは何を理解させる画面か」を確定する。

| Grammar ID | 意味 | counted |
|---|---|---:|
| `contradiction` | 方向、矛盾、問い | yes |
| `entity` | 主役企業・人物・製品の実体固定 | yes |
| `evidence` | 確認済み事実、出典、数字、境界 | yes |
| `gap` | Expected / Actual / Gap | yes |
| `causal` | 世界・企業・市場への経路 | yes |
| `reaction` | 発表と値動きの確認可能な時系列 | yes |
| `comparison` | 企業、銘柄、セクター、材料の差 | yes |
| `verification` | 仮説が強まる／弱まる条件 | yes |
| `analogy` | 身近なたとえから市場へ戻る | yes |
| `assembly` | 既出要素だけで結論を再構成 | no |
| `bridge-text` | 短い論点の橋渡し | no |

Expectedが確認できない回では`gap`を強制しない。Reason Unknown回では`causal`を無理に指定せず、理由付き例外を許可する。`bridge-text`と`assembly`はScene 1〜8の多様性を水増ししない。

### 2.2 Appearance Class

Renderer compatibility registryが、Templateの物理的な見え方を固定する。

```text
open-hero
entity-canvas
document-media
metric-board
progressive-chart
causal-path
dual-lane
timeline-track
split-comparison
matrix-grid
verification-gates
picturebook-canvas
assembly-map
text-bridge
```

### 2.3 Dominant Surface

```text
open-canvas
entity
media
card-board
plot
network
split
matrix
picturebook
assembly
text
```

同じ`card-board`が長時間続くことを検出するため、Appearance Classとは別に保持する。

### 2.4 Transition Role

```text
continuation
major-shift
return
closing
```

`major-shift`は自己申告だけでは合格しない。前BeatとAppearance ClassまたはDominant Surfaceが物理的に異なることをrenderer validatorで確認する。`return`は復帰先Beat IDを必須とする。

## 3. Template Compatibility

既存Templateを最大限再利用し、原則として新規Templateを大量追加しない。明確に不足する市場反応時系列だけ、`event-reaction-timeline`を第一候補とする。

| Visual Template | Allowed Grammar | Appearance Class |
|---|---|---|
| `opening-contradiction` | contradiction | open-hero |
| `market-pulse-grid` | evidence, reaction | metric-board |
| `earnings-surprise` | gap | progressive-chart |
| `expected-actual-bullet` | gap | progressive-chart |
| `expected-actual-gap-flow` | gap | progressive-chart |
| `macro-pressure` | causal | causal-path |
| `causal-lane` | causal | causal-path |
| `tailwind-headwind` | causal, evidence | dual-lane |
| `evidence-boundary` | evidence | dual-lane |
| `source-receipt` | evidence | document-media |
| `news-media` | evidence | document-media |
| `entity-card-full` | entity | entity-canvas |
| `dual-asset-split` | comparison | split-comparison |
| `split-comparison` | comparison | split-comparison |
| `diverging-stock-bars` | comparison | split-comparison |
| `focus-matrix` | comparison, evidence | matrix-grid |
| `verification-checklist` | verification | verification-gates |
| `verification-matrix` | verification | verification-gates |
| `analogy-steps` | analogy | picturebook-canvas / causal-path |
| `event-reaction-timeline` | reaction | timeline-track |
| `final-assembly` | assembly | assembly-map |
| `closing-recap` | assembly | assembly-map |
| `text-focus` | bridge-text | text-bridge |

`event-reaction-timeline`のVariant：

```text
verified-series
reported-sequence
official-time-plus-close
close-only
```

`verified-series`以外では折れ線を描かない。`close-only`は終値カードと順序だけを使い、時刻を創作しない。

## 4. Renderer Stage Shell

共通Surfaceへの閉じ込めをやめ、用途別Stage Shellへ段階的に分割する。

```text
OpenHeroStage
EntityStage
DocumentMediaStage
MetricBoardStage
ProgressiveChartStage
CausalPathStage
DualLaneStage
TimelineStage
SplitComparisonStage
MatrixStage
VerificationGateStage
PictureBookStage
AssemblyStage
TextBridgeStage
```

各Stageは基本背景処理、主領域の幾何形状、見出し位置、最大要素数、motion language、overflow、字幕安全領域を固定する。早朝カフェ背景、左側狐領域、狐の基本サイズ、字幕領域、1920×1080、本番Main外枠は変更しない。

## 5. Stage要件

- OpenHero：全面矩形で囲まず、方向→矛盾→問いを同一Stage上で段階表示。
- Entity：Main全体を対象一つへ使い、Chartや数字ボードを重ねない。5〜8秒を基本。
- DocumentMedia：公式資料・ニュース・Receiptを実体として大きく表示し、無理なcoverをしない。
- ProgressiveChart：Expected線→Actual追加→Gap強調→評価軸注釈。初期同時表示禁止。
- CausalPath：最大4ノード・3矢印。ノード後に矢印。世界からNASDAQまでの経路のみ。
- DualLane：支援材料と相殺材料を同時保持。未数値化の強弱を棒長で表現しない。
- Timeline：発表時刻、取引区分、終値、報道順を精度ラベルに従って表示。直接反応と指数材料を別レーンにする。
- SplitComparison：一つの比較軸。最大2主体、補助3。ランキング禁止。
- VerificationGate：strengthen / weaken両側必須。未確認は未点灯。予定表にしない。
- Assembly：Scene 1〜8の既出要素のみ。新しい数値・証拠は禁止。

## 6. Motion / Shot

| 用途 | 基本時間 |
|---|---:|
| 小ラベル・補助語 | 180〜260ms |
| 数字・主要カード | 300〜460ms |
| shared element reframe | 420ms |
| crossfade | 300ms |
| 因果線 | 420〜720ms |
| highlight | 260〜420ms |
| final hold | 450〜900ms |

- Major Shiftはcutまたは420ms reframe。長いfadeだけで処理しない。
- 全要素へ同じspringを機械適用しない。
- 1 Shotの主要焦点は一つ。通常3〜10秒。10秒超は意味変化点で分割。
- Stage ShellはBeat単位で固定し、ShotはStage内部の焦点・カメラ・表情を変える。
- 1 Sceneの狐表情変更は原則2回以内。

## 7. 狐の境界

狐は左端の定位置と基本サイズを維持する。中央移動、Sceneごとのサイズ変更、新ポーズ自動生成、画面からの消去は禁止する。重要Shot開始で表情と主対象highlightを同期し、Gapなど意味切替点に限定して表情を変える。

内部検査用`foxGuidance`は、既存`set-expression`およびShotの`foxExpression`との一致確認にのみ使い、台本や公開テキストを変更しない。

## 8. Episode / Render Contract

Final Episode Contract 1.1.0では各Visual Beatに次を追加する。

```json
{
  "visualGrammar": {
    "contractVersion": "1.0.0",
    "grammarId": "gap",
    "transitionRole": "major-shift",
    "returnTargetBeatId": null
  }
}
```

Render Spec 2.4.0ではRootにVisual Grammar契約SHAを持ち、各Beatへ`visualGrammarId`と`transitionRole`を追加する。Rendererは`visualTemplate`で描画し、GrammarからTemplateを推測しない。Compatibility matrixと異なる組合せは停止する。

Plot正本：

```text
contracts/visual_grammar_semantics.schema.json
contracts/visual_grammar_semantics.json
```

Renderer正本：

```text
contracts/visual_grammar_renderer_compatibility.schema.json
contracts/visual_grammar_renderer_compatibility.json
```

Renderer compatibilityはplot側へbyte-identical mirrorし、SHAをpreflightへ固定する。

## 9. Pre-TTS Structural Gate

通常回Scene 1〜8：

1. counted Semantic Grammar 6種類以上。
2. Appearance Class 6種類以上。
3. Dominant Surface 5種類以上。
4. Scene 1〜4と5〜8にGrammar / Appearance各3種類以上。
5. Major Shift全体4回以上、前後半各1回以上。
6. 同一Appearance 3Beat連続禁止。
7. 同一Dominant Surface 4Beat連続禁止。
8. 非分析画面2Beat以上。
9. `bridge-text`最大2Beat、連続禁止。
10. Scene 1 contradiction、Scene 6 reaction、Scene 7 comparison、Scene 8 verification、Scene 9 assembly。
11. 主役素材利用可能ならScene 2までにentity。
12. Expected確認済みならScene 4 gap。
13. Scene 5 causalまたは理由付き例外。

## 10. Post-TTS Measured Gate

Scene 1〜8の実測Timeline：

- 同一Appearance Class連続時間：最大28秒。
- 一つのDominant Surface総占有率：45%以下。
- `card-board`総占有率：55%以下。
- 非分析画面合計：10秒以上。
- `bridge-text`占有率：12%以下、合計18秒以下。
- Major Shift後の新Stage保持：4秒以上。
- Scene 4はExpected→Actual→Gap順。
- Scene 5はノード後に因果矢印。
- Scene 7は同一比較基準・単位。
- Scene 8はstrengthen / weaken両方。

Fallback採用後はstructural diversityとmeasured diversityを必ず再実行する。崩れた場合、コードが第三Templateを作らずEpisode Packageへ戻す。

## 11. Failure Code

```text
VG_GRAMMAR_COUNT_TOO_LOW
VG_APPEARANCE_COUNT_TOO_LOW
VG_DOMINANT_SURFACE_OVERWEIGHT
VG_SAME_APPEARANCE_RUN_TOO_LONG
VG_MAJOR_SHIFT_NOT_PHYSICAL
VG_BRIDGE_TEXT_OVERUSED
VG_NON_ANALYSIS_DURATION_TOO_LOW
VG_GAP_REVEAL_ORDER_INVALID
VG_CAUSAL_ARROW_PRECEDES_NODE
VG_REACTION_PRECISION_MISMATCH
VG_VERIFICATION_MISSING_WEAKEN_LANE
VG_GRAMMAR_TEMPLATE_MISMATCH
VG_FALLBACK_DIVERSITY_FAILED
VG_REGISTRY_SHA_MISMATCH
```

JSON PathとBeat IDを必ず出す。

## 12. Scene別完成形

- Scene 1：contradiction / open-hero。方向、突出、反対方向、問いを同一Stageで段階表示。
- Scene 2：EntityStage→return→SplitComparison。Entity上にChartを重ねない。
- Scene 3：DocumentMediaまたはReceipt→MetricBoard。確認済み材料をScene 4へ渡す。
- Scene 4：ProgressiveChart→必要時のみAnalogy→return。
- Scene 5：CausalPathまたはDualLane。支援と相殺を混ぜない。
- Scene 6：Timeline→EvidenceBoundaryまたはMarketPulse。分足なしはclose-only / reported-sequence。
- Scene 7：Entity必要時→SplitComparisonまたはMatrix。最大3銘柄、ランキング禁止。
- Scene 8：VerificationGate。強まる／弱まる条件、未確認は未点灯。
- Scene 9：Assembly。冒頭の問い、Gap、波及範囲、反対材料、一文結論。新証拠禁止。

## 13. A/B Preview

A/Bで同一にする：Episode Package SHA、narration、caption、TTS identity、TTS音声、Scene順、数字、出典、採用経路、動画尺。

変更可能：Visual Grammar metadata、Appearance Class実装、Stage Shell、Shot plan、Motion timing、Renderer commit。

Artifact：

```text
baseline_preview.mp4
candidate_preview.mp4
visual_grammar_ab_manifest.json
visual_grammar_structural_report.json
visual_grammar_timing_report.json
technical_report.json
```

`finalAuthorized`は常にfalse。完成動画の良否はユーザーが目視し、AIは採点しない。

## 14. 実装Phase

- VG-0：Master Design and Contract Freeze。
- VG-1：Semantic Grammar Contract（plot）。
- VG-2：Renderer Compatibility and render_spec 2.4.0。
- VG-3：Distinct Stage Shells。
- VG-4：Motion and Timeline Compiler。
- VG-5：Measured Diversity and Cross-Artifact。
- VG-6：A/B Preview Workflow。
- VG-7：01〜04 Integration and Real-Day Acceptance。

## 15. 回帰・禁止テスト

必須拒否：Grammar/Template不一致、bridge-text水増し、物理差のないmajor-shift、同一Surface 28秒超、card-board 55%超、Gap初期同時表示、分足なしverified-series、Scene 8 weaken欠落、Scene 9新証拠、Fallback後report欠落、registry SHA不一致、TTS identity変更、狐位置・基本サイズ変更、AI visual QA追加、final自動実行。

既存2.2.0/2.3.0 fixture、Financial Visual、Episode Memory、Final Production Package、Renderer Handoff、Real-Day Acceptance、TTS 2ブロック、Asset Registry、Preview inspectionを回帰対象にする。

## 16. 完成条件

技術完成：render_spec 2.4.0、両registry SHA一致、全Stage Shell、structural/measured diversity、TTS identity不変、Preview/音声/delivery manifest、既存CIがPASS。

番組完成：ユーザーがA/B Previewを目視し、Sceneごとの進展、狐の案内役、Gap理解、世界→NASDAQ経路、比較の非ランキング性、Scene 8まで見る理由、単調性低減を確認する。

finalはユーザーが明示依頼した場合だけ実行する。
