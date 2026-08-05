---
name: nasdaq-cafe-editorial-memory
description: Build and update selective long-term editorial memory for 朝のNASDAQカフェ. Use before causal research to retrieve relevant past episodes, threads, hypotheses, and production lessons; use after final approval to promote durable memory from the final episode only.
---

# 朝のNASDAQカフェ｜編集記憶スキル

## 目的

狐に過去回の市場論点を引き継がせる。ただし、全会話履歴を毎回投入したり、過去の仮説を現在の事実より優先したりしない。

この記憶は人格の創作ではなく、番組が実際に確認・説明・保留した内容の編集記録である。

## 実行タイミング

### 調査前：retrieve

`daily_source_package`から主役候補、企業、政策、技術、指標を抽出した後、因果調査を始める前に実行する。

読む順番：

1. `editorial-memory/active_context.md`
2. 対象日の前日の日次記録
3. 対象日が属するISO週の週次記録
4. `threads/index.json`で一致したtopic thread
5. 一致した`claim_ledger.json`項目
6. 当日の説明・画面設計に関係する`production-lessons.md`

出力：

```text
working/memory_context_YYYY-MM-DD.md
```

### 最終確定後：promote

04審問、画像採用、episode packageとrender specの整合、正式validatorを通過した後だけ実行する。

入力は最終成果物から作った`publication_record_YYYY-MM-DD.json`とする。ドラフトを直接記憶へ入れない。

更新対象：

- `daily/YYYY-MM-DD.md`
- 関係する`threads/<thread_id>.md`
- `threads/index.json`
- `claim_ledger.json`
- 必要な場合だけ`active_context.md`
- 複数回で再利用可能と確認した場合だけ`production-lessons.md`

## Retrievalルール

- 全履歴を読まない。
- 文字列が偶然一致しただけのthreadを採用しない。企業・技術・政策・因果経路の少なくとも一つが今日の主役候補と一致すること。
- 最大thread数は原則5。
- 直近の記録を優先するが、古い記録でも現在のclaimの起点なら残す。
- 現在の一次情報と衝突する記憶は、現在の証拠を優先し、衝突自体を調査質問にする。

## Claimの状態

- `active`：まだ検証中
- `strengthened`：新しい証拠で強まった
- `weakened`：反対材料で弱まった
- `resolved`：確認された範囲で問いが解決した
- `invalidated`：過去の仮説が否定された
- `unknown`：証拠不足のまま

状態変更には必ず日付、根拠参照、変更理由を付ける。

## 狐の語りへの利用

記憶がある場合でも、毎回「前回は」と言う必要はない。現在の説明が分かりやすくなる場合だけ使用する。

使用可能：

> 前回このテーマを見たときは、投資額より回収速度が論点でした。今回は、その回収側に新しい数字が出ています。

使用禁止：

> 僕は前から絶対にこうなると思っていました。

> 僕はこの銘柄で以前失敗しました。

記録のない確信、取引、損益、個人的経験を作らない。

## 因果調査との接続

`memory_context`は証拠そのものではない。過去回の参照先と追加調査候補を示す入力である。

過去回の主張を当日台本で再利用する場合、現在も有効かを一次情報・市場データで再確認し、`causal_research_dossier`へ新しいevidenceとして登録する。

## 完了条件

- 今日に関係する過去だけが選択されている
- 過去の仮説と確認済み事実が区別されている
- claimの状態変化が追跡できる
- 狐が記憶を語る場合の出典となる過去回が存在する
- ドラフトや非採用案が恒久記憶へ混入していない
- 記憶が現在の01〜04、一次情報、市場データを上書きしていない
