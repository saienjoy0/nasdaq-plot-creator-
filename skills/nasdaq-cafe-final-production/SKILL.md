---
name: nasdaq-cafe-final-production
version: 1.1.0
description: Deterministically derive all production artifacts from the final post-inquisition episode package.
---

# Final Production Package

## Source of truth

`episode_package_YYYY-MM-DD.md` remains the human editorial source of truth. After the public sections and PR8 memory annex, it contains exactly one machine-readable Final Production Source annex.

The annex is authored only after:

- 04 inquisition is complete and required changes are applied;
- PR8 memory references and status-to-use rules pass;
- Primary / Approved Fallback has one resolved selected path;
- all Scene 1–9 narration, Visual Beats, telops, numbers, assets, cues, and publishing text are final.

## Mandatory pre-build gate

Before `build_final_production_package.py`, run the authoritative episode-memory final gate:

```bash
python skills/nasdaq-cafe-episode-package-memory/validators/validate_episode_package_memory_hardening.py \
  --episode-package episode_package_YYYY-MM-DD.md
```

This gate re-runs the base PR8 validator and the PR6 dossier validation chain. It also requires nine ordered Scenes, one integrated 04 result, canonical annex ordering, and no unexpected content after the Final Production Source annex.

Do not build production artifacts when this gate fails or cannot run.

After artifacts are generated, run the same gate again with public artifacts:

```bash
python skills/nasdaq-cafe-episode-package-memory/validators/validate_episode_package_memory_hardening.py \
  --episode-package episode_package_YYYY-MM-DD.md \
  --public-artifact spoken_script_YYYY-MM-DD.md \
  --public-artifact asset_manifest.json \
  --public-artifact render_spec.json
```

## Deterministic flow

```text
final episode package
→ episode-memory final gate
→ episode_package_ir.json
→ spoken_script_YYYY-MM-DD.md
→ asset_manifest.json
→ render_spec.json
→ production_consistency_report.json
→ public-artifact metadata-leak gate
→ official_execution_preflight.json
```

No downstream artifact may add, paraphrase, reorder, infer, or repair editorial content. Missing or unresolved information stops the build.

## Required invariants

- exactly nine ordered Scenes in the episode package and render spec;
- exactly one integrated 04 inquisition result;
- exact speech/caption/expression/pause data;
- exact Visual Beat start/end cues and display content;
- all placement asset IDs exist in the asset catalog;
- 04 verdict is approved or conditional-pass with all required changes applied;
- image resolution is resolved with one selected path;
- episode date and renderer schema version match;
- public text in the render spec exists verbatim in the human episode package;
- PR8 MEMREF metadata and annex internal fields never enter speech, captions, telops, render spec, or manifest;
- preflight authorizes preview only and keeps final authorization false.

Passing the production consistency validator does not approve market causality or visual quality. Those remain ChatGPT and user responsibilities under 01–04.
