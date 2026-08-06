# 朝のNASDAQカフェ｜Story Engine Overhaul Master Design

- 作成日: 2026-08-06
- 対象リポジトリ: `saienjoy0/nasdaq-plot-creator-`
- 設計ブランチ: `design/story-engine-overhaul`
- 基準main: `0b3648353e76b89a77a7c61668dfe98e3c7fb5cc`
- 状態: 俯瞰設計。細かなschema、prompt、validator条件は後続PRで確定する

## 1. 問題定義

現在のリポジトリは、次の領域が強い。

- Current evidenceとEditorial Memoryの分離
- Expected / Actual / Gap
- 時系列と代替仮説
- causal research dossier
- Evidence IDとprovenance
- 01〜04正本
- episode package以後の決定的生成
- render spec整合
- immutable renderer handoff
- preview / final gate

しかし、次の中央工程が実装されていない。

```text
causal research dossier
→ 面白い物語の発見
→ 複数角度の比較
→ 前史・反転・後への意味の設計
→ 9Sceneの理解変化
→ 狐の完成ナレーション
→ 独立批評
→ 対象箇所だけ修正
```

現在はこの中央を、ChatGPTが01〜04を読んで一度に処理する。

その結果、形式上は正しくても次が起きる。

- Scene 1で答えを全部明かす
- Scene 2〜7で同じ結論を再証明する
- Sceneの存在理由が「数字確認」だけになる
- Scene順を交換しても成立する
- 「確認します」「三点見ます」など制作手続きがナレーションになる
- 04が問題を指摘しても高得点で通過する
- 狐が一人称を「僕」にした監査担当者になる
- 画面を増やしても「動く報告書」にしかならない

## 2. 改造方針

全面再構築しない。

既存の前段と後段を残し、中央だけをStrangler方式で置き換える。

```text
既存前段
Memory → Causal Research

新規中央
Story Discovery → Script Authoring → Independent Creative Review

既存後段
Episode Package → Final Production → Renderer Handoff → Preview
```

01〜04は削除・短縮しない。人間が管理する正本として維持する。

新しいSkillは、01〜04を毎日実行するための手順、成果物、FAIL条件へ変換する。

---

## 3. 4専門家協議

### 専門家A｜市場因果・証拠責任者

要求:

- Story Creationはcausal dossierの事実・Evidence・確信度を変更しない
- 面白さのために時系列を並べ替えない
- 主役銘柄とNASDAQ全体の原因を再混同しない
- Rewrite後に因果表現の強さが変わっていないか検査する
- Story Engineが新しいExpectedを後付けしない

結論:

> Story Engineは市場因果の決定器ではなく、確定済み因果の中から説明上の発見と順序を設計する編集器とする。

### 専門家B｜物語・狐・9Scene責任者

要求:

- 9Sceneを九つの欄ではなく、九段階の理解変化として扱う
- 各SceneにStory roleを持たせる
- Scene 4〜6に意味のあるTurnを置く
- Scene 6〜8まで残る問いを作る
- 冒頭と結末をbookendする
- 狐の反応をナレーション設計前に決める
- IT比喩や小ネタは理解を助ける場合だけ使う

結論:

> ナレーションより先に、視聴者の認識変化を設計する。

### 専門家C｜schema・validator・provenance責任者

要求:

- 面白さをPythonだけで採点しない
- LLM Criticの意味判断とDeterministic Validatorを分離する
- 全中間成果物へdate、input hash、source artifact hashを付ける
- Story Discoveryからepisode packageまでのlineageを固定する
- 重大FAILが残るdraftを`episode_package_final`へ進めない
- 修正前と修正後の差分を記録する

結論:

> Validatorは「面白いこと」ではなく、「面白さを作る必須工程が実行され、重大な未解決がないこと」を証明する。

### 専門家D｜運用・移行・攻撃的QA責任者

要求:

- 新しい中央工程を旧フローへ一度に接続しない
- 2026-08-06の失敗回をregression fixtureにする
- 旧経路と新経路を同じdossierでA/B比較する
- 既存Final ProductionとRenderer契約を壊さない
- external frameworkをruntime dependencyにしない
- preview前にfinalへ進めない既存境界を維持する

結論:

> Story Engineをshadow modeで検証した後、Daily Productionの正式gateへ昇格する。

---

## 4. 参考プロジェクトからの採用

詳細は `references/STORY_CREATION_EXTERNAL_PROJECT_ADOPTION.md` を正本とする。

### 中核

- Doza Assist: Story role、Turn、隣接重複、Information-only拒否
- OpenMontage: Angle Competition、Guided Discovery、BUT / THEREFORE、Progressive Revelation、具体的Reviewer
- video_explainer: Gap Analysis、Issue → Patch → Verification

### 構造補助

- Toonflow: Decision / Execution / Supervision、Event Graph、Markdown Skill
- ViMax: Artifact Preview、Checkpoint、Resume

### 後段候補

- FireRed-OpenStoryline: 承認済み編集workflowのSkill化
- StoryWriter / GOAT / WriteHERE: 階層的OutlineとRecursive Planning

---

## 5. 目標フロー

```text
daily_source_package
↓
既存: Editorial Memory Retrieval
↓
既存: Causal Research Dossier
↓
新規: Story Discovery
  - 前史
  - 中心矛盾
  - 単純な説明候補
  - 説明を壊す証拠
  - 転換点
  - 見出し以上の発見
  - 後への意味
  - 物語角度候補
↓
既存02 + 新規: Angle Selection
  - 主役
  - 中心仮説
  - 選択した物語角度
  - 不採用角度と理由
↓
新規: Narrative Architecture
  - 冒頭と結末を先に固定
  - Scene 1〜9の認識変化
  - Story role
  - BUT / THEREFORE接続
  - Open Loop
  - Midpoint Turn
  - Callback
↓
新規: Fox Script Authoring
  - 狐の感情反応
  - 完成ナレーション
  - 演技意図
  - テロップと数字
↓
新規: Independent Creative Review
  - 問題位置
  - severity
  - concrete fix
  - causality preservation requirement
↓
新規: Targeted Rewrite
  - 問題Sceneだけ修正
  - 全文の不要な再生成を避ける
↓
新規: Re-review + Causality Diff
↓
既存03・04へ統合したFinal Episode Package
↓
既存: Asset Resolution / Final Production / Handoff / Preview
```

---

## 6. 初期Skill構成

最初から細かいSkillを多数作らない。

初期は3 Skill構成とする。

```text
skills/
├── nasdaq-cafe-story-discovery/
├── nasdaq-cafe-script-authoring/
└── nasdaq-cafe-entertainment-critic/
```

### 6.1 `nasdaq-cafe-story-discovery`

責任:

- causal dossierを読む
- 物語になる矛盾を抽出する
- 前後関係を掘る
- naive explanationを複数作る
- 各説明を現在Evidenceでテストする
- 見出し以上の発見を抽出する
- 異なる角度を最低3案作る
- 02に従う選択材料を返す

責任外:

- 最終ナレーション
- 狐の口調
- Visual Beat
- 画像
- render spec
- 売買判断

内部Stage候補:

```text
Stage 0 Input Gate
Stage 1 Before Context
Stage 2 Contradiction Mining
Stage 3 Naive Explanation Test
Stage 4 Turn / Reveal Mining
Stage 5 After Implication
Stage 6 Angle Competition
Stage 7 Editorial Handoff
```

### 6.2 `nasdaq-cafe-script-authoring`

責任:

- 選択済み角度から冒頭と結末を先に決める
- Scene 1〜9の認識変化を設計する
- 01に従って狐の完成ナレーションを書く
- 03の画面・演技・テロップ情報を作る
- 事実・解釈・推論・不明を保持する

内部Stage候補:

```text
Stage 0 Selected Angle Gate
Stage 1 Endpoint Planning
Stage 2 Nine-Scene Belief Arc
Stage 3 Open Loop / Turn Design
Stage 4 Fox Reaction Map
Stage 5 Narration Draft
Stage 6 Production Surface Draft
Stage 7 Self-check without final approval
```

### 6.3 `nasdaq-cafe-entertainment-critic`

責任:

- Authorとは別のcontextで読む
- 04と外部採用ルールで攻撃的に審査する
- 問題Sceneと問題文を特定する
- 具体的な修正指示を返す
- 修正後を再審査する
- 因果や留保が変わった場合は02へ戻す

内部Stage候補:

```text
Stage 0 Artifact / Evidence Load
Stage 1 Story Role Audit
Stage 2 Redundancy / Permutation Audit
Stage 3 Information Gap / Turn / Payoff Audit
Stage 4 Fox Voice Audit
Stage 5 Causality Preservation Audit
Stage 6 Patch Plan
Stage 7 Re-review
```

後段で必要性が確認された場合だけ、Angle DirectorやNarrative Architectを独立Skillへ分割する。

---

## 7. 必須中間成果物

詳細schemaは後続PRで詰める。

### 7.1 `story_discovery_YYYY-MM-DD.json`

概念上の必須項目:

```json
{
  "episode_date": "YYYY-MM-DD",
  "causal_dossier_ref": {
    "path": "...",
    "sha256": "..."
  },
  "obvious_headline": "",
  "before_context": [],
  "central_contradiction": "",
  "naive_explanations": [
    {
      "claim": "",
      "supporting_evidence_ids": [],
      "disproving_evidence_ids": [],
      "status": "survives|weakened|rejected|unresolved"
    }
  ],
  "turning_points": [],
  "headline_beyond_discoveries": [],
  "after_implications": [],
  "angle_candidates": []
}
```

### 7.2 `selected_story_angle_YYYY-MM-DD.json`

```json
{
  "selected_angle_id": "A-001",
  "central_question": "",
  "story_spine": "",
  "opening_promise": "",
  "closing_reframe": "",
  "midpoint_turn": "",
  "why_this_angle": "",
  "rejected_angles": [],
  "causality_scope": "company|sector|nasdaq_support|nasdaq_primary|reason_unknown",
  "confidence": "high|medium|low|unknown"
}
```

### 7.3 `narrative_arc_YYYY-MM-DD.json`

各Sceneに次を持たせる。

```json
{
  "scene": 4,
  "story_role": "setup|test|disproof|complication|turn|reveal|proof|implication|callback",
  "viewer_belief_before": "",
  "new_evidence_ids": [],
  "new_meaning": "",
  "viewer_belief_after": "",
  "remaining_question": "",
  "connector_from_previous": "but|therefore|callback|contrast",
  "indispensable": true,
  "deletion_consequence": "",
  "open_loop_ids_opened": [],
  "open_loop_ids_closed": []
}
```

### 7.4 `creative_review_YYYY-MM-DD.json`

```json
{
  "decision": "pass|revise|blocked",
  "round": 1,
  "findings": [
    {
      "finding_id": "CR-001",
      "severity": "critical|major|suggestion|investigation",
      "code": "REPEATED_CONCLUSION",
      "scene_ids": [3, 4],
      "anchor_text": "",
      "description": "",
      "proposed_fix": "",
      "must_preserve": {
        "evidence_ids": [],
        "causality_scope": "",
        "confidence": ""
      },
      "status": "pending|fixed|accepted|blocked"
    }
  ]
}
```

### 7.5 `rewrite_report_YYYY-MM-DD.json`

- 変更Scene
- 修正前anchor
- 修正後anchor
- 対応finding
- Evidenceの増減
- 因果表現の強さの変化
- 再審査結果

---

## 8. Story role vocabulary

初期vocabulary:

```text
hook
setup
naive_explanation
proof
complication
disproof
turn
reveal
counterevidence
implication
callback
button
```

9Sceneの正式名称は03を維持する。

Story roleはScene名を置き換えず、Sceneの物語上の働きを追加記録する。

同じroleが連続してもよいが、同じ意味・同じ証拠・同じ認識変化が連続することは禁止する。

---

## 9. 初期FAILコード

### 9.1 Story Discovery

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

### 9.2 Narrative Architecture

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
SCENE_NOT_INDISPENSABLE
```

### 9.3 Narration

```text
PROCEDURAL_NARRATION
ABSTRACT_EDITORIAL_LANGUAGE
FOX_VOICE_ABSENT
EXCESSIVE_HEDGING
UNEXPLAINED_JARGON
ANALOGY_NOT_RETURNED_TO_MARKET
TITLE_PROMISE_NOT_RECOVERED
```

### 9.4 Safety / Causality

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
```

重大FAILが残る場合、04の合計点が高くてもPASSにしない。

---

## 10. Reviewer方式

OpenMontageのReviewerとvideo_explainerのPatch方式を組み合わせる。

### LLM Critic

- artifactの具体的Scene、文、fieldを指す
- severityを付ける
- proposed fixを必須にする
- 同じ問題が他Sceneにないか横断確認する
- 作者の自己申告点数を信用しない

### Deterministic Validator

検査候補:

- 3案以上のangleがある
- angleのcentral questionが重複していない
- Scene 1〜9が存在する
- 全Sceneにbelief before / afterがある
- 全Sceneにstory roleがある
- Scene 4〜6のどこかにturnがある
- opening promiseとclosing reframeがある
- open loopが全て閉じるか明示的にunresolvedで終わる
- Critical findingが0
- rewrite後にre-reviewがある
- input/output hashが一致する
- selected angleとepisode packageのstory spineが一致する

Validatorは文章の面白さそのものを証明しない。

---

## 11. Daily Production state追加案

現在の`causal_dossier_valid`と`episode_package_final`の間へ追加する。

```text
causal_dossier_valid
→ story_discovery_valid
→ story_angle_selected
→ narrative_arc_valid
→ script_draft_ready
→ creative_review_passed
→ episode_package_final
```

状態を飛び越えない。

各状態は対象日のartifact pathとSHAへboundする。

旧episode packageが存在していても、新しいStory Engine証跡がなければ新契約の`episode_package_final`へ進めない。

移行期間はcontract versionで旧経路を明示的に区別する。

---

## 12. episode packageとの関係

`episode_package_YYYY-MM-DD.md`は引き続き人間向け編集正本とする。

Story Engineの全JSONを本文へ貼り込まない。

episode packageへは、必要最小限のHuman Review sectionを追加する候補とする。

```text
Story Discovery Summary
Selected Angle
Scene Progression Summary
Creative Review Result
```

機械可読な完全データはsidecar JSONに置き、Final Production Source Annexからhash参照する。

spoken script、telop、render specへ内部critic metadataを漏らさない。

---

## 13. 外部プロジェクトの取り込み方法

本体fork、submodule、実行時API依存は採用しない。

選択的に概念・schema pattern・test patternをローカル実装する。

```text
references/external/<project>/
├── SOURCE.md
├── LICENSE
├── PINNED_COMMIT
├── ADOPTION_NOTES.md
└── NOTICE.md
```

Doza Assistの削除済みstorytelling文書はvendoringしない。

OpenMontage、video_explainer、Toonflow、ViMaxなどからコードを直接移植する場合は、ファイル単位でライセンスと改変内容を記録する。

原則はコードコピーより、NASDAQ向けの独自schema・validator・Skill実装を優先する。

---

## 14. Regression fixture

最初の主fixtureは2026-08-06回とする。

既存出力で確認された問題:

- Scene 1で中心結論をほぼ完了
- AMDの数字確認が複数Sceneで反復
- Scene 6〜7の理解変化が弱い
- 手続き口調
- 狐の反応不足
- 04が高得点で通過

fixtureに必要なもの:

```text
causal_research_dossier
旧episode_package
旧creative review
期待するFAILコード一覧
期待するstory_discovery最小形
期待するnarrative_arcの性質
```

新システムは最低限、旧台本へ次を返す必要がある。

```text
REPEATED_CONCLUSION
NO_BELIEF_CHANGE
ANSWER_REVEALED_TOO_EARLY
PROCEDURAL_NARRATION
FOX_VOICE_ABSENT
NO_LATE_PAYOFF
```

このfixtureをPASSできないSkillは本番経路へ接続しない。

追加fixture候補:

- 単独主因が強い日
- 複合要因の日
- 理由不明の日
- 好決算なのに下落
- 指数とSOXが逆方向
- 個別材料は強いがNASDAQ全体へ波及しない日

---

## 15. 実装PR案

細かな番号は開始時のmainに合わせて再採番する。

### PR-S1｜External Story Pattern Adoption

- 外部採用文書
- Source / commit / license台帳
- 2026-08-06 failure fixture定義
- 新旧責任境界

完成条件:

- 採用・非採用が明示される
- runtime dependencyが増えない
- 01〜04が変更されない

### PR-S2｜Story Discovery Vertical Slice

- `nasdaq-cafe-story-discovery/SKILL.md`
- `story_discovery.schema.json`
- `selected_story_angle.schema.json`
- validator
- 2026-08-06 fixture

完成条件:

- causal dossierから3角度以上を作る
- naive explanation testを残す
- before / turn / afterを残す
- 旧台本を書かない

### PR-S3｜Narrative Arc Contract

- `narrative_arc.schema.json`
- Scene role / belief change / connector / open loop
- deterministic validator
- permutation / redundancy fixture

完成条件:

- 9Sceneを九段階の理解変化として検査できる
- Turnとbookendが必須になる

### PR-S4｜Fox Script Authoring

- `nasdaq-cafe-script-authoring/SKILL.md`
- narration draft contract
- 01・02・03とのmapping
- procedure-language checks

完成条件:

- narrative arcから狐の台本を生成
- dossier外の主張を追加しない
- old episode fixtureより重複が減る

### PR-S5｜Independent Critic and Targeted Rewrite

- `nasdaq-cafe-entertainment-critic/SKILL.md`
- creative review schema
- patch schema
- re-review contract
- causality diff

完成条件:

- 旧2026-08-06台本を重大FAILにする
- 問題Sceneだけ修正できる
- Counterevidenceとconfidenceを維持する

### PR-S6｜Daily Production Integration

- state machine拡張
- AGENTS / README / Runbook更新
- hardening chain
- stale story artifact拒否

完成条件:

- Story Engine証跡なしでepisode finalへ進めない
- 既存Final Production testsが回帰しない

### PR-S7｜Real-Day A/B Acceptance

- 同一dossierから旧・新経路比較
- user review record
- Story Engine acceptance report

完成条件:

- 新しい実日でpreviewまで到達
- ユーザーが内容の改善を目視確認
- finalは自動実行しない

---

## 16. 成功指標

自動指標だけで面白さを確定しない。

### 構造指標

- 同一結論を持つ隣接Scene数
- 新しいEvidenceも意味もないScene数
- Scene deletion test失敗数
- Scene permutation可能数
- Open Loop未回収数
- Scene 4〜6のTurn有無
- procedural narration文数
- abstract editorial phrase比率

### 安全指標

- Evidence ID保持率
- Counterevidence保持率
- confidence drift
- causal scope drift
- Expected source保持
- timestamp order保持

### 人間評価

ユーザーへ旧・新をblindに近い形で比較してもらう。

- 冒頭で続きが気になるか
- Sceneが進むたび理解が変わるか
- 見出し以上の発見があるか
- 狐が自然か
- Scene 6〜8まで見る理由があるか
- 同じ説明が繰り返されていないか
- 最後が冒頭を回収したか

初期の最重要指標はユーザーによる「中身がつまらなくないか」である。

---

## 17. 絶対に変更しない境界

- 01〜04の適用順位
- 02の市場因果判断
- 事実 / 解釈 / 推論 / 不明の区別
- Expectedの根拠区分
- 一社材料とNASDAQ全体原因の分離
- 狐一人の語り
- 投資助言禁止
- 画像生成はChatGPT側
- Primary / Approved Fallbackの事前確定
- GitHub Actionsは機械変換だけ
- AI完成動画視覚検査は行わない
- preview目視前にfinalへ進まない
- episode packageを人間向け編集正本とする

---

## 18. 今回の俯瞰決定

採用する改造は次である。

```text
既存Causal Research
↓
Doza型 Story Discovery
↓
OpenMontage型 Angle Competition / Guided Discovery
↓
NASDAQ独自 Narrative Arc
↓
01型 Fox Script
↓
video_explainer型 Issue / Patch
↓
04 + Independent Critic
↓
既存Final Production
```

外部プロジェクトをそのまま実行するのではなく、優れた設計をローカルSkillと契約へ消化する。

次工程はPR-S1の完成確認後、PR-S2のStory Discovery Vertical Sliceを詳細設計することである。
