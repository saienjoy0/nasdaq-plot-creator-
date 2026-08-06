# 朝のNASDAQカフェ｜Story Engine実装設計書 v1.0

- 作成日: 2026-08-06
- 対象リポジトリ: `saienjoy0/nasdaq-plot-creator-`
- 設計ブランチ: `design/story-engine-overhaul`
- 基準main: `0b3648353e76b89a77a7c61668dfe98e3c7fb5cc`
- 上位設計: `designs/STORY_ENGINE_OVERHAUL_MASTER_DESIGN.md`
- 外部採用正本: `references/STORY_CREATION_EXTERNAL_PROJECT_ADOPTION.md`
- 直接取り込み判断: `references/STORY_ENGINE_DIRECT_IMPORT_MATRIX.md`
- 状態: 実装着手可能なPR分割設計。個別prompt文面とJSON Schemaの全propertyは各PRで確定する

---

# 0. 最終決定

現在のリポジトリは作り直さない。

次の中央区間だけを置き換える。

```text
現行
causal_dossier_valid
→ ChatGPTが01〜04を一度に解釈
→ episode_package_final

改造後
causal_dossier_valid
→ story_discovery_valid
→ story_angle_selected
→ narrative_arc_valid
→ script_draft_ready
→ creative_review_passed
→ episode_package_final
```

既存のMemory、Causal Research、Episode Memory、Final Production、Renderer Handoff、Preview / Final gateは維持する。

01〜04は人間向けの正本として残す。新しいSkillは01〜04を置き換えず、毎日実行できる工程・成果物・失敗条件へ変換する。

Story Engineの目的は、事実を面白く改変することではない。

> 確定済みの事実、因果、時系列、確信度、反対材料を保持したまま、視聴者の理解が進む順序へ変換する。

---

# 1. 4専門家の最終合意

## 1.1 専門家A｜市場因果・証拠責任者

### 保持するもの

- causal research dossierのEvidence ID
- Expected / Actual / Gap
- 主因、増幅、相殺、未確認
- 会社直接材料とNASDAQ全体の範囲
- 時系列
- 確信度
- 重要な反対材料

### Story Engineへ許可すること

- どの証拠を先に見せるかの説明順序設計
- 単純な説明候補を提示し、既存Evidenceで崩すこと
- 見出し以上の発見を一文へ圧縮すること
- 同じ因果を分かりやすい日常語へ変換すること

### 禁止すること

- 新しいExpectedを作る
- dossierにない因果を追加する
- MediumをHigh相当の断定へ強める
- 反対材料を消す
- 発表順をドラマのために変える
- 一社の材料をNASDAQ全体の主因へ昇格する

## 1.2 専門家B｜物語・狐・9Scene責任者

### 必須構造

- 冒頭30秒に方向、矛盾、問い
- Sceneごとの理解変化
- Scene 4〜6に意味のあるTurn
- Scene 6〜8まで残る検証価値
- Scene 9で冒頭を別の理解として回収
- 狐の反応と声をナレーション前に設計

### 基本原則

```text
9Scene
≠ 九つの情報欄

9Scene
= 九段階の理解変化
```

Sceneに新しい証拠がなくても、既存証拠から新しい意味が生まれるなら成立する。

新しい証拠も新しい意味もないSceneは統合・削除対象とする。

## 1.3 専門家C｜契約・validator・lineage責任者

### 二層審査

```text
LLM Critic
= 意味、重複、Turn、狐らしさ、興味深さを判断

Deterministic Validator
= 必須artifact、field、hash、state、未解決findingの有無を判断
```

Pythonだけで面白さを採点しない。

LLMの自己申告だけでPASSさせない。

## 1.4 専門家D｜移行・運用・攻撃的QA責任者

### 移行原則

- まずshadow mode
- 2026-08-06失敗回をfixture化
- 旧経路と新経路を同一dossierで比較
- 既存後段へ影響しない縦切りから開始
- 新しいStory Engineの証跡がない旧episodeは新契約でfinal扱いしない
- preview前にfinalへ進まない

---

# 2. 正本との関係

## 2.1 02との関係

02が最終的に決めるもの:

- 主役
- 主役テーマの例外採用
- Expected / Actual / Gap
- NASDAQまでの因果範囲
- 確信度
- 反対材料

Story Discoveryは、02が決めるための物語候補を返す。

Story Discovery自身が市場因果の最終決定者にならない。

## 2.2 01との関係

Script Authoringは次を機械的に守る。

- 一人称は「僕」
- 狐一人の声
- 短い文
- 数字のあとに意味
- 先生ではなく案内役
- IT比喩0〜2回
- 自虐・貧乏・損失・レバレッジ小ネタ合計0〜1回
- 記録されていない過去や取引を創作しない

## 2.3 03との関係

03のScene 1〜9の正式役割とepisode package正本は維持する。

新しい`story_role`はScene名を置き換えない。

例:

```text
03上のScene 4
+ Story role: disproof / turn
```

03が要求するVisual Beat、画面状態、表情、演技意図、テロップ、数字はScript Authoringの後半Stageで作る。

## 2.4 04との関係

04は削除しない。

ただし、実行方法を次へ変更する。

```text
旧
作者が台本作成
→ 同じ文脈で自己採点

新
作者が台本作成
→ 独立Critic context
→ structured finding
→ targeted rewrite
→ re-review
→ 04の短い統合結果
```

04の得点が高くてもCritical findingが残る場合はPASSしない。

---

# 3. 対象アーキテクチャ

```text
daily_source_package
↓
Editorial Memory Retrieval                         既存
↓
Research Input Manifest                            既存
↓
Causal Research Dossier                            既存
↓
Story Discovery                                    新規
  ├─ before context
  ├─ contradiction mining
  ├─ naive explanation test
  ├─ turn / reveal mining
  ├─ after implication
  └─ angle competition
↓
Selected Story Angle                               新規
↓
Narrative Architecture                             新規
  ├─ opening promise
  ├─ closing reframe
  ├─ nine-scene belief arc
  ├─ open loops
  ├─ midpoint turn
  └─ bookend
↓
Fox Script Authoring                               新規
  ├─ fox reaction map
  ├─ narration
  ├─ performance intent
  ├─ telops / numbers
  └─ production surfaces
↓
Independent Entertainment Critic                   新規
  ├─ findings
  ├─ patch plan
  ├─ targeted rewrite
  ├─ re-review
  └─ causality diff
↓
Final Episode Package                              既存正本へ統合
↓
Episode Memory / Final Production / Handoff        既存
↓
Preview / User Review / Explicit Final             既存
```

---

# 4. 新規ディレクトリ構成

初期実装では3 Skillだけを追加する。

```text
skills/
├── nasdaq-cafe-story-discovery/
│   ├── SKILL.md
│   ├── contracts/
│   │   ├── story_discovery.schema.json
│   │   └── selected_story_angle.schema.json
│   ├── validators/
│   │   ├── validate_story_discovery.py
│   │   └── validate_selected_story_angle.py
│   └── fixtures/
│
├── nasdaq-cafe-script-authoring/
│   ├── SKILL.md
│   ├── contracts/
│   │   ├── narrative_arc.schema.json
│   │   ├── script_draft.schema.json
│   │   └── story_engine_lineage.schema.json
│   ├── validators/
│   │   ├── validate_narrative_arc.py
│   │   ├── validate_script_draft.py
│   │   └── validate_story_lineage.py
│   └── fixtures/
│
└── nasdaq-cafe-entertainment-critic/
    ├── SKILL.md
    ├── contracts/
    │   ├── creative_review.schema.json
    │   ├── rewrite_patch.schema.json
    │   └── rewrite_report.schema.json
    ├── validators/
    │   ├── validate_creative_review.py
    │   ├── validate_rewrite_report.py
    │   └── validate_causality_diff.py
    └── fixtures/
```

共通CLIは後から`script-engine/`へまとめず、初期は各Skill内へ置く。

共通化は重複が実際に発生してから行う。

---

# 5. 成果物の正式配置

日次成果物は次へ置く。

```text
working/YYYY-MM-DD/story-engine/
├── story_discovery_YYYY-MM-DD.json
├── selected_story_angle_YYYY-MM-DD.json
├── narrative_arc_YYYY-MM-DD.json
├── script_draft_YYYY-MM-DD.json
├── creative_review_round1_YYYY-MM-DD.json
├── rewrite_patch_round1_YYYY-MM-DD.json
├── rewrite_report_round1_YYYY-MM-DD.json
├── creative_review_final_YYYY-MM-DD.json
├── causality_diff_YYYY-MM-DD.json
└── story_engine_acceptance_YYYY-MM-DD.json
```

episode packageは引き続き次に置く。

```text
episodes/YYYY-MM-DD/episode_package_YYYY-MM-DD.md
```

Story Engineの完全な内部JSONをepisode package本文へ貼らない。

---

# 6. Artifact共通header

全Story Engine JSONは次を持つ。

```json
{
  "contract_version": "1.0.0",
  "episode_date": "YYYY-MM-DD",
  "created_at": "ISO-8601",
  "producer": "chatgpt",
  "source_contracts": [
    {
      "path": "source-of-truth/02_editorial_bible.md",
      "sha256": "64hex"
    }
  ],
  "inputs": [
    {
      "role": "causal_dossier",
      "path": "research/YYYY-MM-DD/causal_research_dossier_YYYY-MM-DD.json",
      "sha256": "64hex"
    }
  ]
}
```

規則:

- pathはrepo相対
- `..`禁止
- episode date一致
- hash一致
- 古いartifactの流用禁止
- downstreamはupstream SHAを参照する

---

# 7. Story Discovery Skill設計

## 7.1 責任

入力:

- validated causal research dossier
- 02 editorial bible
- current episode date / cutoff
- 必要に応じて承認済みmemory comparison

出力:

- `story_discovery`
- `selected_story_angle`候補

責任外:

- 狐の文章
- Scene完成稿
- Visual Beat
- title / thumbnail完成稿
- image route
- render spec

## 7.2 Stage

### Stage 0｜Input Gate

- dossier validator PASSを確認
- episode dateを確認
- Evidence ID参照整合を確認
- provisional lead、alternatives、counterevidenceを読む
- このStageでは文章を書かない

### Stage 1｜Before Context

主役以前に何が積み上がっていたかを抽出する。

候補:

- 事前期待
- 前四半期から残る懸念
- 同業比較
- 価格への織り込み
- 供給制約
- 評価軸の変化

before contextは現在Evidenceまたはrevalidated historical contextへ接続する。

### Stage 2｜Contradiction Mining

最大3件の矛盾を作る。

例:

- 好決算なのに下落
- 指数上昇なのにSOX下落
- AI需要は強いのに供給企業で明暗

矛盾は単なる値動き差ではなく、視聴者が「なぜ」と言える文にする。

### Stage 3｜Naive Explanation Test

各矛盾へ、視聴者が最初に考えやすい説明を2〜4件作る。

例:

```text
決算が悪かった
半導体全体が売られた
金利だけが原因だった
```

各説明を既存Evidenceで、次へ分類する。

- survives
- weakened
- rejected
- unresolved

この工程で新しい因果を作らない。

### Stage 4｜Turn / Reveal Mining

次を探す。

- 単純な説明を壊す証拠
- 比較対象の逆方向
- 発表内容と価格反応のズレ
- 見出しでは分からない評価軸
- Scene 4〜6で見方を変えられる一点

### Stage 5｜After Implication

その日の結論が正しければ、今後何を見れば強まるか・弱まるかを記録する。

売買判断ではない。

例:

- 次の大型顧客
- 利益率改善
- 供給能力
- 同業へ反応が広がるか

### Stage 6｜Angle Competition

最低3案を作る。

初期angle type:

- contradiction
- comparison
- evaluation-axis-shift
- misconception-disproof
- causal-chain
- reason-unknown

各案は次を持つ。

- central question
- story spine
- opening promise
- midpoint turn
- closing reframe
- required evidence IDs
- counterevidence
- causality scope
- risk
- why distinct

### Stage 7｜Editorial Handoff

02に従って一案を選ぶ。

不採用案と理由を残す。

不採用理由候補:

- NASDAQ説明力が弱い
- Evidence不足
- 前後が浅い
- Turnがない
- 他案と実質同一
- 一社材料を過剰拡大する

## 7.3 Story Discovery FAIL

Critical:

```text
NO_BEFORE_CONTEXT
NO_CENTRAL_CONTRADICTION
NO_NAIVE_EXPLANATION_TEST
NO_HEADLINE_BEYOND_DISCOVERY
NO_AFTER_IMPLICATION
ANGLE_OPTIONS_NOT_DISTINCT
ANGLE_UNSUPPORTED_BY_DOSSIER
CAUSAL_SCOPE_OVERREACH
```

`reason_unknown`回は、証拠不足自体を正しい発見として扱える。

---

# 8. Selected Story Angle契約

必須項目:

```json
{
  "selected_angle_id": "angle-001",
  "angle_type": "contradiction",
  "central_question": "",
  "story_spine": "",
  "opening_promise": "",
  "midpoint_turn": {
    "claim": "",
    "evidence_ids": []
  },
  "closing_reframe": "",
  "causality_scope": "company|sector|nasdaq_support|nasdaq_primary|reason_unknown",
  "confidence": "high|medium|low|unknown",
  "counterevidence_ids": [],
  "why_selected": "",
  "rejected_angles": []
}
```

規則:

- `opening_promise`は方向・矛盾・問いを示す
- 証明全体を冒頭へ入れない
- `closing_reframe`は冒頭を新しい理解で回収する
- `midpoint_turn`はEvidence付き
- `causality_scope`はdossierを超えない

---

# 9. Narrative Architecture設計

## 9.1 Endpoint-first

最初に次だけを決める。

```text
Opening Promise
Closing Reframe
```

その後、間を埋める。

この順序により、中盤が情報一覧へ崩れるのを防ぐ。

## 9.2 Scene共通field

```json
{
  "scene_id": "scene-04",
  "formal_scene_role": "03で定義されたScene役割",
  "story_role": "disproof",
  "viewer_belief_before": "",
  "new_evidence_ids": [],
  "new_meaning": "",
  "viewer_belief_after": "",
  "remaining_question": "",
  "connector_from_previous": "but|therefore|contrast|callback",
  "indispensable": true,
  "deletion_consequence": "",
  "open_loop_ids_opened": [],
  "open_loop_ids_closed": []
}
```

## 9.3 Scene成立条件

Sceneは次のどちらかを満たす。

1. 新しいEvidenceを追加する
2. 既存Evidenceから新しいMeaningを追加する

どちらもない場合はFAIL。

## 9.4 接続条件

原則:

- `but`: 前Sceneの説明を壊す・複雑化する
- `therefore`: 前Sceneから必然的に次へ進む
- `contrast`: 比較対象で意味を変える
- `callback`: 前の問いへ戻る

`and_then`は正式値に入れない。

## 9.5 Midpoint Turn

Scene 4〜6のどこかに、次の一つが必要。

- naive explanationが崩れる
- 原因の範囲が変わる
- 比較対象によって評価軸が見える
- 主役ニュースの意味が変わる
- 理由不明が正しい結論になる

## 9.6 Open Loop

最大2件。

各loopは、

- open scene
- question
- promised evidence
- close scene
- resolution

を持つ。

Scene 8までに閉じる。

理由不明回は、未解決であることをScene 8までに正しい結論として確定する。

## 9.7 Bookend

Scene 9はScene 1の言い換えではなく、Scene 2〜8を通過した後で意味が変わった一文にする。

---

# 10. Script Authoring Skill設計

## 10.1 Stage

### Stage 0｜Selected Angle Gate

- selected angle validator PASS
- narrative arc validator PASS
- Evidenceとconfidenceを固定

### Stage 1｜Fox Reaction Map

各Sceneへ次を一つ決める。

- notices contradiction
- doubts simple explanation
- confirms fact
- becomes cautious
- sees the turn
- narrows conclusion
- admits uncertainty
- closes calmly

感情を大げさにしない。

### Stage 2｜Narration Draft

規則:

- 一人称「僕」
- 狐一人
- 制作手続きを読まない
- 出典主体が必要な箇所だけ示す
- 短い文
- 数字→比較→意味
- 重要な反対材料を一か所へまとめる
- 結論を消す留保の反復を避ける

### Stage 3｜Procedure Language Filter

次の表現は原則修正対象。

```text
確認します
三つ見ます
順番に並べます
数字を置きます
次に見ます
ここまで整理します
```

視聴者に必要な道案内である場合だけ残す。

### Stage 4｜Abstract Language Filter

抽象語を使う場合、直後に具体へ戻す。

対象例:

- 評価軸
- 採点基準
- 確実性
- 織り込み
- 選別
- 質

具体へ戻れない抽象語は削除する。

### Stage 5｜Fox Voice Check

狐らしさは小ネタ数ではなく、次で確認する。

- 矛盾への自然な反応
- 視聴者と同じ目線
- 構造化された説明
- 少しの皮肉
- 不明を不明と言う

### Stage 6｜Production Surface Draft

03に必要な次を作る。

- 完成ナレーション
- 演技意図
- 表情
- 表情切り替え
- 画面モード
- 接続文
- 大テロップ
- 補助テロップ
- 数字
- 画面で伝える内容
- Evidence / uncertainty
- Visual Beat

Visual Beatは新しいEvidenceまたはMeaningへ対応させる。

---

# 11. Independent Entertainment Critic設計

## 11.1 Context分離

Criticは作者の自己評価を読まない。

入力:

- causal dossier
- selected angle
- narrative arc
- script draft
- 01〜04

作者の説明や意図ではなく、artifactを審査する。

## 11.2 Review順

```text
1. Story role audit
2. Adjacent redundancy audit
3. Scene deletion / permutation audit
4. Information gap audit
5. Midpoint turn audit
6. Late payoff audit
7. Fox voice audit
8. Clarity / analogy audit
9. Title promise audit
10. Causality preservation audit
```

## 11.3 Finding形式

```json
{
  "finding_id": "finding-001",
  "severity": "critical|major|suggestion|investigation",
  "code": "REPEATED_CONCLUSION",
  "scene_ids": ["scene-03", "scene-04"],
  "artifact_path": "script_draft.scenes[3].narration",
  "anchor_text": "",
  "description": "",
  "audience_effect": "",
  "proposed_fix": "",
  "patch_type": "merge_scene",
  "must_preserve": {
    "evidence_ids": [],
    "causality_scope": "",
    "confidence": "",
    "counterevidence_ids": []
  }
}
```

Critical findingには`proposed_fix`を必須とする。

修正方法が分からない場合は`investigation`へ下げる。

## 11.4 Critical FAILコード

```text
REPEATED_CONCLUSION
NO_BELIEF_CHANGE
NO_NEW_EVIDENCE
ANSWER_REVEALED_TOO_EARLY
NO_MIDPOINT_TURN
NO_LATE_PAYOFF
ENDING_NOT_BOOKENDED
PERMUTABLE_SCENES
OPEN_LOOP_UNRESOLVED
PROCEDURAL_NARRATION
FOX_VOICE_ABSENT
TITLE_PROMISE_NOT_RECOVERED
CAUSALITY_DRIFT_DURING_REWRITE
COUNTEREVIDENCE_REMOVED
TIMELINE_REORDERED_FOR_DRAMA
COMPANY_CAUSE_PROMOTED_TO_NASDAQ
```

## 11.5 得点との関係

04の30点評価は残す。

ただし判定は次。

```text
Critical 1件以上
→ 再構成または不合格

Critical 0件、Major残り
→ 条件付き合格または再修正

Critical 0件、Major 0件
→ 得点とVisual gateを確認
```

---

# 12. Patch / Rewrite設計

## 12.1 Patch type

```text
merge_scene
remove_scene
reorder_scene
rewrite_scene
replace_connector
move_reveal_later
strengthen_hook_gap
add_counterevidence_block
add_clarity_bridge
add_callback
restore_causality_wording
```

## 12.2 Targeted Rewrite

原則としてfinding対象Sceneだけ変更する。

全体再生成が必要な場合:

- selected angle自体が不成立
- midpoint turnが存在しない
- opening / closingが別テーマ
- Scene順全体がpermutable
- causality scopeが誤っている

この場合はScript AuthoringではなくStory DiscoveryまたはNarrative Architectureへ戻る。

## 12.3 Rewrite report

必須:

- finding ID
- patch type
- changed fields
- before text
- after text
- Evidence ID before / after
- counterevidence before / after
- confidence before / after
- causality scope before / after
- authoring stage returned to
- re-review result

---

# 13. Causality Diff設計

Rewrite前後で次を比較する。

- Evidence ID集合
- Expected source category
- Actual
- Gap
- primary / amplifier / offsetting / unresolved
- causality scope
- confidence
- counterevidence ID集合
- timeline anchors
- public wording strength

禁止差分:

- Evidenceなしで断定強化
- counterevidence削除
- unknown→knownへの変更
- company→NASDAQ primaryへの変更
- timeline順序変更
- Expected追加

禁止差分があれば02へ戻す。

---

# 14. Deterministic Validator設計

## 14.1 Story Discovery validator

検査:

- schema
- date / path / SHA
- dossier Evidence ID参照
- angle 3案以上
- angle central question重複なし
- before contextあり、または明示的にnot-available
- naive explanation testあり
- headline-beyond discoveryあり、またはreason-unknown
- after implicationあり
- causality scopeがdossierを超えない

## 14.2 Narrative Arc validator

検査:

- Scene 1〜9 exactly once and ordered
- story role全Scene
- belief before / after全Scene
- new Evidenceまたはnew Meaning
- connector値
- Scene 4〜6にturn
- open loops最大2件
- loop closure
- opening / closing
- indispensable / deletion consequence

文章意味の類似判定はdeterministic validatorの正式PASS根拠にしない。

重複意味はCriticが判断する。

## 14.3 Creative Review validator

検査:

- round
- artifact SHA
- finding ID unique
- critical findingはfixあり
- fixed findingはrewrite report参照
- final reviewでpending critical 0
- re-reviewあり
- causality diff PASS

## 14.4 Acceptance builder

`story_engine_acceptance`は次をまとめる。

```json
{
  "status": "pass|fail",
  "story_discovery": "pass|fail",
  "selected_angle": "pass|fail",
  "narrative_arc": "pass|fail",
  "script_draft": "pass|fail",
  "creative_review": "pass|fail",
  "causality_diff": "pass|fail",
  "unresolved_critical_findings": [],
  "artifact_refs": []
}
```

---

# 15. Daily Production state machine変更

現行`STATES`の、

```text
causal_dossier_valid
→ episode_package_final
```

を次へ置換する。

```text
causal_dossier_valid
→ story_discovery_valid
→ story_angle_selected
→ narrative_arc_valid
→ script_draft_ready
→ creative_review_passed
→ episode_package_final
```

## 15.1 Error code追加

```text
E_STORY_DISCOVERY_INVALID
E_STORY_ANGLE_INVALID
E_NARRATIVE_ARC_INVALID
E_SCRIPT_DRAFT_INVALID
E_CREATIVE_REVIEW_UNRESOLVED
E_CAUSALITY_DIFF_FAILED
E_STORY_ENGINE_STALE
```

## 15.2 Evidence binding

各transitionは一つの自己申告JSONだけを証拠にしない。

例:

`creative_review_passed`のEvidence:

- final creative review
- rewrite report群
- causality diff
- story engine acceptance

## 15.3 Hardened wrapper

`run_daily_production_hardened.py`は、base state machineを維持する。

Story Engine state追加後も、Final Production / Handoff / Acceptanceのhardened差し替えは変更しない。

---

# 16. Episode Package統合

episode packageへ次の短いHuman Review sectionを追加する。

```markdown
## Story Engine Summary

- Central contradiction:
- Selected angle:
- Opening promise:
- Midpoint turn:
- Closing reframe:
- Headline-beyond discovery:
- Unresolved question:
- Creative review decision:
- Critical findings remaining: 0
- Causality diff: pass
```

完全な内部データはsidecar JSONに置く。

Final Production Source Annexへ次を追加する。

```json
{
  "story_engine": {
    "acceptance_path": "working/YYYY-MM-DD/story-engine/story_engine_acceptance_YYYY-MM-DD.json",
    "acceptance_sha256": "64hex"
  }
}
```

Final Production builderはStory Engine内容を推測・修正しない。

acceptance SHAを確認するだけとする。

---

# 17. 既存ファイル変更一覧

## PR-S1時点

追加のみ:

- `references/STORY_ENGINE_DIRECT_IMPORT_MATRIX.md`
- 外部source / license台帳
- regression fixture定義

01〜04、state machine、builderは変更しない。

## PR-S2〜S5

追加:

- 3 Skills
- schemas
- validators
- tests
- fixtures

既存後段は変更しない。

## PR-S6

変更:

- `AGENTS.md`
- `README.md`
- `docs/DAILY_PRODUCTION_RUNBOOK.md`
- `skills/nasdaq-cafe-daily-production/SKILL.md`
- `scripts/run_daily_production.py`
- `scripts/run_daily_production_hardened.py`は必要なimport / gateのみ
- `tests/daily-production/test_daily_production.py`
- Final Production source schema
- Final Production builderのStory Engine acceptance SHA確認

変更しない:

- market causality
- narration
- render spec public contractの意味
- renderer

---

# 18. Regression Fixture設計

## 18.1 主fixture

2026-08-06回。

入力:

- causal research dossier
- old episode package
- old 04 result
- expected FAIL codes

期待FAIL:

```text
REPEATED_CONCLUSION
NO_BELIEF_CHANGE
ANSWER_REVEALED_TOO_EARLY
PROCEDURAL_NARRATION
FOX_VOICE_ABSENT
NO_LATE_PAYOFF
```

## 18.2 Positive fixture

旧回を手修正した正解本文を固定するのではない。

次の性質だけを期待する。

- Scene 1に方向・矛盾・問い
- Scene 4〜6にTurn
- AMD数字の重複がない
- Scene 6〜8に検証価値
- Scene 9がbookend
- Critical finding 0
- causality diff PASS

## 18.3 追加fixture

- strong-single-cause
- compound-causes
- reason-unknown
- strong-company-weak-index-link
- index-sox-divergence
- high-expected-low-actual-gap
- no-confirmed-expected

---

# 19. Test計画

## 19.1 Contract tests

- valid schema
- missing header
- wrong date
- stale SHA
- external path
- unknown Evidence ID
- duplicate angle
- missing turn
- unresolved loop
- pending critical

## 19.2 Adversarial tests

- angleが3案あるが文言だけ違う
- Scene before / afterが同じ
- new evidenceが前Sceneと同じ
- rewriteでcounterevidence削除
- confidenceをMediumからHigh相当に変更
- company causeをNASDAQ primaryへ変更
- Scene順を交換
- old acceptanceを新しいdateへコピー
- creative reviewを手書きPASSへ改ざん

## 19.3 Existing regression

必須:

- daily production tests
- causal dossier tests
- episode memory tests
- final production package tests
- renderer handoff tests
- real-day acceptance tests

---

# 20. PR分割

## PR-S1｜Reference / License / Failure Fixture

目的:

- 外部採用境界を固定
- 2026-08-06 failure fixtureを登録
- runtime dependencyなし

変更:

- references
- fixture metadata
- design docs

完了条件:

- 直接copy可否が明示
- expected FAILが固定
- 01〜04と本番flow無変更

## PR-S2｜Story Discovery Vertical Slice

追加:

- Story Discovery Skill
- story discovery schema
- selected angle schema
- validators
- 2026-08-06 fixture tests

完了条件:

- 3 angle以上
- before / contradiction / naive test / turn / after
- dossier外主張なし
- narration未生成

## PR-S3｜Narrative Arc Contract

追加:

- Script Authoring SkillのArc部分
- narrative arc schema
- open loop / turn / bookend validator
- permutation fixtures

完了条件:

- 9Scene belief arc
- Scene 4〜6 turn
- open loop最大2
- Scene成立条件を検査

## PR-S4｜Fox Script Authoring

追加:

- narration / production surface contract
- procedure language audit
- fox voice self-check
- 01〜03 mapping tests

完了条件:

- 狐一人
- dossier外主張なし
- production surface完成
- 旧回より重複減少

## PR-S5｜Independent Critic / Patch / Re-review

追加:

- Critic Skill
- creative review schema
- patch / rewrite report
- causality diff

完了条件:

- 旧回をCritical FAIL
- targeted rewrite
- re-review
- critical 0
- causality diff PASS

## PR-S6｜Daily Production Integration

変更:

- state machine
- runbook
- AGENTS / README
- Final Production acceptance binding

完了条件:

- Story Engine証跡なしでepisode finalへ進めない
- stale / forged artifact拒否
- existing downstream tests PASS

## PR-S7｜Shadow A/B / Real-Day Acceptance

実行:

- 同じdossierで旧経路・新経路
- episode package比較
- previewまで
- user review

完了条件:

- 内容改善をユーザーが確認
- technical path PASS
- final未実行

---

# 21. Shadow mode

PR-S2〜S5は正式stateへ接続しない。

同一dossierに対して、

```text
旧episode package
新Story Engine draft
```

を両方生成できるようにする。

比較項目:

- repeated conclusion数
- belief changeなしScene数
- procedure language数
- midpoint turn
- unresolved loop
- fox voice finding
- critical finding
- user preference

自動指標は補助であり、ユーザー評価を代替しない。

---

# 22. Rollback

PR-S6後に問題が出た場合:

- contract versionで旧日をlegacy read-onlyとして維持
- 新規日だけStory Engine contractを必須にする
- state machineの新stateを削除せず、feature flagで新規initを停止
- 既存episode package / render specを破壊しない

旧経路へ黙って戻さない。

rollback理由と対象episodeを記録する。

---

# 23. 成功条件

## 技術

- schema / validator PASS
- hash lineage PASS
- old downstream regression PASS
- stale artifact拒否
- final自動実行なし

## 編集

- 2026-08-06旧回を正しくFAIL
- Sceneが九段階の理解変化
- 中間Turn
- 冒頭と結末の回収
- 同じ説明の反復減少
- 狐が監査担当ではなく案内役
- 手続き口調減少
- 反対材料維持

## ユーザー確認

最終採用は、同じdossierの旧版と新版をユーザーが読み比べ、次を確認したときに行う。

- 前より面白い
- 後半まで見る理由がある
- 狐らしい
- 理解しやすい
- 事実や留保が弱くなっていない

---

# 24. 今回は決めないもの

後続PRで詰める。

- JSON Schema全propertyの細部
- LLM prompt全文
- similarity計算の採否
- Story Engine用CLIの最終コマンド名
- Human review UI
- 承認済み過去回からEditorial DNAを抽出する方法
- post-publication retention analyticsとの接続

---

# 25. 実装開始点

最初に行うのはPR-S1である。

ただし、設計資料はすでにこのbranchへ保存されているため、PR-S1の実装作業は次から始める。

1. `references/external/`のsource / license / pinned commit台帳
2. 2026-08-06 failure fixture metadata
3. fixtureに必要な既存artifactのsafe copyまたはhash参照
4. expected Critical FAIL code
5. PR-S2が読むfixture contract

このPRではSkill本体、state machine、episode package、render specを変更しない。
