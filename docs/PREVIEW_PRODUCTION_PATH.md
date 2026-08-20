# 朝のNASDAQカフェ｜Canonical Preview Production Path

## 目的

本番Previewの入口を一つに固定し、GitHub Actionsの緑色の成功表示だけでは区別できなかった「Preview handoff完成」と「正常なsemantic safe-pause」を機械的に区別する。

## 唯一の本番Preview経路

```text
daily-production-requests/*.json
  ↓
.github/workflows/chatgpt-daily-preview-production.yml
  ↓
Visual Intelligence / semantic closure
  ↓ PASS only
Renderer Current Preview request V4 build / validate
  ↓
immutable Plot handoff artifact
  ↓
Renderer: .github/workflows/nasdaq-cafe-handoff-preview-request-v4.yml
  ↓
Renderer: .github/workflows/nasdaq-cafe-preview-handoff-v2.yml
  ↓
Preview MP4 + technical report
```

機械正本は `contracts/preview_production_path.json` とする。

Plot内の他のworkflowはCI、contract test、canary、technical preview、legacy compatibility用であり、`daily-production-requests/*.json` を本番入力として受け取ってはいけない。

Renderer側のMotion Preview、scheduled preview、visual grammar previewなどは本番handoff Previewの代替入口として扱わない。本番のPlot handoffをRendererへ渡す正規request workflowは `nasdaq-cafe-handoff-preview-request-v4.yml`、実レンダーworkerは `nasdaq-cafe-preview-handoff-v2.yml` とする。

## safe-pauseは失敗ではない

Visual Intelligenceが次のChatGPT / AI-B成果物を必要とする場合、production workflowは安全に停止してよい。ただし単なるActions `success` だけで終了状態を表現しない。

必ず次を生成する。

```text
verification/YYYY-MM-DD/preview_production_outcome.json
```

正規状態は次のいずれか。

```text
PREVIEW_HANDOFF_READY
WAITING_FOR_VISUAL_REQUIREMENTS
WAITING_FOR_VISUAL_SOURCE_SELECTION
WAITING_FOR_VISUAL_INTELLIGENCE_DECISION
WAITING_FOR_VISUAL_RESELECTION
WAITING_FOR_VISUAL_REVIEW
SAFE_PAUSED
FAILED
```

`PREVIEW_HANDOFF_READY` はsemantic closureがPASSし、Renderer Current Preview request V4のbuild/validateを通過し、immutable Preview handoff Artifactのuploadまで成功した場合だけ許可する。

`WAITING_FOR_*` と `SAFE_PAUSED` は正常停止であり、Previewが完成したことを意味しない。

`FAILED` は契約違反、予期しないclosure状態、またはPASS後にCurrent Preview request V4のbuild/validateもしくはimmutable handoff uploadを完了できなかった場合に使う。

Finalはこの契約の対象外であり、このPreview production pathから自動実行してはいけない。

## 機械契約

- 経路: `contracts/preview_production_path.json`
- 終了状態schema: `contracts/preview_production_outcome.schema.json`
- outcome生成: `scripts/write_preview_production_outcome.py`
- invariant test: `tests/preview-production-path/test_preview_production_outcome.py`

CIはPlot内で `daily-production-requests/*.json` を参照するworkflowがcanonical entry workflow一つだけであることを検査する。
