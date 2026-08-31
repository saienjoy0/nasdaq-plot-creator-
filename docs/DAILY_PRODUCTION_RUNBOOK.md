# 朝のNASDAQカフェ｜日次制作Runbook

## 1. 通常の依頼

ユーザーは当日の資料をChatGPTへ渡します。

```text
daily_source_package_YYYY-MM-DD.md
```

通常の指示例:

```text
この資料で今日のNASDAQカフェを作って、previewまで。
```

ChatGPTが行うこと:

1. 現在証拠の追加確認と深掘り
2. 関連記憶の選択と再検証
3. Expected / Actual / Gap、時系列、代替仮説、反対材料の確定
4. 02による主役・因果判断
5. 01による狐一人の語り
6. 03による9シーン制作
7. 04審問と必要修正
8. Primary / Approved Fallbackの確定
9. 最終episode packageの完成

CLIはこの意味を変更せず、以後の機械工程だけを管理します。

## 2. 正式な日次入口

本番運用では`daily-production-requests/*.json`を一件だけ追加し、Current
Production workflowから唯一のfacadeを実行します。

```bash
python scripts/current_production_facade_v12.py \
  --workspace . \
  --renderer-root <pinned-renderer-checkout> \
  closure \
  --episode-date YYYY-MM-DD \
  --phase compile \
  --semantic-freeze semantic-freezes/YYYY-MM-DD.json \
  --build-handoff-on-pass \
  --bundle-root production-bundles \
  --plot-commit <40-hex-plot-commit>
```

次はすべて公開入口ではありません。

```text
scripts/run_daily_production_v12.py（Current内部制御）
scripts/run_semantic_frozen_renderer_closure_v12.py（Current内部wrapper）
scripts/run_daily_renderer_closure_v12.py（Current内部stage）
scripts/run_daily_production.py（Legacy）
scripts/run_daily_production_hardened.py（Legacy/compatibility）
```

生成:

```text
working/YYYY-MM-DD/production_request.json
working/YYYY-MM-DD/production_state.json
```

同一入力での再実行はno-opです。資料やrequestが変わった状態をそのまま再利用しません。

### 2.1 PREVIEW requestのmerge前semantic readiness

Current-v2の正式PREVIEW requestは、Visual Intelligenceのsemantic authoring loopがPASSする前にmainへmergeしてはいけません。PR validationは`current_production_facade_v12.py`だけを公開Current入口として再利用し、handoff/publicationを作らないreadiness確認を行います。

合法な同一PR内の進行は次です。

```text
Visual Requirements semantic
→ PR readiness prepare
→ Candidate Catalog
→ ChatGPT Director semantic
→ PR readiness compile
→ REVIEW_REQUIRED + compiled visual/warnings
→ ChatGPT Critic semantic
→ PR readiness compile PASS
→ merge the same formal PREVIEW request
→ main production compile-only
→ immutable handoff/publication
→ Renderer Preview
```

`PREPARED`と`REVIEW_REQUIRED`はsemantic authoring checkpointであり、production失敗ではありません。このcheckpointに到達しただけで新しいrN+1 production requestを作ってはいけません。同じPRへ要求されたDirector/Critic semantic artifactを追加し、同じformal PREVIEW requestのままreadinessを再実行します。

PR readinessは次をしてはいけません。

```text
Visual Candidateの選択
Director/Critic semanticの作成
下位closure/state machineの直接呼び出し
immutable handoffの作成
publicationの作成
Preview/Final renderの起動
```

readinessの`NOT_READY`はmergeを止め、`requiredAction`をChatGPTへ返す正常なsemantic pauseです。`PASS`した同じrequestだけがformal main productionへ進めます。main側は従来どおり`current_production_facade_v12.py --phase compile`のままfail-closedであり、Director欠落時にcompileをprepareへ自動変換しません。

## 3. 状態確認

```bash
python scripts/run_daily_production_v12.py --workspace . status \
  --episode-date YYYY-MM-DD
```

出力:

- current state
- next state
- requested scope
- SHA・path検査結果

このコマンドはfacade内部の診断用です。本番workflowから直接呼びません。

## 4. ChatGPT成果物の登録

各工程のvalidator結果または正式成果物を証拠として、必ず一段ずつ進めます。

```bash
python scripts/run_daily_production_v12.py --workspace . advance \
  --episode-date YYYY-MM-DD \
  --state research_inputs_bound \
  --evidence working/YYYY-MM-DD/research_input_manifest.json
```

続く状態:

```text
causal_dossier_valid
episode_package_final
memory_usage_valid
assets_resolved
```

状態の飛び越し、後退、証拠なしは拒否されます。

## 5. 最終制作成果物の生成

`assets_resolved`後の生成はfacadeの`closure --phase compile`に集約します。
下位のbuild-productionやhandoff builderを本番入口として直接実行しません。

この工程では次を順に強制します。

```text
PR #8 memory validatorとPR #6 replay
→ Scene 1〜9・04審問結果・Annex順序検査
→ deterministic Final Production生成
→ spoken script / asset manifest / render specのmetadata漏出検査
→ hardened preflight記録
```

生成:

```text
working/YYYY-MM-DD/episode_package_ir.json
episodes/YYYY-MM-DD/spoken_script_YYYY-MM-DD.md
episodes/YYYY-MM-DD/asset_manifest.json
render-specs/YYYY-MM-DD/render_spec.json
verification/YYYY-MM-DD/production_consistency_report.json
verification/YYYY-MM-DD/official_execution_preflight.json
```

`official_execution_preflight.json`には次が保存されます。

```json
{
  "episode_memory_hardening": {
    "pre_build": "pass",
    "public_artifacts": "pass"
  }
}
```

post-build検査に失敗した場合、生成物を削除し、PASS preflightを残しません。

## 6. Renderer handoffと一度だけのRequest公開

PASS closureはimmutable handoff、Current Preview V4 request、publication receiptを
同じPlot runで生成します。

```bash
python scripts/build_current_preview_publication.py \
  --root . \
  --request verification/YYYY-MM-DD/current_preview_request_v4.json \
  --output verification/YYYY-MM-DD/current_preview_publication.json
```

出力された`renderer.targetPath`へ、GitHub接続済みエージェントがrequest-only
PRでexact request bytesを一件だけ追加します。同じepisodeDate、Plot run ID、
request SHAは常に同じtarget pathになり、再試行で別Requestを増やしません。
Rendererのpublication gate PASS後にmergeするとCurrent V4が一度だけ起動します。

handoffはPreview用だけを作り、Finalを自動生成しません。

## 7. Preview結果の記録

Renderer ActionsでPreview MP4、technical report、Current Spine identity、2ブロック
TTS SHAが揃った時だけPreview完成です。Plot側の
`PREVIEW_PUBLICATION_READY`はMP4完成を意味しません。Rendererのstatus receiptと
ArtifactをPlot run IDで照合します。

承認までは`user_review_pending`です。AIによる完成動画の視覚採点へ置き換えません。

## 8. Final要求

previewをユーザーが目視確認し、明示的にfinalを依頼した場合だけ記録します。

`scripts/build_current_final_request_v2.py`は、承認済みPreview identity、
human review、Plot Final authorization、`--explicit-final`がすべて一致する場合だけ
append-only Final requestを生成します。Finalを自動実行しません。

## 9. Publicationとmemory

final完了、公開承認、memory promotionはそれぞれ別状態です。対応する正式記録を`advance`のevidenceとして渡します。

ドラフト、preview未承認、却下された因果、未採用画像、04審問前の台本を恒久記憶へ昇格しません。

## 10. 主な停止コード

```text
E_DATE_MISMATCH
E_STALE_INPUT
E_RESEARCH_INVALID
E_MEMORY_USAGE_INVALID
E_EPISODE_NOT_FINAL
E_INQUISITION_UNRESOLVED
E_ASSET_UNRESOLVED
E_SELECTED_PATH_UNRESOLVED
E_RENDER_SPEC_INVALID
E_PACKAGE_MISMATCH
E_HANDOFF_INVALID
E_RENDERER_CONTRACT_MISMATCH
E_PREVIEW_FAILED
E_FINAL_NOT_AUTHORIZED
E_PUBLICATION_NOT_APPROVED
E_MEMORY_PROMOTION_BLOCKED
```

停止時は原因を修正し、同じ証拠を偽装して通さず、必要な工程へ戻ります。
