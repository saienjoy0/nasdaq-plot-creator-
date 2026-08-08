# 朝のNASDAQカフェ｜統合Story Engine最終設計 v1.1

- 作成日: 2026-08-06
- 対象リポジトリ: `saienjoy0/nasdaq-plot-creator-`
- 基準main: `7d34a1bb69720be3916b97b6868ce99da2174bfb`
- 状態: 実装正本
- 上位正本: プロジェクト指示、01、02、03、04
- 参照設計:
  - `designs/STORY_ENGINE_OVERHAUL_MASTER_DESIGN.md`
  - `designs/STORY_ENGINE_IMPLEMENTATION_BLUEPRINT_v1.0.md`
  - `references/STORY_CREATION_EXTERNAL_PROJECT_ADOPTION.md`
  - `references/STORY_ENGINE_DIRECT_IMPORT_MATRIX.md`

この文書は、従来のPR-S2〜PR-S5分割案を置き換える。

```text
旧案
PR-S2 Story Discovery
PR-S3 Narrative Arc
PR-S4 Fox Script Authoring
PR-S5 Independent Critic / Patch / Re-review

最終案
統合PR-A Unified Story Engine Vertical Slice
```

旧設計の調査結果、外部採用判断、因果保全原則は維持する。変更するのは実装単位と契約の粒度である。

---

## 1. 最終決定

Story Discovery、Narrative Architecture、Fox Script Authoring、Independent Critic、Targeted Rewrite、Causality Diffを、一つのSkillの内部Passとして実装する。

```text
causal_research_dossier
↓
nasdaq-cafe-story-engine
  Pass A  Story Discovery
  Pass B  Narrative Architecture
  Pass C  Episode Package Authoring
  Pass D  Independent Entertainment Critic
  Pass E  Targeted Rewrite
  Pass F  Causality Preservation
  Pass G  Final Re-review
↓
episode_package_final
```

分離するものは責任、実行context、immutable snapshotである。

分離しないものはSkill、Daily Production state、正式なStory Engine artifactである。

### 1.1 一つにまとめる理由

- Story DiscoveryとNarrative Arcは同じ中心矛盾とEvidenceを扱う
- 狐台本とVisual Beatは03の完成制作パッケージとして同時に整合させる必要がある
- Criticは完成したDraft Episode Package全体を評価しなければならない
- 内部Passごとにstateを増やすと日次運用が複雑になる
- 別Skill間の受け渡しだけが増え、内容品質が上がる保証はない

### 1.2 一つにまとめても維持する独立性

一つのSkillであっても、AuthorとCriticは別invocationとする。

```text
Author invocation
→ Draft Episode Package固定
→ SHA-256固定
→ Author context破棄
→ Critic invocation
```

CriticをAuthorの自己採点として実行してはいけない。

---

## 2. 責任境界

### 2.1 Story Engineが変更してよいもの

- 説明順序
- 冒頭の問いの置き方
- 視聴者が最初に考えやすい単純説明
- どの既存EvidenceをTurn、Complication、Boundaryとして使うか
- Scene間の接続
- 重複説明の削除・統合
- 専門語の言い換え
- 身近な比較または短いたとえ
- 狐の短い反応
- テロップの圧縮
- タイトル、サムネイル、概要欄の表現
- Visual Beatの説明順と画面状態

### 2.2 Story Engineが変更してはいけないもの

- 主役ニュースまたは主役テーマ
- 中心仮説
- 事実、数値、日時
- Expected / Actual / Gapの内容
- Expectedの根拠区分
- 情報源区分
- causality scope
- confidence
- 主因、増幅要因、相殺要因、未確認要因
- 重要な反対材料
- 時系列
- 可能性表現、留保
- 主役銘柄とNASDAQ全体の因果範囲
- 9Sceneの正式役割
- 狐の人物設定
- 狐の保有情報、損益、過去の出来事
- 投資助言禁止

### 2.3 戻り先

Story Engine内で直してよいのは、事実と因果を変えない編集上の問題だけである。

```text
事実誤認、根拠不足、時系列不整合、因果過剰
→ Causal Researchまたは02へ戻す

主役・中心仮説が物語として成立しない
→ 02へ戻す

9Sceneの正式役割と矛盾
→ 03へ戻す

狐設定・創作禁止との矛盾
→ 01へ戻す

興味深さ、重複、説明順、難語、接続
→ Story Engine内で修正
```

---

## 3. Skill構成

新規Skillは一つだけとする。

```text
skills/nasdaq-cafe-story-engine/
├── SKILL.md
├── README.md
├── contracts/
│   ├── story_engine_package.schema.json
│   └── story_engine_validation_report.schema.json
├── validators/
│   ├── validate_story_engine_package.py
│   └── validate_story_engine_hardening.py
├── references/
│   ├── adopted_story_rules.md
│   ├── claim_ledger_rules.md
│   ├── failure_codes.md
│   └── patch_rules.md
└── fixtures/
    ├── boring_2026-08-06/
    ├── valid_single_driver/
    ├── valid_multi_factor/
    └── valid_reason_unknown/
```

Story Discovery、Narrative Architect、Screenwriter、Criticの別Skillは初期実装では作らない。

将来分割する条件は次のいずれかに限定する。

- 別々のモデルまたは別権限で実行する必要が出た
- artifactサイズが一つのcontextに収まらない
- retry単位を分離しなければ運用コストが高くなる
- 独立チームが各工程を所有する

---

## 4. 正式入力

Story Engineが読む正式入力は次とする。

```text
causal_research_dossier_YYYY-MM-DD.json
01_fox_character_bible.md
02_editorial_bible.md
03_episode_production_spec.md
04_entertainment_inquisitor.md
当日のEditorial Memory使用記録
必要なResearch Input Manifest
```

各入力はpathとSHA-256へ固定する。

入力に不足がある場合、Story Engineは創作で補完しない。

### 4.1 開始条件

- causal dossier validatorがPASS
- episode_dateが全入力で一致
- 01〜04の正本pathが解決済み
- 主役または主役テーマが確定
- Expected / Actual / Gapが確定またはExpected未確認が明示
- causality scopeとconfidenceが記録済み
- 重要な反対材料が記録済み

開始条件を満たさない場合、台本作成へ進めない。

---

## 5. 正式成果物

正式な機械可読成果物は一つにまとめる。

```text
working/YYYY-MM-DD/story_engine_package_YYYY-MM-DD.json
```

人間向け正式成果物は従来どおり次とする。

```text
episodes/YYYY-MM-DD/episode_package_YYYY-MM-DD.md
```

検証結果は次へ出す。

```text
verification/YYYY-MM-DD/story_engine_validation_report.json
```

Draft Episode Packageは公開成果物ではないが、Story Engine package内にimmutable snapshotとして保持する。

### 5.1 上書き禁止

同じfieldを更新して履歴を消してはいけない。

```json
{
  "author_draft": {
    "episode_package_sha256": "...",
    "snapshot": {}
  },
  "review_rounds": [
    {
      "round": 1,
      "input_sha256": "...",
      "findings": [],
      "patches": [],
      "output_sha256": "..."
    }
  ],
  "final": {
    "episode_package_sha256": "...",
    "review_status": "pass"
  }
}
```

---

## 6. Story Engine packageの構造

```json
{
  "contract_version": "1.1.0",
  "episode_date": "YYYY-MM-DD",
  "source_binding": {},
  "editorial_baseline": {},
  "claim_ledger": [],
  "story_discovery": {},
  "selected_angle": {},
  "narrative_arc": {},
  "author_draft": {},
  "review_rounds": [],
  "causality_diff": {},
  "final": {},
  "final_gate": {}
}
```

### 6.1 source_binding

- causal dossier path / SHA
- 01〜04 path / SHA
- memory usage record path / SHA
- Story Engine Skill version
- generator model identifier
- author invocation identifier
- critic invocation identifier

### 6.2 editorial_baseline

- lead
- lead type: news / theme / composite / reason_unknown
- central hypothesis
- story spine draft
- Expected / Actual / Gap
- Expected evidence category
- primary driver
- amplifiers
- offsets
- unresolved factors
- causality scope
- confidence
- evidence IDs
- counterevidence IDs
- timeline

---

## 7. Claim Ledger

Causality Diffの正本として、公開可能な主張をClaim単位で固定する。

```json
{
  "claim_id": "CL-001",
  "subject": "",
  "predicate": "",
  "object": "",
  "claim_type": "fact|shared_interpretation|inference|unknown",
  "causal_scope": "company|sector|nasdaq_support|nasdaq_primary|reason_unknown",
  "confidence": "high|medium|low|unknown",
  "evidence_ids": [],
  "counterevidence_ids": [],
  "required_modality": "",
  "forbidden_strengthenings": []
}
```

### 7.1 required_modality

例:

```text
fact
→ 断定可能

shared_interpretation
→ 主体を示す

inference medium
→ 主な重荷になったとみられる

inference low
→ 意識された可能性がある

unknown
→ 明確な理由は確認できない
```

### 7.2 Rewrite後の禁止変化

- inferenceをfactへ変更
- low / mediumをhigh相当の表現へ変更
- company scopeをNASDAQ primaryへ変更
- counterevidenceの削除
- required modalityの削除
- Expected未確認を市場期待として断定

---

## 8. Pass A｜Story Discovery

このPassではナレーションを書かない。

### 8.1 必須出力

- obvious headline
- before context
- central contradiction
- naive explanation candidates
- Evidenceによる説明テスト
- explanation update
- headline-beyond discovery
- after implication
- angle candidates

### 8.2 角度候補数

角度は原則2〜3案とする。

3案を機械的に強制しない。

```text
複数の角度がEvidence上成立
→ 2〜3案を比較

一つしか成立しない
→ 1案＋他案を作れない理由

理由不明
→ 原因を創作せず、見せ方の角度を比較
```

### 8.3 角度タイプ

- contradiction
- misconception
- competition
- evaluation_shift
- transmission
- composite
- reason_unknown

### 8.4 選択基準

1. 02の因果を最も正確に保持する
2. 昨夜の重要な矛盾を説明する
3. 見出し以上の発見がある
4. Scene 6〜8まで検証価値を残せる
5. 重要な反対材料を自然に扱える
6. NASDAQへの範囲を過剰に広げない

派手さ、企業知名度、値動きの大きさだけで選ばない。

---

## 9. Pass B｜Narrative Architecture

03の正式9Sceneを維持し、その上に物語上の役割を付与する。

### 9.1 先に固定するもの

- opening promise
- central question
- understanding update
- closing reframe
- open loops

### 9.2 Turnの扱い

Scene 4〜6の劇的Turnを絶対条件にしない。

Scene 4〜7のどこかで、次の一つ以上の理解更新を必須とする。

- turn
- complication
- boundary
- counterevidence
- disproof
- reveal

必須なのはドラマ的反転ではなく、視聴者の理解が一段変わることである。

### 9.3 Scene contract

```json
{
  "scene_id": "scene-04",
  "official_role": "",
  "story_roles": [],
  "viewer_belief_before": "",
  "new_evidence_ids": [],
  "new_meaning": "",
  "viewer_belief_after": "",
  "remaining_question": "",
  "connector": "but|therefore|contrast|callback|continuation",
  "open_loop_ids_opened": [],
  "open_loop_ids_closed": [],
  "deletion_consequence": ""
}
```

### 9.4 Scene成立条件

Sceneは次のどちらかを満たす。

- 新しいEvidenceを示す
- 既存Evidenceから新しいMeaningを生む

新しいEvidenceも新しいMeaningもない場合は重複候補である。

### 9.5 冒頭

Scene 1〜2で方向、矛盾、問いを示す。

結論の方向を隠さない。

ただし、冒頭で次まで説明し切ってはいけない。

- 主要証拠
- 波及経路
- 重要な反対材料
- 仮説の限界
- 今夜の検証条件

旧FAILコード`ANSWER_REVEALED_TOO_EARLY`は廃止する。

新FAILコード:

```text
HOOK_EXHAUSTS_THE_STORY
```

### 9.6 Open Loop

- 中心質問は一つ
- Open Loopは最大2つ
- 原則Scene 8までに回収
- 回収不能ならEvidence-backed unresolvedとして明示
- Scene 9で新しい問いを開かない

### 9.7 Scene順変更

一般的な`reorder_scene` Patchは採用しない。

許可するのは`move_explanation_block`であり、次を守る。

- 発表時系列を変えない
- 値動きと材料の前後を偽装しない
- 同時材料を隠さない
- 比較、補足、説明だけを移動する

---

## 10. Pass C｜Episode Package Authoring

Criticは完成制作パッケージを審問するため、Pass CでDraft Episode Package全体を完成させる。

### 10.1 内部順序

```text
C1 Fox Reaction Map
C2 Narration
C3 Performance Intent / Expression
C4 Visual Beat / Screen State
C5 Telops / Numbers
C6 Title / Thumbnail / Description
C7 Primary / Approved Fallback記録
C8 Draft Episode Package assembly
```

### 10.2 狐の声

- 一人称は必ず「僕」
- 狐一人の語り
- 先生ではなく案内役
- 短い文
- 数字のあとに意味
- 事実 → 違和感 → 解釈 → 留保を必要に応じて使う
- IT比喩0〜2回
- 自虐、貧乏、損失、レバレッジ小ネタ合計0〜1回
- 記録されていない大学生活、香港生活、取引、損失を創作しない
- 視聴者へ売買を勧めない

### 10.3 手続き口調

次を原則として公開ナレーションへ出さない。

- 三点確認します
- 順番に見ます
- 次は市場反応です
- ここで整理します
- 仮説を検証します

説明の進行を宣言せず、説明そのものを進める。

### 10.4 Draft固定

Draft Episode Package完成後、SHA-256を固定する。

Authorの自己採点はCritic入力に含めない。

---

## 11. Pass D｜Independent Entertainment Critic

### 11.1 実行分離

Criticは新しいcontextで実行する。

Criticに渡すもの:

- editorial baseline
- Claim Ledger
- selected angle
- Draft Episode Package
- 01〜04
- Evidence参照
- Draft SHA

Criticに渡さないもの:

- Authorの自己採点
- Authorの制作理由
- 採用しなかった文案
- Authorの思考メモ
- Authorの「面白いはず」という説明

### 11.2 Critic対象

台本だけでなく完成Draft Episode Package全体を審問する。

- 9Scene進行
- ナレーション
- Visual Beat
- 画面状態
- テロップ
- 数字
- 狐の表情と演技
- Primary / Approved Fallback
- 画面多様性
- タイトル
- サムネイル
- 概要欄
- Scene 8の検証条件

### 11.3 Critic finding

```json
{
  "finding_id": "CR-001",
  "code": "REPEATED_CONCLUSION",
  "severity": "critical|major|suggestion|investigation",
  "scene_ids": [],
  "field_paths": [],
  "anchor_text": "",
  "viewer_effect": "",
  "required_fix": "",
  "must_preserve": {
    "claim_ids": [],
    "evidence_ids": [],
    "causal_scope": "",
    "confidence": ""
  },
  "status": "pending|fixed|accepted|blocked"
}
```

### 11.4 必須審問

- 各Sceneで理解が進むか
- Scene順を入れ替えても成立しないか
- 同じ結論を別表現で反復していないか
- Scene 6〜8まで見る理由があるか
- 見出し以上の発見があるか
- 最大の離脱候補はどこか
- 狐が監査報告者になっていないか
- 手続き口調が残っていないか
- タイトルの約束を回収したか
- 反対材料と留保を保持しているか
- 画面がナレーションの文字起こしになっていないか

### 11.5 重大FAIL

```text
REPEATED_CONCLUSION
NO_BELIEF_CHANGE
NO_NEW_EVIDENCE_OR_MEANING
HOOK_EXHAUSTS_THE_STORY
NO_UNDERSTANDING_UPDATE
NO_LATE_PAYOFF
ENDING_NOT_BOOKENDED
PERMUTABLE_SCENES
PROCEDURAL_NARRATION
ABSTRACT_EDITORIAL_LANGUAGE
FOX_VOICE_ABSENT
COUNTEREVIDENCE_UNUSED
TITLE_PROMISE_NOT_RECOVERED
VISUALS_REPEAT_NARRATION
VISUAL_VARIETY_COLLAPSED
```

点数が高くてもCritical findingが残る場合はPASSしない。

---

## 12. Pass E｜Targeted Rewrite

全文再生成を原則禁止する。

### 12.1 Patch types

```text
merge_redundant_content
remove_repetition
rewrite_scene
move_reveal_later
strengthen_information_gap
replace_procedural_bridge
add_callback
simplify_jargon
restore_counterevidence
restore_causality_wording
compress_telop
change_visual_mode
move_explanation_block
```

### 12.2 Patch制約

- findingに紐づく
- 対象Scene / fieldを特定する
- must_preserveを明示する
- 新しいEvidenceを追加しない
- confidenceを強めない
- counterevidenceを削らない
- 事実順序を変えない
- 9Sceneの正式役割を消さない
- タイトルだけを本文より強くしない

### 12.3 Scene削除

9Scene構成自体は維持する。

重複Sceneの内容を削除する場合は、03の正式役割を残したまま別の新しい意味を割り当てる。

---

## 13. Pass F｜Causality Preservation

Author DraftとRewrite後Draftを比較する。

### 13.1 必須一致

- Claim Ledger
- Evidence ID
- Expected根拠区分
- Actual
- Gap
- causality scope
- confidence
- timeline
- counterevidence
- 主因、増幅、相殺、未確認の分類

### 13.2 即時FAIL

```text
UNSUPPORTED_EXPECTED
EVIDENCE_ID_LOST
CAUSALITY_DRIFT_DURING_REWRITE
CONFIDENCE_STRENGTHENED_WITHOUT_EVIDENCE
COUNTEREVIDENCE_REMOVED
TIMELINE_REORDERED_FOR_DRAMA
COMPANY_CAUSE_PROMOTED_TO_NASDAQ
INVESTMENT_ADVICE_INTRODUCED
FOX_HISTORY_INVENTED
CLAIM_MODALITY_STRENGTHENED
```

### 13.3 文面強度検査

field上のconfidenceだけでなく、公開文のmodalityをClaim Ledgerと照合する。

例:

```text
修正前
意識された可能性があります

修正後
市場を動かしました

→ CLAIM_MODALITY_STRENGTHENED
```

---

## 14. Pass G｜Final Re-review

通常は一回のRewriteで終了する。

```text
Round 1 Critic
→ Targeted Rewrite
→ Final Re-review
```

Criticalが残る場合のみRound 2を許可する。

最大2回までとする。

Round 2でもCriticalが残る場合は、表現修正を続けず戻り先を決める。

- 事実・因果: Causal Research / 02
- 角度: Pass A
- 構成: Pass B
- 狐・制作面: Pass C

Criticalを警告扱いで無視して進めてはいけない。

---

## 15. Deterministic Validator

Validatorは文章の面白さを証明しない。

### 15.1 Validator担当

- JSON Schema
- episode_date一致
- path / SHA binding
- Story Engine version
- Author / Critic invocation IDが異なる
- Draft SHAとCritic input SHAの一致
- Claim Ledger存在
- selected angleが候補内に存在
- Scene 1〜9存在
- 全Sceneの必須field
- Open Loop上限
- Critical finding 0
- Rewriteとfindingの対応
- review round上限2
- Causality Diff PASS
- Final Episode Package SHA一致
- Story spine一致
- 明示的禁止語の検出

### 15.2 Critic担当

- 本当に面白いか
- 本当に狐らしいか
- Sceneの意味が重複していないか
- 理解更新が成立するか
- 暗黙の投資誘導がないか
- Turn / Boundaryが意味を持つか
- 後半を見る理由があるか
- Visual Beatが理解を助けるか

Pythonだけで意味判断しない。

---

## 16. Daily Productionへの接続

内部PassをDaily Production stateへ追加しない。

```text
intake_ready
→ research_inputs_bound
→ causal_dossier_valid
→ episode_package_final
```

このstate列は維持する。

ただし、`episode_package_final`への遷移条件を強化する。

### 16.1 必須Evidence

```text
story_engine_package_YYYY-MM-DD.json
episode_package_YYYY-MM-DD.md
story_engine_validation_report.json
```

### 16.2 遷移拒否条件

- Story Engine packageなし
- causal dossier SHA不一致
- 01〜04 SHA不一致
- DraftとFinalのlineage不明
- AuthorとCriticのinvocation ID同一
- Critical finding残存
- review round上限超過
- Causality Diff FAIL
- Final Re-reviewがPASSでない
- Episode Package SHA不一致

既存のDaily Production Skillは機械的なstate管理にとどまり、市場因果や台本文面を判断しない。

---

## 17. Episode Packageとの関係

`episode_package_YYYY-MM-DD.md`を引き続き人間向け編集正本とする。

Story Engine内部情報を本文へ大量に貼らない。

末尾へ次だけを統合する。

```text
Story Discovery Summary
Selected Angle
Scene Progression Summary
04 Entertainment Review Result
Primary / Approved Fallback / Selected Path
Story Engine Validator Result
Causality Preservation Result
```

Author Draftや不採用角度、内部finding全文は公開台本へ漏らさない。

---

## 18. 外部プロジェクト採用境界

既存の外部採用正本を維持する。

### Doza Assist

採用:

- Story role
- Turn / Reveal / Button
- 隣接重複
- Information-only拒否
- Scene deletion test

### OpenMontage

採用:

- 角度比較
- Information Gap
- BUT / THEREFORE
- Progressive Revelation
- artifact-specific Critic

AGPL-3.0のためコード、schema、promptをコピーしない。

### video_explainer

採用:

- Analyze → Finding → Patch → Apply → Verify

ライセンス未確定のためコードをコピーしない。

### Toonflow

採用:

```text
Decision = Pass A / B
Execution = Pass C / E
Supervision = Pass D / F / G
```

### ViMax

採用:

- 一つの中間Artifact
- checkpoint / resume
- immutable snapshot
- 後段でcreative intentを変更しない

外部frameworkをruntime dependencyにしない。

---

## 19. Regression fixtures

### 19.1 boring_2026-08-06

旧台本へ最低限、次を検出する。

```text
REPEATED_CONCLUSION
NO_BELIEF_CHANGE
HOOK_EXHAUSTS_THE_STORY
PROCEDURAL_NARRATION
FOX_VOICE_ABSENT
NO_LATE_PAYOFF
```

改善版は次を満たす。

- Scene 1〜2で方向、矛盾、問い
- 主要証拠をScene 3以降へ残す
- Scene 4〜7で理解更新
- Scene 6〜8まで検証価値
- Scene 9で冒頭を再解釈
- Claim Ledger不変
- counterevidence不変
- confidence不変

### 19.2 valid_single_driver

- 主因が明確
- 無理に3角度を作らない
- 1案＋比較不能理由を許可

### 19.3 valid_multi_factor

- 主因、増幅、相殺を分離
- 一つのニュースへ過剰統合しない

### 19.4 valid_reason_unknown

- 理由不明を正しい結論として保持
- 面白さのために原因を創作しない
- 今夜の検証条件を提示

---

## 20. 実装PR再編

従来のPR-S2〜S5は廃止する。

### 統合PR-A｜Unified Story Engine Vertical Slice

一つのPRで実装する。

- Story Engine Skill
- 統合schema
- Pass A〜G
- Claim Ledger
- Independent Critic context分離
- Targeted Rewrite
- Causality Diff
- Validator
- 4 fixtures

このPRではDaily Productionへ接続しない。

Shadow modeで既存台本を評価・改善する。

コミットは同一PR内で次に分ける。

1. Skill / schema / contracts
2. Pass A〜C / valid fixtures
3. Pass D〜G / Claim Ledger / Patch
4. boring fixture / integration tests

### 統合PR-B｜Production Gate Integration

- `episode_package_final`遷移条件強化
- Story Engine evidence binding
- AGENTS / README / Runbook更新
- Final Production Source Annexへhash参照
- 既存test回帰

### 統合PR-C｜Real-Day Acceptance

- 新しい実日のCausal Dossier
- Unified Story Engine実行
- episode package
- preview
- ユーザー目視確認

finalは自動実行しない。

---

## 21. 非目標

初期実装では次を行わない。

- 01〜04の書き換え
- Causal Researchの置き換え
- 市場因果をLLM Criticに再判断させる
- 外部frameworkのruntime導入
- 画像生成Providerの追加
- Remotion変更
- AI完成動画採点
- 自動final
- Story Engine内部PassのDaily state化
- 多数の独立Skill作成
- 視聴維持率の自動最適化

---

## 22. 完成条件

Unified Story Engineは次をすべて満たしたとき完成とする。

- 一つのSkillで発見、構成、制作、審問、修正、再審問を実行
- AuthorとCriticが別invocation
- Criticが完成Draft Episode Package全体を審問
- 角度数を無理に3案へ固定しない
- 劇的Turnではなく理解更新を要求
- Claim Ledgerで文面強度を保全
- reviewは最大2回
- Critical findingを残して進めない
- 正式なStory Engine artifactは一つ
- immutable snapshotを保持
- Daily Production stateを増やさない
- Story Engine証跡なしでepisode_package_finalへ進めない
- 2026-08-06旧台本を正しくFAIL
- 単独主因、複合要因、理由不明を扱える
- 01の狐、02の因果、03の9Scene、04の審問を維持
- 既存Final ProductionとRenderer Handoffを変更せず利用可能

---

## 23. 4専門家最終承認

### 市場因果責任者

承認条件:

- Claim Ledger
- Causality Diff
- 02への戻り先
- Counterevidence保全

### 物語・狐責任者

承認条件:

- 九段階の理解変化
- Scene 6〜8まで見る理由
- 狐の自然な語り
- Hookが物語を消費し切らない

### Contract / Validator責任者

承認条件:

- Author / Critic context分離
- immutable snapshot
- SHA lineage
- ValidatorとCriticの責任分離

### 運用責任者

承認条件:

- state追加なし
- 統合PR-A / B / C
- shadow mode
- preview後にのみfinal判断

4条件を本設計で満たす。

---

# 最終正本宣言

実装時は本書をStory Engine v1.1の正本とする。

旧`STORY_ENGINE_IMPLEMENTATION_BLUEPRINT_v1.0.md`のうち、S2〜S5の別Skill、別PR、別stateを前提とする箇所は本書で上書きする。

外部採用判断、ライセンス判断、01〜04の優先順位、既存前段・後段を維持するStrangler方針は旧設計から継承する。
