# NASDAQ Cafe project recovery implementation plan

**Root cause:** Runtime changes were qualified independently from the human authoring specification and current-state navigation. Renderer lint was omitted from CI, so 30 errors and three warnings remained invisible behind green functional gates.
**First broken boundary:** Authoring-to-runtime policy, followed independently by the required Renderer lint gate.
**Evidence:** Plot main `9c0b51a6ed15f51094b2c89a47a101ff2442fe83`; bound Renderer `536fbe8a139b2fa9f89cd9c76e9db71fa889c02e`; canon03 requires 480–540 seconds and `gemini-3.1-flash-tts-preview`, while `scripts/duration-policy.ts` accepts standard 180–420 seconds and both production voice profiles use `gemini-3.8-flash-tts` / Charon. Fresh baseline: 99 Plot tests and 25 subtests pass, exact-pinned cross-repository E2E passes, Renderer lint reports 30 errors / 3 warnings.
**Why existing tests missed it:** Canon tests prove integrity, not agreement with the pinned Renderer policy. The exact cross-repository test proves machine contracts without reading the authoring duration/model policy. Renderer CI typechecks and builds but never runs lint.
**Goal:** Restore consistent authoring instructions, zero-diagnostic Renderer lint, and evidence-based project navigation under the existing production architecture.

## Protected invariants

- One Current Plot facade; Current Preview V4 and explicit Final V2 remain authoritative.
- Nine Scenes, unchanged market-causality standards, evidence, narration, visual meaning, fox, background, Charon voice and two TTS blocks.
- No dependency or runtime-model changes. Align canon03 with the already-adopted runtime; do not change the runtime to match stale prose.
- Never alter existing episode packages, sealed freezes, historical approvals, bundles or requests.
- No automatic Final/publication, no invented human approval or audience measurements.
- No new Skills, secondary state machines or inferred causal relationships.

## Current code path and working analogue

`source-of-truth/canon_manifest.json` → materialized canon03 → human/ChatGPT authoring → Current facade → exact-bound Renderer → `duration-policy.ts` and `config/voice-profiles.json` → Preview → human review → explicit Final.

The existing Canon02 update demonstrates intentional packed-canon versioning without rewriting historical freezes. Existing exact-pinned E2E already resolves the Renderer binding and checks Registry identity. Extend that same qualification boundary rather than create another production fixture or authority.

## Approaches

| Option | Effect | Decision |
|---|---|---|
| Change Renderer back to the old model and 8–9 minutes | Changes adopted production behavior and cache identity | Reject |
| Document the mismatch only | Leaves authors producing input that cannot pass Final | Reject |
| Align canon03 and qualify it against the bound runtime | Repairs the owning input contract and prevents recurrence | Select |

## File map

| Repository / file | Responsibility |
|---|---|
| Plot `tests/current-spine/run_exact_cross_repo_current_e2e.py` | Compare decoded canon03 with duration/model/voice policy from the exact bound Renderer before exercising existing E2E |
| Plot `source-of-truth/packed/03_episode_production_spec/part-*.b64` and canon manifest | Version canon03 as 2.6.0, use 200–400-second writing target, 180–420-second standard acceptance and sub-180-second shortened mode; align scene writing budgets and model |
| Plot `tests/canon-manifest/test_canon_manifest.py` | Deliberately update only canon03 byte/hash snapshot |
| Plot Current E2E workflow | Requalify on canon changes, not only implementation changes |
| Plot required merge-gate policy and Current Spine regression tests | Require successful E2E for canon-only changes and reject contradictory authoring directives, including Japanese-adjacent model tokens |
| Renderer lint-flagged files | Replace explicit `any` with existing structural types, remove unused bindings and redundant escapes; preserve runtime behavior |
| Renderer Visual Story CI workflow | Run lint with zero-warning policy before functional gates |
| Plot README, current-state roadmap, programme validation receipt | Replace obsolete PR-8-era status with observed implementation, real media evidence, active/pending work and exact next boundaries |

## Task 1: Authoring/runtime regression and repair

- [x] Add `verify_authoring_runtime_policy(renderer_root)` to the existing exact-pinned E2E. Derive the production model/voice from both profiles and accepted seconds from `duration-policy.ts`; decode canon03 through the existing canon manifest.
- [x] Run exact E2E on baseline. Expected RED: authoring policy has the wrong model/range, before any synthetic production proceeds.
- [x] Update canon03 prose, model references, writing-budget table and standard/shortened rules. Repack using deterministic gzip and the existing ordered physical parts; update manifest SHA/rawBytes and the intentional snapshot.
- [x] Add `source-of-truth/**` to the existing exact E2E workflow trigger and required merge-gate classification.
- [x] Run canon verifier, canon tests, affected suite and exact-pinned E2E. Final result: 109 test cases / 28 subtests and exact E2E PASS, with explicit authoring/runtime result in the existing receipt.
- [x] Reproduce and repair independent-review gaps: contradictory voice/range directives, Japanese-adjacent model tokens, failed E2E on canon-only changes, and Scene-table total. Preserve the 200–400-second global writing target while accurately stating the illustrative table sum of 200–340 seconds.

## Task 2: Renderer required lint repair

- [x] Reproduce the existing lint failure: 30 errors and 3 warnings.
- [x] Use `RenderSpec` / `RenderSpecScene` for legacy migration annotations and structural unknown-safe types for the Final adapter. Preserve all validation and render settings.
- [x] Keep existing bundle hash/path checks, test assertions and preflight outputs byte-equivalent. Fix only redundant escaping, unused properties, repeated-space regex spelling and the placement of non-render fixture keys falsely flagged by the animation lint rule.
- [x] Make the existing Visual Story CI run `npx eslint src scripts --max-warnings=0` alongside its existing typecheck. No lint rules, source paths or assertions may be disabled.
- [x] Run zero-warning lint, typecheck, spec/public-screen/handoff tests, Visual Story tests and build. Compare the modified migration output with baseline for the same temporary fixture.

## Task 3: Current status and unresolved boundaries

- [x] Preserve the old roadmap in Git history and replace the main navigation with the current production path and a maintained status table.
- [x] Record that programme causal-graph/subtitle fixes merged on 3 October; synthetic E2E does not establish episode quality.
- [x] Record latest Collector success separately from Renderer queue polls: run `39048732981` resolves an empty Motion Preview queue; its render/wake/outcome jobs are skipped, so it proves no MP4 generation.
- [x] Inventory open PRs. Do not merge duplicate Skill owners or partially implemented schema 2.5 proposals merely because they are green. Semantic-scope rollout and variable scene-count remain separate versioned migrations.
- [x] State the exact next production boundary: newly authored canon-compatible package, actual Preview, user visual review, audience evidence when available.

## Verification and rollback

Run the same public qualification and required Renderer checks that own each repair. A fresh independent review must inspect the actual diffs and red/green evidence before merge. Keep Renderer lint-only changes independent from the Plot canon change so the exact production pin need not move for the input-contract repair. Revert either repair atomically through a normal reviewed PR; never edit a historical request to manufacture compatibility.

## Material risks

- Canon03 hash intentionally changes; newly authored freezes must use the new manifest. Historical sealed identity must continue to validate against its issuance-time evidence.
- Local deployed production model/voice is preserved; live provider availability is not established by static checks.
- Audience quality, live TTS, actual post-repair Preview and human appearance approval remain unassessed until those steps actually run.
- Stale open PRs and the installed aggregate production skill are not production authority over the explicitly authoritative repository contracts.
