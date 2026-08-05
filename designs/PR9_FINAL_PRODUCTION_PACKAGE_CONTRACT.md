# PR #9｜Final Production Package Contract

## Purpose

Make the post-inquisition episode package the only human editorial source of truth and derive all execution artifacts deterministically without allowing code to change meaning.

## Source annex

The final episode package contains one `FINAL_PRODUCTION_SOURCE` JSON annex. It records the exact renderer-compatible render spec, resolved image path, asset catalog, renderer contract, and 04 completion state.

The builder verifies all public render text exists verbatim in the human-readable episode package. It then derives:

- `working/YYYY-MM-DD/episode_package_ir.json`
- `episodes/YYYY-MM-DD/spoken_script_YYYY-MM-DD.md`
- `episodes/YYYY-MM-DD/asset_manifest.json`
- `render-specs/YYYY-MM-DD/render_spec.json`
- `verification/YYYY-MM-DD/production_consistency_report.json`
- `verification/YYYY-MM-DD/official_execution_preflight.json`

## Safety

- no LLM or editorial inference;
- nine ordered Scenes only;
- chunk and Beat IDs unique and internally linked;
- unresolved asset states rejected;
- Primary/Fallback selection cannot be inferred;
- public text cannot contain PR8 memory markers;
- rerunning identical input produces byte-identical artifacts;
- preflight authorizes preview but never final.

## Verification

Thirty deterministic positive and adversarial tests cover rerun identity, Scene order, review gates, chunk/Beat references, assets, image routes, public-text equality, marker leakage, and final authorization.
