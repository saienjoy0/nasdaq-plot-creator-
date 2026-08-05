# PR5｜監査可能な編集記憶検索エンジン

## 目的

承認済みの編集記憶から、当日の調査に関係する項目だけを決定的に選び、選択理由・除外理由・provenance・現在再検証の要否を残す。

この検索は主役ニュース、市場因果、Expected / Actual / Gapを決定しない。過去回の参照先と追加調査候補を返すだけであり、現在の一次情報と01〜04を上書きしない。

## 入出力

入力：

```text
working/memory_query_plan_YYYY-MM-DD.json
```

出力：

```text
working/memory_context_YYYY-MM-DD.md
working/memory_retrieval_report_YYYY-MM-DD.json
```

既存の`memory_query_plan.schema.json`と`memory_retrieval_report.schema.json`を正本として使う。

## 検索順

1. Query Planをschema検証
2. `entity_aliases.json`でexact / alias / unresolvedを決定
3. thread候補を採点
4. claim候補を採点
5. immutable episode候補を採点
6. production lesson候補を採点
7. provenanceと有効状態を検査
8. 重複・同一episode偏重を除去
9. 種別件数上限と文字数上限を適用
10. ContextとReportを出力

## 採点

- exact entity一致：+8
- alias一致：+7
- thread trigger一致：+6
- claim subject / linked thread一致：+5〜6
- topic一致：+4
- 内容語句一致：+3〜5
- 30日以内：+3
- 90日以内：+2
- active / strengthened：+2
- weakened：+1
- provenance確認済み：+2
- 反対材料を保持：+1

recency、status、provenanceだけでは関連候補にしない。entity、topic、trigger、問い、内容のいずれかが一致した場合だけ採用候補にする。

## 状態制御

- `active` / `strengthened` / `weakened` / `unknown`：現在利用には一次情報で再検証が必要
- `resolved` / `invalidated`：比較質問がある場合だけhistorical contextとして返す
- `invalidated`を現在の因果前提として返さない
- provenanceが存在しない記憶は除外する

## 多様性と上限

- thread最大5
- claim最大10
- episode最大3
- lesson最大3
- 同一内容の重複を除去
- 同一episode由来は最大3項目
- Context全体をQuery Planの文字数上限内に収める

## 監査性

Reportには次を残す。

- 選択したmemory ID、path、score、理由
- provenance path
- status、historical confidence
- current revalidationの要否
- 除外したmemory IDと理由
- distinct episode / thread
- 重複除去数
- unresolved aliasと0件結果のwarning

## 互換性

旧`build_memory_context.py`は互換wrapperとして残す。旧CLIからschema準拠Query Planを生成し、新retrieverを呼び出す。

## 完了条件

- AWS / AI設備投資のQuery Planで2026-07-31のthread、claim、episodeを取得する
- Tesla / 自動運転のQuery Planで無関係なAmazon記憶を取得しない
- invalidated claimを通常検索で除外する
- 比較質問がある場合だけinvalidated claimをhistorical contextで返す
- provenance欠落を除外する
- 文字数上限を超えない
- 同一入力から同一ContextとReportが生成される
- schema検証とCIがPASSする
