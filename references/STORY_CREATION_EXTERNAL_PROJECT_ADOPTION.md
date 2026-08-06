# 外部Story Creationプロジェクト採用判断｜朝のNASDAQカフェ

- 作成日: 2026-08-06
- 対象: `saienjoy0/nasdaq-plot-creator-`
- 目的: 因果調査から完成台本までの空白を、既存の優れたStory Creation設計を参考にして埋める
- 適用順位: プロジェクト指示 → 02 → 01 → 03 → 04 → 本文書

## 1. 結論

現在の外部採用は、STORM、Open Deep Research、GraphRAG、Graphiti、DeerFlowなど、調査・証拠・記憶・運用を中心としている。

次に必要なのは、次の工程を専門に扱うStory Creation層である。

```text
正しい市場因果
→ 物語になる矛盾の発見
→ 複数角度の比較
→ 前後関係・転換点・回収の設計
→ 狐の完成ナレーション
→ 独立批評
→ 対象箇所だけ修正
```

中核採用候補は次の3件とする。

1. Doza Assist: Story Minerと編集判断ルール
2. OpenMontage: Explainerの構造、角度競争、段階的開示、Reviewer契約
3. video_explainer: Gap Analysis → Patch → Script Refinement

構造面の補助候補は次の2件とする。

4. Toonflow: Event Graph、意思決定・実行・監督の三層構造、Markdown Skill化
5. ViMax: 中間成果物のプレビュー、対話的修正、checkpoint/resume

FireRed-OpenStoryline、StoryWriter、GOAT-Storytelling-Agentなどは、初期実装の直接依存にはせず、後段の参考候補とする。

---

## 2. 採用評価基準

外部プロジェクトは、人気や機能数ではなく次で評価する。

1. 見出し以上の発見を作れるか
2. 主役ニュースの前史と後への意味を掘れるか
3. Scene間に理解の変化と転換を作れるか
4. 同じ説明の反復を検出できるか
5. 作者と批評者を分離できるか
6. 事実と市場因果を変えずに表現だけ改善できるか
7. 中間成果物と修正履歴を残せるか
8. 既存の01〜04、Evidence、Memory、Final Production契約を上書きしないか
9. 外部サービスを日次実行時の必須依存にしないか
10. ライセンスと参照元を追跡できるか

---

## 3. Doza Assist

### 参照

- Repository: `DozaVisuals/doza-assist`
- Storytelling foundation導入commit: `cac564e616f92436af2909e9021925d085ef3f5f`
- 追加改善commit: `23e6f99e6dc03059b3a4c11190c42a8891f54340`
- License: MITとして公開案内あり

注意: 2026-07-08のcommit `b93e6b912ca17a85c8ceaca93983c23695063679`で内部storytelling reference文書は公開リポジトリから削除された。削除済み文書をコードとしてvendoringしない。公開されていた時点で確認した設計思想を、NASDAQカフェ用に独自記述して採用する。

### 確認した特徴

- キーワード一致ではなく、物語上の意味で素材を選ぶ
- Hook、Scene、Reveal、Turn、Buttonなど、各素材の役割を明示する
- 隣接した素材が同じ意味・同じ温度なら一方を削除または移動する
- Turnのない並びを「物語ではなくリスト」と判定する
- 中間反転がなければAct未成立として扱う
- TopicとThemeを分ける
- 情報として正しいだけでは採用理由にしない
- 編集判断をStory terms → Audience effect → Informationの順で説明する
- 完成済み作品から編集スタイルを抽出し、AI提案へ反映するEditorial DNAの考え方を持つ

### 今すぐ採用

- Story role vocabulary
- Adjacent redundancy rule
- Midpoint turn requirement
- Topic / Theme separation
- Information-only rejection
- Scene deletion test
- HookとButtonを残し、中間の重複から削る考え方
- 過去の承認済みエピソードから制作上の成功パターンだけを抽出する考え方

### NASDAQカフェ向け変換

ドキュメンタリーの感情曲線を、そのまま市場番組へ持ち込まない。

```text
Emotional turn
→ Explanation turn

Protagonist wants something
→ 中心仮説が説明力を獲得または失う

Reveal
→ 見出しでは分からない証拠または比較

Button
→ Sceneの意味を短く確定し、次の問いへ接続する一文
```

### 採用しない

- インタビューの息継ぎ、filler密度、発話時制などに依存する素材選定
- Final Cut Pro / Premiere / DaVinciへの編集連携
- 削除済み内部文書の直接コピー
- 感情を作るための事実順序変更

---

## 4. OpenMontage

### 参照

- Repository: `calesthio/OpenMontage`
- 確認commit: `4eab34c5cfcccaa4f1970554928feccce73ee930`
- 主な参照ファイル:
  - `skills/creative/storytelling.md`
  - `skills/pipelines/explainer/proposal-director.md`
  - `skills/pipelines/explainer/script-director.md`
  - `skills/meta/reviewer.md`
  - `pipeline_defs/animated-explainer.yaml`

### 確認した特徴

- Research → Proposal → Script → Scene Plan → Assets → Edit → Composeを分離する
- Script前に複数のConcept / Angleを比較する
- Hookは情報を全部出さず、Information Gapを作る
- Guided Discoveryで視聴者が答えへ到達する過程を再構成する
- Scene接続を`AND THEN`ではなく`BUT / THEREFORE`で設計する
- Progressive Revelationで全体像を一度に出さない
- Hook → Setup → Build → Climax → Landingを明示する
- Reviewerが具体的なartifact位置、severity、proposed fixを返す
- Critical findingを直した後に再Reviewする
- Scene PlanにSlideshow Risk、Visual Variety、Shot Intentなどの検査を持つ
- Proposal段階で異なる構造・異なるHookの候補を競争させる

### 今すぐ採用

- Angle Competition
- Information Gap
- Misconception / Naive Explanation first
- Guided Discovery
- BUT / THEREFORE connection
- Progressive Revelation
- Hook promise → Climax payoff → Callback
- Artifact-specific Critique
- Findingごとの具体的修正案
- Stageごとのreview_focus / success_criteria

### NASDAQカフェ向け変換

```text
Misconception
→ 視聴者が最初に考えやすい単純な市場説明

Climax
→ 最も強い因果証拠または反転証拠

CTA
→ 今夜確認すべき検証点。売買行動を促さない

Concept option
→ 同じ事実から作る異なる編集角度
```

OpenMontageの「2回修正後は警告付きで進む」は、そのまま採用しない。NASDAQカフェでは、事実誤認、因果の過剰断定、重大な重複、回収不成立が残る場合はepisode package finalへ進めない。

### 採用しない

- OpenMontage本体の500以上のSkillを丸ごと導入すること
- 画像・音声・動画Provider選択を台本リポジトリへ移すこと
- AIによる完成動画の視覚採点
- 一般Explainer用CTA
- 外部フレームワークに主役や市場因果を決めさせること

---

## 5. video_explainer

### 参照

- Repository: `prajwal-y/video_explainer`
- 確認commit: `c033e28d6eccae43c1762f4653f9c320b16b050e`
- 主な参照ファイル:
  - `docs/REFINEMENT.md`
  - `src/refine/models.py`
  - `src/refine/script/narration_refiner.py`

### 確認した特徴

5段階のRefinementを持つ。

```text
Analyze
→ Script
→ Visual Cue
→ Visual
→ Sync
```

台本側では、SourceとScriptを比較し、次を検出する。

- Missing concepts
- Shallow coverage
- Narrative gaps
- Weak hook
- Poor transition
- Missing tension
- No key insight
- Redundant text
- Lacks specificity
- Lacks mechanism

問題はPatchとして表現される。

- `add_scene`
- `modify_scene`
- `expand_scene`
- `add_bridge`

### 今すぐ採用

- AnalyzeとRewriteを分ける
- 問題をPatchへ変換する
- Scene単位で修正を適用する
- Issue Typeを固定する
- 修正後にverificationを行う
- Source coverageとNarrative flowを別軸で見る

### NASDAQカフェ向け変換

追加するIssue Type候補:

```text
REPEATED_CONCLUSION
NO_BELIEF_CHANGE
NO_NEW_EVIDENCE
ANSWER_REVEALED_TOO_EARLY
PROCEDURAL_NARRATION
SCENE_ORDER_INTERCHANGEABLE
FOX_VOICE_ABSENT
NO_LATE_PAYOFF
ABSTRACT_EDITORIAL_LANGUAGE
NO_BEFORE_CONTEXT
NO_AFTER_IMPLICATION
NO_MIDPOINT_TURN
ENDING_NOT_BOOKENDED
CAUSALITY_DRIFT_DURING_REWRITE
```

Patch Type候補:

```text
merge_scene
remove_scene
reorder_scene
rewrite_scene
replace_connector
move_reveal_later
strengthen_hook_gap
add_counterevidence_block
add_callback
restore_causality_wording
```

### 採用しない

- AI完成画面検査
- Scene componentの自動修正
- 独自の素材・TTS・Remotion構成
- Sourceの網羅率を上げるためだけのScene追加

---

## 6. Toonflow

### 参照

- Repository: `HBAI-Ltd/Toonflow-app`
- 確認commit: `bc61ec7a1b5df31293b286981a5f4ad4635464ee`
- License: Apache-2.0

### 確認した特徴

- Planning → Scriptwriting → Storyboarding → Final Output
- Decision / Execution / Supervisionの三層Agent
- 章イベントをEvent Graphへ構造化する
- ScriptAgentとProductionAgentの中核指示をMarkdown Skillへ外出しする
- 中間成果物を編集・後戻りできる

### 今すぐ採用

- Story DiscoveryをEvent Graph / Evidence Graphとして表現する考え方
- Decision / Execution / Supervisionの分離
- SkillをGitHub上のMD正本ではなく、実行可能な工程へ変換する考え方
- 中間成果物から任意の工程へ戻れる設計

### NASDAQカフェ向け変換

```text
Chapter Event Graph
→ Evidence-backed Story Graph

Decision Layer
→ 02 Editorial Director

Execution Layer
→ Story Miner / Narrative Architect / Screenwriter

Supervision Layer
→ 04 + Independent Critic + Deterministic Validator
```

### 採用しない

- 小説の章・人物・伏線管理
- Infinite Canvas UI
- 画像・動画生成Provider
- 自律的な物語改変

---

## 7. ViMax

### 参照

- Repository: `HKUDS/ViMax`
- 確認commit: `05a48943878312d88fe5a016c12a9654940ecc43`
- Version確認時点: v1.2.0
- License: MIT

### 確認した特徴

- Idea2Video、Script2Video、Novel2Videoを分離する
- Story、Script、Storyboard、Shotを別成果物として扱う
- Agent Loopで企画・修正・レンダー制御を対話的に行う
- ArtifactとStoryboardをPreviewできる
- checkpoint / resumeを持つ
- Scriptのcreative intentを後段で維持する

### 今すぐ採用

- 中間Artifactの保存とPreview
- Story Discovery完了前にScriptへ進まないcheckpoint
- Script修正時にRender Specへ勝手に影響させない境界
- 中断・再開時に旧Artifactを誤使用しないversion binding

### 採用しない

- 画像・動画生成基盤
- Character consistency
- Shot生成
- ViMax本体の実行時依存

---

## 8. FireRed-OpenStoryline

### 参照

- Repository: `FireRedTeam/FireRed-OpenStoryline`
- 確認commit: `c9e945215586f45c12a61c1951ee9a8e9c43a027`
- License: Apache-2.0

### 参考にする点

- 意図を自然言語で指定し、編集操作を透明な工程へ変換する
- Conversational Refinement
- 完成した編集workflowをSkillとして保存し、素材を替えて再利用する
- OpenClaw / Claude Code向けSkill入口を持つ

### 後段で採用

承認済みの良い回が蓄積した後、次をproduction lessonとして抽出する。

- Hookの型
- Sceneの平均役割分布
- Turnの位置
- 狐の説明テンポ
- 画面モードの使い分け

ただし、過去回を表面的に模倣せず、当日の市場因果へ合わせる。

---

## 9. StoryWriter / GOAT-Storytelling-Agent / WriteHERE

### 参考にする点

- Top-down hierarchical planning
- Outline → Chapter / Scene Plan → Writing
- 長文履歴を圧縮して現在Sceneへ必要な情報だけ渡す
- Recursive planning

### 初期採用しない理由

- 主対象がフィクションである
- SurpriseやSuspenseのための創作を市場台本へ持ち込めない
- 登場人物・世界設定・長編整合の機能が過剰

構造の参考に限定し、事実や因果を物語都合で変える機能は導入しない。

---

## 10. 採用マトリクス

| 必要機能 | 主参照 | 補助参照 | NASDAQ実装先 |
|---|---|---|---|
| 前後関係の発見 | Doza Assist | Toonflow | Story Discovery |
| 複数角度の競争 | OpenMontage | ViMax | Angle Director |
| 単純説明の破壊 | OpenMontage | Doza Assist | Story Miner |
| Sceneの役割 | Doza Assist | OpenMontage | Narrative Arc |
| BUT / THEREFORE | OpenMontage | - | Narrative Architect |
| 中間Turn | Doza Assist | OpenMontage | Narrative Validator |
| Gap → Patch | video_explainer | OpenMontage Reviewer | Creative Review |
| 作者と監督の分離 | Toonflow | OpenMontage | Author / Critic split |
| Artifact checkpoint | ViMax | Toonflow | Daily State Machine |
| Workflow Skill再利用 | FireRed | Toonflow | Production Lessons |

---

## 11. 正式採用方針

### Tier A｜初期実装へ直接反映

1. Doza AssistのStory roleと重複・Turn判定
2. OpenMontageのAngle Competition、Guided Discovery、BUT / THEREFORE、Reviewer
3. video_explainerのGap Analysis、Issue、Patch、Verification

### Tier B｜アーキテクチャへ反映

4. ToonflowのDecision / Execution / SupervisionとEvent Graph
5. ViMaxのArtifact Preview、Checkpoint、Resume

### Tier C｜後段候補

6. FireRedのEditing Skill Archive
7. StoryWriter / GOAT / WriteHEREの階層計画
8. GraphRAG / Graphitiによる過去Story Pattern検索

---

## 12. Vendoringとライセンス方針

外部プロジェクトを本番のruntime dependencyにしない。

採用方法は次の順とする。

```text
外部プロジェクトを調査
→ 採用する概念を列挙
→ NASDAQ向けに独自記述
→ ローカルSKILL / schema / validatorへ実装
→ fixtureで再現確認
```

コードまたは文書を直接取り込む場合は、必ず次を保存する。

```text
references/external/<project>/
├── SOURCE.md
├── LICENSE
├── PINNED_COMMIT
├── ADOPTION_NOTES.md
└── NOTICE.md
```

ルール:

- ライセンス未確認のコードをコピーしない
- 削除済み・非公開化された文書をvendoringしない
- 外部のプロンプトをAGENTS.mdへ大量貼付しない
- 外部更新で日次の台本意味が変わらないようcommitを固定する
- 外部コードを使わず概念だけ採用する場合も出典と確認commitを残す
- 01〜04と競合する外部ルールは採用しない

---

## 13. 最終判断

朝のNASDAQカフェは、既存プロジェクトを丸ごとforkするのではなく、次の組み合わせを独自Skillへ消化する。

```text
Doza Assist
= 何が物語か、何が重複か、どこがTurnか

OpenMontage
= どう問いを仕込み、段階的に答えへ進み、具体的にReviewするか

video_explainer
= 問題をどうPatchへ変換し、部分修正して再検証するか

Toonflow
= 意思決定・実行・監督をどう分離するか

ViMax
= 中間成果物をどう確認・保存・再開するか
```

この採用層は、02の市場因果、01の狐、03の9Scene、04の審問を置き換えない。01〜04を、毎日の制作で実行可能な工程へ変換するために使用する。
