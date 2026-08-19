# PR-2 — Semantic Payload / Canonical Artifact Boundary

Date: 2026-08-19
Base: PR-1 current-policy separation

## Current temporal order

```text
visual_requirements.semantic.json
  -> machine materializer
visual_requirements.json
  -> Candidate Builder
visual_candidate_catalog.json
  -> visual_director_decision.semantic.json
  -> machine materializer
visual_director_decision.json
  -> Renderer compile
visual_direction_compiled_render.json
visual_editorial_warning_report.json
  -> visual_critic_review.semantic.json
  -> machine materializer
visual_critic_review.json
  -> visual_intelligence_package.json
```

## Ownership

- Semantic payloads are authored meaning only. They may not contain machine-derived `*Sha256` fields.
- Canonical Requirements, Director Decision and Critic Review are written only by `visual_intelligence_artifacts_v12.py`.
- Director canonical may be corrected only before compile; compiled output freezes it.
- Critic canonical may be corrected only before the VI package exists; package creation freezes it.
- Candidate/compile artifacts are reused on subsequent stages and are not regenerated merely because the Critic stage runs.
- Current production never creates or reads `visual_intelligence_decision.json` as a combined Director/Critic authority.

## Visual Source checkpoint

Daily Authoring seeds Visual Source working files before Requirements exist. Once canonical Requirements exist, deterministic Daily Authoring reruns preserve the already-authored Visual Source checkpoint instead of overwriting it. The old capture/restore workaround is therefore removed from the current closure.

## Semantic Freeze identity

The LLM semantic payloads no longer duplicate `semanticFreezeSha256`. The immutable current production request binds the verified Semantic Freeze, and canonical Requirements bind the Editorial Snapshot. This preserves machine lineage without manual SHA transcription.

## Renderer compatibility

The Renderer keeps its existing strict `visualDirectionPlan` schema. The current Director canonical records the Candidate Catalog artifact file SHA for production lineage, while the Renderer Plan uses the existing canonical-content SHA required by the pinned Renderer contract.

## Acceptance

The exact Cross-Repo E2E must prove:

- pause before Director semantic authoring;
- illegal Director choice rejected before compile;
- compile happens exactly before Critic;
- post-compile Director rewrite is rejected and compiled bytes stay unchanged;
- Critic semantic payload is SHA-free;
- canonical Critic binds exact Director/compiled/warning bytes;
- combined decision authority is absent;
- VI package validator PASSes against the exact pinned Renderer.
