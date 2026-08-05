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

本番運用では必ずhardening wrapperを使います。

```bash
python scripts/run_daily_production_hardened.py --workspace . init \
  --episode-date YYYY-MM-DD \
  --daily-source-package daily_source_package_YYYY-MM-DD.md \
  --requested-scope preview \
  --renderer-commit <40-hex-renderer-commit> \
  --renderer-contract-version 2.2.0
```

`run_daily_production.py`はstate machine本体と単体テスト用です。本番入口として直接使用しません。

hardening wrapperは既存の前進専用state machineを保持したまま、次の工程だけを安全版へ差し替えます。

```text
build-production
→ build_final_production_package_hardened.py

build-handoff
→ build_renderer_handoff_hardened.py

record-preview
→ run_real_day_acceptance_hardened.py
```

生成:

```text
working/YYYY-MM-DD/production_request.json
working/YYYY-MM-DD/production_state.json
```

同一入力での再実行はno-opです。資料やrequestが変わった状態をそのまま再利用しません。

## 3. 状態確認

```bash
python scripts/run_daily_production_hardened.py --workspace . status \
  --episode-date YYYY-MM-DD
```

出力:

- current state
- next state
- requested scope
- SHA・path検査結果

## 4. ChatGPT成果物の登録

各工程のvalidator結果または正式成果物を証拠として、必ず一段ずつ進めます。

```bash
python scripts/run_daily_production_hardened.py --workspace . advance \
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

`assets_resolved`後に実行します。

```bash
python scripts/run_daily_production_hardened.py --workspace . build-production \
  --episode-date YYYY-MM-DD \
  --episode-package episodes/YYYY-MM-DD/episode_package_YYYY-MM-DD.md
```

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

## 6. Renderer handoff

`production_package_valid`後に実行します。

```bash
python scripts/run_daily_production_hardened.py --workspace . build-handoff \
  --episode-date YYYY-MM-DD \
  --bundle-root production-bundles \
  --plot-commit <40-hex-plot-creator-commit>
```

これはpreview bundleだけを作ります。final bundleは作りません。

handoffはhardened preflightの存在を必須とし、bundleへコピーされたpreflightにも同じ証跡が残っていることを再確認します。新規bundleで検証に失敗した場合、そのbundleを削除します。

## 7. Preview結果の記録

Renderer Actionsでpreviewとtechnical reportが得られた後に実行します。

```bash
python scripts/run_daily_production_hardened.py --workspace . record-preview \
  --episode-date YYYY-MM-DD \
  --daily-source-root . \
  --bundle-root production-bundles/YYYY-MM-DD/<bundle-id> \
  --handoff-manifest handoff_manifest.json \
  --renderer-artifact-root <downloaded-artifact-directory> \
  --technical-report renderer_technical_report.json
```

Real-Day Acceptanceは、handoff manifest内のpreflight roleが一件だけで、bundled preflightに完全なhardening証跡がある場合だけMVP判定へ進みます。

ユーザー確認後は、review recordも渡します。

```bash
... record-preview ... --user-review user_review.json
```

承認までは`user_review_pending`です。AIによる完成動画の視覚採点へ置き換えません。

## 8. Final要求

previewをユーザーが目視確認し、明示的にfinalを依頼した場合だけ記録します。

```bash
python scripts/run_daily_production_hardened.py --workspace . request-final \
  --episode-date YYYY-MM-DD \
  --approval-record final_approval.json \
  --explicit-final
```

このコマンドは`final_requested`を記録するだけです。finalレンダーを自動実行しません。

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
