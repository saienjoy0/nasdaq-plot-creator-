# Current-v2 04 Inquisition Heading Projection Repair Implementation Plan

**Root cause:** Current-v2 `scripts/materialize_daily_episode.py::_run_current_v2` normalizes Scene headings but does not apply the already-established legacy normalization from `fixup_chatgpt_daily_materialization.normalize_public_package` that converts `## 04による興味深さ・わかりやすさ審問結果` into the canonical `## H. 04 興味深さ・わかりやすさ審問結果`; therefore the episode-memory hardening gate sees zero canonical inquisition sections even though the section body is present.

**First broken boundary:** `EPISODE_PACKAGE` — Validate Daily Production Package run `32750858038`, job `97507215078`, Current Preview readiness → `build-production` → episode-memory pre-build gate.

**Evidence:** The real 2026-08-17 Current path reaches Visual Intelligence `PASS`, advances through `visual_intelligence_valid`, `episode_package_final`, and `memory_usage_valid`, then fails with `E_PACKAGE_MISMATCH: final episode package must contain exactly one integrated '04 興味深さ・わかりやすさ審問結果' section: found=0`. The run artifact's final episode package contains `## 04による興味深さ・わかりやすさ審問結果` before the memory annex. The hardening validator accepts the canonical heading form and the legacy fixup already performs the exact required mechanical normalization.

**Why existing tests missed it:** Existing memory-hardening tests exercise canonical/synthetic headings, while current-v2 materializer tests verify routing and semantic-authority separation but do not assert the final human-package heading normalization. The legacy path has the normalization; current-v2 bypasses that helper. The real-day path therefore exposed a projection-parity gap not covered by synthetic fixtures.

**Goal:** Preserve the complete 04 review content and all frozen semantics while mechanically canonicalizing the one heading expected by the existing hardening contract, so the same immutable 2026-08-17 PREVIEW request passes the episode-memory pre-build boundary.

**Cascade status:** `CASCADE_DETECTED`. Architecture review result: ownership remains correct. The defect is a projection parity gap at the current-v2 episode-package materializer; no second facade, validator chain, or workflow gate is required.

**Protected invariants:**

- Do not alter 01–04 editorial meaning or the 04 review body.
- Do not alter narration, Scene order, Visual Beat meaning, telops, numbers, sources, Candidate choices, Director decision, or Critic verdict.
- Do not change Semantic Freeze identity or reseal editorial authority for a Markdown-format normalization.
- Keep GitHub Actions mechanical; no semantic inference in Actions.
- Do not weaken or bypass the episode-memory hardening validator.
- Do not create a second Current facade/state machine.
- Do not change the pinned Renderer binding.
- Do not trigger or authorize Final; requested scope remains PREVIEW.

## Current code path

```text
.github/workflows/validate-daily-production-package.yml
→ scripts/current_preview_request_readiness_v12.py
→ scripts/current_production_facade_v12.py
→ scripts/run_semantic_frozen_renderer_closure_v12.py
→ scripts/run_daily_renderer_closure_v12.py
→ scripts/materialize_daily_episode.py::_run_current_v2
→ episodes/<date>/episode_package_<date>.md
→ scripts/run_daily_production_v12.py build-production
→ skills/nasdaq-cafe-episode-package-memory/validators/validate_episode_package_memory_hardening.py
```

The broken value is introduced when `_run_current_v2` copies the contract package through `normalize_scene_headings(...)` into the final human package without normalizing the 04 heading.

## Working analogue

`scripts/fixup_chatgpt_daily_materialization.py::normalize_public_package` already owns the legacy mechanical rule:

```text
## 04による興味深さ・わかりやすさ審問結果
→
## H. 04 興味深さ・わかりやすさ審問結果
```

It also fails closed when neither legacy nor canonical heading is present. Current-v2 should use the same rule at package projection time rather than changing the hardening contract.

## Repair hypothesis

I think the missing current-v2 heading normalization is the root cause because the real artifact contains the complete 04 section under the legacy heading while the hardening regex requires the canonical heading, and adding the same deterministic legacy-to-canonical normalization to the current-v2 package normalizer should make the real pre-build gate pass without changing protected semantics.

## File map

| File | Action | Responsibility | Why this file owns the change |
|---|---|---|---|
| `docs/reliability/plans/2026-08-25-current-v2-inquisition-heading.md` | create | Record evidence-first repair design | Reliability Skill requires a reviewable plan before code changes |
| `tests/current-spine/test_structured_machine_authority_v12.py` | modify | RED regression for current-v2 human-package formatting | This Current-spine test is in the targeted CI path and can prove the materializer performs only mechanical heading normalization |
| `scripts/materialize_daily_episode.py` | modify | Apply canonical 04 heading normalization in the existing current-v2 human-package normalization path | This file creates the failing final package and already normalizes Scene headings |

## Task 1: Regression reproduction

Add a regression that feeds `normalize_scene_headings` a current-v2-style package fragment containing both a legacy Scene heading and `## 04による興味深さ・わかりやすさ審問結果`.

Expected before repair (RED): Scene heading normalizes but the 04 heading remains legacy, so the assertion requiring exactly one canonical `## H. 04 興味深さ・わかりやすさ審問結果` fails.

Expected after repair (GREEN): both heading normalizations occur, body text remains byte-for-byte unchanged, and the legacy 04 heading no longer remains.

Protected negative case: no review body synthesis; the helper must only rename the heading. Missing both recognized 04 heading forms must remain fail-closed when used for current-v2 final package projection.

## Task 2: Minimal owning-layer repair

Extend the existing current-v2 package heading normalizer in `scripts/materialize_daily_episode.py` with the same legacy/canonical constants and one deterministic replacement used by the working legacy analogue. Do not change the validator or any editorial artifact.

## Task 3: Affected-suite and Current E2E verification

Verification order:

1. **RED:** Current Spine PR-5 Targeted Validation fails the new regression on the test-only commit for the legacy 04 heading.
2. **GREEN:** After the materializer patch, the same regression passes.
3. **SUITE:** Current Spine PR-5 Targeted Validation, Current Spine Exact Cross-Repo E2E, Visual Intelligence integrity, and package/memory hardening affected tests pass.
4. **REAL-DAY E2E:** Re-run the exact 2026-08-17 PREVIEW readiness path. It must pass the episode-memory pre-build gate and continue to immutable Preview handoff or reveal the next first broken boundary.
5. Continue DIAGNOSE → REPAIR_DESIGN → REPAIR → VERIFY for any newly exposed first boundary until Preview MP4 is produced.

## Review / rollback

Review the diff for exactly one behavioral change: canonicalization of the 04 heading in the existing current-v2 human-package projection. If narration, review content, render data, Semantic Freeze, Director/Critic authority, or validator logic changes, reject the diff. Rollback is a two-file revert (test + materializer); no data migration is required.
