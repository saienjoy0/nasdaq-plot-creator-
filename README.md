# 朝のNASDAQカフェ｜調査・記憶・台本・日次制作制御

このリポジトリは、朝のNASDAQカフェの01〜04正本、因果深掘りスキル、OpenClaw型の選択的長期記憶、最終台本契約、renderer配送契約、日次制作状態を管理する編集制御面です。

## 目的

毎日の`daily_source_package_YYYY-MM-DD.md`をそのまま要約するのではなく、関連背景、過去経緯、企業関係、供給網、マクロ要因、代替仮説を追加調査し、NASDAQへ届いた因果だけを狐一人の9シーン台本へ変換します。

最終承認された過去回だけを恒久記憶へ昇格し、今日の話題に関係する記憶だけを取得して現在証拠で再検証します。

## 現在地

Current Spineでは、Plotの公開入口は
`scripts/current_production_facade_v12.py`、RendererのPreview入口はCurrent
Preview Request V4だけです。旧Daily Production/hardening入口は履歴・互換用であり、
新しい本番日次制作には使用しません。

```text
ユーザーがdaily_source_packageを渡す
→ 関連記憶検索・replay・SHA固定
→ 現在証拠によるmemory revalidation
→ causal research dossier
→ ChatGPTが02で編集判断
→ ChatGPTが01・03で狐の9シーンを完成
→ ChatGPTが04審問と修正
→ Primary / Approved Fallback確定
→ episode package memory usage検証
→ final production package生成・整合検査
→ immutable renderer handoff bundle
→ SHA固定されたRenderer publication receipt
→ Rendererのrequest-only PR
→ renderer preview
→ real-day acceptance
→ ユーザー目視確認
→ 明示依頼がある場合だけfinal
→ publication approval
→ memory promotion
```

完成済みの制御契約:

- 監査可能な記憶検索・安全な昇格
- PR #6型の現在証拠による記憶再検証
- episode package内のScene・surface・Evidence単位memory usage
- 04審問後episode packageからの決定的なIR・spoken script・asset manifest・render spec生成
- SHA-bound renderer handoff bundle
- 新しい実日previewのacceptance gate
- 前進専用・証拠SHA付き日次state machine CLI

まだ実績として必要なこと:

- 次にユーザーから渡される新しい実日のdaily source packageで全工程を実行する
- preview MP4をユーザーが目視確認する

2026-07-31 seedは新しい実日のMVP証明には使用しません。preview確認前にfinalへ進みません。

## 日次入口

運用手順は次を正本とします。

- [`docs/DAILY_PRODUCTION_RUNBOOK.md`](docs/DAILY_PRODUCTION_RUNBOOK.md)

本番開始は`daily-production-requests/*.json`を一件だけ追加し、
`.github/workflows/chatgpt-daily-preview-production.yml`から行います。Workflowは
必ず次のCurrent facadeを呼びます。

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

このfacadeも主役、市場因果、狐の文章、04審問、画像生成、Primary/Fallbackを
決めません。Currentの詳細な入口分類は
[`docs/current-spine/CURRENT_ENTRYPOINTS.md`](docs/current-spine/CURRENT_ENTRYPOINTS.md)を正本とします。

## 基本フロー

```text
daily_source_package
→ memory query plan
→ selective editorial-memory retrieval
→ deterministic retrieval replay
→ research input manifest
→ causal research dossier with memory revalidation
→ 02_editorial_bible による編集判断
→ 01_fox_character_bible による狐の語り
→ 03_episode_production_spec による9シーン制作
→ 04_entertainment_inquisitor による審問・手直し
→ Primary / Approved Fallbackの最終採用
→ episode memory annex / final production source
→ spoken script / asset manifest / render spec
→ production consistency validator
→ immutable renderer handoff
→ previewとユーザー確認
→ 明示依頼がある場合だけfinal
→ approved publication record
→ daily / weekly / thread / claim memoryへの昇格
```

## 主なディレクトリ

- `source-of-truth/`：番組の01〜04正本
- `editorial-memory/`：日次・週次・継続テーマ・仮説・制作知識の記憶
- `skills/nasdaq-cafe-causal-research/`：台本前段の因果深掘り
- `skills/nasdaq-cafe-editorial-memory/`：関連記憶の取得と承認後昇格
- `skills/nasdaq-cafe-episode-package-memory/`：最終台本内memory usage検査
- `skills/nasdaq-cafe-final-production/`：episode packageから制作成果物を決定的生成
- `skills/nasdaq-cafe-renderer-handoff/`：renderer配送bundle
- `skills/nasdaq-cafe-real-day-acceptance/`：新しい実日preview受入
- `skills/nasdaq-cafe-daily-production/`：日次state machine
- `designs/`：実装設計、現在地、ロードマップ
- `verification/`：検査・acceptance記録

## 記憶の使い方

調査前の取得:

```bash
python scripts/editorial_memory_retrieval.py \
  --query-plan working/memory_query_plan_YYYY-MM-DD.json \
  --context-output working/memory_context_YYYY-MM-DD.md \
  --report-output working/memory_retrieval_report_YYYY-MM-DD.json
```

その後、同一検索結果のreplay確認とSHA固定を行います。記憶は現在の証拠ではありません。過去仮説を当日台本へ使う場合は、現在のtier 1 / tier 2証拠で再検証します。

最終承認後だけ昇格します。

```bash
python scripts/promote_episode_memory.py publication_record_YYYY-MM-DD.json
```

## 絶対ルール

- GitHub Actions、Codex、Remotion、外部研究フレームワーク、記憶層へ市場因果や台本の意味を判断させない
- `daily_source_package`だけを言い換えて台本にしない
- 事実、共有解釈、推論、不明を分ける
- 一社の材料をNASDAQ全体の原因へ自動昇格させない
- 売買助言、目標株価、確定的な将来予測を出さない
- ドラフト、却下された因果、未採用画像経路を恒久記憶へ入れない
- 記録のない狐の保有、損益、取引、大学生活上の出来事を創作しない
- preview確認前にfinalへ進まない
- validator FAIL、未解決画像経路、対象日不一致、古いrender specをrendererへ渡さない
