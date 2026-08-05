# PR6｜Editorial Memory Revalidation Bridge

## 目的

監査可能な編集記憶検索を、当日の因果調査へ安全に接続する。
過去の仮説を現在の事実へ直接変換せず、次の経路を強制する。

```text
過去記憶
→ 調査質問
→ 現在証拠
→ 再検証結果
→ 因果調査
→ 02による編集判断
```

このPRは主役、市場因果、Expected / Actual / Gapを決定しない。

## 正式フロー

```text
daily_source_package
→ memory query plan
→ deterministic memory retrieval
→ lineage-verified research input manifest
→ causal research dossier with memory revalidation
→ editorial decision under 02
→ fox narration under 01
→ nine-scene episode package under 03
```

## Research Input Manifest

`research/YYYY-MM-DD/research_input_manifest.json`は次を固定する。

- daily source package
- memory query plan
- memory context
- memory retrieval report
- episode date、market date、timezone、information cutoff
- repo相対path
- 各ファイルのSHA-256
- selected memoryの用途別分類

分類は次の4種類。

- `current_revalidation_required`
- `historical_context_only`
- `procedural`
- `not_selected`

`core` memoryはproceduralとして残し、claimレベルの再検証対象にはしない。
selected non-core memoryは全件、dossierで一つだけ再検証結果を持つ。

## Retrieval Lineage

同じ日付であるだけでは入力を結合しない。
Manifest builderはretrieverを同じQuery Planで再実行し、次を検査する。

1. Reportの`query_plan_path`が渡されたQuery Planと一致する
2. 再実行したContextと渡されたContextがバイト単位で一致する
3. 再実行したReportと渡されたReportがバイト単位で一致する
4. Query Plan、Context、Report、Daily packageがrepo/workspace内に存在する
5. path traversal、絶対path、symlinkによるrepo外参照を拒否する
6. Manifestにはrepo相対pathだけを保存する
7. Validator schema自体もrepo/workspace外から差し替えられない

Dossier validatorも同じretrieval replayを再実行する。Manifestの`validation=pass`だけを信用しない。

## Memory Revalidation

必須フィールド:

```text
memory_reference_type
memory_reference_id
historical_confidence
retrieval_use_mode
revalidation_status
current_evidence_ids
difference_from_previous
editorial_use
notes
```

`revalidation_status`:

- `not_used`
- `supported`
- `partially_supported`
- `weakened`
- `invalidated`
- `unresolved`
- `historical_context_only`

## 証拠ルール

結論を持つ次の4状態は、現在のtier 1 / tier 2の`fact`または`reported_interpretation`を必要とする。

- `supported`
- `partially_supported`
- `weakened`
- `invalidated`

次は禁止する。

- discovery-only、unavailable、tier 3、unknown、grounded inferenceだけで再検証結論を作る
- 空のsource referenceを現在証拠として扱う
- `editorial-memory/`配下のpath、memory ID、context、reportを`E-###`へ登録する
- memoryを他の現在証拠へ混ぜてExpected、Actual、causal edgeへ残す
- Actualのstatementだけを置き、現在Evidence IDを空にする
- invalidated / resolved memoryを現在の因果前提に使う
- historical contextを現在のcausal edge根拠に使う
- `not_used`へcurrent evidenceを残す

`not_used`と`unresolved`は正しい結論として許可する。

## ManifestとReportの完全照合

ValidatorはID集合だけでなく、selected memoryごとに次を完全照合する。

- 正確に一つのbucketだけに存在すること
- bucketと`use_mode`の一致
- `requires_current_revalidation`
- `retrieval_status`
- memory path
- provenance paths
- historical confidence

重複bucket、改変metadata、Reportにないmemory、Manifestから消えたmemoryを拒否する。

## Evidence Reference Integrity

存在確認の対象:

- Expected / Actual
- research questions
- timeline
- causal edges
- contrary evidence
- alternative hypothesesのsupporting / weakening evidence
- memory revalidation current evidence

どの場所でもdossier内に存在しない`E-###`を参照できない。
また、editorial memory由来のsource referenceは、他の現在証拠と混在していてもEvidence登録自体を拒否する。

## Validator ERROR条件

1. dossier / manifest / reportの日付不一致
2. Manifestまたは入力ファイルのSHA不一致
3. Query Plan・Context・Reportのretrieval replay不一致
4. repo外path、絶対path、path traversal
5. repo外schema directory
6. selected memoryの重複bucketまたはmetadata改変
7. selected non-core memoryの再検証漏れ
8. duplicate revalidation
9. retrieval use modeまたはhistorical confidenceの不一致
10. 結論状態に現在の高品質証拠がない
11. invalidated / resolved memoryの現在利用
12. historical contextの現在因果利用
13. ExpectedまたはActualをmemoryだけで作成
14. Actual statementに現在証拠がない
15. NASDAQ-wide edgeに現在のtier 1 / tier 2証拠がない
16. causal edgeへmemory由来Evidenceを混在させる
17. dossier内に存在しないevidence ID参照
18. daily input provenanceがManifestのpath/SHAと一致しない

## テスト

25件の決定的unit testを実行する。

主な正常系:

- Manifest生成の決定性
- current revalidation required / procedural分類
- supported
- weakened
- 実retrieverによるend-to-end lineage replay

主な拒否系:

- 同日だが別Query PlanのReport
- 別検索・改変Context
- repo外path、絶対path、外部schema directory
- 同じmemoryの複数bucket登録
- bucketとuse modeの矛盾
- Manifest selected metadata改変
- partially supported + discovery-only
- weakened + unavailable
- invalidated + tier 3
- research question内の未知Evidence ID
- alternative hypothesis内の未知Evidence ID
- Actual statement without Evidence ID
- memory由来Evidenceと現在Evidenceの混在
- memory-only Expected
- quality evidenceのないNASDAQ-wide edge

新workflowはさらに既存retrieval、promotion、memory contractの回帰検査を行う。

## 非対象

- 01〜04正本
- retrieval scoring
- memory promotion
- episode package schema
- render spec
- renderer
- 自動主役選定
- 自動因果確定
- vector DB / Graph DB

## 次のPR

PR #7で、再検証済みmemoryだけをepisode packageへ接続する。
