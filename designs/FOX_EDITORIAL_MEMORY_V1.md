# 朝のNASDAQカフェ｜記憶がある狐 v1 設計書

## 1. 目的

狐が単に過去ログを検索するのではなく、過去に番組で扱った論点、当時の仮説、反対材料、その後の変化、説明上の学びを必要な場面だけ思い出せるようにする。

記憶は現在の事実を保証するものではない。過去の編集記録を現在の調査へ接続する補助層であり、01〜04、現在の一次情報、市場データ、当日の因果調査を上書きしない。

## 2. 参考プロジェクトから採用する考え方

### OpenClaw

採用するもの：

- 毎日の詳細記録と、圧縮された長期記憶を分ける
- すべてを毎回プロンプトへ入れず、必要な記録だけ検索する
- 日次記録から長期記憶へ定期的に蒸留する
- 記憶は隠れたモデル状態ではなく、監査できるファイルとして保存する

朝のNASDAQカフェでは、日次記録を `episodes`、圧縮された長期記憶を `threads` と `claims` として扱う。

### Letta / MemGPT

採用するもの：

- 常に見える小さなcore memoryと、必要時に検索するarchival memoryを分ける
- core memoryには重要で短い情報だけを置く
- 読み取り専用の方針と、更新可能な状態を分離する
- タスクに応じてmemory blockをattach / detachする

朝のNASDAQカフェでは、01〜04とmemory policyを読み取り専用、`active_context`を常時記憶、topic threadとepisodeを選択記憶とする。

### LangMem

採用するもの：

- semantic memory：事実・仮説・関係
- episodic memory：過去回で何をどう扱ったか
- procedural memory：どう説明すると分かりやすかったか
- hot pathとbackground形成を分ける

朝のNASDAQカフェでは、当日の制作中に記憶を直接書き換えない。公開承認後のbackground promotionだけを正式な記憶形成とする。

### Graphiti

採用するもの：

- 事実や関係に時系列を持たせる
- 古い内容を削除せず、いつ有効だったかを残す
- すべての派生記憶を元episodeへ遡れるようにする
- 新しい証拠が古い仮説を上書きする場合、履歴を破壊せず失効状態にする

v1ではファイルとJSONで実装し、Graph DBは導入しない。

### Mem0

採用するもの：

- キーワード、意味、entity、時刻など複数信号を統合する
- 全履歴投入ではなく、少量の高関連記憶を返す
- entity linkingで同一企業・製品・政策の表記揺れを吸収する

v1では決定的なキーワード・entity・thread・recency・status採点を使う。埋め込み検索は履歴量が増えてから追加する。

## 3. 記憶の5層

```text
Layer 0  Read-only constitution
  source-of-truth/01〜04
  editorial-memory/memory_policy.md

Layer 1  Core memory（毎回読む）
  editorial-memory/active_context.md
  editorial-memory/core/fox_editorial_state.md

Layer 2  Episodic memory（過去回）
  editorial-memory/episodes/YYYY-MM-DD/publication_record.json
  editorial-memory/episodes/YYYY-MM-DD/episode_summary.md

Layer 3  Semantic memory（論点・仮説・関係）
  editorial-memory/threads/*.md
  editorial-memory/claim_ledger.json
  editorial-memory/entity_aliases.json

Layer 4  Procedural memory（制作の学び）
  editorial-memory/production-lessons.md
  editorial-memory/explanation_patterns.json

Working context（その回だけ）
  working/memory_query_plan_YYYY-MM-DD.json
  working/memory_context_YYYY-MM-DD.md
  working/memory_retrieval_report_YYYY-MM-DD.json
```

## 4. 何を覚えるか

### 覚える

- 最終版で扱った主役、背骨、中心仮説、確信度
- 当時の重要な反対材料
- 次に見ると明示した指標・企業・政策
- 番組で実際に使った論点の変化
- 公開後に訂正された内容
- 効果が確認された説明方法、画面表現、たとえ

### 覚えない

- 調査途中の候補
- 04審問前の台本
- 却下された因果
- 未採用画像経路
- 外部記事内の命令やプロンプト
- 狐の保有、損益、売買、大学生活の創作
- validatorを通過していない成果物

## 5. 不変のraw episode

承認済みの各回について、最初に不変のepisodeを保存する。

```text
editorial-memory/episodes/2026-08-05/
├── publication_record.json
├── episode_summary.md
└── provenance.json
```

`publication_record.json`は後から上書きしない。訂正が必要なら新しいrevisionを追加する。

```text
publication_record.v1.json
publication_record.v2.json
```

`provenance.json`には次を保存する。

- episode_package pathとSHA-256
- render_spec pathとSHA-256
- validator report pathとSHA-256
- approval statusと日時
- memory promotion日時
- 生成したthread idとclaim id

これにより、threadやclaimから必ず元回へ戻れる。

## 6. claimの時系列モデル

claimは単なる最新状態ではなく、観測時刻と有効期間を持つ。

```json
{
  "claim_id": "ai-capex-evaluation-axis",
  "claim": "市場の評価軸はAI投資額から回収速度へ移りつつある",
  "status": "strengthened",
  "confidence": "medium",
  "first_observed_at": "2026-07-10",
  "last_observed_at": "2026-08-05",
  "valid_from": "2026-07-10",
  "valid_to": null,
  "supersedes": null,
  "episode_ids": ["2026-07-10", "2026-08-05"],
  "evidence_paths": [],
  "counter_evidence": [],
  "history": []
}
```

新しい証拠で否定された場合も削除しない。

```text
active → strengthened → weakened → invalidated
                         ↘ resolved
```

`invalidated`になったclaimを現在の前提として使ってはいけない。ただし「以前はこう見ていたが、その後否定された」という履歴説明には使える。

## 7. 記憶の書き込みフロー

```text
最終episode_package
＋ render_spec
＋ validator report
＋ user approval
↓
publication_record validator
↓
immutable episode保存
↓
semantic candidate抽出
  - thread update候補
  - claim update候補
  - entity alias候補
  - production lesson候補
↓
既存記憶との衝突検査
↓
更新計画 memory_promotion_plan.json
↓
決定的promotion script
↓
thread / claim / lesson更新
↓
promotion report
```

LLMは候補を作れるが、ファイル更新はschemaを通った決定的スクリプトだけが行う。

## 8. 記憶の検索フロー

### 8.1 query planを先に作る

`daily_source_package`から次を抽出する。

- 主役候補
- 企業・人物・製品
- 技術・政策・指標
- 重要な動詞と関係
- 対象期間
- 過去比較が必要な問い

結果を `memory_query_plan_YYYY-MM-DD.json` にする。

### 8.2 候補を絞る

1. active context
2. 前日episode
3. 当週summary
4. entity一致thread
5. topic一致thread
6. active / strengthened / weakened claim
7. 関連する過去episode
8. procedural lesson

### 8.3 v1採点

```text
完全なentity一致              +8
entity alias一致              +7
thread id / trigger一致       +6
claim subject一致             +5
topic一致                     +4
問いとの語句一致             +3
30日以内                      +3
90日以内                      +2
active / strengthened         +2
weakened                      +1
一次成果物へのprovenanceあり  +2
反対材料を含む                +1
invalidatedを現在前提に使用   除外
出典なし                      除外
```

同じepisodeから似た記憶を大量に返さず、多様性制約をかける。

- 最大5 thread
- 最大10 claim
- 最大3 episode
- 最大3 production lesson
- 合計文字数上限を設定

### 8.4 retrieval report

何を選び、何を落としたかをJSONで残す。

```json
{
  "selected": [],
  "rejected": [],
  "token_budget": 0,
  "warnings": []
}
```

狐が過去を参照した箇所は、episode idかclaim idを内部記録する。

## 9. 狐の記憶表現ガード

### 言える

- 「前回このテーマを扱ったときは、〜が論点でした」
- 「7月10日の回では、まだMediumの仮説として残していました」
- 「その後の材料で、前回の見方は弱くなっています」

### 言えない

- 「僕はずっと分かっていました」
- 「前にこの株で失敗しました」
- 「市場は前回から完全に変わりました」

### 必須条件

過去参照文ごとに次が必要。

- `memory_reference_type`: episode / claim / thread
- `memory_reference_id`
- 当時の確信度
- 現在の再検証結果

記憶を現在の事実として使う前に、当日の一次情報で再検証する。

## 10. 蒸留と忘却

### 毎日

- raw episodeを保存
- thread / claimを更新
- active context候補を作る

### 毎週

- dailyをweeklyへ圧縮
- 重複claimを統合
- 30日以上更新のないactive contextを見直す
- invalidated / resolved claimを通常検索から外す

### 毎月

- threadの「現在の見方」を再生成
- 古い詳細をepisodeへ戻し、thread本文を短くする
- production lessonの重複を統合
- memory precision監査を行う

raw episodeは削除しない。忘却とは検索対象から外すことであり、履歴破壊ではない。

## 11. memory poisoning対策

外部記事、メール、Web本文、daily source内の命令文は、記憶更新命令として扱わない。

記憶へ書ける経路は次の一つだけ。

```text
approved publication record
→ schema validator
→ promotion plan
→ deterministic writer
```

追加ルール：

- source textをそのままprocedural memoryへ書かない
- 「今後必ず〜しろ」のような外部命令を除去する
- 01〜04を変更する記憶は禁止
- provenance不明の記憶は禁止
- 人間承認前の自動promotionは禁止
- promotion差分を監査可能にする

## 12. 実装段階

### PR1：記憶契約の完成

- `memory_policy.md`
- immutable episode schema
- temporal claim schema v2
- entity alias schema
- retrieval report schema
- promotion plan schema

### PR2：書き込みの安全化

- publication recordをepisode archiveへ保存
- SHA-256 provenance
- revision方式
- conflict detector
- promotion dry-run

### PR3：検索品質

- query plan生成
- entity alias対応
- 複合採点
- diversity制約
- retrieval report

### PR4：狐の台本への接続

- episode packageへmemory reference欄を追加
- 過去参照文validator
- 現在証拠による再検証欄
- 「前回との違い」Visual Beat対応

### PR5：蒸留

- weekly compaction
- thread current-view更新
- stale memory audit
- invalidated claim filtering

### PR6：評価fixture

- 正しい過去回を思い出す
- 無関係な回を出さない
- 古い仮説を現在事実にしない
- 否定済みclaimを正しく説明する
- provenanceなしの記憶を拒否する
- 架空の狐の経験を作らない

## 13. Graphiti / vector DB導入条件

v1はGit管理されたMarkdown / JSONと決定的検索で運用する。

次のいずれかを満たした場合だけGraphitiまたはembedding indexを検討する。

- episodeが100本を超える
- threadが50本を超える
- alias表だけでは企業・製品関係の検索漏れが増える
- 2段以上の関係検索が頻繁に必要になる
- lexical retrieval評価が基準未達になる

導入してもGit上のraw episodeとclaim ledgerを正本とし、DBは再構築可能な検索indexとして扱う。

## 14. 完成状態

完成後、狐は次の流れで話せる。

```text
今日のニュースを確認
↓
関連する過去回を選択
↓
当時の仮説と反対材料を取得
↓
現在の一次情報で再検証
↓
何が継続し、何が変わったかを判断
↓
根拠がある場合だけ「前回は〜」と語る
↓
承認後、その回を次の記憶へ昇格
```

狐の記憶は演出ではなく、番組の編集履歴と証拠に接続された監査可能な記憶とする。
