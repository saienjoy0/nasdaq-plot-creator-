# Current Preview Semantic Readiness Gate Implementation Plan

**Root cause:** A `daily-production-requests/*.json` PREVIEW request can be merged before the Current Visual Intelligence semantic authoring loop is complete. Main production is intentionally compile-only, so an unresolved request reaches `run_daily_renderer_closure_v12.py --phase compile` and fails on the missing Director semantic artifact. The lower-level compile contract is behaving correctly; the missing control is a pre-merge semantic-readiness gate.

**First broken boundary:** `VISUAL_INTELLIGENCE` before Director decision; observed real run 32700865747.

**Evidence:**
- `.github/workflows/chatgpt-daily-preview-production.yml` always calls the canonical facade with `--phase compile`.
- `docs/DAILY_PRODUCTION_RUNBOOK.md` defines formal production entry as compile-only after ChatGPT semantic work is complete.
- `scripts/run_daily_renderer_closure_v12.py` intentionally requires `visual_director_decision.semantic.json` in compile mode.
- `.github/workflows/visual-intelligence-real-day-canary.yml` already has the correct authoring lifecycle: `prepare` produces Candidate Catalog; `compile` consumes AI-B decisions.
- `Validate Daily Production Package` currently treats Current-v2 as owned and skips exact-day Current closure; it also does not treat `daily-production-requests/**` as an episode-date source. Therefore PR #166 could pass generic PR checks while its main production request was not compile-ready.

**Why existing tests missed it:** Current spine tests prove that workflows route through the facade, but they do not prove that a changed PREVIEW request is semantically ready for the compile-only production lane. The existing validation workflow skips exact-day Current closure when Current-v2 owns the episode, which is precisely the case that required the readiness check.

**Goal:** Make a PREVIEW request PR itself run the existing Current facade as a non-publishing readiness check. The PR remains blocked while AI-B Director/Critic work is incomplete, but the check produces the Candidate Catalog / compiled visual evidence needed for ChatGPT to author the next semantic file. Only a PASS request can merge; main production remains compile-only and mechanical.

**Protected invariants:**
- Do not change episode facts, narration, Scene order, Visual Beat meaning, Expected/Actual/Gap, or 04 conclusions.
- Do not make GitHub Actions choose Visual Candidates or author Director/Critic semantics.
- Do not weaken compile fail-closed behavior in formal main production.
- Do not add a second Current facade or state machine.
- Do not auto-render Preview or Final in the PR readiness lane.
- Do not auto-request Final.
- Continue using exact pinned Renderer binding.
- Preserve Semantic Freeze identity.

## Current code path

```text
PR with daily-production-requests/<date>*.json
→ Validate Daily Production Package
   → Current-v2 detected
   → RUN_EXACT_DAY=false
   → generic regressions only
→ PR can merge
→ main ChatGPT Daily Preview Production
→ current_production_facade_v12.py --phase compile
→ run_semantic_frozen_renderer_closure_v12.py
→ run_daily_renderer_closure_v12.py --phase compile
→ Visual Requirements / assets pass
→ missing visual_director_decision.semantic.json
→ FAIL
```

## Working analogue

`.github/workflows/visual-intelligence-real-day-canary.yml` already expresses the legal semantic lifecycle:

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

The repair must reuse this lifecycle through `scripts/current_production_facade_v12.py`; it must not invoke the lower-level closure directly.

## Repair hypothesis

I think the root cause is the absence of a pre-merge Current semantic-readiness lane for production request PRs, because Current-v2 validation deliberately skips exact-day closure while main production is compile-only; adding a non-publishing facade-based readiness runner that selects `prepare` only when Director semantics are absent and otherwise runs `compile` should block premature merges and expose the next required AI-B action without changing production semantics.

## File map

| File | Action | Responsibility | Why this file owns the change |
|---|---|---|---|
| `scripts/current_preview_request_readiness_v12.py` | Create | PR-only readiness coordinator; parses one PREVIEW request, selects legal authoring phase, invokes canonical facade without handoff, writes actionable receipt | Keeps orchestration testable while reusing the only Current public entrypoint |
| `.github/workflows/validate-daily-production-package.yml` | Modify | Detect changed production request, run readiness coordinator on Current-v2 PRs, upload VI evidence on non-ready outcomes | This is an existing PR validation gate that already has Renderer checkout/dependencies and is expected to protect merge |
| `tests/current-spine/test_current_preview_request_readiness.py` | Create | RED/GREEN regression for request with Requirements present but Director absent; status mapping for Director/Critic pauses and PASS | Reproduces the r8 control-flow hole without depending on 2026-08-17 forever |
| `tests/current-spine/test_current_production_facade_contract.py` | Modify | Static guard that PR validation includes request paths and routes readiness only through canonical facade | Prevents future bypass/regression |
| `skills/nasdaq-cafe-daily-production/SKILL.md` | Modify | Operational rule: do not merge/create formal Preview request as ready until PR readiness reaches PASS; use Candidate/Review evidence to author semantics | Prevents agents from repeating r7/r8 request churn |
| `docs/DAILY_PRODUCTION_RUNBOOK.md` | Modify | Explicitly document pre-merge prepare/compile authoring loop and compile-only main entry | Aligns operator documentation with existing architecture |

## Task 1: Regression reproduction first

**Files:**
- Create `tests/current-spine/test_current_preview_request_readiness.py`

**Interfaces:**
- Consumes a synthetic PREVIEW request and semantic-file presence matrix.
- Exercises pure/readiness selection functions from the new coordinator.
- Produces expected phase + readiness state + required action.

### RED cases

1. Requirements present, Director absent:
   - expected selected phase: `prepare`
   - facade result: `PREPARED`
   - readiness result: `NOT_READY`
   - required action: `AUTHOR_VISUAL_INTELLIGENCE_DECISION`

2. Director present, Critic absent:
   - selected phase: `compile`
   - facade result: `REVIEW_REQUIRED`
   - readiness result: `NOT_READY`
   - required action: `AUTHOR_VISUAL_CRITIC_REVIEW`

3. Director + Critic present and facade PASS:
   - selected phase: `compile`
   - readiness result: `PASS`

4. Machine failure:
   - facade FAIL or non-zero unexpected exit
   - readiness result: `FAIL`, not a human-pause classification.

Run before implementation:

```bash
python -m pytest -q tests/current-spine/test_current_preview_request_readiness.py
```

Expected before implementation: FAIL because coordinator module/functions do not exist.

## Task 2: Add PR-only readiness coordinator

**Files:**
- Create `scripts/current_preview_request_readiness_v12.py`

**Required behavior:**

1. Inputs:
   - `--workspace`
   - `--renderer-root`
   - `--request`
   - optional `--output`
2. Parse request and validate:
   - `confirmation == PREVIEW`
   - episode date valid
   - Semantic Freeze path/date/SHA match exact bytes
3. Determine semantic phase mechanically:
   - if `working/<date>/visual-intelligence/visual_director_decision.semantic.json` is absent → `prepare`
   - otherwise → `compile`
4. Invoke only:

```text
scripts/current_production_facade_v12.py
```

No direct call to semantic wrapper, daily closure, state machine, handoff builder, or Renderer workflow.
5. Never pass `--build-handoff-on-pass`.
6. Interpret outcome:
   - `PASS` → readiness `PASS`, exit 0
   - `PREPARED` → readiness `NOT_READY`, preserve facade `requiredAction`, exit non-zero dedicated readiness code
   - `REVIEW_REQUIRED` → readiness `NOT_READY`, required action `AUTHOR_VISUAL_CRITIC_REVIEW`, exit non-zero dedicated readiness code
   - `FAIL` / missing outcome → readiness `FAIL`, exit 2
7. Write `verification/<date>/current_preview_request_readiness.json` with request path/SHA, selected phase, facade outcome path/status, required action, reason, Renderer commit, and no publication/handoff fields.

**Important:** `prepare` is used only in the PR readiness lane to materialize Candidate Catalog. Formal main production stays compile-only.

Run GREEN:

```bash
python -m pytest -q tests/current-spine/test_current_preview_request_readiness.py
```

Expected: PASS.

## Task 3: Wire readiness into the existing required PR validation lane

**Files:**
- Modify `.github/workflows/validate-daily-production-package.yml`

**Changes:**

1. Add PR path trigger:

```text
daily-production-requests/**
```

2. Include production-request filenames in exact episode-date detection.
3. Detect at most one changed production request for the episode and export:

```text
CURRENT_PREVIEW_REQUEST_PATH
RUN_CURRENT_PREVIEW_READINESS=true|false
```

4. After Renderer checkout/dependencies and generic regressions, add a Current-v2-only readiness step:

```bash
python scripts/current_preview_request_readiness_v12.py \
  --workspace . \
  --renderer-root .renderer \
  --request "$CURRENT_PREVIEW_REQUEST_PATH"
```

5. On NOT_READY, the check must block merge while still uploading:
   - `working/<date>/visual-intelligence/`
   - `verification/<date>/`
   - `render-specs/<date>/render_spec.json`

This gives ChatGPT the legal Candidate Catalog or compiled visual/warnings needed for the next semantic authoring action.
6. Do not build handoff or publish Renderer requests in this PR lane.

## Task 4: Strengthen current-spine contract tests

**Files:**
- Modify `tests/current-spine/test_current_production_facade_contract.py`

**Assertions:**

- validation workflow includes `daily-production-requests/**`;
- validation workflow invokes `scripts/current_preview_request_readiness_v12.py`;
- readiness coordinator invokes `scripts/current_production_facade_v12.py`;
- readiness coordinator does not contain direct calls to:
  - `run_semantic_frozen_renderer_closure_v12.py`
  - `run_daily_renderer_closure_v12.py`
  - `run_daily_production_v12.py`
  - handoff/publication builders;
- main `chatgpt-daily-preview-production.yml` remains `--phase compile` and remains the only publishing path.

Run:

```bash
python tests/current-spine/test_current_production_facade_contract.py
python tests/current-spine/test_current_spine_characterization.py
```

Expected: PASS.

## Task 5: Update operator/agent contract

**Files:**
- Modify `skills/nasdaq-cafe-daily-production/SKILL.md`
- Modify `docs/DAILY_PRODUCTION_RUNBOOK.md`

**Required documented sequence:**

```text
Visual Requirements semantic
→ PR readiness prepare
→ Candidate Catalog
→ ChatGPT Director semantic
→ PR readiness compile
→ REVIEW_REQUIRED + compiled visual/warnings
→ ChatGPT Critic semantic
→ PR readiness compile PASS
→ merge one formal PREVIEW request
→ main production compile-only
→ immutable handoff/publication
→ Renderer Preview
```

Explicitly state that PREPARED / REVIEW_REQUIRED are authoring checkpoints and must not cause creation of a new rN production request. Update the same PR with the required semantic artifact and let the readiness check rerun.

## Task 6: Affected-suite and exact-path verification

Run fresh:

```bash
python -m pytest -q tests/current-spine/test_current_preview_request_readiness.py
python tests/current-spine/test_current_production_facade_contract.py
python tests/current-spine/test_current_spine_characterization.py
```

Then run the relevant Current cross-repo E2E / validation workflow on the branch.

### Real incident proof

Recreate the r8 semantic state on a test branch/request:

```text
Requirements semantic present
Director semantic absent
PREVIEW request present
```

Expected after repair:

```text
PR validation: NOT_READY
selected phase: prepare
requiredAction: AUTHOR_VISUAL_INTELLIGENCE_DECISION
Candidate Catalog artifact: present
main production: not run because PR cannot merge
```

Then add Director semantic to the same PR.

Expected:

```text
PR validation reruns
selected phase: compile
status: REVIEW_REQUIRED if Critic semantic absent
compiled visual + warning report artifacts: present
requiredAction: AUTHOR_VISUAL_CRITIC_REVIEW
```

Then add Critic semantic to the same PR.

Expected:

```text
PR validation: PASS
```

Only then merge. Main production should execute compile-only and proceed beyond the former r8 boundary.

## Review / rollback

**Review focus:** no semantic authority moved into Actions; no second Current entrypoint; no publishing in PR readiness; main remains compile-only.

**Rollback:** remove readiness step/coordinator and documentation changes. No persisted production semantics, state schema, Renderer contract, or daily artifacts need migration.

**Do not implement:** changing formal compile mode to silently behave like prepare. That would blur the existing two-phase contract and hide premature production requests instead of preventing them.
