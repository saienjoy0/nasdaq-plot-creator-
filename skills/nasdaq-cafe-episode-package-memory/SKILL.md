---
name: nasdaq-cafe-episode-package-memory
version: 1.0.0
description: Validate how revalidated editorial memory is used in the final human-readable episode package without changing editorial meaning.
---

# Episode Package Memory Usage

## Purpose

This skill validates the bridge from a validated causal research dossier to the final, post-inquisition `episode_package_YYYY-MM-DD.md`.

The episode package remains the human editorial source of truth. Memory metadata is stored in one machine-readable annex at the end of the package, and each public use is marked by an invisible HTML comment immediately after the exact anchor text.

## Required inputs

- final post-inquisition episode package
- validated causal research dossier v0.2
- dossier-linked research input manifest
- manifest-linked memory retrieval report

## Contract

The episode package must contain exactly one annex:

```text
<!--BEGIN_EPISODE_MEMORY_ANNEX-->
```json
{ ... }
```
<!--END_EPISODE_MEMORY_ANNEX-->
```

Each public use must contain exactly one marker:

```text
<!--MEMREF:MR-001:U-001-->
```

The marker must immediately follow the exact anchor text. Markers and the annex are production metadata and must never enter spoken script, captions, telops, render-spec public text, or viewer-visible output.

## Validation behavior

The validator:

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

## Responsibility boundary

This skill does not select the lead, decide market causality, write or improve narration, perform the entertainment inquisition, choose an image path, create a render spec, or render video.

Passing validation means declared memory usage is structurally and evidentially traceable. It does not prove that the editorial interpretation is correct.
