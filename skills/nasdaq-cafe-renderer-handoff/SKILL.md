---
name: nasdaq-cafe-renderer-handoff
version: 1.2.0
description: Build an immutable, SHA-bound, preview-gated bundle for the Nasdaq Cafe renderer.
---

# Renderer Handoff Bundle

## Purpose

Package only validator-PASS production artifacts and resolved assets for delivery to `saienjoy0/saienjoy0-nasdaq-cafe-remotion` without allowing the renderer to infer or change editorial meaning.

## Mandatory guarded entrypoint

Use `scripts/build_renderer_handoff_hardened.py`, not the base handoff builder, for production bundles.

The guarded entrypoint first requires the source `official_execution_preflight.json` to contain Final Production hardening:

```json
{
  "episode_memory_hardening": {
    "pre_build": "pass",
    "public_artifacts": "pass"
  }
}
```

It then re-runs the episode-memory final gate against the current episode package, spoken script, asset manifest, and render spec. This second check occurs after any Financial Visual Cross-Artifact update and before bundle construction.

On success, it atomically records:

```json
{
  "episode_memory_hardening": {
    "pre_build": "pass",
    "public_artifacts": "pass",
    "handoff_recheck": "pass"
  }
}
```

The deterministic base handoff builder then hashes and copies these final bytes. The guarded entrypoint verifies that the copied bundle preflight retains the complete three-stage evidence. A newly created bundle is deleted if this post-copy verification fails.

## Preview contract

Preview bundles require:

- complete three-stage episode-memory hardening evidence;
- zero unresolved states;
- render-spec date and schema version match;
- consistency report PASS;
- resolved Primary/Fallback/not-required path;
- all required files and assets exist and match declared SHA values;
- `final_authorized=false` and no final approval record.

## Final contract

Final bundles are a separate mode. They require both a final-authorized preflight and an explicit approval record with matching episode date, `approval_status=approved_preview`, `final_requested=true`, and a pinned preview-manifest SHA.

Preview never auto-promotes to final.

## Bundle properties

- deterministic bundle ID from the canonical manifest;
- source and destination path safety;
- renderer repository, base commit, and contract version pinned;
- file SHA-256 and size recorded;
- hardened preflight bytes included in bundle identity;
- asset bytes copied and reverified;
- same input is idempotent;
- tampered existing bundles fail closed.

The bundle is transport and provenance only. It performs no market-causality, narration, template, image-path, financial-visual, or publication decision.
