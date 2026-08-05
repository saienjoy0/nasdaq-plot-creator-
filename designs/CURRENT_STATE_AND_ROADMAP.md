# 朝のNASDAQカフェ｜現在地・次の工程・最終ゴール

- 基準日: 2026-08-05
- 基準main SHA: `379c6456b86231d620807ac990ee030f7dc267b8`
- 文書化PR: **PR #7**
- 次の実装PR: **PR #8**
- 現在のフェーズ: **調査・記憶基盤の完成後、制作パッケージ統合へ移る直前**

---

## 1. 現在地

現在は、**過去の番組記憶を安全に検索し、当日の一次情報で再検証したうえで因果調査へ渡せるところまで完成した**。

完成済みの経路:

```text
memory query plan
→ 関連記憶検索
→ deterministic retrieval replay
→ SHA-bound research input manifest
→ 現在証拠によるmemory revalidation
→ causal research dossier v0.2
```

まだ完成していない経路:

```text
causal research dossier
→ 最終episode package
→ 04審問後の制作正本
→ Primary / Approved Fallback確定
→ spoken script / asset manifest / render spec
→ renderer handoff
→ preview
```

したがって、現時点で正しい説明は次である。

> 調査と記憶の安全基盤は完成した。これから完成台本、画像採用、render spec、preview配送を一つの制作契約へ接続する。

次の説明はまだ誤りである。

> 当日資料を置けば完成動画まで完全自動で出る。

---

## 2. 最終ゴール

ゴールは記憶機能を増やすことではない。

ユーザーが当日の`daily_source_package_YYYY-MM-DD.md`を渡した後、ChatGPTが市場因果と制作内容を完成させ、検証済み成果物だけをrendererへ渡し、preview確認後にだけfinal・公開・記憶化できる一周を完成させることである。

```text
当日資料
↓
現在情報と市場データの確認
↓
関連記憶の選択検索
↓
過去仮説の現在証拠による再検証
↓
Expected / Actual / Gap、時系列、主因、増幅、相殺、反対材料の確定
↓
02による編集判断
↓
01による狐の語り
↓
03による9シーンepisode package
↓
04による審問と必要箇所の修正
↓
Primary / Approved Fallbackの最終採用
↓
spoken script / asset manifest / render spec
↓
全成果物の整合validator PASS
↓
rendererへ配送
↓
GitHub Actions preview
↓
ユーザー目視確認
↓
明示依頼がある場合だけfinal
↓
approved publication record
↓
承認内容だけmemory promotion
```

### MVPゴール

実際の新しい当日資料一件で、次を成功させた時点。

- 因果調査
- 最終episode package
- 画像採用経路確定
- production bundle
- renderer handoff
- preview MP4生成
- ユーザーが目視確認可能

### 運用ゴール

毎日の通常運用を次へ固定できた時点。

```text
ユーザーが当日資料を渡す
→ ChatGPTが制作判断を完成
→ validator済みbundleを配送
→ Actions preview
→ ユーザー確認
→ 明示依頼時だけfinal
→ 承認記録
→ memory promotion
```

---

## 3. 担当範囲

### ChatGPTが担当する

- 最新情報確認
- 主役選定
- Expected / Actual / Gap
- 時系列
- 主因・増幅・相殺・反対材料
- 世界からNASDAQへの因果経路
- 9シーン構成
- 狐ナレーション
- 04審問と修正
- Primary / Approved Fallback
- 必要画像の生成
- 最終採用経路
- episode packageとrender specの意味

### `nasdaq-plot-creator-`が担当する

- 01〜04正本の保持
- 因果調査契約
- 記憶の検索・再検証・昇格
- episode package制作契約
- 成果物間の整合契約
- 正式validator
- renderer handoff manifest
- approved publication record

### deterministic codeが担当する

- schema検査
- SHA・lineage検査
- Evidence ID参照検査
- memory status利用制御
- asset存在確認
- 成果物間一致検査
- 古い入力の誤実行防止
- bundle作成

### rendererが担当する

- render spec検証
- Gemini TTS 2ブロック
- 字幕・Visual Beat同期
- Remotion preview
- 軽量技術検査
- Artifact保存
- 明示依頼がある場合だけfinal

### ユーザーが担当する

- Primary画像の採用・不採用
- previewの目視確認
- final実行の明示
- 公開承認

---

## 4. 完成済み

### PR #1｜基盤

- 01〜04正本の保持・復元
- causal research Skill初期契約
- editorial memory architecture
- memory policy、core、daily、weekly、thread、claim
- schemaとCI

### PR #2｜安全な記憶昇格

- dry-run / explicit apply
- immutable revision
- conflict detection
- stale plan防止
- SHA確認
- atomic rollback
- no-op再実行

### PR #3｜実エピソード受入試験

- renderer側の実episode package / render spec / validator recordを使用
- production record互換
- 実データpromotion preflight
- 再実行no-op

### PR #4｜最初の正式記憶

- `2026-07-31/v001`
- AI設備投資回収thread
- AI capex evaluation claim
- Amazon / AWS / Apple / SOXX alias
- 反対材料を含むprovenance

### PR #5｜監査可能な記憶検索

- Query Plan
- alias解決
- relevance scoring
- status / provenance filtering
- duplicate・diversity・文字数制限
- 選択理由・除外理由
- AWS正例、Tesla無関係負例

### PR #6｜記憶再検証Bridge

- deterministic retrieval replay
- Context / Reportのバイト一致
- SHA-bound research input manifest
- causal research dossier v0.2
- memory revalidation contract
- Report / Manifest完全照合
- repo外path・schema拒否
- current evidence品質検査
- memory-only Expected / Actual / causal edge拒否
- Evidence ID完全参照検査
- 25件の正常系・攻撃的テスト
- 実retriever end-to-end CI

### PR #7｜現在地とロードマップの文書化

- この文書
- READMEの現在地更新
- 次の実装をPR #8として固定

PR #7は文書だけであり、制作機能は追加しない。

---

## 5. まだ完成していないもの

- dossierからepisode packageへのmemory reference接続
- 過去記憶をどのSceneでどう使用したかの監査
- episode package全体の正式validator統合
- 04審問後の最終版だけを制作正本にする固定
- Primary / Fallback最終採用経路検査
- spoken script / asset manifest / render specの一括整合検査
- renderer配送用bundle manifest
- plot-creatorとrendererのcontract version照合
- 実日の全工程acceptance
- 日次の安全な一つの入口

---

## 6. 次に行う実装

# PR #8｜Episode Package Memory Reference

推奨ブランチ:

```text
feat/pr8-episode-package-memory-references
```

### 目的

再検証済みの過去記憶だけを、最終episode packageへ安全に接続する。

### 入力

- validated causal research dossier v0.2
- 02による編集判断
- 01〜04に従いChatGPTが作った最終episode package

### 追加する内部参照

```text
memory_reference_type
memory_reference_id
historical_confidence
current_revalidation_status
current_evidence_ids
difference_from_previous
editorial_use
scene_ids
public_usage_mode
```

`public_usage_mode`候補:

- `current_supported_context`
- `historical_comparison`
- `counterevidence`
- `monitoring_point`
- `internal_only`

### 必須ルール

1. memory referenceはdossier内に実在する
2. revalidation statusがdossierと一致する
3. current evidence IDが実在する
4. `supported`または適切な`partially_supported`だけを現在文脈へ使える
5. `historical_context_only`は過去比較に限定する
6. `weakened`と`invalidated`は変化説明・反対材料に限定する
7. `unresolved`と`not_used`を現在事実として台本へ入れない
8. memory referenceなしの過去回言及を拒否する
9. 利用Sceneと用途を追跡できる
10. タイトル・サムネイルを本文より強くしない

### 成果物

- episode package memory reference schema
- dossier → episode package validator
- status別許可・拒否表
- positive / adversarial tests
- AGENTSと制作契約の最小更新

### 非目的

- 自動台本生成
- 主役決定
- 04審問の機械化
- render spec生成
- renderer変更

### 完了条件

- 未再検証memoryをepisode packageへ入れられない
- historical onlyを現在事実として使えない
- weakened / invalidatedを肯定材料に使えない
- memory利用Sceneとevidenceを追跡できる
- memoryを使わない回もPASSする

---

## 7. その後の順番

## PR #9｜Final Production Package Contract

- 04審問後のepisode packageを唯一の制作正本にする
- 同じ内容からspoken script、asset manifest、render specを作る契約を固定する
- Scene順、ナレーション、Visual Beat、テロップ、数字、表情、asset ID、表示合図、復帰先、memory referenceを一致検査する
- Primary / Approved Fallbackの最終採用経路を一つに固定する

## PR #10｜Renderer Handoff Bundle

- validator PASS済み成果物だけをrendererへ渡す
- plot-creatorとrendererのcontract versionを固定する
- 全ファイルのSHAと対象日を持つ`handoff_manifest.json`を作る

出力候補:

```text
production-bundles/YYYY-MM-DD/
├── episode_package_YYYY-MM-DD.md
├── spoken_script_YYYY-MM-DD.md
├── asset_manifest.json
├── render_spec.json
├── official_execution_preflight.json
├── asset_resolution_log.json
├── image_generation_log.json
├── picturebook_backlog_delta.json
└── handoff_manifest.json
```

## PR #11｜Real-Day End-to-End Acceptance

実際の新しい当日資料一件で次を通す。

```text
daily source
→ memory retrieval
→ causal dossier
→ episode package
→ 04審問後の最終版
→ image path resolution
→ production bundle
→ renderer handoff
→ preview MP4
```

自動finalへは進まない。

このPRで実データpreviewまで成功し、ユーザーが目視確認できた時点でMVP完成とする。

## PR #12｜Daily Operational Entry Point

- 入力ファイル検出
- 対象日確定
- 古いrender spec誤実行防止
- 必須成果物一覧
- validator順序制御
- renderer handoff
- preview実行
- 停止理由の明示

この入口は工程管理であり、編集AIではない。

行ってはいけないこと:

- 主役の自動決定
- 因果の自動決定
- ナレーションの自動変更
- Primary / Fallbackの自動推測
- preview確認前のfinal

---

## 8. 固定する優先順位

```text
PR #8  記憶をepisode packageへ安全接続
↓
PR #9  最終制作成果物の共通正本と整合検査
↓
PR #10 renderer配送契約
↓
PR #11 実日のpreview acceptance
↓
PR #12 日次入口と運用安定化
```

この順番より先にrendererの見た目改修や追加自動化へ進まない。

理由:

- 台本側からrendererへ渡す正式契約が閉じていない
- memory利用がepisode packageで追跡可能になっていない
- Primary / Fallbackとrender specの一貫性が未固定
- 実日の全工程acceptanceが未完了

---

## 9. 停止条件

次のどれかが残る場合はrendererへ渡さない。

- 因果調査未完了
- Expected根拠不明を確定扱い
- 重要反対材料欠落
- memory再検証未完了
- 04審問未反映
- Primary / Fallback未確定
- asset不明
- episode packageとrender spec不一致
- validator FAIL
- unresolved stateあり
- 対象日不一致
- 古いrender spec

次のどれかが残る場合はfinalへ進まない。

- preview未生成
- preview未確認
- ユーザーの明示依頼なし

次のどれかが残る場合はmemory promotionしない。

- publication record未承認
- preview未承認
- rejected因果を含む
- 未採用画像経路を含む
- pre-inquisition narrationを含む

---

## 10. 次のAIへの直接指示

次に着手する実装はPR #8である。

```text
ブランチ:
feat/pr8-episode-package-memory-references

目的:
validated causal dossierのmemory revalidationを、最終episode packageへ安全に接続する。
```

開始前に読むもの:

- `AGENTS.md`
- `source-of-truth/01_fox_character_bible.md`
- `source-of-truth/02_editorial_bible.md`
- materialized 03
- materialized 04
- `designs/PR6_EDITORIAL_MEMORY_REVALIDATION_BRIDGE.md`
- causal dossier v0.2 schema
- memory revalidation schema
- episode production specのScene・source・evidence関連項目

PR #8では01〜04を変更しない。
PR #8では台本を自動生成しない。
PR #8ではrendererを変更しない。
PR #8ではmemory利用の監査契約とvalidatorだけを完成させる。

---

## 11. 最終結論

現在地は、**安全に覚え、安全に思い出し、安全に当日証拠で再検証できるところ**である。

次は、**再検証済み記憶を最終台本のどこでどう使ったか追跡可能にするPR #8**である。

全体のゴールは、

```text
当日資料
→ 編集判断済み制作パッケージ
→ validator PASS
→ preview
→ ユーザー確認
→ final
→ 承認済み記憶
```

という一周を、意味を変えず、安全に、毎日繰り返せる状態にすることである。
