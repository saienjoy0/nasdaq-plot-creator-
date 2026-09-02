# Required Main Merge Gates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `nasdaq-cafe-production-reliability` as coordinator and `superpowers:test-driven-development` for source changes. Use `superpowers:verification-before-completion` before enabling repository rulesets.

**Goal:** Make Plot and Renderer `main` fail closed so each PR must satisfy the CI appropriate to its changed paths, without path-filter deadlocks and without allowing a PR to rewrite the gate that judges the same PR.

**Architecture:** Each repository gets a trusted merge-control plane stored on protected `main`. It runs via `pull_request_target`, executes only base-branch code, reads PR changed-file metadata as data, waits for existing path-specific `pull_request` workflows on the exact PR head SHA, and writes one commit status to that head. The repository ruleset requires that status. Existing workflows remain the test owners.

**Required status context:** `Nasdaq Cafe Required Merge Gate`

**Tech Stack:** GitHub Actions, Python 3.12 stdlib, GitHub PR/Actions/Commit Status REST APIs, repository rulesets.

**Spec:** `docs/reliability/plans/2026-09-02-current-production-reliability-closure-design.md`

## Protected invariants

- Required gate code executes from base/main only; never execute PR-head code in `pull_request_target`.
- Path-filtered workflows are never required directly by ruleset.
- Existing workflows own validation; the trusted gate observes their exact-head results.
- Request-only PRs still use existing exactly-one append-only request validators.
- Unknown non-doc changes fail closed.
- Missing workflow at startup is WAITING, not immediate failure.
- For duplicate/rerun workflow results, only the newest exact-head run/attempt is authoritative.
- Only `conclusion == success` passes.
- Direct updates, deletion, and force pushes on `main` are blocked after ruleset activation.
- No routine bypass actor.
- `AGENTS.md` is control-plane input, not docs-only.

## Root cause and working analogue

**Root cause:** both repositories currently have no active branch ruleset, so source-level checks can be bypassed by repository operations. A naive always-on `pull_request` gate is also insufficient because the PR can modify the workflow/checker that judges it.

**First broken boundary:** repository merge-control / `GITHUB_ACTIONS` policy boundary.

**Working GitHub pattern:** `pull_request_target` loads workflow/default checkout from the trusted base branch. GitHub commit statuses can be required by rulesets. This design uses that trust separation without ever executing PR code in the privileged job.

## Shared state model

Both repositories implement the same checker interface; only policy JSON differs.

```python
def load_policy(path: Path) -> dict: ...

def classify_changes(policy: dict, changes: list[dict]) -> dict:
    """PR-file API records: filename, status, previous_filename when renamed."""

def select_latest_runs(expected: set[str], runs: list[dict], head_sha: str) -> dict[str, dict]:
    """Select newest exact-head pull_request run per workflow by (run_number, run_attempt, id)."""

def evaluate_latest_runs(expected: set[str], selected: dict[str, dict]) -> dict: ...

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

Stable states/errors:

```text
PASS
WAITING_FOR_WORKFLOW
WAITING_FOR_COMPLETION
MIXED_REQUEST_PR
UNCLASSIFIED_CHANGE
EXPECTED_WORKFLOW_FAILED
EXPECTED_WORKFLOW_TIMEOUT
```

Rules:

```text
no exact-head run yet                         -> WAITING_FOR_WORKFLOW
latest exact-head run queued/in_progress      -> WAITING_FOR_COMPLETION
old success + newer pending                   -> WAITING_FOR_COMPLETION
old success + newer failure                   -> EXPECTED_WORKFLOW_FAILED
old failure + newer success                   -> latest success is authoritative
all expected latest exact-head runs success   -> PASS
workflow never appears before 2700s deadline  -> EXPECTED_WORKFLOW_TIMEOUT
```

The poller paginates when the Actions API returns more runs than one page.

## Policy JSON contract

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

Request-only groups are evaluated first. If one request-only path is changed together with any other file, return `MIXED_REQUEST_PR`.

## File map

### Renderer

```text
create  contracts/required_merge_gate_policy.json
create  scripts/required_merge_gate.py
create  scripts/test_required_merge_gate.py
create  .github/workflows/required-merge-gate.yml
modify  .github/workflows/visual-story-engine-ci.yml
modify  .github/workflows/visual-story-media-ci.yml
modify  .github/workflows/current-preview-final-identity-ci.yml
```

### Plot

```text
create  contracts/required_merge_gate_policy.json
create  scripts/required_merge_gate.py
create  tests/current-spine/test_required_merge_gate.py
create  .github/workflows/required-merge-gate.yml
modify  .github/workflows/validate-daily-production-package.yml
create  docs/reliability/repository-protection-policy.md after ruleset rollout
```

## Task 1: RED — classification, startup race, and latest-run semantics

- [ ] Create Renderer `scripts/test_required_merge_gate.py`.
- [ ] Create Plot `tests/current-spine/test_required_merge_gate.py`.

Renderer cases:

```text
one handoff Preview request added -> REQUEST_ONLY + Current Request Publication Gate
one Final request added           -> REQUEST_ONLY + Current Request Publication Gate
request + second file             -> MIXED_REQUEST_PR
Final/Preview control-plane path  -> Current Preview Final Identity CI + Visual Story Engine CI
src/**                            -> Visual Story Engine CI + Visual Story Media CI
public/**                         -> Visual Story Media CI
AGENTS.md                         -> Visual Story Engine CI
docs/** or README.md only         -> DOCS_ONLY
unknown non-doc                   -> UNCLASSIFIED_CHANGE
```

Plot cases:

```text
one final-authorization request   -> REQUEST_ONLY + ChatGPT Daily Final Authorization
daily-production/data path        -> Validate Daily Production Package
renderer_binding.json             -> Validate Daily Production Package + Current Spine Exact Cross-Repo E2E + Current Renderer Runtime Qualification Handoff + Visual Intelligence v1.2
current Final builder             -> Validate Daily Production Package + Current Preview Final Request Builders CI + Current Renderer Runtime Qualification Handoff
Visual Intelligence path          -> Validate Daily Production Package + Visual Intelligence v1.2
AGENTS.md                          -> Validate Daily Production Package
docs/** or README.md only         -> DOCS_ONLY
unknown non-doc                   -> UNCLASSIFIED_CHANGE
```

Exact-head/run cases in both tests:

```text
wrong head SHA ignored
no run yet -> WAITING_FOR_WORKFLOW
queued/in_progress latest -> WAITING_FOR_COMPLETION
old success + newer in_progress -> WAITING_FOR_COMPLETION
old success + newer failure -> EXPECTED_WORKFLOW_FAILED
old failure + newer success -> PASS for that workflow
missing until fake deadline -> EXPECTED_WORKFLOW_TIMEOUT
all expected latest successes -> PASS
```

Run RED:

```bash
# Renderer
python3 scripts/test_required_merge_gate.py

# Plot
PYTHONPATH=scripts python3 tests/current-spine/test_required_merge_gate.py
```

Expected pre-implementation failure: checker/policy missing. Commit RED before implementation.

## Task 2: GREEN — Renderer checker/policy

Create Renderer policy groups.

Request-only:

```text
handoff-preview-requests-v4/*.json -> Current Request Publication Gate
final-render-requests-v2/*.json    -> Current Request Publication Gate
```

Current identity/control-plane paths include current Preview/Final workflows, required gate workflow/policy/checker, request validator, Final authorization verifier, approved-preview restore, Preview identity capture, render-only adapter, Codespace helper, and corresponding tests.

Expected workflows:

```text
Current Preview Final Identity CI
Visual Story Engine CI
```

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
  -> Visual Story Engine CI
```

Media-sensitive:

```text
src/**
public/**
render-specs/**
scripts/*media*
  -> Visual Story Media CI
```

Actions query:

```text
GET /repos/{repository}/actions/runs?head_sha={head_sha}&event=pull_request&per_page=100
```

Run GREEN:

```bash
python3 scripts/test_required_merge_gate.py
python3 -m py_compile scripts/required_merge_gate.py scripts/test_required_merge_gate.py
```

## Task 3: Align Renderer path-specific triggers with policy

- [ ] Add `tsconfig*.json` to `visual-story-engine-ci.yml` if absent.
- [ ] Add `public/**` to `visual-story-media-ci.yml`.
- [ ] Add gate policy/checker/test/workflow plus `wake_repository_codespace.py` and its tests to `current-preview-final-identity-ci.yml` path/syntax coverage where they belong.

Run:

```bash
python3 scripts/test_required_merge_gate.py
python3 scripts/test_current_preview_final_identity_contract.py
npm ci
npm run typecheck
```

Require exact PR-head mapped Renderer workflows GREEN.

## Task 4: Create trusted Renderer status producer

Create `.github/workflows/required-merge-gate.yml`:

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

env:
  GH_TOKEN: ${{ github.token }}
```

No path filters.

Trusted checkout only:

```yaml
- uses: actions/checkout@v6
  with:
    ref: ${{ github.event.pull_request.base.sha }}
    fetch-depth: 1
    persist-credentials: false
    clean: true
```

Never checkout PR head/merge ref in this privileged workflow.

Publish initial pending status:

```bash
HEAD_SHA="${{ github.event.pull_request.head.sha }}"
gh api --method POST "repos/${GITHUB_REPOSITORY}/statuses/${HEAD_SHA}" \
  -f state=pending \
  -f context='Nasdaq Cafe Required Merge Gate' \
  -f description='Waiting for required exact-head workflows' \
  -f target_url="${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}"
```

Run trusted checker with `continue-on-error: true`:

```bash
python3 scripts/required_merge_gate.py \
  --policy contracts/required_merge_gate_policy.json \
  --repository "$GITHUB_REPOSITORY" \
  --pr-number "${{ github.event.pull_request.number }}" \
  --head-sha "${{ github.event.pull_request.head.sha }}"
```

The checker gets changed files only from:

```text
GET /repos/{repository}/pulls/{pr_number}/files?per_page=100&page=N
```

It never imports or executes PR content.

Final status step runs `if: always()`:

```text
checker success -> status success
checker failure -> status failure
```

Use the same context and target URL. After publishing failure, explicitly `exit 1` so the control-plane workflow is auditable. If the run is cancelled/times out before final publication, the earlier pending status remains and blocks merge.

## Task 5: GREEN — Plot checker/policy/trusted gate

Use identical state model and workflow shape.

Plot baseline groups:

```text
final-authorization-requests-v1/*.json -> REQUEST_ONLY -> ChatGPT Daily Final Authorization

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

Preserve additional existing ownership:

```text
Current cross-repo paths -> Current Spine Exact Cross-Repo E2E
runtime qualification paths -> Current Renderer Runtime Qualification Handoff
Visual Intelligence paths -> Visual Intelligence v1.2
Preview/Final builder/publication paths -> Current Preview Final Request Builders CI
```

Broaden `Validate Daily Production Package` `pull_request.paths` with:

```yaml
- "scripts/**"
- "tests/**"
- "contracts/**"
- ".github/workflows/**"
- "skills/**"
- "AGENTS.md"
```

Run:

```bash
PYTHONPATH=scripts python3 tests/current-spine/test_required_merge_gate.py
python3 -m py_compile scripts/required_merge_gate.py tests/current-spine/test_required_merge_gate.py
```

Require exact PR-head workflows selected by the Plot policy.

## Task 6: Bootstrap verification before ruleset activation

Rollout order is mandatory:

```text
merge trusted gate/policy/checker source while repository is still unprotected
-> open verification PRs
-> observe trusted head status
-> activate ruleset
```

Before activation, verify in each repository:

```text
docs-only PR: status success without unrelated CI
valid one-file request: pending -> request workflow success -> status success
implementation PR: pending -> mapped workflows success -> status success
negative implementation PR: mapped workflow fails -> status failure
self-change PR: modifies gate/checker/policy, but current judging workflow still checks out base.sha
```

Close negative disposable PRs without merge.

## Task 7: Install active main rulesets

For Plot and Renderer:

```text
Ruleset name: current-production-main-v1
Enforcement: Active
Target: refs/heads/main
Bypass list: none
Restrict deletions: ON
Require pull request before merging: ON
Required approving reviews: 0
Require status checks: ON
Required context: Nasdaq Cafe Required Merge Gate
Expected source app: GitHub Actions, if selectable
Require branch up to date: ON
Block force pushes: ON
```

Do not directly require path-filtered workflows.

Verify:

```bash
gh api repos/saienjoy0/nasdaq-plot-creator-/rulesets
gh api repos/saienjoy0/saienjoy0-nasdaq-cafe-remotion/rulesets
```

Create `docs/reliability/repository-protection-policy.md` with repository, ruleset ID/name, active state, target, required status context/source, and verification date. No secrets.

## Task 8: Negative policy verification

Require evidence that:

```text
failure status blocks merge
valid request-only PR merges only after request workflow + required status success
ruleset blocks direct main updates/deletion/force-push according to API/ruleset evaluation
PR changing gate itself is still judged by pre-existing trusted base gate
```

Do not perform a force push as a test.

## Review / rollback

Rollback order:

1. change ruleset Enforcement to `Evaluate` or remove the required status rule;
2. revert gate/checker/policy source;
3. adjust authoritative workflow triggers;
4. reactivate only after the replacement status producer is observed.

Never remove/rename the required status producer while an Active ruleset still requires it.

Block rollout if:

- privileged gate executes PR code or checks out PR head;
- a PR can modify the gate judging that same PR;
- missing expected workflow fails before polling deadline;
- old success masks a newer run;
- unknown non-doc path passes;
- path-filtered workflow is required directly;
- final status context/source is not observed before activation.
