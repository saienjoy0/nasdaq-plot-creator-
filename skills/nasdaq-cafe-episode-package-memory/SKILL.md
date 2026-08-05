---
name: nasdaq-cafe-episode-package-memory
version: 1.1.0
description: Validate how revalidated editorial memory is used in the final human-readable episode package without changing editorial meaning.
---

# Episode Package Memory Usage

## Purpose

Validate the bridge from a validated causal research dossier to the final, post-inquisition `episode_package_YYYY-MM-DD.md`.

The episode package remains the human editorial source of truth. Memory metadata is stored in one machine-readable annex after the public and 04 sections, and each public use is marked by an invisible HTML comment immediately after the exact anchor text.

## Contract

The package must contain Scene 1 through Scene 9 exactly once and in order, followed by exactly one integrated `04 興味深さ・わかりやすさ審問結果` section.

The Editorial Memory Usage Annex follows the 04 section. After it, the package may contain only whitespace or exactly one Final Production Source annex. When the Final Production Source annex is present, it must be the final section.

Each public use has exactly one marker:

```text
<!--MEMREF:MR-001:U-001-->
```

Markers and memory-annex metadata must never enter spoken script, captions, telops, asset-manifest public fields, render-spec public text, or viewer-visible output.

## Authoritative validation order

```text
validate_episode_package_memory.py
→ validate_episode_package_memory_hardening.py
```

The base validator replays PR #6 lineage and validates memory identity, status, Evidence IDs, Scene/surface anchors, title/thumbnail restrictions, Expected/causality restrictions, and unrecorded fox personal history.

The hardening validator additionally:

- requires all nine Scenes exactly once and in order;
- requires exactly one integrated 04 result before the memory annex;
- fixes Memory Annex → optional Final Production Source Annex → EOF ordering;
- requires the filename date to match the memory episode date;
- strips the Final Production Source annex only for the base PR #8 replay, preventing its JSON from being mistaken for public prose;
- scans supplied public artifacts for MEMREF and internal memory fields;
- rejects repo-external artifact paths;
- fails closed if the base validator cannot run.

Example:

```bash
python skills/nasdaq-cafe-episode-package-memory/validators/validate_episode_package_memory_hardening.py \
  --episode-package episodes/YYYY-MM-DD/episode_package_YYYY-MM-DD.md \
  --public-artifact episodes/YYYY-MM-DD/spoken_script_YYYY-MM-DD.md \
  --public-artifact episodes/YYYY-MM-DD/asset_manifest.json \
  --public-artifact render-specs/YYYY-MM-DD/render_spec.json \
  --output verification/YYYY-MM-DD/episode_memory_hardening.json
```

## Boundary

This skill does not select the lead, decide market causality, write narration, perform the entertainment inquisition, choose image routes, create render specs, or render video. A PASS proves structural and evidential traceability, not editorial correctness.
