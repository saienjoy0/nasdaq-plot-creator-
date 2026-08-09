# 朝のNASDAQカフェ｜Story Engine Understanding Progression 設計書 v1.1

- 作成日: 2026-08-09
- 対象: Story Plan / Fox Authoring / Entertainment Critic / Final Episode Package Review
- 状態: 実装正本

## 1. 中心思想

> **朝のNASDAQカフェは、質問を連鎖させる番組ではない。視聴者の理解を連鎖させる番組である。**

「最後に答えがあるから見る」のではなく、Sceneごとに一段理解し、その理解によって次の比較・テスト・境界・反対材料・検証を見る価値が生まれる構造を作る。

固定するのは市場の意味と視聴者の理解変化であり、狐の語尾や疑問形は固定しない。

```text
Viewer Understanding Before
↓
Evidence / Meaning
↓
Payoff
↓
Viewer Understanding After
↓
Continuation Reason (Scene 1–7) / Closure (Scene 8)
```

## 2. Frozen contract

Understanding Progressionは以下を変更しない。

- lead
- Expected / Actual / Gap
- Evidence IDs
- chronology
- confidence
- primary / amplifier / offset / counterevidence
- causal scope
- material counterevidence
- reason_unknown
- Scene 1–9 formal roles

Payoffを作るための新因果創作は禁止する。

## 3. Story Plan v1.2

Scene fieldは次とする。

```json
{
  "scene_id": "scene-04",
  "formal_role": "expected_actual_gap",
  "story_role": "explanation",
  "viewer_belief_before": "...",
  "new_evidence_ids": ["E-004", "E-005"],
  "new_meaning": "...",
  "viewer_belief_after": "...",
  "continuation_reason": "...",
  "connector": "but"
}
```

`remaining_question`は廃止し、`continuation_reason`へ置換する。

### Scene 1–7

必須:

- viewer_belief_before
- new_meaning
- viewer_belief_after
- continuation_reason

Continuationは疑問形でなくてよい。許可型:

- question
- comparison
- test
- boundary
- counterevidence
- implication
- verification

### Scene 8

Scene 8は次のSceneへのhookを要求しない。

```text
continuation_reason = ""
```

必須:

- payoff
- belief update
- strengthen / weaken / uncertainty条件
- opening promiseの回収
- closing reframe

### Scene 9

固定Closing。

- new evidenceなし
- new meaningなし
- continuationなし

## 4. new_meaningの安全定義

`new_meaning`は「新しい原因」を意味しない。

有効なPayoff:

- 単純説明を一つ消す
- 不確実性を狭める
- 事実時系列を理解する
- Expected / Actual / Gapを理解する
- peer差を具体化する
- 仮説を価格反応でテストする
- causal scopeを限定する
- 反対材料を理解する
- 何が未確認か理解する
- 仮説の強弱条件を理解する
- reason_unknownである理由を理解する

## 5. Authoring

Story Planは意味契約でありspoken copyではない。

禁止:

- 「次に見ます」
- 「続いて確認します」
- 「時系列を固定します」
- 「ここまでが確認済み事実です」
- 「仮説を検証します」

狐は自然な話し言葉へ変換する。

Authoring末尾にsurface-only Spoken Delivery Passを1回だけ行う。

変更可:

- 語順
- 文長
- 接続
- 話し言葉
- 短い狐反応
- 疑問の明示/暗示
- 短い比喩

変更不可:

- Claim ID / Evidence ID
- 数字
- Expected / Actual / Gap
- chronology
- claim type
- confidence
- scope
- counterevidence
- formal role

## 6. Entertainment Critic

04の6項目30点制は維持する。

Scene 1–7はProgression Check:

- payoff_delivered
- belief_changed
- continuation_reason_natural
- procedural_language_dominant

Scene 8はClosure Check:

- payoff_delivered
- belief_changed
- closure_effective
- opening_promise_recovered
- procedural_language_dominant

Scene 8へnext-hookを要求しない。

追加Failure:

- NO_PAYOFF
- FAKE_OPEN_LOOP
- DEAD_END_SCENE
- OPENING_PROMISE_NOT_RECOVERED
- ENDING_NOT_BOOKENDED
- NO_NEW_EVIDENCE_OR_MEANING

既存の因果FailureはCriticalのまま。

## 7. Fake Open Loop

Fake Open Loopとは、現在Scene内で答えられる材料を持っているのに、suspenseのためだけに答えを隠し、次Sceneが新しいEvidence / Meaning / Comparison / Test / Boundaryを追加しない状態。

有効なContinuationは、現在SceneがPayoffを渡した結果として次の確認価値が生まれる。

## 8. Final title / thumbnail audit

Story Engine段階では最終タイトル・サムネイルを審査しない。

Story Engineでは`opening_promise`回収のみ確認する。

最終episode package完成後、04最終審問で:

- FINAL_TITLE_PROMISE_NOT_RECOVERED
- THUMBNAIL_PROMISE_NOT_RECOVERED

を確認する。

## 9. External Critic policy

通常の04 editorial reviewは必須。

有料の外部Independent Criticは品質強化オプション。

外部Critic未実行時:

```text
critic_certified = false
external_critic_status = not_run
```

Daily Productionは明示的な`external_critic_optional` policyで進められる。

厳格モードでは従来どおり`orchestrator_signed` receiptを要求できる。

古いreceiptを新しいdraftへ付け替えてはいけない。Reviewed inputのblobが変われば旧receiptはfail closedする。

## 10. 2026-08-06 regression

Frozen:

- AMD Q3 outlook 約130億ドル
- usual consensus 約125.2億ドル
- Gap 約+4.8億ドル
- AMD -7.04%
- NVIDIA +3.43%
- SOXX -2.12%
- Nasdaq Composite -0.83%
- Alphabet -4.03%
- Microsoft -1.09%
- Dow上昇
- SpaceX/NVIDIAはsupporting/relative evidence
- confidence Medium
- AMD一社をNASDAQ全体原因へしない
- missing minute/rates/VIX等を残す

全Sceneを同じ基準で審査する。Scene 1–2を聖域化しない。

期待する理解進展:

1. 半導体全面安ではない
2. 悪決算だけではない
3. 通常予想未達でもない
4. 採点軸が一つではない可能性
5. NVIDIA側に具体的採用証拠
6. 値動きと仮説の整合テスト
7. NASDAQ全体へのscopeを限定
8. 強弱条件・不確実性・opening callback
9. fixed close

## 11. Implementation slices

### R1 — Understanding Progression Contract

- Story Plan v1.2
- remaining_question → continuation_reason
- validator
- migration adapter
- regression tests

### R2 — Fox Delivery + Critic

- Authoring Skill
- surface-only pass
- Scene 1–7 Progression Check
- Scene 8 Closure Check
- failure vocabulary
- external Critic optionalityをhonest lineageとして分離

### R3 — 2026-08-06 Migration + A/B

- v1.2 Story Plan
- spoken delivery rewrite
- structured 04 review
- frozen causal metadata
- A/B review record

## 12. Definition of Done

- Story Plan v1.2 validates
- Scenes 1–7 have continuation value without question-factory behavior
- Scene 8 closes instead of opening another hook
- Scene 9 fixed
- procedural narration Majorなし
- Fake Open Loopなし
- Scene 6/7に独自Payoff
- Fact / Evidence / Timeline / Confidence / Scope diff = zero
- external Critic absence is explicit, never fabricated
- final title/thumbnail audit remains downstream
