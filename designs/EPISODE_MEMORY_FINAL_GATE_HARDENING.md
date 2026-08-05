# Episode Memory Final Gate Hardening

## Purpose

Close the execution gap between Episode Package Memory Reference, deterministic Final Production, Financial Visual Cross-Artifact, immutable Renderer Handoff, Real-Day Acceptance, and the Daily Control Plane.

This change adds no editorial judgment. It validates and transports only content already completed by ChatGPT under 01–04.

## Canonical package order

```text
public editorial content
→ Scene 1–9
→ 04 興味深さ・わかりやすさ審問結果
→ Editorial Memory Usage Annex
→ Final Production Source Annex, when present
→ EOF
```

After the memory annex, only whitespace or one Final Production Source annex is allowed. When present, that annex must be final.

## Authoritative production entry

```text
run_daily_production_hardened.py
→ validate_episode_package_memory.py
→ validate_episode_package_memory_hardening.py
→ build_final_production_package_hardened.py
→ Financial Visual Cross-Artifact, when required
→ build_renderer_handoff_hardened.py
→ run_real_day_acceptance_hardened.py
→ user visual review
```

The base Daily, Final Production, Handoff, and Acceptance scripts remain deterministic implementations and unit-test targets. They are not production entrypoints.

## Three-stage evidence

### 1. Pre-build

The episode-memory final gate requires:

- Scene 1–9 exactly once and in order;
- exactly one integrated 04 result;
- canonical annex ordering;
- package filename/date agreement;
- merged PR #8 validation and PR #6 lineage replay.

### 2. Public artifacts

After deterministic Final Production generation, spoken script, asset manifest, and render spec are scanned for MEMREF and internal memory fields. On failure, generated outputs are deleted.

The following evidence is atomically persisted in `official_execution_preflight.json`:

```json
{
  "episode_memory_hardening": {
    "pre_build": "pass",
    "public_artifacts": "pass"
  }
}
```

### 3. Handoff recheck

Financial Visual Cross-Artifact may update final public files after Final Production. Therefore, immediately before bundle creation, the current episode package, spoken script, asset manifest, and render spec are rechecked.

On success, the preflight becomes:

```json
{
  "episode_memory_hardening": {
    "pre_build": "pass",
    "public_artifacts": "pass",
    "handoff_recheck": "pass"
  }
}
```

The base Handoff builder then hashes and copies these final bytes. A newly created bundle is deleted if the copied preflight loses this evidence.

## Guarded Real-Day Acceptance

Real-Day Acceptance requires:

- exactly one preflight role in the handoff manifest;
- complete three-stage hardening in the bundled preflight;
- base Real-Day validation PASS;
- pinned renderer technical PASS and preview MP4;
- no final render execution.

The existing acceptance-report schema is preserved; verification is recorded in `validation.warnings`.

## Fail-closed conditions

- Scene missing, duplicated, or out of order;
- missing or duplicated 04 result;
- malformed or misplaced annexes;
- package filename/date mismatch;
- MEMREF or memory internal fields in public artifacts;
- repo-root escape;
- base PR #8 or PR #6 validation unavailable or failing;
- post-build leak with generated artifacts retained;
- final public files changed after the previous scan without handoff recheck;
- renderer bundle missing three-stage hardening evidence;
- Real-Day Acceptance attempted with an unhardened bundle.

## Permanent regression matrix

CI runs:

- Episode Package Memory base and hardening tests;
- Final Production base and hardening tests;
- Financial Visual contract regressions;
- Renderer Handoff base and hardening tests;
- Real-Day Acceptance base and hardening tests;
- Daily Control Plane base and hardening tests;
- PR #6 memory revalidation;
- retrieval, promotion, and editorial-memory contract regressions.

## Responsibility boundary

This hardening does not modify 01–04, select the lead or market causality, create Expected / Actual / Gap, rewrite fox narration, choose financial visuals or image routes, render preview/final, or replace user visual review.

## Goal

MVP proof requires the exact chain:

```text
post-inquisition episode package
→ revalidated memory use
→ leak-free production artifacts
→ handoff-time final-byte recheck
→ immutable hardened preview bundle
→ renderer technical PASS
→ preview MP4
→ user visual review
```
