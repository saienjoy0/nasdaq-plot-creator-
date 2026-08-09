---
name: nasdaq-cafe-story-engine
version: 1.1.6
description: Turn a validated causal dossier into a reviewed 9-Scene episode package without changing market causality.
---

# Unified Story Engine

Run after `causal_dossier_valid` and before `episode_package_final`.

Story Discovery, Narrative Architecture, Authoring, Critic, Rewrite and Re-review are **internal Story Engine passes**. They are not Daily Production states. The intended public Daily Production transition is:

```text
causal_dossier_valid
→ episode_package_final
```

The v1.1 gate implementation lives in `scripts/run_daily_production_story_engine_v1_1.py`. Older `story_plan_valid`, `script_draft_ready`, and `creative_review_passed` states are compatibility history only and must not be used once the v1.1 gate is activated.

**Operating rule:** the normal 01–04 editorial review, causality guards, Scene guards, hash-bound acceptance, projection report, renderer validation and user Preview review remain mandatory. A cryptographically proven external Independent Critic is an optional quality upgrade, not a prerequisite for daily operation. When no `orchestrator_signed` Critic receipt exists, the Daily Production wrapper must use the explicit uncertified-production policy and preserve `critic_certified=false` / `external_critic_status=not_certified`; it must never claim that an external independent review occurred.

The strict certification path remains available. A `repository_provenance` receipt is sufficient to validate artifact separation, review lineage and regression behavior but does not itself become cryptographic proof of an external Critic execution. The legacy `production_eligible` field continues to mean external-Critic-certified eligibility; the validator separately reports whether production is allowed by the selected operating policy.

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

## Pass D — Editorial Critic

The 04 entertainment/clarity review is required even when the external Independent Critic is not purchased or connected. Review the complete production package, not narration alone. Each finding must name exact Scene IDs/field paths, viewer effect, required fix and claims/evidence to preserve. Any unresolved Critical finding blocks finalization.

When an external Independent Critic is available, start it in a separate invocation/context. Give it the baseline, Claim Ledger, selected angle, completed Draft Episode Package, 01–04, evidence references and draft SHA. Do not provide Author self-scoring or thought notes.

### Review-lineage and optional external certification contract

The Story Engine retains both of the following pre-authored artifacts:

- `working/YYYY-MM-DD/story-engine/templates/critic_request.json`
- `working/YYYY-MM-DD/story-engine/templates/critic_execution_receipt.json`

The request freezes the review input set and records Author-only context that must be excluded from a future external Critic. The receipt binds review lineage and the final review artifact.

Run `scripts/story-engine/validate_critic_execution_receipt.py`. It verifies input Git blob SHAs, 03/04 logical source SHAs, Author/Critic ID separation recorded by the artifact, review round, PASS threshold, and absence of unresolved Critical findings.

A `repository_provenance` receipt is non-cryptographic evidence. It can support normal daily operation only through the explicit optional-Critic policy; it must be reported as `not_certified` and must not be described as proof that a distinct external model process executed.

A certified external Critic path requires `separate_invocation`, a valid receipt, and `attestation_strength=orchestrator_signed`. Distinct string IDs alone do not prove independence. GitHub Actions must never invent or rewrite the Critic judgment.

### Cryptographic orchestrator attestation

A receipt that declares `attestation_strength=orchestrator_signed` must reference `critic_orchestrator_attestation.json`.

The attestation binds the episode date, Author invocation ID, Critic invocation ID, sealed Critic Request SHA-256, final Review SHA-256, a distinct orchestrator run ID, the runtime verification record, and the process-boundary assertions that Author context was not shared and the Critic started only after the Request was sealed.

The entire attestation payload is signed with Ed25519. Verification is performed by `scripts/story-engine/validate_critic_orchestrator_attestation.py`. Only an `active` public key in `skills/nasdaq-cafe-story-engine/trust/trusted_critic_orchestrators.json` is accepted. The matching private key must remain outside this repository and outside the Author execution context.

For the built-in external runner, the runtime verification record must satisfy `critic_external_verification.schema.json`: Docker isolation, digest-pinned adapter image, repository not mounted, Critic input read-only, Author context not mounted, exit code 0, and Request/Review SHA bindings.

### External Critic operational path

This path is optional until budget and an external host are available.

Use `scripts/story-engine/run_external_critic_pipeline.py` as the provider-neutral operational entry point. Do not call the model adapter directly from Daily Production or GitHub Actions.

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

The low-level runner is `scripts/story-engine/run_external_critic_orchestrator.py`. The Critic adapter image must be pinned as `image@sha256:<digest>`. The container receives only `/critic/input` read-only and `/critic/output` writable. It receives only environment variable names explicitly allowed with `--pass-env`; the host/Author environment is not forwarded wholesale.

The adapter must read:

- `NASDAQ_CAFE_CRITIC_REQUEST=/critic/input/critic_request.json`
- `NASDAQ_CAFE_CRITIC_BUNDLE=/critic/input/bundle_manifest.json`

and write:

- `NASDAQ_CAFE_CRITIC_REVIEW_OUT=/critic/output/creative_review.json`

The private signing key must never be placed in this repository, a GitHub Actions secret used by the production renderer, the Critic input bundle, or the Author context.

### Built-in OpenAI Critic adapter

The maintained provider implementation is under `critic-adapters/openai/`.

It uses the OpenAI Responses API with Structured Outputs and defaults to `gpt-5.6`. It receives only the sealed Critic bundle, does not enable web search or tools, and emits a schema-constrained `creative_review.json`. It does **not** apply patches, sign receipts, or decide production eligibility.

Use `scripts/story-engine/run_openai_critic_pipeline.py` for the OpenAI path. It always forwards only:

- `OPENAI_API_KEY`
- `OPENAI_CRITIC_MODEL`
- `OPENAI_CRITIC_MAX_OUTPUT_TOKENS`
- `OPENAI_CRITIC_TIMEOUT_SECONDS`

The OpenAI SDK version is pinned in `critic-adapters/openai/requirements.txt` and the adapter is built in Story Engine gate CI without calling the model.

The manual `Publish OpenAI Critic Adapter` workflow builds and pushes the adapter to GHCR and emits an immutable `image@sha256:<digest>` release artifact. That workflow does not receive `OPENAI_API_KEY` and must never invoke a model.

### External signing key provisioning

When external certification is enabled in the future, generate the production Ed25519 key only on the trusted external orchestrator host:

```text
scripts/story-engine/bootstrap_external_critic_key.py
```

The bootstrap requires an encryption password from an environment variable, writes the private key with owner-only permissions, refuses any private-key path inside the repository, and prints the public trust-registry row. Commit only the public row to `trusted_critic_orchestrators.json`; never commit or upload the private key.

A self-authored JSON file, an unknown key, a revoked key, a tampered signed field, a Request/Review SHA mismatch, an invalid runtime record, or an Author/Critic ID collision must all fail closed.

GitHub Actions may verify signatures and hashes and may build/publish the model-free adapter image. It must not create the external Critic review, receive the external private signing key, create the private-key signature, rewrite the attestation, or upgrade a repository-provenance receipt to certified status.

## Pass E — Targeted Rewrite

Patch only finding-linked fields. Full regeneration is not the default. General Scene reordering is forbidden. `move_explanation_block` may move comparison or explanation only when real chronology remains unchanged.

## Pass F — Causality Preservation

Compare draft and rewrite against the Claim Ledger. Reject evidence loss, modality strengthening, counterevidence removal, chronology distortion, company-to-Nasdaq scope promotion, investment advice or invented fox history.

## Pass G — Final Re-review

Normally use one review → patch → re-review cycle. A second round is allowed only while Critical findings remain. Never exceed two rounds. If Critical findings remain, block and return to Pass A/B/C or upstream research.

## Unified production gate

The v1.1 gate requires one `story_engine_acceptance.json` bound to:

- validated causal dossier
- materialized Story Plan
- materialized Story Script
- final creative review
- sealed Critic request
- Critic execution receipt
- causality/Scene guards

The acceptance is validated by `scripts/story-engine/validate_story_engine_acceptance_v1_1.py`. It also checks that materialized Story Plan/Script differ from the reviewed templates only by deterministic lineage bindings and that the materialized review is semantically identical to the pre-authored review.

Two operating policies are supported:

1. **External Critic required** — call the validator with `--require-production`. This preserves the original strong gate and requires an Ed25519-verified `orchestrator_signed` receipt.
2. **External Critic optional** — call the validator with `--require-production --allow-uncertified-production`. All editorial, causality, Scene, hash and lineage checks still have to PASS, but production may proceed without external certification. The result must report `production_policy=external_critic_optional`, `critic_certified=false`, `external_critic_status=not_certified`, and warning `W_EXTERNAL_CRITIC_NOT_CERTIFIED` until a signed receipt exists.

The Daily Production wrapper uses policy 2. Therefore absence of a paid external Critic does not stop `causal_dossier_valid → episode_package_final`. This does not change the rule that final rendering happens only after Preview and explicit user authorization.

The legacy `production_eligible` field remains a certification signal and may remain `false` in optional mode. Use `production_allowed_by_policy` to determine whether the selected operating policy permits the transition. Never reinterpret `production_eligible=false` as evidence that the editorial package itself failed.

## Current migration status

For the committed 2026-08-06 regression fixture, the available receipt remains `repository_provenance`. Therefore:

```text
artifact / lineage validation = PASS
external Critic certification = NOT CERTIFIED
daily production policy = ALLOWED (external Critic optional)
```

The software path for a real independent Critic remains complete for future use. Do not fabricate runtime credentials or attestations.

Optional future certification sequence:

1. choose a trusted external orchestrator host;
2. retain the immutable Critic adapter image digest;
3. on that host, run `bootstrap_external_critic_key.py` and keep the encrypted private key outside the repository;
4. add only the generated public key row to `trusted_critic_orchestrators.json` and validate CI;
5. provide the model API key only to the external orchestrator process and run one real isolated Critic execution;
6. require the resulting `orchestrator_signed` receipt to pass the strict v1.1 production acceptance.

Until then, daily production continues under the explicit optional policy. Do not spend on an external Critic merely to satisfy the pipeline.

## Required artifacts

- `working/YYYY-MM-DD/story_engine_package_YYYY-MM-DD.json` for the unified editorial/provenance record when produced
- `working/YYYY-MM-DD/story-engine/story_engine_acceptance.json` for the production transition
- `episodes/YYYY-MM-DD/episode_package_YYYY-MM-DD.md`
- `verification/YYYY-MM-DD/story_engine_validation_report.json` when the unified package validator is run
- `working/YYYY-MM-DD/story-engine/templates/critic_request.json`
- `working/YYYY-MM-DD/story-engine/templates/critic_execution_receipt.json`
- `working/YYYY-MM-DD/story-engine/templates/critic_external_verification.json` when the built-in external runner is used
- `working/YYYY-MM-DD/story-engine/templates/critic_orchestrator_attestation.json` when a trusted external orchestrator is active

Run `validators/validate_story_engine_hardening.py` for the unified Story Engine package and the v1.1 receipt/acceptance validators for the production gate. Passing deterministic validators does not itself prove the story is interesting; that judgment belongs to the required 04 editorial review, the user's Preview review, and, when enabled, the optional external Independent Critic.
