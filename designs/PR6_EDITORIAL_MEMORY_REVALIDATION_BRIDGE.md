# PR6｜Editorial Memory Revalidation Bridge

## 目的

監査可能な編集記憶検索を、当日の因果調査へ安全に接続する。

過去回の仮説をそのまま現在の事実へ変換せず、次の経路を強制する。

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
→ selective editorial-memory retrieval
→ research input manifest
→ causal research dossier with memory revalidation
→ editorial decision under 02
→ fox narration under 01
→ nine-scene episode package under 03
```

## 追加成果物

```text
research/YYYY-MM-DD/research_input_manifest.json
research/causal_research_dossier_YYYY-MM-DD.json  # contract_version 0.2.0
```

## Research Input Manifest

Manifestは次の入力を固定する。

- daily source package
- memory query plan
- memory context
- memory retrieval report
- episode date
- market date
- timezone
- information cutoff
- 各ファイルのSHA-256
- selected memoryの用途別分類

分類:

- `current_revalidation_required`
- `historical_context_only`
- `procedural`
- `not_selected`

`core` memoryはprocedural intakeとして残し、claimレベルの再検証対象にはしない。selected non-core memoryは全件、dossierで一つの再検証結果を持つ。

## Builder

```bash
python scripts/build_research_input_manifest.py \
  --episode-date YYYY-MM-DD \
  --market-date YYYY-MM-DD \
  --timezone Asia/Tokyo \
  --information-cutoff ISO-8601 \
  --daily-source-package PATH \
  --memory-query-plan PATH \
  --memory-context PATH \
  --memory-retrieval-report PATH \
  --output research/YYYY-MM-DD/research_input_manifest.json
```

BuilderはLLMを使わない。schema、日付、存在、SHA、use modeだけを決定的に処理する。

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

`editorial_use`:

- `not_used`
- `research_lead`
- `comparison`
- `counterevidence`
- `explanation_context`
- `monitoring_point`
- `procedural_only`

## 証拠ルール

- `supported`には現在のtier 1 / tier 2のfactまたはreported interpretationが必要。
- `weakened`と`invalidated`には現在の反対証拠が必要。
- `historical_context_only`は比較または説明背景に限る。
- `not_used`と`unresolved`は正しい結論として許可する。
- `editorial-memory/`配下のpath、memory ID、memory context、retrieval reportは現在証拠ではない。
- memoryを`E-###`へ置き換えて契約を満たしてはいけない。
- memoryはExpected、Actual、causal edge、NASDAQ-wide causeの唯一の根拠になれない。

## Dossier v0.2

現行v0.1を上書きせず、次を追加したv0.2 schemaを新設する。

- `research_input_manifest`
- `memory_revalidation`
- causal edge `scope`
- editorial handoff `memory_differences`

既存v0.1は互換性のため残す。

## Validator

```bash
python skills/nasdaq-cafe-causal-research/validators/validate_causal_research_dossier.py \
  research/YYYY-MM-DD/causal_research_dossier_YYYY-MM-DD.json \
  --research-input-manifest research/YYYY-MM-DD/research_input_manifest.json \
  --memory-retrieval-report working/memory_retrieval_report_YYYY-MM-DD.json
```

ERROR条件:

1. dossier / manifest / reportの日付不一致
2. Manifestまたは入力ファイルのSHA不一致
3. reportにないmemory IDの参照
4. selected non-core memoryの再検証漏れ
5. duplicate revalidation
6. retrieval use modeまたはhistorical confidenceの不一致
7. supportedなのに現在証拠がない
8. supportedにdiscovery-only / unavailable / memory pathを使用
9. weakened / invalidatedなのに反対証拠がない
10. invalidated / resolved memoryを現在の前提に利用
11. historical contextを現在の因果前提に利用
12. Expectedをmemoryだけで作成
13. NASDAQ-wide edgeに現在のtier 1 / tier 2証拠がない
14. causal edgeをmemoryだけで支持
15. dossier内に存在しないevidence IDを参照

WARNING条件:

- historical confidenceがlow
- current evidenceがtier 2のみ
- difference_from_previousが空
- supportedにcontext-only evidenceが含まれる

Validator PASSは構造とprovenanceが揃ったことを示す。市場解釈の正しさを証明しない。

## テスト

13件の決定的unit testを追加する。

正常系:

- manifest生成が決定的
- current revalidation required / procedural分類
- supported
- weakened
- historical context only

拒否系:

- 日付不一致
- supported without evidence
- memory path as current evidence
- invalidated current premise
- selected memory未分類
- SHA mismatch
- memory-only Expected
- quality evidenceのないNASDAQ-wide edge
- unknown evidence ID

新workflowは次を実行する。

- schema syntax
- new 13 tests
- existing retrieval tests
- existing promotion tests
- existing memory contract validator

## 変更対象

- `AGENTS.md`
- `scripts/build_research_input_manifest.py`
- `skills/nasdaq-cafe-causal-research/SKILL.md`
- `skills/nasdaq-cafe-causal-research/contracts/research_input_manifest.schema.json`
- `skills/nasdaq-cafe-causal-research/contracts/memory_revalidation.schema.json`
- `skills/nasdaq-cafe-causal-research/contracts/causal_research_dossier_v0.2.schema.json`
- `skills/nasdaq-cafe-causal-research/validators/validate_causal_research_dossier.py`
- `tests/memory-revalidation/**`
- `.github/workflows/memory-revalidation-bridge.yml`

## 非対象

- 01〜04正本
- memory retrieval scoring
- promotion
- episode package schema
- render spec
- renderer
- 自動主役選定
- 自動因果確定
- vector DB / Graph DB

## 完了条件

- Manifestがschema-validかつdeterministic
- 同一episode dateとSHAが固定される
- selected non-core memoryが全件分類される
- current evidenceなしのsupportedを拒否
- memory-only Expected / causal edge / NASDAQ-wide causeを拒否
- invalidated / resolvedの現在利用を拒否
- 正常fixtureがPASS
- 危険fixtureがFAIL
- 既存retrieval / promotion / contractsが回帰しない
- GitHub Actionsが編集判断を行わない

## 次のPR

PR #7で、再検証済みmemoryだけをepisode packageへ接続する。

予定フィールド:

```text
memory_reference_type
memory_reference_id
historical_confidence
current_revalidation_status
current_evidence_ids
difference_from_previous
editorial_use
```
