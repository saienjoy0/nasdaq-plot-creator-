# 朝のNASDAQカフェ｜Story Engine直接取り込み判断表 v1.1

- 更新日: 2026-08-07
- 対象リポジトリ: `saienjoy0/nasdaq-plot-creator-`
- 実装設計: `designs/STORY_ENGINE_IMPORT_IMPLEMENTATION_PLAN_v1.1.md`
- 目的: 外部Story Creationプロジェクトから、実際にvendorする資産、adaptする構造、clean-roomで再実装する思想、採用しないものを固定する

## 1. 原則

外部project本体をruntime dependencyとして導入しない。

採用方式は4分類とする。

1. `direct-vendor`
   - MIT / Apache-2.0等でlicenseとpinned commitを確認できる独立資産
   - SOURCE、commit、LICENSE、NOTICE、変更内容を保存する
2. `adapt`
   - license上利用可能な構造・小さなhelperをNASDAQ契約へ薄く変換する
3. `clean-room`
   - 一般的設計思想のみ参照し、コード・schema・prompt本文はコピーしない
4. `reject`
   - 強いcopyleft、目的不一致、過剰なruntime依存、外部provider等

優先順位は常にプロジェクト指示 → 02 → 01 → 03 → 04 → 外部assetである。

---

## 2. 最新採用マトリクス

| Project | Pinned commit | License確認 | 方式 | 今回採用 | 直接コピー |
|---|---|---|---|---|---|
| Doza Assist | `b93e6b912ca17a85c8ceaca93983c23695063679` | MIT LICENSE本文確認 | `direct-vendor` + adapter | Storytelling Foundation、Turn、adjacent redundancy、information-only rejection、story roles | `docs/storytelling-foundation-oss.md`とLICENSEを帰属付きvendor |
| Toonflow | `bc61ec7a1b5df31293b286981a5f4ad4635464ee` | Apache-2.0 LICENSE本文確認 | `adapt` | Decision / Execution / Supervision、execution→review gate、具体的finding | domain promptは直接実行しない |
| ViMax | `05a48943878312d88fe5a016c12a9654940ecc43` | MIT LICENSE本文確認 | `adapt` | targeted revision、dependent artifact stale化、partial failure preservation、wrong-output guards | tightly coupled runtimeはコピーしない |
| FireRed-OpenStoryline | `c9e945215586f45c12a61c1951ee9a8e9c43a027` | Apache-2.0 LICENSE本文確認 | `adapt` | 問題Stageだけへ戻るlocalized rerun、workflow skill化 | 編集runtime全体はコピーしない |
| video_explainer | `c033e28d6eccae43c1762f4653f9c320b16b050e` | `pyproject.toml` / READMEでMIT宣言、root LICENSE取得不可 | `clean-room` | approved plan→script、information gap、BUT/THEREFORE、mechanism explanation | 初期はcode/prompt本文をコピーしない |
| OpenMontage | `4eab34c5cfcccaa4f1970554928feccce73ee930` | AGPL-3.0 LICENSE本文確認 | `clean-room` | Angle Competition、Guided Discovery、Progressive Revelation、artifact-specific review/checkpoint | code/schema/promptをコピーしない |

---

## 3. Doza Assistは今回から実際にvendorする

旧判断ではStorytelling文書を「削除済み」としてvendoring対象外にしていた。

2026-08-07の再確認では、`b93e6b912ca17a85c8ceaca93983c23695063679`に次が存在することを確認した。

- `docs/storytelling-foundation-oss.md`
- `editorial_dna/storytelling.py`
- `LICENSE`

Repository LICENSEはMITである。

したがって、`docs/storytelling-foundation-oss.md`を元commit固定・帰属付きで`references/external/doza-assist/`へ保存する。

ただしruntimeへ全文を無条件注入しない。

NASDAQ用Adapterが01〜04と整合するruleだけを選ぶ。

採用:

- Turnのない並びはlist
- adjacent redundancyはmomentumを壊す
- information onlyではstory roleにならない
- Hook / Reveal / Turn / Button等のrole思考
- TopicとTheme / Claimの分離
- midpoint turn
- final self-check

除外:

- filler density
- breath gap
- tense shift
- documentary emotional valence
- clip in/out point
- FCP/Premiere等の編集固有処理

`editorial_dna/storytelling.py`はtask別rule routingの参考として有用だが、Doza固有prompt検出とpath構造へ結合しているため初期にはvendorしない。
NASDAQ側で小さなrule selectorを独自実装する。

---

## 4. ToonflowはAgent責任分離だけadaptする

参照:

- `data/skills/script_agent_decision.md`
- `data/skills/script_agent_supervision.md`
- `src/agents/scriptAgent/index.ts`

採用:

```text
Decision
→ Execution
→ Supervision
```

NASDAQ変換:

```text
02 Editorial Lock / Story Plan decision
→ Fox Script Author
→ Independent Critic + 04 + deterministic guard
```

採用する実行規則:

- execution失敗時にreviewへ進まない
- reviewerは作者の自己評価に依存しない
- reviewerは成果物を実際に読み、場所、問題、視聴者影響、修正案を返す
- reviewとrewriteの責任を分ける

不採用:

- short-drama課金点
- 情緒爆点
- 大三角
- 小説章 / 人物 / 伏線管理
- UI / DB / model provider

---

## 5. ViMaxはTargeted RevisionとStale Graphをadaptする

参照:

- `agent_runtime/vimax_adapters.py`
- `tests/test_wrong_output_guards.py`

採用:

- `revision_target`相当の対象artifactだけを修正する
- upstream artifact変更時にdependent artifactをstaleへする
- partial failureで成功済みartifactを破壊しない
- missing dependencyのまま後段を開始しない
- silent wrong outputをfixtureで検査する

NASDAQ依存関係:

```text
causal dossier
→ story_plan
→ script_draft
→ creative_review
→ story_acceptance
```

前段変更時は後段をすべてstaleにする。

不採用:

- ViMax provider
- LangChain runtime
- image/video generation
- character consistency
- camera/shot pipeline

---

## 6. FireRed-OpenStorylineはAffected-stage rerunをadaptする

参照:

- `.storyline/skills/default_editing_workflow_skill/SKILL.md`
- `docs/source/en/guide.md`

採用:

問題が出ても全工程を最初からやり直さず、責任Stageだけへ戻る。

```text
市場因果・数字・Expected・timeline
→ 02 / Causal Research

central contradiction / angle / no turn
→ Story Plan

狐口調 / clarity / repeated wording
→ Fox Script

Critic finding
→ Targeted Patch

9Scene基本役割 / production package
→ 03

画像route
→ image selection

render contract
→ render_spec / validator
```

このreturn stageをfindingへ必須記録する。

---

## 7. video_explainerはclean-room採用

`pyproject.toml`には`license = {text = "MIT"}`がありREADMEでもMITとされるが、pinned commitでroot LICENSE本文を取得できなかった。

License gateを厳格に保つため、初期はcode・enum・prompt本文をvendorしない。

参照する一般原則:

- approved planからscriptを書く
- central questionを一本にする
- information gapを開いてから説明する
- sourceの具体的数字を使う
- mechanismを説明する
- `BUT / THEREFORE`でScene間の因果をつなぐ
- narrationとvisual descriptionを対応させる

02が要求する「主役一本＋NASDAQへの因果」を優先し、source全項目の網羅は目的にしない。

---

## 8. OpenMontageはAGPLのためclean-room only

採用する一般原則:

- Stage分離
- Angle Competition
- Guided Discovery
- Progressive Revelation
- Information Gap
- BUT / THEREFORE
- artifact location付きfinding
- Critical修正後のre-review
- checkpoint / success criteria

禁止:

- code
- schema
- prompt本文
- runtime dependency
- 部分vendor

---

## 9. 03 / 04との衝突防止

外部Storytelling projectの一般的な「scene削除・再配置」は、そのままNASDAQへ入れない。

03は9Sceneの順番と役割を原則維持する。
04は9Sceneの基本役割を変更禁止としている。

そのため本番Patchから次を除外する。

```text
remove_scene
merge_scene
reorder_scene
```

許可:

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

また、Scene 9は固定エンディングで新しい論点を追加しない。
Bookend / Closing ReframeはScene 8で完了する。

---

## 10. 今回のdirect-vendor配置

```text
references/external/doza-assist/
├── SOURCE.md
├── PINNED_COMMIT
├── LICENSE
├── MODIFICATIONS.md
└── storytelling-foundation-oss.md
```

Toonflow / ViMax / FireRed / video_explainer / OpenMontageは、初期PRではsource registryのみでよい。
実行コードを増やす必要が出た場合に個別License gateを通す。

---

## 11. 外部runtime dependencyは禁止

- submodule禁止
- 日次clone禁止
- latest自動取得禁止
- 外部APIへ市場因果判断を委譲禁止
- 外部story engineへ主役変更を許可しない
- 外部画像/動画providerを台本repoへ追加しない

pinned referenceとNASDAQ固有Adapterだけで日次出力を再現できる状態にする。

---

## 12. License gate

直接assetを追加する前に必ず確認する。

- pinned commit
- license本文
- file固有license header
- NOTICE義務
- copyright notice
- dependency追加
- 配布方式との互換性
- 直接vendorする必要性

一つでも不明なら`clean-room`へ倒す。

---

## 13. 最終判断

外部コード量を成功指標にしない。

成功は次で判断する。

- 2026-08-06旧台本を正しくFAILできる
- 問題Scene / 文を特定できる
- minimal patchを返せる
- 9Sceneが九段階の理解変化になる
- Scene 4〜6にTurnがある
- Scene 6〜8を見る理由がある
- Scene 8で回収しScene 9へ新論点を残さない
- rewriteでEvidence、timeline、confidence、counterevidenceが変わらない
- Story Engine acceptanceなしではepisode finalへ進めない

この条件を満たすため、Dozaの安全なFoundation assetは直接vendorし、それ以外は薄いadapt / clean-roomを優先する。