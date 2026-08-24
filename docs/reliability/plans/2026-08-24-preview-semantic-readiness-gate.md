# Current Preview Semantic Readiness Gate Implementation Plan

> **For agentic workers:** implement task-by-task with test-first changes, review after each task, and fresh verification before claiming completion.

**Goal:** Prevent a formal PREVIEW request from reaching the compile-only main production lane until the Current Visual Intelligence semantic authoring loop has reached PASS.

**Architecture:** Keep `scripts/current_production_facade_v12.py` as the only public Current entrypoint. Add one PR-only, non-publishing readiness coordinator that mechanically chooses `prepare` when Director semantics are absent and `compile` once they exist, converts facade pauses into actionable PR-blocking receipts, and never creates handoff/publication output. Main production remains compile-only and fail-closed.

**Tech Stack:** Python 3.12, pytest, GitHub Actions YAML, existing Current facade, Visual Intelligence bridge 1.2.0, pinned Remotion renderer 2.4.0.

**Spec:** `docs/reliability/investigations/2026-08-24-preview-readiness-systematic-debugging.md`

## Global Constraints

- Do not change episode facts, narration, Scene order, Visual Beat meaning, Expected/Actual/Gap, or 04 conclusions.
- GitHub Actions must not choose Visual Candidates or author Director/Critic semantics.
- Do not weaken formal compile fail-closed behavior.
- Do not create a second Current facade or state machine.
- Do not publish Renderer requests or build handoff in the PR readiness lane.
- Do not auto-render Preview or Final from PR validation.
- Keep the exact pinned Renderer binding and Semantic Freeze identity.
- Keep `.github/workflows/chatgpt-daily-preview-production.yml` compile-only.

---

## Evidence baseline

Real production run `32700865747` failed at the first Visual Intelligence Director boundary with:

```text
compile phase requires AI-B visual_director_decision.semantic.json
```

PR #166 had `visual_requirements.semantic.json` and a formal PREVIEW request, but no Director semantic artifact. Its PR checks passed because Current-v2 exact-day closure was explicitly skipped and only generic regressions ran; the Daily Renderer Closure Gate log reported `RUN_EXACT_DAY=false` and `79 passed`.

The working analogue already exists in `.github/workflows/visual-intelligence-real-day-canary.yml`:

```text
prepare → Candidate Catalog → DECISION_REQUIRED
→ Director semantic
→ compile → REVIEW_REQUIRED
→ Critic semantic
→ compile → PASS
```

---

## File structure

| File | Action | Responsibility |
|---|---|---|
| `scripts/current_preview_request_readiness_v12.py` | Create | Pure PR-readiness coordinator around the canonical facade |
| `tests/current-spine/test_current_preview_request_readiness.py` | Create | TDD regression for r8-like request readiness states |
| `.github/workflows/validate-daily-production-package.yml` | Modify | Trigger and execute readiness for changed PREVIEW requests |
| `tests/current-spine/test_current_production_facade_contract.py` | Modify | Static architecture guard preventing bypass/publishing drift |
| `skills/nasdaq-cafe-daily-production/SKILL.md` | Modify | Operational contract for semantic readiness before merge |
| `docs/DAILY_PRODUCTION_RUNBOOK.md` | Modify | Human/operator sequence matching the implementation |

---

### Task 1: Create the failing readiness regression

**Files:**
- Create: `tests/current-spine/test_current_preview_request_readiness.py`

**Interfaces:**
- Consumes: `choose_phase(root: Path, date: str) -> str`
- Consumes: `classify_facade_outcome(outcome: dict) -> tuple[str, str | None]`
- Produces: executable RED tests defining the desired coordinator behavior.

- [ ] **Step 1: Write the RED tests**

Use these exact behaviors:

```python
from pathlib import Path

import current_preview_request_readiness_v12 as readiness


def test_choose_prepare_when_director_semantic_missing(tmp_path: Path):
    vi = tmp_path / "working/2026-08-17/visual-intelligence"
    vi.mkdir(parents=True)
    assert readiness.choose_phase(tmp_path, "2026-08-17") == "prepare"


def test_choose_compile_when_director_semantic_exists(tmp_path: Path):
    vi = tmp_path / "working/2026-08-17/visual-intelligence"
    vi.mkdir(parents=True)
    (vi / "visual_director_decision.semantic.json").write_text("{}\n", encoding="utf-8")
    assert readiness.choose_phase(tmp_path, "2026-08-17") == "compile"


def test_prepared_is_not_ready_and_preserves_required_action():
    state, action = readiness.classify_facade_outcome({
        "status": "PREPARED",
        "requiredAction": "AUTHOR_VISUAL_INTELLIGENCE_DECISION",
    })
    assert state == "NOT_READY"
    assert action == "AUTHOR_VISUAL_INTELLIGENCE_DECISION"


def test_review_required_maps_to_critic_action():
    state, action = readiness.classify_facade_outcome({"status": "REVIEW_REQUIRED"})
    assert state == "NOT_READY"
    assert action == "AUTHOR_VISUAL_CRITIC_REVIEW"


def test_pass_is_ready():
    state, action = readiness.classify_facade_outcome({"status": "PASS"})
    assert state == "PASS"
    assert action is None
```

- [ ] **Step 2: Run RED and verify the failure is correct**

Run:

```bash
PYTHONPATH=scripts python -m pytest -q tests/current-spine/test_current_preview_request_readiness.py
```

Expected: collection/import failure because `current_preview_request_readiness_v12.py` does not exist. Do not proceed unless the failure is caused by the missing production module rather than a typo in the test.

- [ ] **Step 3: Commit the RED test only**

```bash
git add tests/current-spine/test_current_preview_request_readiness.py
git commit -m "test: reproduce current preview readiness gap"
```

---

### Task 2: Implement the minimal PR-only readiness coordinator

**Files:**
- Create: `scripts/current_preview_request_readiness_v12.py`

**Interfaces:**
- Produces: `choose_phase(root: Path, date: str) -> str`
- Produces: `classify_facade_outcome(outcome: dict) -> tuple[str, str | None]`
- CLI consumes: `--workspace`, `--renderer-root`, `--request`, optional `--output`.
- CLI writes: `verification/<date>/current_preview_request_readiness.json`.

- [ ] **Step 1: Implement only the functions needed by the RED tests**

```python
def choose_phase(root: Path, date: str) -> str:
    director = (
        root / "working" / date / "visual-intelligence" /
        "visual_director_decision.semantic.json"
    )
    return "compile" if director.is_file() else "prepare"


def classify_facade_outcome(outcome: dict) -> tuple[str, str | None]:
    status = outcome.get("status")
    if status == "PASS":
        return "PASS", None
    if status == "PREPARED":
        return "NOT_READY", outcome.get("requiredAction") or "AUTHOR_VISUAL_INTELLIGENCE_DECISION"
    if status == "REVIEW_REQUIRED":
        return "NOT_READY", "AUTHOR_VISUAL_CRITIC_REVIEW"
    return "FAIL", None
```

- [ ] **Step 2: Run GREEN**

```bash
PYTHONPATH=scripts python -m pytest -q tests/current-spine/test_current_preview_request_readiness.py
```

Expected: all tests PASS.

- [ ] **Step 3: Add request validation and canonical-facade invocation**

The coordinator must validate:

```text
confirmation == PREVIEW
episodeDate is YYYY-MM-DD
semanticFreeze.path == semantic-freezes/<date>.json
semanticFreeze.sha256 matches the exact file bytes
```

Invoke only:

```bash
python scripts/current_production_facade_v12.py \
  --workspace <root> \
  --renderer-root <renderer> \
  closure \
  --episode-date <date> \
  --phase <prepare|compile> \
  --semantic-freeze <freeze>
```

Do **not** pass `--build-handoff-on-pass`.

- [ ] **Step 4: Write the readiness receipt**

Required shape:

```json
{
  "contractVersion": "1.0.0",
  "episodeDate": "YYYY-MM-DD",
  "requestPath": "daily-production-requests/...json",
  "requestSha256": "64-hex",
  "selectedPhase": "prepare|compile",
  "state": "PASS|NOT_READY|FAIL",
  "facadeStatus": "PASS|PREPARED|REVIEW_REQUIRED|FAIL",
  "requiredAction": null,
  "reason": null,
  "previewHandoffReady": false,
  "previewPublicationReady": false
}
```

`NOT_READY` exits with a dedicated non-zero readiness code; machine failure exits 2; PASS exits 0.

- [ ] **Step 5: Run the new test and compile-check**

```bash
PYTHONPATH=scripts python -m pytest -q tests/current-spine/test_current_preview_request_readiness.py
python -m py_compile scripts/current_preview_request_readiness_v12.py
```

Expected: PASS / exit 0.

- [ ] **Step 6: Commit**

```bash
git add scripts/current_preview_request_readiness_v12.py tests/current-spine/test_current_preview_request_readiness.py
git commit -m "feat: add current preview semantic readiness coordinator"
```

---

### Task 3: Wire readiness into PR validation without adding a second production lane

**Files:**
- Modify: `.github/workflows/validate-daily-production-package.yml`

**Interfaces:**
- Consumes changed `daily-production-requests/*.json`.
- Invokes `scripts/current_preview_request_readiness_v12.py` after renderer checkout and regressions.
- Produces uploaded readiness/VI evidence only; no handoff/publication.

- [ ] **Step 1: Extend PR path triggers**

Add:

```yaml
- "daily-production-requests/**"
- "scripts/current_preview_request_readiness_v12.py"
- "tests/current-spine/test_current_preview_request_readiness.py"
```

- [ ] **Step 2: Extend date detection**

Add this regex to the existing date-pattern tuple:

```python
r"^daily-production-requests/(\d{4}-\d{2}-\d{2})[^/]*\.json$",
```

- [ ] **Step 3: Resolve one changed PREVIEW request**

Export:

```text
CURRENT_PREVIEW_REQUEST_PATH=<path or empty>
RUN_CURRENT_PREVIEW_READINESS=true|false
```

Reject more than one changed production request in the same PR.

- [ ] **Step 4: Run the coordinator**

Add after dependency install + generic regressions:

```yaml
- name: Verify Current Preview semantic readiness
  if: env.RUN_CURRENT_PREVIEW_READINESS == 'true'
  run: |
    PYTHONPATH=scripts python scripts/current_preview_request_readiness_v12.py \
      --workspace . \
      --renderer-root .renderer \
      --request "$CURRENT_PREVIEW_REQUEST_PATH"
```

Do not call the semantic wrapper, lower-level closure, state machine, handoff builder, or publication builder directly from this step.

- [ ] **Step 5: Upload evidence even when readiness is NOT_READY**

Add an `if: always()` artifact step containing:

```text
working/<date>/visual-intelligence/
verification/<date>/
render-specs/<date>/render_spec.json
```

This is evidence for ChatGPT to author the next semantic artifact; it is not a production handoff.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/validate-daily-production-package.yml
git commit -m "ci: block preview requests until current semantics are ready"
```

---

### Task 4: Add static architecture guards

**Files:**
- Modify: `tests/current-spine/test_current_production_facade_contract.py`

**Interfaces:**
- Verifies PR validation uses the readiness coordinator.
- Verifies the coordinator uses only the canonical facade.
- Verifies main remains compile-only/publishing owner.

- [ ] **Step 1: Add assertions**

Required assertions:

```python
readiness = read("scripts/current_preview_request_readiness_v12.py")

if 'daily-production-requests/**' not in production_validation:
    raise AssertionError("PR validation does not watch production requests")
if 'scripts/current_preview_request_readiness_v12.py' not in production_validation:
    raise AssertionError("PR validation does not run Current readiness")
if 'scripts/current_production_facade_v12.py' not in readiness:
    raise AssertionError("readiness bypasses canonical facade")
for forbidden in (
    "run_semantic_frozen_renderer_closure_v12.py",
    "run_daily_renderer_closure_v12.py",
    "run_daily_production_v12.py",
    "build_current_preview_publication.py",
):
    if forbidden in readiness:
        raise AssertionError(f"readiness contains forbidden lower-level owner: {forbidden}")
if "--phase compile" not in production:
    raise AssertionError("main production is no longer compile-only")
```

Adapt variable names to the existing test file; do not restructure unrelated assertions.

- [ ] **Step 2: Run architecture guards**

```bash
python tests/current-spine/test_current_production_facade_contract.py
python tests/current-spine/test_current_spine_characterization.py
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/current-spine/test_current_production_facade_contract.py
git commit -m "test: guard current preview readiness architecture"
```

---

### Task 5: Align agent and operator contracts

**Files:**
- Modify: `skills/nasdaq-cafe-daily-production/SKILL.md`
- Modify: `docs/DAILY_PRODUCTION_RUNBOOK.md`

**Interfaces:**
- Documents the same legal lifecycle as the code.
- Prevents agents from generating rN+1 production requests merely because a semantic checkpoint was reached.

- [ ] **Step 1: Document this exact sequence**

```text
Visual Requirements semantic
→ PR readiness prepare
→ Candidate Catalog
→ ChatGPT Director semantic
→ PR readiness compile
→ REVIEW_REQUIRED + compiled visual/warnings
→ ChatGPT Critic semantic
→ PR readiness compile PASS
→ merge the same formal PREVIEW request
→ main production compile-only
→ immutable handoff/publication
→ Renderer Preview
```

- [ ] **Step 2: Add the no-request-churn rule**

Document explicitly:

```text
PREPARED and REVIEW_REQUIRED are semantic authoring checkpoints, not failed production attempts.
Do not create a new rN production request for these checkpoints; update the same PR with the required semantic artifact and rerun readiness.
```

- [ ] **Step 3: Commit**

```bash
git add skills/nasdaq-cafe-daily-production/SKILL.md docs/DAILY_PRODUCTION_RUNBOOK.md
git commit -m "docs: define pre-merge current semantic readiness loop"
```

---

### Task 6: Verify the exact incident path before completion

**Files:**
- No new production files required.
- Uses the changed tests/workflow and a test PR state.

**Interfaces:**
- Proves the former r8 state cannot merge into the formal compile-only lane.

- [ ] **Step 1: Run fresh local/CI regression commands**

```bash
PYTHONPATH=scripts python -m pytest -q tests/current-spine/test_current_preview_request_readiness.py
python tests/current-spine/test_current_production_facade_contract.py
python tests/current-spine/test_current_spine_characterization.py
```

Expected: all PASS.

- [ ] **Step 2: Recreate the r8 semantic state on a test PR**

State:

```text
Requirements semantic present
Director semantic absent
PREVIEW request present
```

Expected readiness receipt:

```text
state=NOT_READY
selectedPhase=prepare
requiredAction=AUTHOR_VISUAL_INTELLIGENCE_DECISION
Candidate Catalog exists
no handoff
no publication
```

The PR must remain blocked.

- [ ] **Step 3: Add Director semantic to the same PR**

Expected:

```text
selectedPhase=compile
state=NOT_READY
facadeStatus=REVIEW_REQUIRED
requiredAction=AUTHOR_VISUAL_CRITIC_REVIEW
compiled visual exists
warning report exists
```

- [ ] **Step 4: Add Critic semantic to the same PR**

Expected:

```text
state=PASS
facadeStatus=PASS
```

Only now may the PREVIEW request merge.

- [ ] **Step 5: Verify formal main production**

After merge, main must still execute:

```text
current_production_facade_v12.py --phase compile
```

and must proceed beyond the former Director-missing boundary into immutable handoff/publication. Continue verification to Preview; if a new first broken boundary appears, return to systematic debugging instead of claiming the pipeline fixed.

- [ ] **Step 6: Review before merge**

Review specifically for:

```text
no AI choice in Actions
no second Current entrypoint
no lower-level bypass
no handoff/publication in PR readiness
main remains compile-only
same-PR semantic progression
```

- [ ] **Step 7: Completion evidence**

Do not claim fixed until fresh evidence shows:

```text
new regression PASS
affected Current-spine tests PASS
r8-like PR blocked before merge
Director/Critic semantic progression works on same PR
readiness PASS permits merge
main compile passes former boundary
Preview reached or next first broken boundary identified
```

## Rollback

Remove the readiness coordinator, its PR-validation step, contract-test assertions, and documentation changes. No episode semantic artifacts, production state schema, Renderer contract, or Formal Preview/Final identity require migration.

## Explicit non-solution

Do **not** change `run_daily_renderer_closure_v12.py --phase compile` to silently act like `prepare` when Director semantic is missing. That would hide a premature formal production request and blur the established semantic ownership boundary instead of preventing the invalid request from merging.
