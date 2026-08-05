---
name: nasdaq-cafe-episode-package-memory
version: 1.1.0
description: Validate how revalidated editorial memory is used in the final human-readable episode package without changing editorial meaning.
---

# Episode Package Memory Usage

## Purpose

This skill validates the bridge from a validated causal research dossier to the final, post-inquisition `episode_package_YYYY-MM-DD.md`.

The episode package remains the human editorial source of truth. Memory metadata is stored in one machine-readable annex after the public and 04 sections, and each public use is marked by an invisible HTML comment immediately after the exact anchor text.

## Required inputs

- final post-inquisition episode package
- validated causal research dossier v0.2
- dossier-linked research input manifest
- manifest-linked memory retrieval report
- optional generated public artifacts for metadata-leak scanning

## Contract

The episode package must contain Scene 1 through Scene 9 exactly once and in order, followed by exactly one integrated `04 興味深さ・わかりやすさ審問結果` section.

The Editorial Memory Usage Annex follows the 04 section:

```text
<!--BEGIN_EPISODE_MEMORY_ANNEX-->
```json
{ ... }
```
<!--END_EPISODE_MEMORY_ANNEX-->
```

After the memory annex, the package may contain only whitespace or exactly one Final Production Source annex. When the Final Production Source annex is present, it must be the final section.

Each public use must contain exactly one marker:

```text
<!--MEMREF:MR-001:U-001-->
```

The marker must immediately follow the exact anchor text. Markers and the annex are production metadata and must never enter spoken script, captions, telops, asset manifest public fields, render-spec public text, or viewer-visible output.

## Authoritative validation order

Run:

```text
validate_episode_package_memory.py
→ validate_episode_package_memory_hardening.py
```

The hardening validator invokes the base PR #8 validator. A base failure, import failure, PR #6 replay failure, or hardening failure stops production.

## Validation behavior

The base validator:

1. resolves all paths inside the repository root;
2. verifies the dossier SHA-256;
3. re-runs the PR #6 dossier/retrieval/manifest validation chain;
4. requires exact equality between annex memory metadata and dossier revalidation;
5. verifies current Evidence IDs and quality;
6. enforces the status-to-public-use matrix;
7. verifies annex usage ↔ marker ↔ anchor ↔ Scene/surface in both directions;
8. blocks memory as Expected evidence in Scene 4 and price-causality evidence in Scene 6;
9. blocks unsupported memory use in titles and thumbnails;
10. blocks concrete fox personal-history claims until a dedicated personal-memory contract exists.

The hardening validator additionally:

1. requires all nine Scenes exactly once and in order;
2. requires exactly one integrated 04 inquisition result before the memory annex;
3. allows only the Final Production Source annex after the memory annex;
4. requires the Final Production Source annex to be last when present;
5. requires the filename date to match the memory annex episode date;
6. scans supplied public artifacts for MEMREF, annex markers, and internal memory fields;
7. rejects public-artifact paths outside the repository root;
8. fails closed if the base validator cannot run.

Example:

```bash
python skills/nasdaq-cafe-episode-package-memory/validators/validate_episode_package_memory_hardening.py \
  --episode-package episodes/YYYY-MM-DD/episode_package_YYYY-MM-DD.md \
  --public-artifact episodes/YYYY-MM-DD/spoken_script_YYYY-MM-DD.md \
  --public-artifact episodes/YYYY-MM-DD/asset_manifest.json \
  --public-artifact render-specs/YYYY-MM-DD/render_spec.json \
  --output verification/YYYY-MM-DD/episode_memory_hardening.json
```

## Responsibility boundary

This skill does not select the lead, decide market causality, write or improve narration, perform the entertainment inquisition, choose an image path, create a render spec, or render video.

Passing validation means declared memory usage is structurally and evidentially traceable and the submitted package has the required final-package shape. It does not prove that the editorial interpretation is correct.
