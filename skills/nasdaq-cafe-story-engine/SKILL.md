---
name: nasdaq-cafe-story-engine
version: 1.1.4
description: Turn a validated causal dossier into an independently reviewed 9-Scene episode package without changing market causality.
---

# Unified Story Engine

Run after `causal_dossier_valid` and before `episode_package_final`.

Story Discovery, Narrative Architecture, Authoring, Critic, Rewrite and Re-review are **internal Story Engine passes**. They are not Daily Production states. The intended public Daily Production transition is:

```text
causal_dossier_valid
→ episode_package_final
```

The v1.1 gate implementation lives in `scripts/run_daily_production_story_engine_v1_1.py`. Older `story_plan_valid`, `script_draft_ready`, and `creative_review_passed` states are compatibility history only and must not be used once the v1.1 gate is activated.

**Activation rule:** do not route the production workflow through the v1.1 gate until an `orchestrator_signed` Critic execution receipt exists. A `repository_provenance` receipt is sufficient to validate artifact separation and regression behavior, but it must leave `production_eligible=false`.

## Absolute boundary

The engine may change explanation order, Scene connections, wording, compression, visual presentation and publishing copy. It may not change the lead, facts, numbers, Expected / Actual / Gap, chronology, causal scope, confidence, counterevidence, uncertainty, official Scene roles or fox history.

When evidence or causality is defective, return to Causal Research or 02. Do not repair factual defects as entertainment edits.

## Pass A — Story Discovery

Do not write narration. Extract before context, central contradiction, naive explanations, evidence tests, explanation update, headline-beyond discovery and after implications. Produce 2–3 angle candidates only when multiple angles survive. One angle plus a reason is valid. For reason-unknown episodes, compare ways to explain uncertainty rather than inventing a cause.

## Pass B — Narrative Architecture

Keep the official Scene 1–9 roles from 03. Record the viewer belief before and after each Scene, new evidence or new meaning, connector, deletion consequence and open-loop movement. Use no more than two open loops; resolve or evidence-back them by Scene 8. Scene 9 opens none.

Scenes 4–7 require at least one real understanding update: `turn`, `complication`, `boundary`, `counterevidence`, `disproof` or `reveal`. Do not force a dramatic reversal.

Scene 1–2 may state direction, contradiction and the central question. Use `HOOK_EXHAUSTS_THE_STORY` when the opening consumes the proof, limitations, counterevidence and validation conditions needed later.

## Pass C — Draft Episode Package

Complete narration, acting intention, expressions, Visual Beats, screen states, telops, numbers, title, thumbnail, description and Primary/Fallback records. Freeze the draft path and SHA-256.

The fox uses `僕`, remains an equal guide, explains meaning after numbers, uses IT analogies 0–2 times and never invents trades or personal history. Avoid procedural narration that merely announces the outline.

## Pass D — Independent Critic

Start a separate invocation/context. Give it the baseline, Claim Ledger, selected angle, completed Draft Episode Package, 01–04, evidence references and draft SHA. Do not provide Author self-scoring or thought notes.

Review the complete production package, not narration alone. Each finding must name exact Scene IDs/field paths, viewer effect, required fix and claims/evidence to preserve. Any unresolved Critical finding blocks finalization.

### Production isolation contract

Production requires both of the following pre-authored artifacts:

- `working/YYYY-MM-DD/story-engine/templates/critic_request.json`
- `working/YYYY-MM-DD/story-engine/templates/critic_execution_receipt.json`

The request freezes the exact Critic input set and records Author-only context that must be excluded. The receipt binds a different Critic invocation ID, the frozen request, and the final review artifact.

Run `scripts/story-engine/validate_critic_execution_receipt.py`. It verifies input Git blob SHAs, 03/04 logical source SHAs, Author/Critic ID separation, review round, PASS threshold, and absence of unresolved Critical findings.

A shadow run that only isolates the Critic input artifact must declare `critic_isolation_mode=logical_shadow` and `production_eligible=false`. Production mode requires `separate_invocation`, a valid receipt, and `attestation_strength=orchestrator_signed`. Distinct string IDs alone do not prove independence.

`repository_provenance` proves artifact separation and repository lineage. It is deliberately reported as non-cryptographic evidence of process separation and cannot unlock production. GitHub Actions must never invent or rewrite the Critic judgment.

### Cryptographic orchestrator attestation

A receipt that declares `attestation_strength=orchestrator_signed` must reference `critic_orchestrator_attestation.json`.

The attestation binds the episode date, Author invocation ID, Critic invocation ID, sealed Critic Request SHA-256, final Review SHA-256, a distinct orchestrator run ID, the runtime verification record, and the process-boundary assertions that Author context was not shared and the Critic started only after the Request was sealed.

The entire attestation payload is signed with Ed25519. Verification is performed by `scripts/story-engine/validate_critic_orchestrator_attestation.py`. Only an `active` public key in `skills/nasdaq-cafe-story-engine/trust/trusted_critic_orchestrators.json` is accepted. The matching private key must remain outside this repository and outside the Author execution context.

For the built-in production runner, the runtime verification record must satisfy `critic_external_verification.schema.json`: Docker isolation, digest-pinned adapter image, repository not mounted, Critic input read-only, Author context not mounted, exit code 0, and Request/Review SHA bindings.

### External Critic operational path

Use `scripts/story-engine/run_external_critic_pipeline.py` as the operational entry point. Do not call the model adapter directly from Daily Production or GitHub Actions.

The pipeline is:

```text
sealed critic_request.json
↓
zero-call preflight
↓
copy only approved inputs into a temporary sealed bundle
↓
reconstruct verified 03 / 04 plaintext into that bundle
↓
Docker Critic adapter with repository NOT mounted
↓
creative_review.json
↓
review threshold / Critical-finding checks
↓
runtime verification record
↓
Ed25519 orchestrator attestation
↓
orchestrator_signed critic_execution_receipt.json
↓
repository trust validation
```

The zero-call preflight is `scripts/story-engine/preflight_external_critic_orchestrator.py`. It must pass before any model/API call. It verifies the request bundle, Docker availability, digest-pinned adapter image syntax, required adapter environment variables, and that the out-of-repository private key matches an active public key already registered in the trust registry.

The low-level runner is `scripts/story-engine/run_external_critic_orchestrator.py`. The Critic adapter image is provider-neutral but must be pinned as `image@sha256:<digest>`. The container receives only `/critic/input` read-only and `/critic/output` writable. It receives only environment variable names explicitly allowed with `--pass-env`; the host/Author environment is not forwarded wholesale.

The adapter must read:

- `NASDAQ_CAFE_CRITIC_REQUEST=/critic/input/critic_request.json`
- `NASDAQ_CAFE_CRITIC_BUNDLE=/critic/input/bundle_manifest.json`

and write:

- `NASDAQ_CAFE_CRITIC_REVIEW_OUT=/critic/output/creative_review.json`

The private signing key must never be placed in this repository, a GitHub Actions secret used by the production renderer, the Critic input bundle, or the Author context.

The trust registry is intentionally empty until a real external Critic orchestrator is provisioned. A self-authored JSON file, an unknown key, a revoked key, a tampered signed field, a Request/Review SHA mismatch, an invalid runtime record, or an Author/Critic ID collision must all fail closed.

GitHub Actions may verify signatures and hashes. It must not create the Critic review, create the private-key signature, rewrite the attestation, or upgrade a repository-provenance receipt to production eligibility.

## Pass E — Targeted Rewrite

Patch only finding-linked fields. Full regeneration is not the default. General Scene reordering is forbidden. `move_explanation_block` may move comparison or explanation only when real chronology remains unchanged.

## Pass F — Causality Preservation

Compare draft and rewrite against the Claim Ledger. Reject evidence loss, modality strengthening, counterevidence removal, chronology distortion, company-to-Nasdaq scope promotion, investment advice or invented fox history.

## Pass G — Final Re-review

Normally use one Critic → patch → re-review cycle. A second round is allowed only while Critical findings remain. Never exceed two rounds. If Critical findings remain, block and return to Pass A/B/C or upstream research.

## Unified production gate

The v1.1 gate requires one `story_engine_acceptance.json` bound to:

- validated causal dossier
- materialized Story Plan
- materialized Story Script
- final creative review
- sealed Critic request
- Critic execution receipt
- causality/Scene guards

The acceptance is validated by `scripts/story-engine/validate_story_engine_acceptance_v1_1.py`. It also checks that materialized Story Plan/Script differ from the Critic-reviewed templates only by deterministic lineage bindings and that the materialized review is semantically identical to the pre-authored review.

Artifact validation may PASS while `production_eligible=false`. Daily Production may advance directly from `causal_dossier_valid` to `episode_package_final` only when the same acceptance also passes `--require-production`, which requires an Ed25519-verified `orchestrator_signed` receipt from an active trusted orchestrator key.

## Current migration status

For the committed 2026-08-06 regression fixture, the available receipt is intentionally `repository_provenance`. Therefore:

```text
artifact / lineage validation = PASS
production eligibility = BLOCKED
```

The code path for a real external Critic execution now exists, but three external items are intentionally not fabricated by this repository:

1. a real Critic adapter container image that calls the chosen model provider, pinned by image digest;
2. an Ed25519 private key held outside the repository/Author/GitHub Actions renderer environment;
3. the matching public key registered as `active` in `trusted_critic_orchestrators.json`.

Keep the current compatibility workflow unchanged until those three items are provisioned and a real orchestrator-signed acceptance passes. The v1.1 wrapper then becomes a small explicit activation switch rather than another Story Engine redesign.

## Required artifacts

- `working/YYYY-MM-DD/story_engine_package_YYYY-MM-DD.json` for the unified editorial/provenance record when produced
- `working/YYYY-MM-DD/story-engine/story_engine_acceptance.json` for the production transition
- `episodes/YYYY-MM-DD/episode_package_YYYY-MM-DD.md`
- `verification/YYYY-MM-DD/story_engine_validation_report.json` when the unified package validator is run
- `working/YYYY-MM-DD/story-engine/templates/critic_request.json`
- `working/YYYY-MM-DD/story-engine/templates/critic_execution_receipt.json`
- `working/YYYY-MM-DD/story-engine/templates/critic_external_verification.json` when the built-in external runner is used
- `working/YYYY-MM-DD/story-engine/templates/critic_orchestrator_attestation.json` when a trusted external orchestrator is active

Run `validators/validate_story_engine_hardening.py` for the unified Story Engine package and the v1.1 receipt/acceptance validators for the production gate. Passing deterministic validators does not itself prove the story is interesting; that judgment belongs to the independent Critic and the user's A/B review.
