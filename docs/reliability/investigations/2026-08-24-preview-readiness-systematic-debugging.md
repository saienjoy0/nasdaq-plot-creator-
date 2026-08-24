# Preview Readiness Systematic Debugging Record

## Scope

Apply the `systematic-debugging` protocol to the 2026-08-17 Current Preview failure before proposing implementation changes.

## Phase 1 — Root Cause Investigation

### 1. Read the real error

Real production run: `32700865747`.

First failed production step: `Run canonical current production facade`.

Terminal error:

```text
compile phase requires AI-B visual_director_decision.semantic.json
```

The same run successfully passed the earlier Current boundaries through `assets_resolved`; Remotion/TTS were never reached.

### 2. Reproduce consistently

The production request merged by PR #166 contained:

- a PREVIEW request for `2026-08-17`;
- the exact existing Semantic Freeze identity;
- `visual_requirements.semantic.json`;
- no `visual_director_decision.semantic.json`.

Main production is deterministic and invokes `current_production_facade_v12.py ... --phase compile`, so that repository state deterministically reaches the missing-Director condition.

### 3. Check recent changes

PR #166 explicitly says GitHub Actions should materialize Requirements and the legal Candidate Catalog but should not choose the Director result. The PR nevertheless added the formal PREVIEW request in the same change. That allowed a request to merge before the semantic authoring lifecycle was complete.

### 4. Gather evidence across component boundaries

Observed boundary status:

```text
PR content                         requirements present, director absent
PR validation                     success
Daily Renderer Closure Gate       success
Exact-day Current-v2 closure      skipped
main Preview Production           started
Current facade                    compile
Requirements / asset preparation  PASS
Director semantic boundary        missing
Renderer/TTS/Remotion              not reached
```

The PR-side `Daily Renderer Closure Gate` log explicitly set:

```text
RUN_EXACT_DAY=false
Legacy exact-day closure skipped: 2026-08-17 is owned by the current-v2 semantic/Visual Intelligence path.
```

It then ran 79 regression tests, all passing. Therefore the successful PR check did not exercise the same Current-v2 exact-day boundary that failed after merge.

### 5. Trace data/control flow backward

Failure site:

```text
run_daily_renderer_closure_v12.py --phase compile
→ requires working/<date>/visual-intelligence/visual_director_decision.semantic.json
```

Caller:

```text
current_production_facade_v12.py
```

Production caller:

```text
.github/workflows/chatgpt-daily-preview-production.yml
→ always uses --phase compile
```

Contract/documentation confirms this is intentional: formal main Preview production is compile-only after ChatGPT semantic authoring is complete.

Therefore the bad state originates earlier: a formal PREVIEW request is permitted to merge before Director/Critic semantic readiness has reached PASS.

## Phase 2 — Pattern Analysis

### Working reference

`.github/workflows/visual-intelligence-real-day-canary.yml` already models the legal lifecycle:

```text
prepare
→ Candidate Catalog
→ DECISION_REQUIRED
→ AI-B Director semantic
→ compile
→ REVIEW_REQUIRED
→ AI-B Critic semantic
→ compile
→ PASS
```

### Broken path

```text
Requirements semantic
→ formal PREVIEW request merged
→ main compile
→ missing Director
→ FAIL
```

### Meaningful differences

1. Canary exposes `prepare` and `compile`; main correctly exposes only formal `compile`.
2. PR validation skips exact-day Current-v2 closure.
3. PR validation therefore cannot surface Candidate Catalog / Review evidence as a merge-blocking semantic checkpoint.
4. A production request can be committed before the semantic loop reaches PASS.
5. Static Current-spine tests prove routing through the facade, but not semantic readiness of a request about to enter the compile-only lane.

## Phase 3 — Single Hypothesis

> The root cause is the missing pre-merge Current Preview semantic-readiness gate: Current-v2 PR validation skips the exact-day Current boundary while main production is intentionally compile-only, so a PREVIEW request can merge before Director/Critic semantic artifacts are complete.

### Minimal falsification test

Create a PR-state fixture with:

```text
Requirements present
Director absent
PREVIEW request present
```

Expected current behavior: PR checks can pass.

Expected repaired behavior: PR readiness returns `NOT_READY`, runs the canonical facade in `prepare`, exposes `AUTHOR_VISUAL_INTELLIGENCE_DECISION`, and blocks merge without publishing/handoff.

If adding only this readiness lane fails to prevent the real state from reaching main, the hypothesis is wrong and investigation must return to Phase 1.

## Phase 4 — Implementation constraint

Do not change formal compile semantics to silently behave like prepare. The lower-level compile failure is correct and fail-closed.

Implementation must:

- keep main production compile-only;
- reuse `current_production_facade_v12.py` as the sole public Current entry;
- add no second state machine;
- add no semantic choice to GitHub Actions;
- run a PR-only non-publishing readiness loop;
- use TDD: failing request-readiness regression first;
- prove the exact r8 state is blocked pre-merge after repair.

The concrete implementation plan is `docs/reliability/plans/2026-08-24-preview-semantic-readiness-gate.md`.
