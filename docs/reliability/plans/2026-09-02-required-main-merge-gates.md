# Required Main Merge Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `nasdaq-cafe-production-reliability` as coordinator and `superpowers:test-driven-development` for source changes. Use `superpowers:verification-before-completion` before enabling repository rulesets.

**Goal:** Make Plot and Renderer `main` fail closed at repository level so request-only, implementation, and docs-only PRs cannot bypass the CI evidence appropriate to their change class, while avoiding path-filter required-check deadlocks and preventing a PR from weakening its own required gate.

**Architecture:** Each repository gets one trusted `Required Merge Gate` control plane stored on `main`. It runs on `pull_request_target`, never executes PR code, classifies the PR using GitHub PR-file metadata as data, waits for the existing path-specific `pull_request` workflows required for that change class, and writes a dedicated commit status to the PR head SHA. Repository rulesets require that status context, not the `pull_request_target` workflow check run. Because the gate workflow and checker are loaded from the protected base branch, a PR cannot change the gate that is judging that same PR. Existing path-specific workflows remain the actual test owners.

**Tech Stack:** GitHub Actions, Python 3.12 stdlib, GitHub Actions/PR/Commit Status REST APIs, GitHub repository rulesets.

**Spec:** `docs/reliability/plans/2026-09-02-current-production-reliability-closure-design.md`

## Global Constraints

- Do not make any path-filtered workflow itself a required repository status check.
- The trusted gate MUST execute only code from the base `main` commit. PR files may be inspected as API/git metadata but MUST NOT be checked out and executed in the privileged `pull_request_target` job.
- Existing workflows remain owners of their tests; the gate observes exact-head results and does not duplicate editorial/production validation.
- Docs-only PRs may pass without waiting for unrelated CI.
- Request-only PRs must still prove exactly-one append-only request through the existing request workflow.
- Unknown non-doc changes fail `UNCLASSIFIED_CHANGE`.
- A missing expected workflow is a WAITING state until the poll deadline, not an immediate failure; this prevents startup races.
- For multiple runs of one expected workflow on the same head SHA, evaluate only the newest run/attempt identity; an old success cannot mask a newer failure.
- Direct pushes, force pushes, and branch deletion on `main` are blocked after rollout.
- No routine ruleset bypass actor is configured.
- Required approving review count stays `0`; PR + required gate status remains mandatory.

---

**Root cause:** Source-level PR gates are not repository-enforced because both `main` branches currently have no active protection/ruleset. A second defect in a naive required-gate design is self-modification: a normal `pull_request` workflow executes the PR's workflow/code, so the PR could weaken the very gate intended to judge it.

**First broken boundary:** repository merge control / `GITHUB_ACTIONS` policy boundary.

**Evidence:** both repositories report `protected: false` and no rulesets. GitHub documents that `pull_request` runs PR-controlled workflow/code while `pull_request_target` runs the workflow from the trusted base repository; GitHub also permits commit statuses to be required by a ruleset.

**Why existing tests missed it:** CI validates source contracts but repository configuration lives outside Git, and there is no trusted base-branch control plane that converts path-specific CI into one repository-enforceable exact-head result.

## Current authoritative workflows to preserve

### Renderer

| Workflow name | Existing role |
|---|---|
| `Current Request Publication Gate` | exact one-file append-only Preview/Final request validation |
| `Current Preview Final Identity CI` | Preview/Final identity, restore, Final control-plane, Wake contracts |
| `Visual Story Engine CI` | Renderer/Visual Story non-media contract and build |
| `Visual Story Media CI` | media/still validation |

### Plot

| Workflow name | Existing role |
|---|---|
| `Validate Daily Production Package` | daily/current package validation + Current Preview semantic readiness |
| `Current Spine Exact Cross-Repo E2E` | exact pinned Renderer + Current semantic/VI chain |
| `Current Renderer Runtime Qualification Handoff` | exact Renderer runtime qualification and request-builder lineage |
| `Visual Intelligence v1.2` | VI contract and cross-repo acceptance |
| `Current Preview Final Request Builders CI` | Preview/Final request and authorization builders |
| `ChatGPT Daily Final Authorization` | one-file explicit Final authorization request + publication |

## Repair hypothesis

I think the merge-control gap is caused by repository policy having no trusted always-on representation of the path-specific CI contract; a base-branch `pull_request_target` gate that never executes PR code, waits for exact-head authoritative workflows, and posts one dedicated head-commit status should enforce existing CI without path-filter deadlocks or gate self-bypass.

## Required status contract

Use one dedicated commit status context in both repositories:

```text
Nasdaq Cafe Required Merge Gate
```

Status lifecycle on the PR head SHA:

```text
pending  -> gate started / waiting for required exact-head workflows
success  -> all policy-required latest runs succeeded
failure  -> classification error or an expected latest run failed
pending  -> remains pending if trusted gate is cancelled/times out before final status; merge stays blocked
```

Ruleset source restriction should select the GitHub Actions app for this status when GitHub UI permits selecting an expected source app.

## File map

### Renderer

| File | Action | Responsibility |
|---|---|---|
| `contracts/required_merge_gate_policy.json` | create | path/change-class → authoritative workflow names |
| `scripts/required_merge_gate.py` | create | pure classification + exact-head run evaluation/polling |
| `scripts/test_required_merge_gate.py` | create | race, latest-run, request-only, unknown-path regressions |
| `.github/workflows/required-merge-gate.yml` | create | trusted `pull_request_target` orchestration + status publication |
| `.github/workflows/visual-story-engine-ci.yml` | modify | add `tsconfig*.json` if absent so policy-mapped config changes get Engine CI |
| `.github/workflows/visual-story-media-ci.yml` | modify | add `public/**` so runtime visual assets get Media CI |
| `.github/workflows/current-preview-final-identity-ci.yml` | modify | include gate/checker/policy files in Current control-plane regression |

### Plot

| File | Action | Responsibility |
|---|---|---|
| `contracts/required_merge_gate_policy.json` | create | Plot path/change-class → authoritative workflow names |
| `scripts/required_merge_gate.py` | create | same public interface and state model as Renderer |
| `tests/current-spine/test_required_merge_gate.py` | create | Plot classification/result regressions |
| `.github/workflows/required-merge-gate.yml` | create | trusted `pull_request_target` gate + status publication |
| `.github/workflows/validate-daily-production-package.yml` | modify | baseline trigger covers all Plot source/test/contract/workflow/skill changes |
| `docs/reliability/repository-protection-policy.md` | create after rollout | ruleset/status evidence |

## Shared checker interfaces

Both repositories implement the same Python interface; repository differences live only in policy JSON.

```python
def load_policy(path: Path) -> dict: ...

def classify_changes(policy: dict, changes: list[dict]) -> dict:
    """changes are PR-file API records with filename/status/previous_filename."""

def select_latest_runs(expected: set[str], runs: list[dict], head_sha: str) -> dict[str, dict]:
    """For each workflow name, select newest exact-head pull_request run by (run_number, run_attempt, id)."""

def evaluate_latest_runs(expected: set[str], selected: dict[str, dict]) -> dict:
    """Return WAITING, PASS, or FAIL with stable reason code."""

def poll_expected_workflows(
    repository: str,
    head_sha: str,
    expected: set[str],
    token: str,
    *,
    request_fn,
    sleep_fn,
    monotonic_fn,
    timeout_seconds: int = 2700,
    poll_seconds: int = 10,
) -> dict: ...
```

Stable result/error codes:

```text
PASS
WAITING_FOR_WORKFLOW
WAITING_FOR_COMPLETION
MIXED_REQUEST_PR
UNCLASSIFIED_CHANGE
EXPECTED_WORKFLOW_FAILED
EXPECTED_WORKFLOW_TIMEOUT
```

`EXPECTED_WORKFLOW_MISSING` is not emitted before the deadline; a not-yet-created workflow is normal startup race and remains `WAITING_FOR_WORKFLOW`.

Only latest exact-head `conclusion == "success"` passes. `failure`, `cancelled`, `timed_out`, `action_required`, `stale`, `neutral`, or a latest completed `skipped` result fails. `queued`, `waiting`, `pending`, or `in_progress` waits.

## Policy contract

JSON shape:

```json
{
  "contractVersion": "1.0.0",
  "protectedBranch": "main",
  "statusContext": "Nasdaq Cafe Required Merge Gate",
  "docsOnlyPatterns": ["docs/**", "README.md", "CHANGELOG.md"],
  "requestOnlyGroups": [],
  "workflowGroups": [],
  "unclassifiedNonDocs": "FAIL"
}
```

`AGENTS.md` is intentionally NOT docs-only; it is policy/control-plane input and must map to authoritative CI.

Request group example:

```json
{
  "name": "renderer-final-request",
  "patterns": ["final-render-requests-v2/*.json"],
  "exactlyOneAdded": true,
  "expectedWorkflows": ["Current Request Publication Gate"]
}
```

Normal group example:

```json
{
  "name": "renderer-final-control-plane",
  "patterns": [".github/workflows/nasdaq-cafe-final-v2.yml", "scripts/restore-approved-preview-for-final.py"],
  "expectedWorkflows": ["Current Preview Final Identity CI", "Visual Story Engine CI"]
}
```

Request-only classification runs before broad workflow groups. A request file plus any second changed file is `MIXED_REQUEST_PR`.

## Task 1: RED — checker state machine and startup race

**Files:**
- Create Renderer `scripts/test_required_merge_gate.py`
- Create Plot `tests/current-spine/test_required_merge_gate.py`

- [ ] **Step 1: Renderer test cases**

```text
one handoff Preview request added -> REQUEST_ONLY + Current Request Publication Gate
one Final request added -> REQUEST_ONLY + Current Request Publication Gate
request + second file -> MIXED_REQUEST_PR
Final/Preview control-plane path -> Current Preview Final Identity CI + Visual Story Engine CI
src/** -> Visual Story Engine CI + Visual Story Media CI
public/** -> Visual Story Media CI
AGENTS.md -> Visual Story Engine CI
docs/** or README.md only -> DOCS_ONLY
unknown non-doc -> UNCLASSIFIED_CHANGE
```

- [ ] **Step 2: Exact-head/race test cases in both repositories**

Use fake run objects containing `name`, `head_sha`, `status`, `conclusion`, `run_number`, `run_attempt`, and `id`:

```text
wrong head SHA -> ignored
no run yet for expected workflow -> WAITING_FOR_WORKFLOW
queued/in_progress latest run -> WAITING_FOR_COMPLETION
old success + newer in_progress -> WAITING_FOR_COMPLETION
old success + newer failure -> EXPECTED_WORKFLOW_FAILED
old failure + newer success -> PASS for that workflow
all expected latest exact-head runs success -> PASS
missing workflow until fake monotonic deadline -> EXPECTED_WORKFLOW_TIMEOUT
```

- [ ] **Step 3: Plot classification test cases**

```text
one final-authorization request -> REQUEST_ONLY + ChatGPT Daily Final Authorization
daily-production request/data path -> Validate Daily Production Package
renderer_binding.json -> Validate Daily Production Package + Current Spine Exact Cross-Repo E2E + Current Renderer Runtime Qualification Handoff + Visual Intelligence v1.2
current Final builder -> Validate Daily Production Package + Current Preview Final Request Builders CI + Current Renderer Runtime Qualification Handoff
Visual Intelligence path -> Validate Daily Production Package + Visual Intelligence v1.2
AGENTS.md -> Validate Daily Production Package
docs/** or README.md only -> DOCS_ONLY
unknown non-doc -> UNCLASSIFIED_CHANGE
```

- [ ] **Step 4: Run RED**

Renderer:

```bash
python3 scripts/test_required_merge_gate.py
```

Plot:

```bash
PYTHONPATH=scripts python3 tests/current-spine/test_required_merge_gate.py
```

Expected: missing checker/policy import/file error. Do not create production gate code before this RED.

## Task 2: GREEN — implement policy/checker in Renderer

**Files:**
- Create `contracts/required_merge_gate_policy.json`
- Create `scripts/required_merge_gate.py`
- Complete `scripts/test_required_merge_gate.py`

- [ ] **Step 1: Renderer policy groups**

Request-only:

```text
handoff-preview-requests-v4/*.json -> Current Request Publication Gate
final-render-requests-v2/*.json -> Current Request Publication Gate
```

Current identity/control plane includes:

```text
.github/workflows/current-request-publication-gate.yml
.github/workflows/nasdaq-cafe-handoff-preview-request-v4.yml
.github/workflows/nasdaq-cafe-preview-handoff-v2.yml
.github/workflows/nasdaq-cafe-preview-status.yml
.github/workflows/nasdaq-cafe-final-request-v2.yml
.github/workflows/nasdaq-cafe-final-v2.yml
.github/workflows/nasdaq-cafe-codespace-wake.yml
.github/workflows/required-merge-gate.yml
contracts/required_merge_gate_policy.json
scripts/required_merge_gate.py
scripts/validate-current-request.py
scripts/verify-final-authorization-bundle.py
scripts/render-approved-current-final.ts
scripts/capture-preview-current-spine-identity.py
scripts/restore-approved-preview-for-final.py
scripts/wake_repository_codespace.py
scripts/test_current_*.py
scripts/test_final_*.py
scripts/test_codespace_wake_gateway.py
scripts/test_required_merge_gate.py
```

Expected: `Current Preview Final Identity CI` and `Visual Story Engine CI`.

Renderer baseline:

```text
src/**
scripts/**
contracts/**
package.json
package-lock.json
tsconfig*.json
AGENTS.md
.github/workflows/**
```

Expected: `Visual Story Engine CI`.

Media-sensitive:

```text
src/**
public/**
render-specs/**
scripts/*media*
```

Expected: `Visual Story Media CI`.

- [ ] **Step 2: Implement polling with injected HTTP/time functions**

Production API query:

```text
GET /repos/{repository}/actions/runs?head_sha={head_sha}&event=pull_request&per_page=100
```

Use pagination if `total_count > returned workflow_runs count`; do not silently ignore page 2+.

- [ ] **Step 3: Run GREEN**

```bash
python3 scripts/test_required_merge_gate.py
python3 -m py_compile scripts/required_merge_gate.py scripts/test_required_merge_gate.py
```

## Task 3: Ensure Renderer authoritative workflows cover policy paths

**Files:**
- Modify `.github/workflows/visual-story-engine-ci.yml`
- Modify `.github/workflows/visual-story-media-ci.yml`
- Modify `.github/workflows/current-preview-final-identity-ci.yml`

- [ ] Add `tsconfig*.json` to Engine CI if not already present.
- [ ] Add `public/**` to Media CI.
- [ ] Add gate policy/checker/test/workflow and `wake_repository_codespace.py`/its tests to Current Preview Final Identity CI path/syntax coverage where applicable.
- [ ] Run:

```bash
python3 scripts/test_required_merge_gate.py
python3 scripts/test_current_preview_final_identity_contract.py
npm ci
npm run typecheck
```

Require exact PR-head `Current Preview Final Identity CI`, `Visual Story Engine CI`, and `Visual Story Media CI` according to mapped paths.

## Task 4: Create trusted Renderer gate and head status publisher

**Files:**
- Create `.github/workflows/required-merge-gate.yml`

Workflow trigger/permissions:

```yaml
name: Required Merge Gate Control Plane

on:
  pull_request_target:
    branches: [main]
    types: [opened, synchronize, reopened]

permissions:
  contents: read
  pull-requests: read
  actions: read
  statuses: write
```

No `paths`/`paths-ignore`.

- [ ] **Step 1: Checkout only trusted base code**

```yaml
- uses: actions/checkout@v6
  with:
    ref: ${{ github.event.pull_request.base.sha }}
    fetch-depth: 1
    persist-credentials: false
    clean: true
```

Do NOT checkout PR head or merge ref in this privileged job.

- [ ] **Step 2: Publish pending status to exact PR head**

Use:

```bash
HEAD_SHA="${{ github.event.pull_request.head.sha }}"
gh api --method POST "repos/${GITHUB_REPOSITORY}/statuses/${HEAD_SHA}" \
  -f state=pending \
  -f context='Nasdaq Cafe Required Merge Gate' \
  -f description='Waiting for required exact-head workflows'
```

- [ ] **Step 3: Run trusted base checker**

The checker fetches changed files through the PR files REST endpoint using PR number; it never imports/executes a file from the PR head.

CLI:

```bash
python3 scripts/required_merge_gate.py \
  --policy contracts/required_merge_gate_policy.json \
  --repository "$GITHUB_REPOSITORY" \
  --pr-number "${{ github.event.pull_request.number }}" \
  --head-sha "${{ github.event.pull_request.head.sha }}"
```

Run this step with `continue-on-error: true`, id `gate`.

- [ ] **Step 4: Always publish final head status**

If `steps.gate.outcome == 'success'`, post `success`; otherwise post `failure`. Include `target_url=${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}`.

Then explicitly fail the workflow job when the checker failed so the control-plane run itself is auditable.

If the job is externally cancelled or hits timeout before the final publication, the earlier `pending` status remains and merge stays blocked.

## Task 5: Implement Plot checker/policy and trusted gate

**Files:**
- Create Plot `contracts/required_merge_gate_policy.json`
- Create Plot `scripts/required_merge_gate.py`
- Create Plot `tests/current-spine/test_required_merge_gate.py`
- Create Plot `.github/workflows/required-merge-gate.yml`
- Modify Plot `.github/workflows/validate-daily-production-package.yml`

Use the exact same checker interfaces, states, pagination, trusted `pull_request_target` pattern, and status context as Renderer.

Plot policy:

```text
final-authorization-requests-v1/*.json
  -> REQUEST_ONLY -> ChatGPT Daily Final Authorization

daily-production-requests/**
daily-authoring-parts/**
daily-authoring/**
daily-inputs/**
working/**
research/**
episodes/**
render-specs/**
daily-assets/**
  -> Validate Daily Production Package

scripts/**
tests/**
contracts/**
.github/workflows/**
skills/**
AGENTS.md
  -> Validate Daily Production Package
```

Additional exact groups preserve current triggers:

```text
contracts/renderer_binding.json and Current cross-repo entrypoints/tests
  -> Current Spine Exact Cross-Repo E2E

renderer binding/runtime qualification files
  -> Current Renderer Runtime Qualification Handoff

Visual Intelligence contracts/scripts/tests
  -> Visual Intelligence v1.2

Preview/Final request-builder/publication files/tests
  -> Current Preview Final Request Builders CI
```

- [ ] Broaden `Validate Daily Production Package` `pull_request.paths` with:

```yaml
- "scripts/**"
- "tests/**"
- "contracts/**"
- ".github/workflows/**"
- "skills/**"
- "AGENTS.md"
```

Keep existing episode/data paths.

- [ ] Run:

```bash
PYTHONPATH=scripts python3 tests/current-spine/test_required_merge_gate.py
python3 -m py_compile scripts/required_merge_gate.py tests/current-spine/test_required_merge_gate.py
```

Then require exact PR-head path-specific CI selected by the Plot policy.

## Task 6: Bootstrap verification before ruleset activation

Because the trusted gate source must already exist on `main`, rollout is two-stage:

1. merge source gate/policy/checker while repository is still unprotected, only after normal review/CI;
2. open verification PRs and observe the trusted gate/status;
3. only then activate rulesets.

Use three disposable PR classes in each repository:

```text
docs-only -> status success without waiting for unrelated CI
valid one-file request -> status pending then success after request workflow
implementation -> status pending then success after mapped workflows
```

Use one negative PR where a mapped workflow intentionally fails; required status must become `failure`. Close negative PR without merge.

Also verify self-change trust:

```text
PR modifies required-merge-gate.yml / required_merge_gate.py / policy
current gate run still checks out github.event.pull_request.base.sha
current required status is emitted by trusted base code, not PR head code
```

## Task 7: Install active `main` rulesets

One-time admin operation in both repositories:

```text
Ruleset name: current-production-main-v1
Enforcement: Active
Target: refs/heads/main
Bypass list: none
Restrict deletions: ON
Require pull request before merging: ON
Required approving reviews: 0
Require status checks: ON
Required status context: Nasdaq Cafe Required Merge Gate
Expected source app: GitHub Actions, if selectable
Require branch up to date: ON
Block force pushes: ON
```

Do not directly require any path-filtered workflow.

Verify with:

```bash
gh api repos/saienjoy0/nasdaq-plot-creator-/rulesets
gh api repos/saienjoy0/saienjoy0-nasdaq-cafe-remotion/rulesets
```

Create Plot `docs/reliability/repository-protection-policy.md` recording repository, ruleset ID/name, active state, target, required status context/source, and verification date. No secrets.

## Task 8: Negative repository-policy verification

- [ ] A failing required status prevents merge.
- [ ] A valid request-only PR can merge after request workflow + required status success even when unrelated path-filtered workflows never run.
- [ ] Ruleset/API evidence proves direct main updates and force pushes are blocked; do not force-push as a test.
- [ ] After the ruleset is active, a PR changing the gate itself is still judged by the base/main gate version that existed before that PR.

## Review / rollback

Source rollback order:

1. set ruleset Enforcement to `Evaluate` or temporarily remove the required status rule;
2. revert trusted gate/checker/policy source;
3. restore/adjust authoritative workflow triggers;
4. reactivate ruleset only after the replacement status is observed.

Never remove/rename the required status producer while an Active ruleset still requires its context.

Block rollout if:

- privileged gate executes PR code or checks out PR head;
- a PR can alter the gate used to judge that same PR;
- missing expected workflow fails immediately instead of waiting;
- an old success masks a newer exact-head run;
- unknown non-doc path passes;
- a path-filtered workflow is required directly by ruleset;
- final status context/source is not observed and verified before activation.
