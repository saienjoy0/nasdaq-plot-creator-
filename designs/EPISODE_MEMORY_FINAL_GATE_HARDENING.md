# Episode Memory Final Gate Hardening

## Purpose

Close the execution gap between the merged Episode Package Memory Reference contract, deterministic Final Production Package, immutable Renderer Handoff Bundle, and Real-Day Acceptance gate.

This change does not add editorial judgment. It validates and transports only content that ChatGPT has already completed under 01–04.

## Canonical package order

```text
public editorial content
→ Scene 1–9
→ 04 興味深さ・わかりやすさ審問結果
→ Editorial Memory Usage Annex
→ Final Production Source Annex, when present
→ EOF
```

After the memory annex, only whitespace or exactly one Final Production Source annex is allowed. When present, the Final Production Source annex must be final.

## Authoritative execution chain

```text
validate_episode_package_memory.py
→ validate_episode_package_memory_hardening.py
→ build_final_production_package_hardened.py
→ build_renderer_handoff_hardened.py
→ run_real_day_acceptance_hardened.py
```

### Episode-memory hardening

- requires Scene 1–9 exactly once and in order;
- requires exactly one integrated 04 result before the memory annex;
- fixes cross-annex ordering;
- verifies package filename date;
- re-runs the merged PR #8 validator and therefore PR #6 lineage;
- temporarily removes only the final-production annex during the base PR #8 replay so final-production JSON is not mistaken for public prose;
- scans supplied public artifacts for MEMREF and internal memory fields.

### Guarded Final Production

- runs the episode-memory gate before generation;
- invokes the existing deterministic Final Production builder;
- scans spoken script, asset manifest, and render spec after generation;
- deletes generated outputs on post-build failure;
- atomically persists this evidence into `official_execution_preflight.json`:

```json
{
  "episode_memory_hardening": {
    "pre_build": "pass",
    "public_artifacts": "pass"
  }
}
```

### Guarded Renderer Handoff

- rejects a source preflight without complete hardening evidence;
- invokes the existing immutable handoff builder;
- verifies that the copied bundle preflight retains the same evidence;
- deletes a newly created bundle if the evidence is lost after copying.

Because the preflight bytes are SHA-bound in the handoff manifest and bundle ID, the hardening evidence is immutable inside the bundle.

### Guarded Real-Day Acceptance

- requires exactly one preflight role in the handoff manifest;
- loads the bundled preflight and verifies complete hardening evidence;
- invokes the existing Real-Day Acceptance runner;
- keeps the existing acceptance-report schema unchanged;
- records hardening verification as a validation warning rather than adding an unsupported top-level field.

## New fail-closed conditions

- Scene missing, duplicated, or out of order;
- missing or duplicated 04 result;
- arbitrary content after the memory annex;
- malformed or misplaced Final Production Source annex;
- package filename/date mismatch;
- MEMREF or memory internal fields in public artifacts;
- repo-root escape for output or public-artifact paths;
- base PR #8 or PR #6 validation unavailable or failing;
- post-build leak with generated artifacts left behind;
- renderer handoff built from an unhardened preflight;
- acceptance attempted with a bundle that lost hardening evidence.

## Regression matrix

Permanent CI runs:

- Episode Package Memory base tests;
- episode-memory hardening tests;
- Final Production base and hardening tests;
- Renderer Handoff base and hardening tests;
- Real-Day Acceptance base and hardening tests;
- Final Episode financial-visual contract regression;
- PR #6 memory revalidation;
- retrieval, promotion, and editorial-memory contract regressions.

## Responsibility boundary

This hardening does not:

- modify 01–04;
- select the lead or market causality;
- create Expected / Actual / Gap;
- rewrite fox narration;
- choose financial visuals, recipes, images, Primary, or Fallback;
- render preview or final;
- replace the user’s visual review.

## Goal

A Real-Day Acceptance report may count toward MVP only when the exact chain below is proven:

```text
post-inquisition episode package
→ revalidated memory use
→ leak-free deterministic production artifacts
→ immutable hardened preview bundle
→ pinned renderer technical PASS
→ preview MP4
→ user visual review
```
