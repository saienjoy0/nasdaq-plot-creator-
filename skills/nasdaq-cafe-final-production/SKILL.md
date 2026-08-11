---
name: nasdaq-cafe-final-production
version: 1.2.0
description: Deterministically derive all production artifacts from the final post-inquisition episode package.
---

# Final Production Package

## Source of truth

`episode_package_YYYY-MM-DD.md` remains the human editorial source of truth. Its canonical ending is:

```text
04 inquisition result
→ Editorial Memory Usage Annex
→ Final Production Source Annex
→ EOF
```

The Final Production Source annex is authored only after 04 changes are applied, PR #8 memory usage is valid, image resolution is final, and all Scene 1–9 production content is complete.

## Mandatory guarded entrypoint

Use:

```bash
python scripts/build_final_production_package_hardened.py \
  --episode-package episode_package_YYYY-MM-DD.md \
  --output-root .
```

Do not use the base builder as the production entrypoint.

The guarded builder:

1. re-runs the base PR #8 validator and PR #6 lineage through the episode-memory hardening gate;
2. requires nine ordered Scenes and one integrated 04 result;
3. invokes the deterministic base Final Production builder;
4. after Renderer 2.4 canonical projection, attaches any explicitly bound verified one-minute Collector series before the pinned Renderer validator runs;
5. scans spoken script, asset manifest, and render spec for memory metadata leakage;
6. removes generated artifacts on post-build failure;
7. atomically persists `episode_memory_hardening={pre_build: pass, public_artifacts: pass}` into `official_execution_preflight.json`.

## Verified intraday rendering

When a Visual Beat is explicitly authored as `event-reaction-timeline / verified-series / verified-intraday-series` and a normalized Collector one-minute file exists, do not reduce that file to a handful of display numbers for the chart itself.

Keep the legacy `seriesObjectIds` only as optional summary objects for backward compatibility. Add these explicit fields to that Beat's `reactionTimelineBinding`:

```json
{
  "intradaySeriesPath": "research/YYYY-MM-DD/evidence/RA-..._intraday_series.json",
  "eventMarker": {
    "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
    "label": "公式発表名",
    "sourceLabel": "公式ソース"
  },
  "displayTimezone": "America/New_York"
}
```

`intradaySeriesPath` must point inside the production workspace to the normalized Collector output whose `kind` is `intraday`, `resolution` is `1m`, and `precision` is `verified-intraday-series`. The guarded production entrypoint copies that complete normalized series into `render_spec.json` only after canonical projection and before referential checks, pinned Renderer validation, and persisted preflight hashes.

This attachment step is mechanical. It may not choose the symbol, event time, display window, causal interpretation, or whether timing evidence is editorially relevant. Those decisions remain ChatGPT-authored under 01–04. Intraday timing alignment remains timing evidence and never becomes causal proof by itself.

Historical render specs and Beats without `intradaySeriesPath` keep the existing legacy summary path unchanged.

## Deterministic flow

```text
final episode package
→ episode-memory pre-build gate
→ episode_package_ir.json
→ spoken_script_YYYY-MM-DD.md
→ asset_manifest.json
→ render_spec.json
→ Renderer 2.4 canonical projection
→ explicit verified intraday-series attachment when bound
→ pinned Renderer validator
→ production_consistency_report.json
→ public-artifact metadata-leak gate
→ hardened official_execution_preflight.json
```

No downstream artifact may add, paraphrase, reorder, infer, or repair editorial content. Missing or unresolved information stops the build.

## Required invariants

- exactly nine ordered Scenes in the human package and render spec;
- exactly one integrated 04 inquisition result;
- exact speech, captions, expressions, pauses, Visual Beats, telops, numbers, assets, and cues;
- resolved image route with one selected path;
- date and renderer schema match;
- public render text exists verbatim in the human package;
- a bound verified intraday series is attached before pinned Renderer validation and included in the validated render-spec SHA;
- MEMREF and memory internal fields never enter public artifacts;
- hardened preflight authorizes preview only and keeps final authorization false.

A PASS does not approve market causality or visual quality. Those remain ChatGPT and user responsibilities under 01–04.
