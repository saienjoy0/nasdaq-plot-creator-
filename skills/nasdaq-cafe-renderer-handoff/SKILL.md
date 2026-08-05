---
name: nasdaq-cafe-renderer-handoff
version: 1.0.0
description: Build an immutable, SHA-bound, preview-gated bundle for the Nasdaq Cafe renderer.
---

# Renderer Handoff Bundle

## Purpose

Package only validator-PASS production artifacts and resolved assets for delivery to `saienjoy0/saienjoy0-nasdaq-cafe-remotion` without allowing the renderer to infer or change editorial meaning.

## Preview contract

Preview bundles require:

- final production preflight PASS;
- zero unresolved states;
- render-spec date and schema version match;
- consistency report PASS;
- resolved Primary/Fallback/not-required path;
- all required files and assets exist and match declared SHA values;
- `final_authorized=false` and no final approval record.

## Final contract

Final bundles are a separate mode. They require both a final-authorized preflight and an explicit approval record with:

- matching episode date;
- `approval_status=approved_preview`;
- `final_requested=true`;
- a pinned preview-manifest SHA.

Preview never auto-promotes to final.

## Bundle properties

- deterministic bundle ID from the canonical manifest;
- source and destination path safety;
- renderer repository, base commit, and contract version pinned;
- file SHA-256 and size recorded;
- asset bytes copied and reverified;
- same input is idempotent;
- tampered existing bundles fail closed.

The bundle is transport and provenance only. It performs no market-causality, narration, template, image-path, or publication decision.
