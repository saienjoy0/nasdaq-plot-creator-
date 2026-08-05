---
name: nasdaq-cafe-editorial-memory
description: Build and update selective long-term editorial memory for 朝のNASDAQカフェ. Use before causal research to retrieve relevant past episodes, threads, hypotheses, and production lessons; use after final approval to promote durable memory from the final episode only.
---

# 朝のNASDAQカフェ｜編集記憶スキル

## 目的

狐に過去回の市場論点を引き継がせる。ただし、全会話履歴を毎回投入したり、過去の仮説を現在の事実より優先したりしない。

この記憶は人格の創作ではなく、番組が実際に確認・説明・保留した内容の編集記録である。

## 正式な記憶方針

最初に次を読む。

1. `editorial-memory/memory_policy.md`
2. `editorial-memory/core/fox_editorial_state.md`
3. `editorial-memory/active_context.md`

`memory_policy.md`は記憶の読み取り、現在利用、昇格、不変性、訂正、poisoning対策を定義する。記憶の都合で01〜04や現在の証拠を変更してはいけない。

## 実行タイミング

### 調査前：retrieve

`daily_source_package`から主役候補、企業、政策、技術、指標を抽出した後、因果調査を始める前に実行する。

読む順番：

1. `editorial-memory/active_context.md`
2. `editorial-memory/core/fox_editorial_state.md`
3. 対象日の前日の承認済みepisode
4. 対象日が属するISO週の週次記録
5. `threads/index.json`で一致したtopic thread
6. 一致した`claim_ledger.json`項目
7. 当日の説明・画面設計に関係する`production-lessons.md`

先に`memory_query_plan_YYYY-MM-DD.json`を作り、検索後に`memory_retrieval_report_YYYY-MM-DD.json`を残す。

出力：

```text
working/memory_query_plan_YYYY-MM-DD.json
working/memory_context_YYYY-MM-DD.md
working/memory_retrieval_report_YYYY-MM-DD.json
```

### 最終確定後：promote

04審問、画像採用、episode packageとrender specの整合、正式validatorを通過した後だけ実行する。

入力は最終成果物から作った`publication_record_YYYY-MM-DD.json`とする。ドラフトを直接記憶へ入れない。

昇格前に次を作る。

```text
editorial-memory/episodes/YYYY-MM-DD/publication_record.vN.json
editorial-memory/episodes/YYYY-MM-DD/episode_summary.md
editorial-memory/episodes/YYYY-MM-DD/provenance.json
working/memory_promotion_plan_YYYY-MM-DD.json
```

更新対象：

- `daily/YYYY-MM-DD.md`
- 関係する`threads/<thread_id>.md`
- `threads/index.json`
- `claim_ledger.json`
- `entity_aliases.json`
- 必要な場合だけ`active_context.md`
- 複数回で再利用可能と確認した場合だけ`production-lessons.md`

## Retrievalルール

- 全履歴を読まない。
- 文字列が偶然一致しただけのthreadを採用しない。企業・技術・政策・因果経路の少なくとも一つが今日の主役候補と一致すること。
- entity aliasを解決してから採点する。
- 最大thread数は5、claimは10、episodeは3、lessonは3。
- 直近の記録を優先するが、古い記録でも現在のclaimの起点なら残す。
- 同じepisode由来の似た記憶を大量に返さない。
- provenanceのない記憶を現在利用へ採用しない。
- 現在の一次情報と衝突する記憶は、現在の証拠を優先し、衝突自体を調査質問にする。
- 採用・却下理由をretrieval reportへ残す。

## Claimの状態

- `active`：まだ検証中
- `strengthened`：新しい証拠で強まった
- `weakened`：反対材料で弱まった
- `resolved`：確認された範囲で問いが解決した
- `invalidated`：過去の仮説が否定された
- `unknown`：証拠不足のまま

状態変更には必ず日付、元episode、根拠参照、反対材料、変更理由を付ける。

`resolved`と`invalidated`には`valid_to`を設定し、現在の因果前提として利用しない。

## 狐の語りへの利用

記憶がある場合でも、毎回「前回は」と言う必要はない。現在の説明が分かりやすくなる場合だけ使用する。

使用可能：

> 前回このテーマを見たときは、投資額より回収速度が論点でした。今回は、その回収側に新しい数字が出ています。

使用禁止：

> 僕は前から絶対にこうなると思っていました。

> 僕はこの銘柄で以前失敗しました。

記録のない確信、取引、損益、個人的経験を作らない。

過去参照文には内部的に次を持たせる。

- `memory_reference_type`
- `memory_reference_id`
- `historical_confidence`
- `current_revalidation_status`
- `current_evidence_ids`

## 因果調査との接続

`memory_context`は証拠そのものではない。過去回の参照先と追加調査候補を示す入力である。

過去回の主張を当日台本で再利用する場合、現在も有効かを一次情報・市場データで再確認し、`causal_research_dossier`へ新しいevidenceとして登録する。

## 昇格の安全契約

恒久記憶へ書ける経路は次だけである。

```text
approved publication record
→ schema validation
→ immutable episode archive
→ conflict detection
→ memory promotion plan
→ deterministic writer
→ promotion report
```

`memory_promotion_plan`の`mode=apply`は、`safe_to_apply=true`かつconflictが0件の場合だけ許可する。

承認済みepisodeは上書きせず、訂正時はrevisionを追加する。

## 契約とvalidator

契約は`contracts/`に置く。

- immutable episode
- temporal claim v2
- entity aliases
- memory query plan
- memory retrieval report
- memory promotion plan
- publication record compatibility contract

検査：

```bash
python -m pip install jsonschema
python skills/nasdaq-cafe-editorial-memory/validators/validate_memory_contracts.py --require-jsonschema
```

schema PASSは市場因果の正しさを証明しない。構造、不変性、provenance、危険な状態遷移の拒否だけを保証する。

## 完了条件

- 今日に関係する過去だけが選択されている
- 過去の仮説と確認済み事実が区別されている
- claimの有効期間と状態変化が追跡できる
- 狐が記憶を語る場合の出典となる過去回が存在する
- 採用・却下理由がretrieval reportに残る
- promotion前に差分とconflictを検査できる
- ドラフトや非採用案が恒久記憶へ混入していない
- 記憶が現在の01〜04、一次情報、市場データを上書きしていない
