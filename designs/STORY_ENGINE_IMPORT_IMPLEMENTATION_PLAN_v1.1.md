# 朝のNASDAQカフェ｜Story Engine Import Implementation Plan v1.1

- 作成日: 2026-08-07
- 対象リポジトリ: `saienjoy0/nasdaq-plot-creator-`
- 基準: `main@7d34a1bb69720be3916b97b6868ce99da2174bfb`
- 上位設計: `designs/STORY_ENGINE_IMPLEMENTATION_BLUEPRINT_v1.0.md`
- 外部採用正本: `references/STORY_ENGINE_DIRECT_IMPORT_MATRIX.md`
- 状態: v1.0の思想を維持し、03/04との衝突と過剰分割を除いた実装正本

---

## 0. 最終決定

Story Engineを新しい巨大システムとして作らない。

既存の優れたStorytelling OSSから、ライセンス上安全で目的に合う資産・構造を再利用し、NASDAQカフェ固有の差分だけを薄いAdapterとGuardとして実装する。

```text
validated causal dossier
        ↓
     02 LOCK
事実・因果・時系列・確信度を固定
        ↓
     STORY PLAN
        ↓
     FOX SCRIPT
        ↓
 INDEPENDENT CRITIC
        ↓
 TARGETED PATCH
        ↓
 CAUSALITY GUARD
        ↓
      04 PASS
        ↓
episode_package_final
        ↓
既存 image / render_spec / validator / preview
```

変更対象は `causal_dossier_valid → episode_package_final` の中央区間だけとする。

Memory、Causal Research、Episode Memory、画像採用、Final Production、Renderer Handoff、Preview / Final gateは作り直さない。

---

## 1. v1.0からの重要修正

### 1.1 中間Stateを減らす

v1.0:

```text
causal_dossier_valid
→ story_discovery_valid
→ story_angle_selected
→ narrative_arc_valid
→ script_draft_ready
→ creative_review_passed
→ episode_package_final
```

v1.1:

```text
causal_dossier_valid
→ story_plan_valid
→ script_draft_ready
→ creative_review_passed
→ episode_package_final
```

Story Discovery、Angle Competition、Narrative Arcは削除しない。

ただし別々の本番Stateや大量のsidecarへ分割せず、`story_plan.json`の内部Stageとして扱う。

### 1.2 本番sidecarを4つへ縮小する

```text
working/YYYY-MM-DD/story-engine/
├── story_plan.json
├── script_draft.json
├── creative_review.json
└── story_acceptance.json
```

Rewrite round、finding history、causality diffは`creative_review.json`の履歴として保持する。

Debug用途で補助artifactを出すことは許可するが、本番契約の必須artifactを増やさない。

### 1.3 Scene 9をBookendにしない

03の正式仕様ではScene 9は固定エンディングであり、新しい論点を追加しない。

よってv1.0の「Scene 9で冒頭を別の理解として回収」は修正する。

```text
Scene 8後半 = Closing Reframe / Bookend
Scene 9     = 固定エンディングのみ
```

Scene 9は`closing-recap`で既出要点を回収できるが、新しいEvidence、因果、問い、投資判断を追加しない。

### 1.4 9Sceneの削除・並べ替えをPatchにしない

03は9Sceneの順番と役割を原則維持する。
04も9Sceneの基本的役割を変更禁止としている。

したがって本番Patchから次を外す。

```text
remove_scene
merge_scene
reorder_scene
```

許可するPatch:

```text
rewrite_scene
compress_scene
replace_connector
move_reveal_within_scene
move_content_to_compatible_scene
add_clarity_bridge
add_callback
restore_counterevidence
restore_causality_wording
adjust_visual_beat
```

9Sceneの基本骨格そのものが成立しない場合はPatchで誤魔化さず03へ戻す。

---

## 2. 変えてはいけないもの

Story Engineは02で確定した次を変更しない。

- 主役ニュース / 主役テーマ
- Expected / Actual / Gap
- Expectedの根拠区分と出典
- 主因 / 増幅 / 相殺 / 未確認
- 主役銘柄の直接材料とNASDAQ全体の因果範囲
- timeline anchors
- confidence
- counterevidence
- confirmed / interpretation / inference / unknownの区別

Story Engineが許可されるのは、同じ証拠を「どの順番で理解させるか」「どこで問いを開き、どこで回収するか」「どの言葉なら狐が自然に説明できるか」の設計である。

---

## 3. 外部OSS採用方式

各外部assetを次の4分類へ固定する。

| 分類 | 意味 |
|---|---|
| `direct-vendor` | MIT / Apache-2.0等で、独立して安全に使える資産を元commit固定・帰属付きで保存する |
| `adapt` | 許諾されたコード/文書を参考に薄く改変する。ただしNASDAQ固有契約を優先する |
| `clean-room` | 設計思想のみ参照し、コード・schema・prompt本文はコピーしない |
| `reject` | runtime依存、目的不一致、強いcopyleft、過剰機能などのため導入しない |

外部repo本体をsubmoduleや日次runtime dependencyにしない。

外部repoのlatestを日次に自動取得しない。

採用は必ずpinned commitへ固定する。

---

## 4. Doza Assist｜直接vendorするStorytelling Foundation

### Source

- Repository: `DozaVisuals/doza-assist`
- Pinned commit: `b93e6b912ca17a85c8ceaca93983c23695063679`
- License: MIT
- Vendor対象:
  - `docs/storytelling-foundation-oss.md`
  - `LICENSE`
- 参考コード:
  - `editorial_dna/storytelling.py`

### 採用判断

`docs/storytelling-foundation-oss.md`は上記pinned commitで公開され、Repository LICENSEはMITであるため、帰属とlicenseを保持して`direct-vendor`可能と判断する。

ただし文書をそのままNASDAQ台本生成promptへ全量注入しない。

理由:

- documentary/interview固有のbreath、filler、emotional valence規則が混在する
- 01〜04より優先されてはいけない
- 不要なcontextを毎回入れると台本の判断がぶれる

### 直接使う原則

NASDAQ Adapterで次だけを選択する。

- Hookは問い、反直感、明確なGapから始める
- Adjacent redundancyはmomentumを壊す
- Turnのない並びはstoryではなくlist
- TopicとTheme/Claimを分ける
- Information onlyではScene採用理由にならない
- Story roleを明示する
- midpoint reversal / turnを置く
- roleを守りながら重複部分を先に圧縮する
- 最終Self-checkを持つ

### 使わない原則

- speech filler密度
- breath gap
- tense shift
- documentary protagonist emotional transformation
- clip in/out point
- FCP/Premiere向け編集判断

### Adapter

`nasdaq_story_rules.md`を新規作成し、各採用ruleについて次を記録する。

```text
external rule
→ NASDAQ meaning
→ 01〜04 binding
→ allowed use
→ forbidden use
```

例:

```text
Doza: A sequence without a turn is a list.
→ NASDAQ: Scene 4〜6のどこかで中心仮説の説明力が変わる必要がある
→ 03: Scene 4〜6の正式役割は維持
→ 04: Scene 6〜8まで見る理由を作る
→ 禁止: Turnを作るためにEvidence順やmarket timelineを改変しない
```

---

## 5. Toonflow｜責任分離をadaptする

### Source

- Repository: `HBAI-Ltd/Toonflow-app`
- Pinned commit: `bc61ec7a1b5df31293b286981a5f4ad4635464ee`
- License: Apache-2.0
- 参照:
  - `data/skills/script_agent_decision.md`
  - `data/skills/script_agent_supervision.md`
  - `src/agents/scriptAgent/index.ts`

### 採用する構造

```text
Decision
→ Execution
→ Supervision
```

NASDAQ変換:

```text
Decision     = 02 Editorial Lock + Story Plan選定
Execution    = Fox Script Author
Supervision  = Independent Critic + 04 + deterministic guard
```

採用ルール:

- Execution成功前にReviewしない
- Reviewerは作者の自己説明を根拠にしない
- Reviewerは具体的な位置、問題、影響、修正案を返す
- Reviewは成果物を実際に読む
- Reviewと修正を同じAgent responsibilityにしない

直接実行しないもの:

- short-drama用の課金点
- 情緒爆点
- 大三角
- 小説章管理
- Toonflow DB / UI / provider

Toonflow prompt本文をNASDAQのruntime promptへそのまま貼らない。
構造のみadaptし、01〜04へ合わせて独自Skillを作る。

---

## 6. ViMax｜Targeted RevisionとStale Invalidationをadaptする

### Source

- Repository: `HKUDS/ViMax`
- Pinned commit: `05a48943878312d88fe5a016c12a9654940ecc43`
- License: MIT
- 参照:
  - `agent_runtime/vimax_adapters.py`
  - `tests/test_wrong_output_guards.py`

### 採用する構造

ViMaxはstructured text artifactを先に作り、特定artifactだけをrevisionし、その変更で後段artifactをstaleにする。

NASDAQへ次のようにadaptする。

```text
story_plan changed
→ script_draft stale
→ creative_review stale
→ story_acceptance stale

script_draft changed
→ creative_review stale
→ story_acceptance stale

creative_review patch applied
→ final review required
→ story_acceptance stale until re-review + causality guard pass
```

targeted patchは問題Scene / fieldだけを変更する。

partial failure時も、成功済み上流artifactを破壊しない。

異なるepisode_date / causal dossier SHAへ既存Story Engine artifactを流用しない。

### 導入しないもの

- ViMax画像生成
- ViMax動画生成
- character consistency
- LangChain/provider stack
- ViMax session runtimeそのもの

小さなstale dependency graphだけをNASDAQ用にclean-room/adapt実装する。

---

## 7. FireRed-OpenStoryline｜Affected-stage rerunをadaptする

### Source

- Repository: `FireRedTeam/FireRed-OpenStoryline`
- Pinned commit: `c9e945215586f45c12a61c1951ee9a8e9c43a027`
- License: Apache-2.0
- 参照:
  - `.storyline/skills/default_editing_workflow_skill/SKILL.md`
  - `docs/source/en/guide.md`

### 採用する構造

問題が出たら全pipelineを最初から回さず、責任のあるStageへ戻る。

NASDAQ return map:

```text
market fact / causality / Expected / timeline problem
→ 02 / Causal Research

angle / central contradiction / no turn problem
→ STORY PLAN

fox voice / clarity / repeated wording problem
→ FOX SCRIPT

critic finding only
→ TARGETED PATCH

9Scene role / package production contract problem
→ 03

image / selected path problem
→ image-selection stage

render contract problem
→ render_spec / validator
```

このreturn mapをCritic findingへ機械的に記録する。

---

## 8. video_explainer｜Information GapとPlan→Scriptをclean-room採用する

### Source

- Repository: `prajwal-y/video_explainer`
- Pinned commit: `c033e28d6eccae43c1762f4653f9c320b16b050e`
- `pyproject.toml` / README: MIT宣言
- root `LICENSE` file: pinned commitで取得できず
- 参照:
  - `src/script/generator.py`

### License判断

MIT宣言は確認できるが、root LICENSE本文をpinned commitで取得できていないため、初期実装ではコード・prompt本文をdirect-vendorしない。

`clean-room`として次の一般原則を採用する。

- approved planからscriptを書く
- central questionを一本にする
- information gapを作ってから説明する
- mechanismを説明する
- sourceの具体的数字を使う
- Scene接続を`BUT / THEREFORE`中心にする
- visual descriptionをnarrationの意味へ結ぶ

NASDAQではsource網羅率を目的にしない。
主役一本＋NASDAQへの因果だけを残す02を優先する。

---

## 9. OpenMontage｜Clean-room only

### Source

- Repository: `calesthio/OpenMontage`
- Pinned commit: `4eab34c5cfcccaa4f1970554928feccce73ee930`
- License: AGPL-3.0

### 採用する一般原則

- Proposal / Script / Scene Plan / Review / CheckpointのStage分離
- Angle Competition
- Guided Discovery
- Progressive Revelation
- BUT / THEREFORE
- artifact location付きReviewer finding
- Criticalを直してからre-review
- Stageごとのsuccess criteria

### 禁止

- codeコピー
- schemaコピー
- prompt本文コピー
- OpenMontage runtime dependency
- AGPL資産の部分vendor

すべてNASDAQ用にclean-room実装する。

---

## 10. Story Plan contract

正式artifact:

`working/YYYY-MM-DD/story-engine/story_plan.json`

最小構造:

```json
{
  "contract_version": "1.1.0",
  "episode_date": "YYYY-MM-DD",
  "causal_dossier_sha256": "64hex",
  "central_contradiction": "",
  "central_question": "",
  "headline_beyond_discovery": "",
  "naive_explanations": [],
  "angle_candidates": [],
  "selected_angle": {},
  "story_spine": "",
  "opening_promise": "",
  "midpoint_turn": {},
  "closing_reframe": {},
  "open_loops": [],
  "scenes": []
}
```

### Naive Explanation

各候補はdossier Evidenceで次へ分類する。

```text
survives
weakened
rejected
unresolved
```

新しい因果は作らない。

### Angle Competition

最低3案を作るが、文言だけ違う案は別案と数えない。

各案:

- central question
- angle type
- story spine
- turn
- causality scope
- evidence IDs
- counterevidence IDs
- risk
- why distinct

02の主役・causal scopeを変更する案は失格。

### 9Scene belief arc

各Scene:

```json
{
  "scene_id": "scene-01",
  "formal_role": "03の正式役割",
  "story_role": "",
  "viewer_belief_before": "",
  "new_evidence_ids": [],
  "new_meaning": "",
  "viewer_belief_after": "",
  "remaining_question": "",
  "connector": "but|therefore|contrast|callback|opening|closing"
}
```

Scene成立条件:

- new Evidenceがある
- または既存Evidenceからnew Meaningがある

どちらもない場合はCritical。

### Midpoint Turn

Scene 4〜6のどこかに必要。

優先位置:

1. Scene 6
2. Scene 5
3. Scene 4

Scene 4で答えを出し切り、Scene 6〜8が確認作業の反復になる構成は失格。

Turnは次のいずれか:

- naive explanationが崩れる
- hypothesisの説明力が強まる / 弱まる
- company scopeとNASDAQ scopeが分離される
- comparisonで評価軸が見える
- reason unknownが正しい結論になる

Turnを作るためにtimelineを変えない。

### Open Loop

最大2本。

Scene 8までに閉じる。

Scene 9へ未解決の新しい問いを持ち越さない。

### Closing Reframe

Scene 8後半に置く。

Scene 1の単純な言い換えではなく、Scene 2〜8を通過した結果として意味が変わった一文にする。

---

## 11. Fox Script Authoring

入力:

- validated causal dossier
- validated story_plan
- 01
- 03

作者は04の自己採点結果を見ながら文章を書かない。

Narration rule:

- 一人称「僕」
- 狐一人
- 数字→比較→意味
- 結論を先にする
- 必要な出典主体だけ自然に示す
- Procedure languageを減らす
- Scene間はBUT / THEREFORE / contrast / callbackで意味を接続する
- IT比喩0〜2
- 自虐等0〜1
- 記録されていない狐の経験を作らない

Procedure language警報:

```text
確認します
三つ見ます
順番に見ます
数字を置きます
次に見ます
ここまで整理します
```

視聴者への必要な案内でない限り書き換える。

---

## 12. Independent Critic

入力:

- causal dossier
- story_plan
- script_draft
- 01〜04

入力しないもの:

- 作者の自己評価
- 「ここは面白くした」等の作者意図説明

Findingは次を必須にする。

```json
{
  "finding_id": "finding-001",
  "severity": "critical|major|suggestion|investigation",
  "code": "NO_LATE_PAYOFF",
  "scene_ids": ["scene-07"],
  "artifact_path": "scenes[6].narration",
  "anchor": "",
  "problem": "",
  "viewer_effect": "",
  "minimal_fix": "",
  "return_stage": "story_plan|fox_script|03|02|image|render",
  "must_preserve": {}
}
```

Blocking codes:

```text
REPEATED_CONCLUSION
NO_BELIEF_CHANGE
ANSWER_REVEALED_TOO_EARLY
NO_MIDPOINT_TURN
NO_LATE_PAYOFF
PROCEDURAL_NARRATION
FOX_VOICE_ABSENT
OPEN_LOOP_UNRESOLVED
CAUSALITY_DRIFT
COUNTEREVIDENCE_REMOVED
TIMELINE_DRIFT
NASDAQ_SCOPE_OVERREACH
```

Criticalが1件でも残る場合は`creative_review_passed`へ進めない。

04の点数が高くてもCritical findingを上書きしない。

---

## 13. Targeted Patch

原則としてfinding対象fieldだけを修正する。

修正前後を記録する。

```text
finding_id
patch_type
changed_fields
before
 after
evidence IDs before / after
counterevidence before / after
confidence before / after
causality scope before / after
return stage
re-review result
```

全体書き直しが必要な条件:

- central contradiction自体が不成立
- angleがdossierで支持されない
- midpoint turnが成立しない
- openingとScene 8 reframeが別テーマ
- causal scopeが誤っている

この場合はFox Scriptを全生成し直すのではなくStory Planへ戻る。

---

## 14. Causality Guard

Patch前後で最低限次を比較する。

- Evidence ID集合
- Expected / source category
- Actual
- Gap
- primary / amplifier / offsetting / unresolved
- causality scope
- confidence
- counterevidence ID集合
- timeline anchors
- public wording strength

禁止差分:

```text
Medium → High相当へ断定強化
unknown → known
company → NASDAQ primary
counterevidence削除
Expected追加
timeline順序変更
Evidenceなしの新因果
```

禁止差分が一つでもあればPatchを破棄し02へ戻す。

---

## 15. Stale Dependency Graph

ViMaxのtargeted revision / stale invalidation思想をNASDAQ向けに縮小実装する。

```text
causal_dossier change
→ story_plan stale
→ script_draft stale
→ creative_review stale
→ story_acceptance stale

story_plan change
→ script_draft stale
→ creative_review stale
→ story_acceptance stale

script_draft change
→ creative_review stale
→ story_acceptance stale

creative_review patch
→ final re-review required
→ story_acceptance stale
```

各artifactはupstream SHAを保持する。

日付一致だけでは再利用を許可しない。

---

## 16. 2026-08-06 failure fixture

最初の回帰fixtureは2026-08-06回。

旧台本へ期待するCritical:

```text
REPEATED_CONCLUSION
NO_BELIEF_CHANGE
ANSWER_REVEALED_TOO_EARLY
PROCEDURAL_NARRATION
FOX_VOICE_ABSENT
NO_LATE_PAYOFF
```

新経路に要求する性質:

- Scene 1に方向・矛盾・問い
- Sceneごとにnew evidenceまたはnew meaning
- Scene 4〜6にTurn
- Scene 6〜8に検証価値
- Scene 8でBookend / Closing Reframe
- Scene 9は固定終了で新論点なし
- Critical 0
- causality guard PASS
- 旧版より重複が少ない
- 事実、timeline、counterevidence、confidenceを弱めない

正解本文をgolden textとして固定しない。
性質と因果保存をテストする。

---

## 17. PR実装単位

旧S1〜S7を3本へ圧縮する。

### PR-A｜Foundation + Story Plan

旧S1 + S2 + S3相当。

実装:

- external source / license registry
- Doza Storytelling Foundation direct vendor
- NASDAQ storytelling adapter rules
- 2026-08-06 failure fixture
- `story_plan` contract
- validator
- shadow mode Story Plan

本番state machineにはまだ接続しない。

### PR-B｜Fox Author + Independent Critic

旧S4 + S5相当。

実装:

- Fox Script Authoring
- Independent Critic
- targeted patch
- causality guard
- stale dependency graph
- 2026-08-06 old/new text A/B artifact

本番後段にはまだ接続しない。

### PR-C｜Daily Integration + A/B Acceptance

旧S6 + S7相当。

実装:

```text
causal_dossier_valid
→ story_plan_valid
→ script_draft_ready
→ creative_review_passed
→ episode_package_final
```

- Story Engine acceptance SHA binding
- stale / forged artifact拒否
- existing downstream regression
- same dossier A/B
- preview生成
- user visual/text review

ユーザー確認前にfinalへ進まない。

---

## 18. Runtime dependency policy

禁止:

- Doza / Toonflow / ViMax / FireRed / OpenMontage / video_explainer本体をpip/npm dependencyにする
- submodule
- 日次実行で外部repo clone
- latest branch取得
- 外部APIへ主役・因果・台本の意味を委任
- external project更新で同じdossierから別結果になる構成

許可:

- pinned external reference assets
- attribution付きvendor document
- small isolated helperをlicense gate後にvendor
- NASDAQ用Adapter / Validatorから固定参照

---

## 19. Attribution layout

直接vendorする場合:

```text
references/external/<project>/
├── SOURCE.md
├── PINNED_COMMIT
├── LICENSE
├── NOTICE.md        # 必要な場合
├── MODIFICATIONS.md
└── vendor asset
```

`SOURCE.md`には最低限次を記録する。

- repository
- pinned commit
- original path
- license
- fetched date
- adoption mode
- why imported
- runtime usage
- excluded rules

---

## 20. Acceptance

技術PASS:

- story_plan schema PASS
- Evidence参照PASS
- upstream SHA PASS
- stale artifact拒否
- Critic final critical 0
- causality guard PASS
- 01〜04 mapping PASS
- downstream regression PASS

編集PASS:

- 9Sceneが九段階の理解変化になっている
- Scene 4〜6に意味のあるTurn
- Scene 6〜8を見る理由が残る
- Scene 8で冒頭の問いを新しい理解として回収
- Scene 9は新論点を増やさない
- 狐が監査担当ではなく案内役
- 同じ結論の反復が減る
- 見出し以上の発見が一つ以上ある
- counterevidenceと留保が残る

最終採用:

同じcausal dossierの旧版と新版をユーザーが比較し、

- 前より興味深い
- 後半まで見る理由がある
- 狐らしい
- 分かりやすい
- 因果が弱くなっていない

を確認した後に新Story Engineを本番defaultへ切り替える。

---

## 21. 実装開始順

1. Doza外部資産をpinned vendor登録
2. Direct Import Matrixを最新調査へ更新
3. NASDAQ Story Rule Adapterを作る
4. 2026-08-06 failure fixtureを固定
5. `story_plan.json` schema / validator
6. shadow Story Plan生成
7. Fox Author / Critic / Patch / Guard
8. A/B
9. Daily Productionへ接続
10. preview
11. user review
12. 明示依頼がある場合だけfinal

この順序を変更して、Story Engine未検証のままDaily Productionへ接続しない。