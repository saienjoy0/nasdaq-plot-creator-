# Required Main Merge Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `nasdaq-cafe-production-reliability` as coordinator and `superpowers:test-driven-development` for source changes. Use `superpowers:verification-before-completion` before enabling repository rulesets.

**Goal:** Make Plot and Renderer `main` fail closed at repository level so request-only PRs, implementation PRs, and docs-only PRs cannot bypass the CI evidence appropriate to their change class, while avoiding GitHub path-filter required-check deadlocks.

**Architecture:** Add one always-on `Required Merge Gate` workflow to each repository. A repository-specific policy JSON maps changed paths to existing authoritative workflow names; the gate polls GitHub Actions runs for the PR head SHA and requires all expected workflows to finish successfully. Unclassified non-document changes fail closed. After the gate has proven a stable check context, install an active repository ruleset on `main` requiring PRs and only that always-on gate; keep existing path-filtered workflows as the actual test owners.

**Tech Stack:** GitHub Actions, Python 3.12 stdlib, GitHub Actions REST API, GitHub repository rulesets.

**Spec:** `docs/reliability/plans/2026-09-02-current-production-reliability-closure-design.md`

## Global Constraints

- Do not make any path-filtered workflow itself a required repository status check.
- Existing workflows remain the owners of their tests; the new gate observes their result and must not reimplement production validation logic.
- Docs-only PRs may pass with gate-local syntax/diff hygiene only.
- Request-only PRs must still prove exactly-one append-only request through the existing request workflow.
- Any non-doc change that matches no policy group must fail `UNCLASSIFIED_CHANGE`, not silently pass.
- Direct pushes, force pushes, and branch deletion on `main` must be blocked after rollout.
- No ruleset bypass actors are configured for routine use.
- Required approving review count stays `0` so the single-owner repository can continue using PRs without requiring an artificial second reviewer; PR + required status check remains mandatory.
- Repository protection configuration is applied only after the gate succeeds on a test PR in each repository.

---

**Root cause:** Source-level PR gates are not repository-enforced because both `main` branches currently have no active branch protection/ruleset, so direct updates or a merge that ignores failed optional checks can bypass the intended reliability contract.

**First broken boundary:** repository merge control / `GITHUB_ACTIONS` policy boundary.

**Evidence:** both repository branch metadata reported `protected: false`; both `/rulesets` collections were empty.

**Why existing tests missed it:** CI validates source contracts but repository configuration lives outside Git. No always-on check currently represents “all CI required for this exact PR class passed,” and no ruleset enforces such a check.

## GitHub behavior that constrains the design

GitHub documents that when a workflow is skipped by `paths`, `branches`, or commit-message filtering, a required check can remain Pending and block merging. Therefore the current path-filtered workflows MUST NOT be required directly. The required check must come from a workflow that runs on every PR to `main`.

## Current authoritative workflows to preserve

### Renderer

| Workflow name | Job evidence | Existing role |
|---|---|---|
| `Current Request Publication Gate` | `validate-request-only-pr` | exact one-file append-only Preview/Final request validation |
| `Current Preview Final Identity CI` | `contract` | Preview/Final identity, restore, control-plane and Wake contracts |
| `Visual Story Engine CI` | `contract-and-build` | Renderer/Visual Story non-media contract and build |
| `Visual Story Media CI` | `media` | media/still validation |

### Plot

| Workflow name | Job evidence | Existing role |
|---|---|---|
| `Validate Daily Production Package` | `validate` | daily/current package validation + Current Preview semantic readiness |
| `Current Spine Exact Cross-Repo E2E` | `exact-current-e2e` | exact pinned Renderer + Current semantic/VI chain |
| `Current Renderer Runtime Qualification Handoff` | `build-fresh-handoff` | exact Renderer runtime qualification and request-builder lineage |
| `Visual Intelligence v1.2` | `cross-repo` | VI contract and cross-repo acceptance |
| `Current Preview Final Request Builders CI` | `contract` | Preview/Final request and authorization builders |
| `ChatGPT Daily Final Authorization` | `authorize` | one-file explicit Final authorization request + publication |

## Repair hypothesis

I think the merge-control gap is caused by repository policy having no stable always-on representation of the path-specific CI contract; adding a policy-driven always-on observer check and making that single check mandatory should enforce the existing tests without duplicating them or deadlocking PRs whose path-filtered workflows correctly do not run.

## File map

### Renderer repository

| File | Action | Responsibility |
|---|---|---|
| `contracts/required_merge_gate_policy.json` | create | change-class → expected workflow names; docs/request/core mappings |
| `scripts/required_merge_gate.py` | create | classify changed files, poll Actions runs for exact head SHA, fail closed |
| `scripts/test_required_merge_gate.py` | create | pure regression tests for classification and workflow-result evaluation |
| `.github/workflows/required-merge-gate.yml` | create | always-on PR workflow that invokes policy checker |
| `.github/workflows/visual-story-engine-ci.yml` | modify only if needed | broaden baseline path coverage so every non-doc/non-request Renderer code change has at least one authoritative workflow |
| `.github/workflows/current-preview-final-identity-ci.yml` | modify | include gate-policy source in identity regression when Final/Preview control-plane mapping changes |

### Plot repository

| File | Action | Responsibility |
|---|---|---|
| `contracts/required_merge_gate_policy.json` | create | Plot change-class → expected workflow names |
| `scripts/required_merge_gate.py` | create | same interface as Renderer, Plot-specific policy data |
| `tests/current-spine/test_required_merge_gate.py` | create | Plot policy/classification regression |
| `.github/workflows/required-merge-gate.yml` | create | always-on PR workflow |
| `.github/workflows/validate-daily-production-package.yml` | modify | broaden baseline code-path trigger to cover previously unclassified `scripts/**`, `tests/**`, `contracts/**`, `.github/workflows/**`, `skills/**` changes |
| `docs/reliability/repository-protection-policy.md` | create | exact ruleset names/check contexts/verification evidence after rollout |

## Shared policy contract

Both repositories use the same JSON schema shape, with repository-specific patterns:

```json
{
  "contractVersion": "1.0.0",
  "protectedBranch": "main",
  "requiredGateWorkflow": "Required Merge Gate",
  "docsOnlyPatterns": ["docs/**", "*.md"],
  "requestOnlyGroups": [],
  "workflowGroups": [],
  "unclassifiedNonDocs": "FAIL"
}
```

Each `requestOnlyGroups[]` object contains:

```json
{
  "name": "renderer-final-request",
  "patterns": ["final-render-requests-v2/*.json"],
  "exactlyOneAdded": true,
  "expectedWorkflows": ["Current Request Publication Gate"]
}
```

Each `workflowGroups[]` object contains:

```json
{
  "name": "current-final-control-plane",
  "patterns": [".github/workflows/nasdaq-cafe-final-v2.yml", "scripts/restore-approved-preview-for-final.py"],
  "expectedWorkflows": ["Current Preview Final Identity CI"]
}
```

A changed path may match multiple workflow groups; expected workflow names are the set union.

## Task 1: RED — prove unprotected/path-filtered CI cannot be used directly as the required contract

**Files:**
- Create Renderer `scripts/test_required_merge_gate.py`
- Create Plot `tests/current-spine/test_required_merge_gate.py`

**Interfaces:** tests initially expect missing `contracts/required_merge_gate_policy.json` and `scripts/required_merge_gate.py`.

- [ ] **Step 1: Add pure policy test fixtures**

Each repository test creates temporary changed-file sets and asserts these behaviors through functions that will later be implemented:

```python
classify_changes(policy, [("A", "path")]) -> {
    "class": "REQUEST_ONLY" | "DOCS_ONLY" | "CODE",
    "expected_workflows": tuple[str, ...],
}

evaluate_workflow_runs(expected, runs, head_sha) -> None
```

Required cases:

```text
Renderer one Preview request added -> REQUEST_ONLY + Current Request Publication Gate
Renderer one Final request added -> REQUEST_ONLY + Current Request Publication Gate
Renderer request + any second file -> FAIL mixed-request PR
Renderer Final control-plane file -> CODE + Current Preview Final Identity CI
Renderer src/media file -> CODE + Visual Story Engine CI and Visual Story Media CI
Renderer unknown non-doc file -> UNCLASSIFIED_CHANGE
Renderer docs-only -> DOCS_ONLY + no external workflow

Plot one final-authorization request added -> REQUEST_ONLY + ChatGPT Daily Final Authorization
Plot daily-production request -> CODE/REQUEST class + Validate Daily Production Package
Plot renderer_binding.json -> Validate Daily Production Package + Current Spine Exact Cross-Repo E2E + Current Renderer Runtime Qualification Handoff + Visual Intelligence v1.2
Plot Final builder script -> Validate Daily Production Package + Current Preview Final Request Builders CI + Current Renderer Runtime Qualification Handoff
Plot unknown non-doc file -> UNCLASSIFIED_CHANGE
Plot docs-only -> DOCS_ONLY

workflow run for wrong head SHA -> ignored
expected workflow missing -> fail
expected workflow queued/in_progress -> wait/not-success state
expected workflow conclusion failure/cancelled/timed_out -> fail
all expected workflow runs for exact head SHA success -> pass
```

- [ ] **Step 2: Run RED**

Renderer:

```bash
python3 scripts/test_required_merge_gate.py
```

Plot:

```bash
PYTHONPATH=scripts python3 tests/current-spine/test_required_merge_gate.py
```

Expected: import/file-not-found failure because the gate/policy do not exist.

## Task 2: Implement the policy-driven checker in Renderer

**Files:**
- Create Renderer `contracts/required_merge_gate_policy.json`
- Create Renderer `scripts/required_merge_gate.py`
- Modify Renderer `scripts/test_required_merge_gate.py`

**Interfaces:**

```python
load_policy(path: Path) -> dict
match_pattern(path: str, pattern: str) -> bool
classify_changes(policy: dict, changes: list[tuple[str, str]]) -> dict
evaluate_workflow_runs(expected: set[str], runs: list[dict], head_sha: str) -> dict
poll_expected_workflows(repo: str, head_sha: str, expected: set[str], token: str, timeout_seconds=2700, poll_seconds=10) -> dict
```

CLI:

```text
python3 scripts/required_merge_gate.py \
  --policy contracts/required_merge_gate_policy.json \
  --base-sha <base> \
  --head-sha <head> \
  --repository <owner/repo>
```

The CLI obtains changed paths with `git diff --name-status BASE HEAD`, reads `GITHUB_TOKEN`, polls:

```text
GET /repos/{repository}/actions/runs?head_sha={head_sha}&event=pull_request&per_page=100
```

and matches exact workflow `name` + exact `head_sha`.

- [ ] **Step 1: Create Renderer policy**

At minimum map:

```text
request-only:
  handoff-preview-requests-v4/*.json -> Current Request Publication Gate
  final-render-requests-v2/*.json -> Current Request Publication Gate

current Final/Preview control-plane:
  current request/preview/final workflows
  validate-current-request.py
  verify-final-authorization-bundle.py
  capture/restore/render-approved/wake helper + their tests
  -> Current Preview Final Identity CI

Renderer core:
  src/**
  scripts/**
  contracts/**
  package.json
  package-lock.json
  tsconfig*.json
  .github/workflows/**
  -> Visual Story Engine CI

media-sensitive:
  src/**
  public/**
  assets/**
  scripts/*media*
  visual/media test files
  -> Visual Story Media CI
```

Explicitly exclude request directories from the broad `.json`/core matching by applying request-only classification before workflow groups.

- [ ] **Step 2: Implement checker with fail-closed states**

Stable error codes printed to stderr:

```text
MIXED_REQUEST_PR
UNCLASSIFIED_CHANGE
EXPECTED_WORKFLOW_MISSING
EXPECTED_WORKFLOW_FAILED
EXPECTED_WORKFLOW_TIMEOUT
```

Never treat `skipped`, `neutral`, `cancelled`, `timed_out`, `action_required`, or `stale` as success for an expected workflow. Only `conclusion == "success"` passes.

- [ ] **Step 3: Run GREEN**

```bash
python3 scripts/test_required_merge_gate.py
python3 -m py_compile scripts/required_merge_gate.py scripts/test_required_merge_gate.py
```

## Task 3: Create Renderer always-on Required Merge Gate

**Files:**
- Create Renderer `.github/workflows/required-merge-gate.yml`

- [ ] **Step 1: Add an unconditional PR trigger**

```yaml
name: Required Merge Gate

on:
  pull_request:
    branches: [main]

permissions:
  contents: read
  actions: read

jobs:
  required-merge-gate:
    name: Required Merge Gate
    runs-on: ubuntu-24.04
    timeout-minutes: 50
```

Do not add `paths`, `paths-ignore`, or a workflow-level skip condition.

- [ ] **Step 2: Checkout full enough history and invoke checker**

```yaml
- uses: actions/checkout@v6
  with:
    ref: ${{ github.event.pull_request.head.sha }}
    fetch-depth: 0
    persist-credentials: false

- name: Enforce repository PR evidence
  env:
    GITHUB_TOKEN: ${{ github.token }}
  run: |
    python3 scripts/required_merge_gate.py \
      --policy contracts/required_merge_gate_policy.json \
      --base-sha "${{ github.event.pull_request.base.sha }}" \
      --head-sha "${{ github.event.pull_request.head.sha }}" \
      --repository "$GITHUB_REPOSITORY"

- name: Diff hygiene
  run: git diff --check "${{ github.event.pull_request.base.sha }}" "${{ github.event.pull_request.head.sha }}"
```

- [ ] **Step 3: Test three real PR shapes before any ruleset is enabled**

Create/observe temporary PRs for:

```text
docs-only -> gate success without waiting for path-specific CI
request-only -> gate waits for Current Request Publication Gate and succeeds
implementation -> gate waits for mapped Engine/Media/Identity workflows and succeeds
```

A deliberate failing implementation test must prove the gate fails when one expected workflow fails.

## Task 4: Implement the same gate contract in Plot

**Files:**
- Create Plot `contracts/required_merge_gate_policy.json`
- Create Plot `scripts/required_merge_gate.py`
- Create Plot `tests/current-spine/test_required_merge_gate.py`
- Create Plot `.github/workflows/required-merge-gate.yml`
- Modify Plot `.github/workflows/validate-daily-production-package.yml`

- [ ] **Step 1: Use the same Python public interface and stable errors as Renderer**

Do not create a different state model. Repository-specific behavior belongs only in the policy JSON.

- [ ] **Step 2: Create Plot policy groups**

At minimum:

```text
final-authorization-requests-v1/*.json
  -> ChatGPT Daily Final Authorization

daily-production-requests/**, daily-authoring/**, daily-inputs/**, working/**,
research/**, episodes/**, render-specs/**, daily-assets/**
  -> Validate Daily Production Package

scripts/**, tests/**, contracts/**, .github/workflows/**, skills/**
  -> Validate Daily Production Package (baseline)

contracts/renderer_binding.json + Current Spine/cross-repo entrypoints
  -> Current Spine Exact Cross-Repo E2E
  -> Current Renderer Runtime Qualification Handoff
  -> Visual Intelligence v1.2

Preview/Final request/authorization builder files and their tests
  -> Current Preview Final Request Builders CI
  -> Current Renderer Runtime Qualification Handoff where already owned

Visual Intelligence contract/scripts/tests
  -> Visual Intelligence v1.2
```

- [ ] **Step 3: Broaden only the baseline validation trigger**

In `validate-daily-production-package.yml`, add broad code/reliability patterns if they are not already covered:

```yaml
      - "scripts/**"
      - "tests/**"
      - "contracts/**"
      - ".github/workflows/**"
      - "skills/**"
```

This ensures every Plot non-doc code change has at least the baseline authoritative workflow for the Required Merge Gate to observe. Do not remove the existing exact-day/request paths.

- [ ] **Step 4: Run RED→GREEN tests**

```bash
PYTHONPATH=scripts python3 tests/current-spine/test_required_merge_gate.py
python3 -m py_compile scripts/required_merge_gate.py tests/current-spine/test_required_merge_gate.py
```

Then require existing Plot PR CI relevant to the gate change:

```text
Validate Daily Production Package = success
Current Spine Exact Cross-Repo E2E = success when policy/binding boundary is touched
Current Renderer Runtime Qualification Handoff = success when mapped boundary is touched
Visual Intelligence v1.2 = success when mapped boundary is touched
Current Preview Final Request Builders CI = success when builder boundary is touched
```

## Task 5: Verify the stable required-check context before repository configuration

**Files:** none.

- [ ] **Step 1: Open one docs-only PR in each repository after the gate source is merged but before rulesets are enabled**

- [ ] **Step 2: Query exact check runs for the PR head SHA**

```bash
gh api "repos/OWNER/REPO/commits/HEAD_SHA/check-runs" --jq '.check_runs[] | [.name,.status,.conclusion] | @tsv'
```

Record the exact successful job/check context emitted by `.github/workflows/required-merge-gate.yml`. Expected intended name: `Required Merge Gate`.

Do not guess the status-check context in repository settings; use the observed API value.

## Task 6: Install active `main` rulesets in both repositories

**Files:** repository configuration plus Plot `docs/reliability/repository-protection-policy.md`.

**One-time admin operation:** GitHub repository Settings → Rules → Rulesets → New branch ruleset.

For each repository configure exactly:

```text
Ruleset name: current-production-main-v1
Enforcement status: Active
Target: default branch / refs/heads/main
Bypass list: none
Restrict deletions: ON
Require a pull request before merging: ON
Required approving reviews: 0
Dismiss stale approvals: OFF (no approvals required)
Require status checks before merging: ON
Required status check: exact observed Required Merge Gate context from Task 5
Require branches to be up to date before merging: ON
Block force pushes: ON
```

Do not require `Validate Daily Production Package`, `Current Request Publication Gate`, `Visual Story Engine CI`, or other path-filtered workflows directly.

- [ ] **Step 1: Verify rulesets through GitHub API**

```bash
gh api repos/saienjoy0/nasdaq-plot-creator-/rulesets
gh api repos/saienjoy0/saienjoy0-nasdaq-cafe-remotion/rulesets
```

Expected: exactly one active `current-production-main-v1` targeting `main` with pull-request, required-status-check, deletion, and non-fast-forward protections.

- [ ] **Step 2: Record immutable rollout evidence**

Create `docs/reliability/repository-protection-policy.md` containing:

```text
repository
ruleset name
ruleset id
active status
protected target
required check context
verification date
```

No secret/token values.

## Task 7: Negative verification — prove bypass is actually blocked

- [ ] **Step 1: Failing-check PR**

Create a disposable test PR whose Expected Workflow intentionally fails. Confirm GitHub reports the Required Merge Gate failure and merge is blocked. Close without merge.

- [ ] **Step 2: Direct main update test**

From an authenticated local/CI-safe environment, attempt a non-destructive direct push of a disposable commit to `main` and require GitHub to reject it because PR/ruleset policy applies. Immediately delete the disposable local commit/branch; no force push.

If policy permissions make a direct-push test unsafe, use GitHub's ruleset evaluation UI/API evidence instead and record why the destructive probe was omitted.

- [ ] **Step 3: Request-only positive test**

Open a valid one-file append-only request PR. Confirm:

```text
path-specific request workflow = success
Required Merge Gate = success
unrelated path-filtered workflows may be absent
merge is allowed only after Required Merge Gate success
```

## Review / rollback

Source rollback: revert the Required Merge Gate PRs. Repository-configuration rollback: set ruleset Enforcement status to `Evaluate` or disable the required status check before removing source workflows, never delete the gate source first while an Active ruleset still requires it.

Block rollout if:

- Required Merge Gate can be skipped by a path/branch filter;
- policy permits an unknown non-doc path;
- gate accepts any conclusion other than `success` for an expected workflow;
- gate matches a workflow run from a different head SHA;
- a ruleset directly requires a path-filtered workflow;
- the observed required check context is not verified before activation.
