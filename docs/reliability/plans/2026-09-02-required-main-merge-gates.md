# Required Main Merge Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `nasdaq-cafe-production-reliability` as coordinator and `superpowers:test-driven-development` for source changes. Use `superpowers:verification-before-completion` before enabling repository rulesets.

**Goal:** Make Plot and Renderer `main` fail closed at repository level so request-only PRs, implementation PRs, and docs-only PRs cannot bypass the CI evidence appropriate to their change class, while avoiding GitHub path-filter required-check deadlocks.

**Architecture:** Add one always-on `Required Merge Gate` workflow to each repository. A repository-specific policy JSON maps changed paths to existing authoritative workflow names; the gate polls GitHub Actions runs for the PR head SHA and requires all expected workflows to finish successfully. Unclassified non-document changes fail closed. After the gate has proven a stable check context, install an active repository ruleset on `main` requiring PRs plus only that always-on gate; existing path-filtered workflows remain the actual test owners.

**Tech Stack:** GitHub Actions, Python 3.12 stdlib, GitHub Actions REST API, GitHub repository rulesets.

**Spec:** `docs/reliability/plans/2026-09-02-current-production-reliability-closure-design.md`

## Global Constraints

- Do not make any path-filtered workflow itself a required repository status check.
- Existing workflows remain the owners of their tests; the new gate observes their result and must not reimplement production validation logic.
- Docs-only PRs may pass with gate-local diff hygiene only.
- Request-only PRs must still prove exactly-one append-only request through the existing request workflow.
- Any non-doc change that matches no policy group must fail `UNCLASSIFIED_CHANGE`, not silently pass.
- Direct pushes, force pushes, and branch deletion on `main` must be blocked after rollout.
- No ruleset bypass actors are configured for routine use.
- Required approving review count stays `0`; PR + required status check remains mandatory.
- Repository protection is applied only after the gate succeeds on a real test PR in each repository.

---

**Root cause:** Source-level PR gates are not repository-enforced because both `main` branches currently have no active protection/ruleset, so direct updates or a merge that ignores failed optional checks can bypass the intended reliability contract.

**First broken boundary:** repository merge control / `GITHUB_ACTIONS` policy boundary.

**Evidence:** both repository branch metadata reported `protected: false`; both `/rulesets` collections were empty.

**Why existing tests missed it:** CI validates source contracts but repository configuration lives outside Git. No always-on check currently represents “all CI required for this exact PR class passed,” and no ruleset enforces such a check.

## GitHub behavior that constrains the design

GitHub documents that when a workflow is skipped by `paths`, `branches`, or commit-message filtering, a required check can remain Pending and block merging. Therefore current path-filtered workflows MUST NOT be required directly. The required check must come from a workflow that runs on every PR to `main`.

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
| `contracts/required_merge_gate_policy.json` | create | change-class → expected workflow names |
| `scripts/required_merge_gate.py` | create | classify changed files, poll Actions runs for exact head SHA, fail closed |
| `scripts/test_required_merge_gate.py` | create | pure regression tests for classification and workflow-result evaluation |
| `.github/workflows/required-merge-gate.yml` | create | always-on PR workflow that invokes policy checker |
| `.github/workflows/visual-story-engine-ci.yml` | modify | broaden baseline trigger to all Renderer source/control-plane changes |
| `.github/workflows/visual-story-media-ci.yml` | modify | explicitly cover all media-sensitive paths named in policy |
| `.github/workflows/current-preview-final-identity-ci.yml` | modify | include Required Merge Gate policy/checker changes in Current control-plane CI |

### Plot repository

| File | Action | Responsibility |
|---|---|---|
| `contracts/required_merge_gate_policy.json` | create | Plot change-class → expected workflow names |
| `scripts/required_merge_gate.py` | create | same interface as Renderer, Plot-specific policy data |
| `tests/current-spine/test_required_merge_gate.py` | create | Plot policy/classification regression |
| `.github/workflows/required-merge-gate.yml` | create | always-on PR workflow |
| `.github/workflows/validate-daily-production-package.yml` | modify | make baseline validation trigger on every Plot source/test/contract/workflow/skill change |
| `docs/reliability/repository-protection-policy.md` | create | exact ruleset names/check contexts/verification evidence after rollout |

## Shared policy contract

Both repositories use the same JSON shape, with repository-specific patterns:

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

A request-only group has this exact shape:

```json
{
  "name": "renderer-final-request",
  "patterns": ["final-render-requests-v2/*.json"],
  "exactlyOneAdded": true,
  "expectedWorkflows": ["Current Request Publication Gate"]
}
```

A normal workflow group has this exact shape:

```json
{
  "name": "current-final-control-plane",
  "patterns": [".github/workflows/nasdaq-cafe-final-v2.yml", "scripts/restore-approved-preview-for-final.py"],
  "expectedWorkflows": ["Current Preview Final Identity CI"]
}
```

A changed path may match multiple workflow groups; expected workflow names are the set union.

## Task 1: RED — define classification and exact-head workflow-result behavior

**Files:**
- Create Renderer `scripts/test_required_merge_gate.py`
- Create Plot `tests/current-spine/test_required_merge_gate.py`

**Interfaces:**

```python
classify_changes(policy, [("A", "path")]) -> {
    "class": "REQUEST_ONLY" | "DOCS_ONLY" | "CODE",
    "expected_workflows": tuple[str, ...],
}

evaluate_workflow_runs(expected, runs, head_sha) -> None
```

- [ ] **Step 1: Write Renderer test cases**

Required cases:

```text
one handoff-preview-requests-v4 file added -> REQUEST_ONLY + Current Request Publication Gate
one final-render-requests-v2 file added -> REQUEST_ONLY + Current Request Publication Gate
request file + any second file -> MIXED_REQUEST_PR
Final/Preview control-plane path -> CODE + Current Preview Final Identity CI + Visual Story Engine CI
src/** -> CODE + Visual Story Engine CI + Visual Story Media CI
public/** or assets/** -> CODE + Visual Story Media CI
unknown non-doc path -> UNCLASSIFIED_CHANGE
docs-only -> DOCS_ONLY + no external workflow
wrong head SHA run -> ignored
missing expected workflow -> failure
queued/in_progress expected workflow -> waiting state
failure/cancelled/timed_out expected workflow -> failure
all expected exact-head runs success -> pass
```

- [ ] **Step 2: Write Plot test cases**

Required cases:

```text
one final-authorization-requests-v1 file added -> REQUEST_ONLY + ChatGPT Daily Final Authorization
daily-production-requests/** -> CODE + Validate Daily Production Package
contracts/renderer_binding.json -> Validate Daily Production Package + Current Spine Exact Cross-Repo E2E + Current Renderer Runtime Qualification Handoff + Visual Intelligence v1.2
scripts/build_current_final_request_v2.py -> Validate Daily Production Package + Current Preview Final Request Builders CI + Current Renderer Runtime Qualification Handoff
scripts/publish_current_final_authorization_v1.py -> Validate Daily Production Package + Current Preview Final Request Builders CI
Visual Intelligence script/test path -> Validate Daily Production Package + Visual Intelligence v1.2
unknown non-doc path -> UNCLASSIFIED_CHANGE
docs-only -> DOCS_ONLY
```

- [ ] **Step 3: Run RED**

Renderer:

```bash
python3 scripts/test_required_merge_gate.py
```

Plot:

```bash
PYTHONPATH=scripts python3 tests/current-spine/test_required_merge_gate.py
```

Expected: import/file-not-found failure because policy/checker do not exist.

## Task 2: Implement the shared checker contract in Renderer

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

CLI consumes these required arguments:

```text
--policy
--base-sha
--head-sha
--repository
```

The workflow supplies them from `github.event.pull_request.base.sha`, `github.event.pull_request.head.sha`, and `GITHUB_REPOSITORY`; no literal sample SHAs are embedded in source.

The checker obtains changes with:

```bash
git diff --name-status "$BASE_SHA" "$HEAD_SHA"
```

and polls:

```text
GET /repos/{repository}/actions/runs?head_sha={head_sha}&event=pull_request&per_page=100
```

matching exact workflow `name` and exact `head_sha`.

- [ ] **Step 1: Create Renderer policy with exact groups**

Request-only groups:

```text
handoff-preview-requests-v4/*.json -> Current Request Publication Gate
final-render-requests-v2/*.json -> Current Request Publication Gate
```

Current identity/control-plane group must include:

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
scripts/wake-repository-codespace.py
scripts/test-current-*.py
scripts/test-final-*.py
scripts/test_codespace_wake_gateway.py
scripts/test_required_merge_gate.py
```

Expected workflow: `Current Preview Final Identity CI`.

Renderer baseline group:

```text
src/**
scripts/**
contracts/**
package.json
package-lock.json
tsconfig*.json
.github/workflows/**
```

Expected workflow: `Visual Story Engine CI`.

Renderer media-sensitive group:

```text
src/**
public/**
assets/**
scripts/*media*
scripts/test-*media*
```

Expected workflow: `Visual Story Media CI`.

Request-only classification is evaluated before broad workflow groups, so request JSON files are not converted into implementation PRs.

- [ ] **Step 2: Implement fail-closed errors**

Stable stderr codes:

```text
MIXED_REQUEST_PR
UNCLASSIFIED_CHANGE
EXPECTED_WORKFLOW_MISSING
EXPECTED_WORKFLOW_FAILED
EXPECTED_WORKFLOW_TIMEOUT
```

Only `conclusion == "success"` passes an expected workflow. `skipped`, `neutral`, `cancelled`, `timed_out`, `action_required`, and `stale` do not pass.

- [ ] **Step 3: Run GREEN**

```bash
python3 scripts/test_required_merge_gate.py
python3 -m py_compile scripts/required_merge_gate.py scripts/test_required_merge_gate.py
```

## Task 3: Guarantee Renderer authoritative workflows trigger for every policy-mapped code path

**Files:**
- Modify Renderer `.github/workflows/visual-story-engine-ci.yml`
- Modify Renderer `.github/workflows/visual-story-media-ci.yml`
- Modify Renderer `.github/workflows/current-preview-final-identity-ci.yml`

- [ ] **Step 1: Broaden Visual Story Engine CI `pull_request.paths` to include exactly**

```yaml
      - "src/**"
      - "scripts/**"
      - "contracts/**"
      - "package.json"
      - "package-lock.json"
      - "tsconfig*.json"
      - ".github/workflows/**"
```

Keep existing narrower patterns too if they cover files outside this baseline; remove exact duplicates only.

- [ ] **Step 2: Ensure Visual Story Media CI covers the media-sensitive policy**

Its `pull_request.paths` must include:

```yaml
      - "src/**"
      - "public/**"
      - "assets/**"
      - "scripts/*media*"
      - "scripts/test-*media*"
```

- [ ] **Step 3: Add new gate-policy/checker files to Current Preview Final Identity CI paths and py_compile**

Include:

```text
.github/workflows/required-merge-gate.yml
contracts/required_merge_gate_policy.json
scripts/required_merge_gate.py
scripts/test_required_merge_gate.py
```

- [ ] **Step 4: Re-run Renderer tests**

```bash
python3 scripts/test_required_merge_gate.py
python3 scripts/test-current-preview-final-identity-contract.py
npm ci
npm run typecheck
```

## Task 4: Create Renderer always-on Required Merge Gate

**Files:**
- Create Renderer `.github/workflows/required-merge-gate.yml`

- [ ] **Step 1: Add unconditional PR trigger**

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

No `paths`, `paths-ignore`, or workflow-level skip condition.

- [ ] **Step 2: Invoke checker using exact PR event values**

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

- [ ] **Step 3: Before ruleset activation, prove docs/request/code PR classes**

Use three disposable PRs:

```text
docs-only -> Required Merge Gate succeeds without expected external workflows
valid one-file request -> waits for Current Request Publication Gate then succeeds
implementation -> waits for policy-mapped Engine/Media/Identity workflows then succeeds
```

A fourth disposable implementation PR must intentionally make one mapped workflow fail; Required Merge Gate must fail too. Close all disposable negative PRs without merge.

## Task 5: Implement Plot policy/checker and baseline trigger

**Files:**
- Create Plot `contracts/required_merge_gate_policy.json`
- Create Plot `scripts/required_merge_gate.py`
- Create Plot `tests/current-spine/test_required_merge_gate.py`
- Create Plot `.github/workflows/required-merge-gate.yml`
- Modify Plot `.github/workflows/validate-daily-production-package.yml`

- [ ] **Step 1: Use the exact same Python public interface/error codes as Renderer**

Repository-specific path/workflow mapping belongs only in Plot policy JSON.

- [ ] **Step 2: Define exact Plot policy groups**

Request-only:

```text
final-authorization-requests-v1/*.json -> ChatGPT Daily Final Authorization
```

Daily package/data baseline:

```text
daily-production-requests/**
daily-authoring-parts/**
daily-authoring/**
daily-inputs/**
working/**
research/**
episodes/**
render-specs/**
daily-assets/**
```

Expected: `Validate Daily Production Package`.

Source/reliability baseline:

```text
scripts/**
tests/**
contracts/**
.github/workflows/**
skills/**
```

Expected: `Validate Daily Production Package`.

Exact Current cross-repo group:

```text
contracts/renderer_binding.json
tests/current-spine/**
tests/editorial-semantic-boundary/**
tests/remotion-compat/run_visual_intelligence_v12_cross_repo.py
scripts/run_daily_production_v12.py
scripts/run_daily_renderer_closure_v12.py
scripts/run_semantic_frozen_renderer_closure_v12.py
scripts/current_production_facade_v12.py
```

Expected: `Current Spine Exact Cross-Repo E2E`.

Runtime qualification group:

```text
contracts/renderer_binding.json
contracts/visual_grammar_renderer_compatibility.json
contracts/chatgpt_daily_authoring_v2.schema.json
tests/current-spine/current_authoring_runtime_fixture.py
tests/current-spine/test_current_authoring_materializer_parity.py
tests/current-spine/run_exact_cross_repo_current_e2e.py
tests/current-spine/test_current_preview_final_request_builders.py
tests/current-spine/test_current_production_facade_contract.py
tests/remotion-compat/run_visual_intelligence_v12_cross_repo.py
tests/remotion-compat/test_visual_director_handoff.py
scripts/build_current_preview_request_v4.py
scripts/build_current_final_request_v2.py
```

Expected: `Current Renderer Runtime Qualification Handoff`.

Visual Intelligence group:

```text
contracts/renderer_binding.json
contracts/human_preview_review.schema.json
contracts/final_render_authorization.schema.json
scripts/renderer_binding.py
scripts/financial_candidate_provider.py
scripts/renderer_strict_projection.py
scripts/visual_intelligence_*.py
scripts/run_visual_intelligence_v12.py
scripts/validate_visual_intelligence_package.py
scripts/write_human_preview_review.py
scripts/build_final_render_authorization_v12.py
scripts/run_daily_production_v12.py
scripts/run_daily_renderer_closure_v12.py
scripts/build_final_production_package_v12.py
tests/remotion-compat/*visual_intelligence*.py
tests/remotion-compat/test_final_render_authorization_v12.py
```

Expected: `Visual Intelligence v1.2`.

Preview/Final builder group:

```text
scripts/build_current_preview_request_v4.py
scripts/build_current_preview_publication.py
scripts/build_current_final_authorization_bundle_v1.py
scripts/build_current_final_request_v2.py
scripts/publish_current_final_authorization_v1.py
tests/current-spine/test_current_preview_final_request_builders.py
tests/current-spine/test_current_preview_publication.py
tests/current-spine/test_current_final_authorization_publication.py
.github/workflows/chatgpt-daily-final-authorization.yml
.github/workflows/current-preview-final-request-builders-ci.yml
```

Expected: `Current Preview Final Request Builders CI`.

- [ ] **Step 3: Broaden Plot baseline validation trigger exactly**

Add these patterns to `Validate Daily Production Package` `pull_request.paths`:

```yaml
      - "scripts/**"
      - "tests/**"
      - "contracts/**"
      - ".github/workflows/**"
      - "skills/**"
```

Keep existing episode/data paths. Remove only duplicate path entries.

- [ ] **Step 4: Create Plot always-on Required Merge Gate using the same YAML shape as Renderer**

Only repository policy content differs.

- [ ] **Step 5: Run Plot GREEN**

```bash
PYTHONPATH=scripts python3 tests/current-spine/test_required_merge_gate.py
python3 -m py_compile scripts/required_merge_gate.py tests/current-spine/test_required_merge_gate.py
```

Then require exact PR-head GitHub CI selected by the policy, including baseline `Validate Daily Production Package`.

## Task 6: Verify the stable required-check context before repository configuration

**Files:** none.

- [ ] **Step 1: Open one docs-only test PR in Renderer and one in Plot after gate source is merged but before rulesets are active**

- [ ] **Step 2: Resolve each test PR head SHA through GitHub CLI**

Renderer example:

```bash
export REPOSITORY="saienjoy0/saienjoy0-nasdaq-cafe-remotion"
export PR_NUMBER="$(gh pr list --repo "$REPOSITORY" --state open --search 'Required Merge Gate context verification' --json number --jq '.[0].number')"
export HEAD_SHA="$(gh pr view "$PR_NUMBER" --repo "$REPOSITORY" --json headRefOid --jq '.headRefOid')"
gh api "repos/${REPOSITORY}/commits/${HEAD_SHA}/check-runs" --jq '.check_runs[] | [.name,.status,.conclusion] | @tsv'
```

Repeat with `REPOSITORY=saienjoy0/nasdaq-plot-creator-` and that repository's test PR number.

Record the exact successful check name emitted by `.github/workflows/required-merge-gate.yml`; intended job name is `Required Merge Gate`, but repository configuration uses the observed API value, not an assumption.

## Task 7: Install active `main` rulesets in both repositories

**Files:** repository configuration plus Plot `docs/reliability/repository-protection-policy.md`.

This is a one-time repository-admin operation. In each repository use GitHub Settings → Rules → Rulesets → New branch ruleset and configure exactly:

```text
Ruleset name: current-production-main-v1
Enforcement status: Active
Target: default branch / refs/heads/main
Bypass list: none
Restrict deletions: ON
Require a pull request before merging: ON
Required approving reviews: 0
Dismiss stale approvals: OFF
Require status checks before merging: ON
Required status check: exact observed Required Merge Gate context from Task 6
Require branches to be up to date before merging: ON
Block force pushes: ON
```

Do not require any path-filtered workflow directly.

- [ ] **Step 1: Verify installed rulesets**

```bash
gh api repos/saienjoy0/nasdaq-plot-creator-/rulesets
gh api repos/saienjoy0/saienjoy0-nasdaq-cafe-remotion/rulesets
```

Expected: active `current-production-main-v1` targeting `main` in both repositories, with PR/status/deletion/non-fast-forward protections.

- [ ] **Step 2: Record rollout evidence**

Create `docs/reliability/repository-protection-policy.md` with:

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

## Task 8: Negative verification — prove bypass is blocked

- [ ] **Step 1: Failing-check PR**

Create a disposable implementation PR that intentionally fails one expected workflow. Confirm Required Merge Gate fails and GitHub blocks merge. Close without merge.

- [ ] **Step 2: Direct-main protection**

Use GitHub ruleset evaluation/API evidence first. If a direct-push probe is performed, use a disposable commit with no production data changes and require GitHub to reject the push. Never force-push `main`.

- [ ] **Step 3: Request-only positive test**

Open a valid one-file append-only request PR. Confirm:

```text
path-specific request workflow = success
Required Merge Gate = success
unrelated path-filtered workflows may be absent
merge remains blocked until Required Merge Gate succeeds
```

## Review / rollback

Source rollback: revert Required Merge Gate source PRs. Repository-configuration rollback: change ruleset Enforcement to `Evaluate` or remove the required status rule before removing source workflow files. Never delete/rename the required gate while an Active ruleset still requires its check context.

Block rollout if:

- Required Merge Gate itself can be skipped by path/branch filtering;
- policy permits an unknown non-doc path;
- gate accepts any conclusion other than `success` for an expected workflow;
- gate matches a workflow run from a different head SHA;
- a ruleset directly requires a path-filtered workflow;
- the observed required check context is not verified before activation.
