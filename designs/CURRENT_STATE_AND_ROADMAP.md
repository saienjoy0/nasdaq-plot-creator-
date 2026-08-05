# 朝のNASDAQカフェ｜現在地・次の工程・最終ゴール

- 基準日: 2026-08-05
- 基準main SHA: `379c6456b86231d620807ac990ee030f7dc267b8`
- 対象リポジトリ: `saienjoy0/nasdaq-plot-creator-`
- 現在のフェーズ: **調査・記憶基盤の完成後、制作パッケージ統合へ移る直前**

---

## 1. 現在地を一文で表す

現在は、**過去の番組記憶を安全に検索し、当日の一次情報で再検証したうえで因果調査へ渡せるところまで完成した**。

しかし、まだ次は完成していない。

```text
当日資料
→ 完成した9シーン台本
→ 画像採用経路確定
→ render_spec
→ preview
```

つまり、記憶基盤は完成したが、**日々の完成制作パッケージを一周させる統合工程はこれから**である。

---

## 2. 最終ゴール

最終ゴールは、記憶機能そのものを増やすことではない。

ユーザーが当日の`daily_source_package_YYYY-MM-DD.md`を渡した後、ChatGPTが編集判断を完成させ、検証済み成果物をrendererへ渡し、preview確認後だけ公開・記憶化できる状態を作ることである。

```text
ユーザーが当日資料を渡す
↓
ChatGPTが世界のニュースと現在証拠を確認
↓
関連する過去記憶だけを検索
↓
過去仮説を現在証拠で再検証
↓
Expected / Actual / Gap、時系列、主因、増幅、相殺、反対材料を確定
↓
02で編集判断
↓
01で狐の語りへ変換
↓
03で9シーンのepisode_packageを完成
↓
04で興味深さ・わかりやすさを審問し、必要箇所だけ修正
↓
Primary / Approved Fallbackを事前確定
↓
必要な当日固有画像をChatGPT側で生成、またはFallback採用
↓
spoken_script / asset_manifest / render_specを同じ完成内容から生成
↓
全成果物の整合validator PASS
↓
rendererリポジトリへ安全に配送
↓
GitHub ActionsがTTS・字幕・Remotion previewを機械的に実行
↓
ユーザーがpreviewを目視確認
↓
明示依頼がある場合だけfinal
↓
approved publication record
↓
承認済み内容だけを恒久記憶へ昇格
```

### ゴール判定

次をすべて満たしたとき、日次制作ループのMVP完成とする。

1. 実際の当日資料から因果調査成果物を作れる
2. 01〜04に従った最終episode packageを作れる
3. 再検証済みの過去記憶だけを台本へ参照できる
4. Primary / Fallbackの採用経路が一つに確定している
5. episode package、spoken script、asset manifest、render specが一致する
6. 未解決状態ゼロで正式validatorを通過する
7. rendererへ内容を変えず配送できる
8. GitHub Actionsでpreviewを生成できる
9. preview確認前にfinalへ進まない
10. 承認後だけ恒久記憶へ昇格できる

---

## 3. リポジトリの役割

### このリポジトリが担当すること

`nasdaq-plot-creator-`は、朝のNASDAQカフェの編集制御面である。

- 01〜04正本の保持
- 因果調査契約
- 過去記憶の検索・再検証・昇格
- episode package制作契約
- 最終制作成果物の整合契約
- rendererへ渡す前の正式validator
- 承認済みpublication recordの管理

### このリポジトリが担当しないこと

- MP4レンダー
- Gemini TTS実行
- 字幕同期処理
- Remotion実行
- 完成動画のAI視覚判定
- 市場因果の自動決定
- 主役ニュースの自動決定
- 狐の台本内容の機械的な書き換え

### rendererリポジトリの役割

`saienjoy0/saienjoy0-nasdaq-cafe-remotion`は、完成済み`render_spec.json`を動画へ変換する実行環境である。

```text
validated render_spec
→ asset existence check
→ Gemini TTS 2ブロック
→ 字幕・Visual Beat同期
→ Remotion preview
→ technical report / artifact保存
```

rendererは編集者ではない。

---

## 4. 完成済みの工程

### PR #1｜基盤

完成済み:

- 01〜04正本の保持・復元
- 因果調査Skillの初期契約
- editorial memory architecture
- memory policy
- core memory
- daily / weekly / thread / claim構造
- schemaとCI

### PR #2｜安全な記憶昇格

完成済み:

- dry-runと明示applyの分離
- immutable episode revision
- conflict detection
- stale plan防止
- SHA確認
- atomic rollback
- no-op再実行

### PR #3｜実エピソード受入試験

完成済み:

- renderer側の実episode package / render spec / validator recordを利用
- production record互換
- 実データでpromotion preflight
- 同一入力の再実行no-op

### PR #4｜最初の正式記憶

完成済み:

- 2026-07-31/v001を恒久記憶へ登録
- AI設備投資回収thread
- AI capex evaluation claim
- Amazon / AWS / Apple / SOXX alias
- 反対材料と留保を含むprovenance

### PR #5｜監査可能な記憶検索

完成済み:

- Query Plan
- alias解決
- thread / claim / episode / lesson検索
- relevance scoring
- status / provenance filtering
- duplicate・diversity・文字数制限
- 選択理由と除外理由
- AWS正例、Tesla無関係負例

### PR #6｜記憶再検証Bridge

完成済み:

- Query Plan / Context / Reportの決定的再実行
- バイト単位lineage確認
- SHA-bound research input manifest
- causal research dossier v0.2
- memory revalidation contract
- Report / Manifest完全照合
- repo外path・schema拒否
- current evidence品質検査
- memory-only Expected / Actual / causal edge / NASDAQ-wide cause拒否
- Evidence ID完全参照検査
- 25件の正常系・攻撃的テスト
- 実retriever end-to-end CI

### 現在できること

```text
Query Plan
→ 関連記憶検索
→ 検索結果の再現確認
→ Research Input Manifest
→ 現在証拠による記憶再検証
→ Causal Research Dossier v0.2
```

ここまでは正式基盤としてmainに入っている。

---

## 5. まだ完成していないもの

次はまだ自動・契約化されていない。

- causal dossierから最終episode packageへの正式なmemory reference接続
- episode package内で過去記憶をどのScene・どの用途に使ったかの監査
- `supported`、`historical_context_only`、`weakened`などの公開利用制御
- episode package全体の正式schemaとvalidatorの統合
- 04審問後の最終版だけを正本にする固定
- Primary / Approved Fallbackの最終採用経路の機械検査
- spoken script、asset manifest、render specの一括整合検査
- renderer配送用bundle manifest
- plot-creatorとrendererの契約バージョン照合
- 実際の新しい当日資料を使った全工程acceptance
- 一つの安全な日次実行入口

したがって、現時点で次の表現は誤りである。

```text
当日資料を置けば、完成動画まで完全自動で出る
```

正しくは次である。

```text
調査と記憶の安全基盤は完成した。
これから完成台本・画像採用・render_spec・preview配送を一つの制作契約へ接続する。
```

---

## 6. 次に行うPR

# PR #7｜Episode Package Memory Reference

### 目的

再検証済みの過去記憶だけを、最終episode packageへ安全に接続する。

### 推奨ブランチ

```text
feat/pr7-episode-package-memory-references
```

### 入力

- validated causal research dossier v0.2
- 02による編集判断
- 01〜04に従ってChatGPTが作った最終episode package

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

1. episode packageのmemory referenceはdossier内に実在すること
2. dossierのrevalidation statusと一致すること
3. current evidence IDがdossier内に実在すること
4. `supported`または適切な`partially_supported`だけが現在文脈に使えること
5. `historical_context_only`は過去比較としてだけ使えること
6. `weakened`と`invalidated`は反対材料または変化説明としてだけ使えること
7. `unresolved`、`not_used`は現在事実として台本へ入れないこと
8. memory referenceがない過去回言及を拒否すること
9. 一つのmemoryを複数Sceneで使う場合も用途を明示すること
10. memoryはタイトル・サムネイルを本文より強くしないこと

### PR #7の成果物

- episode package memory reference schema
- dossier → episode package validator
- status別の許可・拒否表
- positive / adversarial tests
- AGENTS・制作契約の最小更新

### PR #7の非目的

- 自動で台本を書くこと
- 主役を決めること
- 04の審問を機械化すること
- render_specを生成すること
- rendererを変更すること

### PR #7完了条件

- 再検証されていない記憶をepisode packageへ入れられない
- historical onlyを現在事実として利用できない
- weakened / invalidatedを肯定材料として利用できない
- memory参照Sceneとevidenceが追跡可能
- 記憶を使わない回も正常にPASSする

---

## 7. PR #7の後の順番

## PR #8｜Final Production Package Contract

目的:

- 04審問後のepisode packageを唯一の制作正本にする
- 同じ内容からspoken script、asset manifest、render specを作る契約を固定する
- ChatGPTが完成させた内容をコードが勝手に変更しないようにする

検査対象:

- Scene 1〜9の順番
- ナレーション
- Visual Beat
- 大・補助テロップ
- 数字
- 表情
- asset ID
- 表示合図
- 復帰先
- Primary / Fallback最終採用経路
- memory reference

## PR #9｜Renderer Handoff Bundle

目的:

- validator PASS済み成果物だけをrendererへ渡す
- plot-creatorとrendererの入力契約を固定する

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

`handoff_manifest.json`は全ファイルのSHA、contract version、対象日、validator結果を持つ。

## PR #10｜Real-Day End-to-End Acceptance

目的:

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

このPRでは自動finalへ進まない。

### MVPゴール

PR #10で実データのpreviewまで成功し、ユーザーが目視確認できた時点で、日次制作ループのMVP完成とする。

## PR #11｜Daily Operational Entry Point

目的:

日次作業を迷わず始められる一つの入口を作る。

ただし、これは編集AIではなく工程管理である。

可能な処理:

- 入力ファイル検出
- 対象日確定
- 既存古いrender specの誤実行防止
- 必須成果物一覧表示
- validator順序制御
- renderer handoff
- preview実行
- 停止理由の明示

行ってはいけない処理:

- 主役の自動決定
- 因果の自動決定
- ナレーションの自動変更
- Primary / Fallbackの自動推測
- preview確認前のfinal

### 運用ゴール

PR #11と実運用確認が終わった時点で、毎日の通常運用を次へ固定する。

```text
ユーザーが当日資料を渡す
→ ChatGPTが制作と判断を完成
→ validator済みbundleを配送
→ Actions preview
→ ユーザー確認
→ 明示依頼時だけfinal
→ 承認記録
→ memory promotion
```

---

## 8. 優先順位

次は必ずこの順番で進める。

```text
PR #7  記憶をepisode packageへ安全接続
↓
PR #8  最終制作成果物の共通正本と整合検査
↓
PR #9  renderer配送契約
↓
PR #10 実日のpreview acceptance
↓
PR #11 日次入口と運用安定化
```

先にrendererの見た目改修や追加自動化へ進まない。

理由:

- まだ台本側からrendererへ渡す正式契約が閉じていない
- 記憶参照がepisode packageへ追跡可能になっていない
- Primary / Fallbackとrender specの一貫性が未固定
- 実日の全工程acceptanceが未完了

---

## 9. 各担当の責任境界

### ChatGPTが完成させる

- 最新情報確認
- 主役選定
- Expected / Actual / Gap
- 時系列
- 主因・増幅・相殺・反対材料
- 世界からNASDAQへの因果経路
- 9シーン
- 狐ナレーション
- 04審問と修正
- Primary / Approved Fallback
- 必要画像の生成
- 最終採用経路
- episode package / render specの意味

### deterministic codeが行う

- schema検査
- SHA検査
- lineage検査
- Evidence ID参照検査
- memory status利用制御
- asset参照存在確認
- 成果物間の一致検査
- 古い入力の誤実行防止
- bundle作成

### GitHub Actionsが行う

- renderer input検証
- TTS 2ブロック
- 字幕・Visual Beat同期
- preview render
- 軽量技術検査
- Artifact保存
- 明示依頼がある場合だけfinal

### ユーザーが行う

- Primary画像の採用・不採用
- previewの目視確認
- final実行の明示
- 公開承認

---

## 10. 絶対に崩さない停止条件

次のどれかが残る場合はrendererへ渡さない。

- 因果調査未完了
- Expected根拠不明を確定扱い
- 重要反対材料欠落
- memory再検証未完了
- 04審問未反映
- Primary / Fallback未確定
- 参照asset不明
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

## 11. 次のAIへの直接指示

次に着手するのはPR #7である。

```text
ブランチ:
feat/pr7-episode-package-memory-references

目的:
validated causal dossierのmemory revalidationを、最終episode packageへ安全に接続する。
```

PR #7を始める前に確認するもの:

- `AGENTS.md`
- `source-of-truth/01_fox_character_bible.md`
- `source-of-truth/02_editorial_bible.md`
- materialized 03
- materialized 04
- `designs/PR6_EDITORIAL_MEMORY_REVALIDATION_BRIDGE.md`
- causal dossier v0.2 schema
- memory revalidation schema
- episode production specのmemory / source / Scene / evidence関連項目

PR #7では01〜04を変更しない。
PR #7では台本を自動生成しない。
PR #7ではrendererを変更しない。
PR #7ではmemory利用の監査契約とvalidatorだけを完成させる。

---

## 12. 最終結論

現在地は、**安全に覚え、安全に思い出し、安全に当日証拠で再検証できるところ**である。

次は、**その再検証済み記憶を、最終台本のどこでどう使ったか追跡できるようにするPR #7**である。

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
