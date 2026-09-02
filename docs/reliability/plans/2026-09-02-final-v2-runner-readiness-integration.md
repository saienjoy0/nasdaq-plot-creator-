# Current Final V2 Runner Readiness Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `nasdaq-cafe-production-reliability` as coordinator and `superpowers:test-driven-development` for each code task. Use `superpowers:verification-before-completion` before any success claim.

**Goal:** Make an explicitly authorized Current Final self-progress from successful authorization preflight to the self-hosted Renderer without requiring a separate human/ChatGPT Codespace Wake request.

**Architecture:** Current Final V2 owns the decision that a new Final render actually requires runner readiness. One shared Renderer Python helper owns GitHub Codespaces lifecycle API behavior; both the standalone diagnostic Wake workflow and Current Final V2 call that helper. The Final render itself remains unchanged and still uses the exact approved Renderer commit and immutable Preview/authorization lineage.

**Tech Stack:** GitHub Actions YAML, Python 3.12 stdlib, GitHub Codespaces REST API, existing Renderer Current Final V2.

**Spec:** `docs/reliability/plans/2026-09-02-current-production-reliability-closure-design.md`

## Global Constraints

- Final MUST NOT start before explicit user Final approval and valid Plot Final authorization.
- Do not change narration, Scene order, Visual Beat meaning, RenderSpec bytes, TTS bytes, Registry identity, Renderer binding, or Final fingerprint semantics.
- Do not create a second Final workflow/state machine.
- The Codespace REST implementation must have one code owner; workflows may orchestrate but must not duplicate lifecycle code.
- Existing standalone `Nasdaq Cafe Codespace Wake` remains available as a diagnostic/manual recovery entrypoint.
- Missing `CODESPACE_LIFECYCLE_TOKEN`, no matching repository Codespace, timeout, or non-409 API error must fail closed before the self-hosted Final job.

---

**Root cause:** Current Final V2 schedules the Final job directly on `[self-hosted, linux, x64, nasdaq-cafe-codespace]` but does not own runner readiness, while the only durable wake mechanism is a separate request-driven workflow. A sleeping Codespace therefore turns an otherwise authorized Final into an indefinite queue until another actor creates a wake request.

**First broken boundary:** `GITHUB_ACTIONS` — self-hosted runner readiness.

**Evidence:** Final runs reached successful identity/authorization preflight and then remained queued until `Nasdaq Cafe Codespace Wake` was separately triggered; after the standalone Wake reported the repository Codespace `Available`, the queued Final acquired the runner.

**Why existing tests missed it:** tests proved the standalone Wake gateway and Final identity/control-plane contracts independently, but no regression required Current Final V2 itself to own runner readiness between preflight and the self-hosted job.

## Current code path

```text
.github/workflows/nasdaq-cafe-final-request-v2.yml
  resolve
    -> validate-current-request.py final
  final (reusable workflow)
    -> .github/workflows/nasdaq-cafe-final-v2.yml
       preflight (ubuntu)
         -> exact Final outcome lookup
         -> Plot authorization Artifact validation
       final (self-hosted nasdaq-cafe-codespace)
         -> approved Preview restore
         -> exact TTS re-verification
         -> approved Renderer compile
         -> render-approved-current-final.ts
```

The missing boundary is between reusable `preflight` and reusable `final`.

## Working analogue

Two existing working patterns already prove the desired ownership shape:

1. `.github/workflows/nasdaq-cafe-final-request.yml` has a `wake-codespace` job and requires runner readiness before its Final workflow call.
2. `.github/workflows/nasdaq-cafe-codespace-wake.yml` successfully starts the most recently used Codespace for the current repository, tolerates HTTP 409 when already starting/available, waits until `state == "Available"`, and fails on timeout/other API errors.

The repair reuses that behavior instead of inventing a new wake protocol.

## Repair hypothesis

I think the remaining Final queue failure is caused by runner readiness being owned outside Current Final V2, because the exact same queued Final proceeds immediately after the standalone Wake makes the repository Codespace `Available`; extracting that proven lifecycle code and invoking it after successful Final preflight should remove the manual boundary without changing Final authorization or render semantics.

## File map

| File | Action | Responsibility | Why this file owns the change |
|---|---|---|---|
| Renderer `scripts/wake-repository-codespace.py` | create | Sole Codespaces lifecycle API helper | Prevents duplicated REST/polling behavior across workflows |
| Renderer `scripts/test-wake-repository-codespace.py` | create | Unit regression for selection/start/poll/failure semantics | Proves helper behavior without real Codespace calls |
| Renderer `scripts/test-final-v2-runner-readiness.py` | create | Orchestration regression for preflight → wake → Final | Reproduces the real missing boundary at workflow-contract level |
| Renderer `.github/workflows/nasdaq-cafe-codespace-wake.yml` | modify | Call shared helper instead of embedded Python REST implementation | Existing diagnostic Wake remains supported with one lifecycle owner |
| Renderer `.github/workflows/nasdaq-cafe-final-v2.yml` | modify | Add `wake-codespace` job between preflight and self-hosted Final | Current Final V2 owns readiness only after authorization says render is needed |
| Renderer `.github/workflows/current-preview-final-identity-ci.yml` | modify | Run new regression/helper tests and syntax checks | Existing Current Final control-plane CI owns these contracts |

## Task 1: Capture the missing Current Final runner-readiness boundary as RED

**Files:**
- Create: Renderer `scripts/test-final-v2-runner-readiness.py`
- Modify: Renderer `.github/workflows/current-preview-final-identity-ci.yml`

**Interfaces:**
- Consumes: `.github/workflows/nasdaq-cafe-final-v2.yml`, `.github/workflows/nasdaq-cafe-codespace-wake.yml`
- Produces: a contract test that fails unless Final V2 explicitly owns runner readiness and both workflows use the shared helper

- [ ] **Step 1: Write the failing workflow-contract regression**

Create `scripts/test-final-v2-runner-readiness.py` with these exact assertions:

```python
#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
final_v2 = (ROOT / '.github/workflows/nasdaq-cafe-final-v2.yml').read_text(encoding='utf-8')
wake = (ROOT / '.github/workflows/nasdaq-cafe-codespace-wake.yml').read_text(encoding='utf-8')
helper = ROOT / 'scripts/wake-repository-codespace.py'

if '\n  wake-codespace:\n' not in final_v2:
    raise AssertionError('Current Final V2 does not own Codespace readiness')
if 'needs: [preflight, wake-codespace]' not in final_v2:
    raise AssertionError('Current Final self-hosted job is not gated by preflight + runner readiness')
if "needs.preflight.outputs.already_completed != 'true'" not in final_v2:
    raise AssertionError('Current Final wake is not suppressed for an already completed Final')
if 'CODESPACE_LIFECYCLE_TOKEN: ${{ secrets.CODESPACE_LIFECYCLE_TOKEN }}' not in final_v2:
    raise AssertionError('Current Final wake does not receive the lifecycle token')
if not helper.is_file():
    raise AssertionError('shared Codespace lifecycle helper is missing')
for workflow_name, text in [('Final V2', final_v2), ('standalone Wake', wake)]:
    if 'scripts/wake-repository-codespace.py' not in text:
        raise AssertionError(f'{workflow_name} does not use the shared Codespace lifecycle helper')
for forbidden in ('https://api.github.com/user/codespaces?per_page=100', 'urllib.request.Request'):
    if forbidden in final_v2 or forbidden in wake:
        raise AssertionError(f'workflow duplicates Codespace lifecycle implementation: {forbidden}')
print('Current Final V2 runner readiness contract PASS')
```

- [ ] **Step 2: Add the regression to the existing Current Final CI**

In `.github/workflows/current-preview-final-identity-ci.yml`, add the file to `paths`, run:

```bash
python3 scripts/test-final-v2-runner-readiness.py
```

and include it in `python3 -m py_compile`.

- [ ] **Step 3: Run RED**

Run:

```bash
python3 scripts/test-final-v2-runner-readiness.py
```

Expected pre-fix result:

```text
AssertionError: Current Final V2 does not own Codespace readiness
```

Do not implement the wake job until this exact failure is observed.

- [ ] **Step 4: Commit RED only**

```bash
git add scripts/test-final-v2-runner-readiness.py .github/workflows/current-preview-final-identity-ci.yml
git commit -m "test: require Final V2 runner readiness"
```

## Task 2: Extract the single Codespace lifecycle owner

**Files:**
- Create: Renderer `scripts/wake-repository-codespace.py`
- Create: Renderer `scripts/test-wake-repository-codespace.py`

**Interfaces:**
- Produces `select_repository_codespace(listing: dict, repository: str) -> dict`
- Produces `ensure_available(repository: str, token: str, *, request_fn=request_json, sleep_fn=time.sleep, timeout_seconds: int = 420, poll_seconds: int = 7) -> str`
- CLI consumes `--repository` and `--github-output`; token comes only from `CODESPACE_LIFECYCLE_TOKEN`
- CLI writes `name=<codespace>` and `state=Available` to the provided GitHub output file

- [ ] **Step 1: Write unit tests before helper implementation**

Create `scripts/test-wake-repository-codespace.py` using in-memory fake API responses. Cover exactly:

```python
# newest matching repository Codespace is selected
# already Available -> no POST, returns name
# Shutdown -> POST start_url, then polls until Available
# POST HTTP 409 -> tolerated, then polls
# no matching repository -> SystemExit
# timeout before Available -> SystemExit
# non-409 HTTP error -> SystemExit
```

The fake `request_fn(method, url)` must record calls so assertions prove whether POST occurred.

- [ ] **Step 2: Run RED**

```bash
python3 scripts/test-wake-repository-codespace.py
```

Expected: import/file-not-found failure for `wake-repository-codespace.py`.

- [ ] **Step 3: Implement the helper by moving, not redesigning, the proven standalone logic**

Use Python stdlib only. Preserve these exact API semantics from the existing standalone workflow:

```text
GET  https://api.github.com/user/codespaces?per_page=100
POST selected.start_url or /user/codespaces/{name}/start when state != Available
GET  https://api.github.com/user/codespaces/{name} every 7 seconds
PASS only when state == Available
HTTP 409 from POST is tolerated
all other HTTP errors fail
420-second deadline
```

`main()` must require a non-empty `CODESPACE_LIFECYCLE_TOKEN`; never print the token.

- [ ] **Step 4: Run unit GREEN**

```bash
python3 scripts/test-wake-repository-codespace.py
python3 -m py_compile scripts/wake-repository-codespace.py scripts/test-wake-repository-codespace.py
```

Expected: both PASS / exit 0.

- [ ] **Step 5: Commit helper**

```bash
git add scripts/wake-repository-codespace.py scripts/test-wake-repository-codespace.py
git commit -m "refactor: share Codespace readiness helper"
```

## Task 3: Make standalone Wake consume the shared helper

**Files:**
- Modify: Renderer `.github/workflows/nasdaq-cafe-codespace-wake.yml`
- Modify: Renderer `scripts/test_codespace_wake_gateway.py`

**Interfaces:**
- Consumes: `scripts/wake-repository-codespace.py`
- Preserves: existing request schema `{requestVersion:"1.0", confirmation:"WAKE_CODESPACE"}` and wake receipt Artifact contract

- [ ] **Step 1: Extend the existing gateway test**

Require the workflow to contain:

```text
python3 scripts/wake-repository-codespace.py
--repository "$GITHUB_REPOSITORY"
--github-output "$GITHUB_OUTPUT"
```

and forbid inline Codespaces REST URLs/Python `urllib` implementation in the YAML.

- [ ] **Step 2: Run RED against the current inline workflow**

```bash
python3 scripts/test_codespace_wake_gateway.py
```

Expected: failure stating the shared helper invocation is missing.

- [ ] **Step 3: Replace only the `Start the most recently used repository Codespace` inline Python body**

The workflow step becomes:

```yaml
- name: Start the most recently used repository Codespace
  id: wake
  shell: bash
  env:
    CODESPACE_LIFECYCLE_TOKEN: ${{ secrets.CODESPACE_LIFECYCLE_TOKEN }}
  run: |
    set -euo pipefail
    python3 scripts/wake-repository-codespace.py \
      --repository "$GITHUB_REPOSITORY" \
      --github-output "$GITHUB_OUTPUT"
```

Keep the existing receipt/upload steps unchanged.

- [ ] **Step 4: Run GREEN**

```bash
python3 scripts/test_codespace_wake_gateway.py
python3 scripts/test-wake-repository-codespace.py
```

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/nasdaq-cafe-codespace-wake.yml scripts/test_codespace_wake_gateway.py
git commit -m "refactor: route Wake gateway through shared helper"
```

## Task 4: Insert runner readiness into Current Final V2 at the owning boundary

**Files:**
- Modify: Renderer `.github/workflows/nasdaq-cafe-final-v2.yml`
- Modify: Renderer `scripts/test-final-v2-runner-readiness.py`

**Interfaces:**
- Consumes: `preflight.outputs.already_completed`, shared helper, `CODESPACE_LIFECYCLE_TOKEN`
- Produces: a successful `wake-codespace` job before the self-hosted render when and only when a new Final is required

- [ ] **Step 1: Add the wake job after `preflight`**

The job must be structurally equivalent to:

```yaml
wake-codespace:
  needs: preflight
  if: needs.preflight.outputs.already_completed != 'true'
  runs-on: ubuntu-24.04
  timeout-minutes: 12
  steps:
    - uses: actions/checkout@v6
      with:
        ref: ${{ github.sha }}
        fetch-depth: 1
        persist-credentials: false
        clean: true
    - name: Wake registered Codespace runner
      id: wake
      shell: bash
      env:
        CODESPACE_LIFECYCLE_TOKEN: ${{ secrets.CODESPACE_LIFECYCLE_TOKEN }}
      run: |
        set -euo pipefail
        python3 scripts/wake-repository-codespace.py \
          --repository "$GITHUB_REPOSITORY" \
          --github-output "$GITHUB_OUTPUT"
    - name: Record runner readiness
      shell: bash
      run: |
        echo "stage=GITHUB_ACTIONS" >> "$GITHUB_STEP_SUMMARY"
        echo "status=PASS" >> "$GITHUB_STEP_SUMMARY"
        echo "codespace=${{ steps.wake.outputs.name }}" >> "$GITHUB_STEP_SUMMARY"
        echo "state=${{ steps.wake.outputs.state }}" >> "$GITHUB_STEP_SUMMARY"
```

- [ ] **Step 2: Gate the self-hosted job on both preflight and wake**

Change the Final job to:

```yaml
needs: [preflight, wake-codespace]
if: >-
  always() &&
  needs.preflight.result == 'success' &&
  needs.preflight.outputs.already_completed != 'true' &&
  needs.wake-codespace.result == 'success'
```

Do not change any Final render steps.

- [ ] **Step 3: Run orchestration GREEN**

```bash
python3 scripts/test-final-v2-runner-readiness.py
python3 scripts/test-current-preview-final-identity-contract.py
python3 scripts/test-final-control-plane-renderer-boundary.py
```

Expected: all PASS.

- [ ] **Step 4: Run affected suite**

```bash
npm ci
npm run typecheck
python3 scripts/test-wake-repository-codespace.py
python3 scripts/test_codespace_wake_gateway.py
python3 scripts/test-final-v2-runner-readiness.py
```

Then require GitHub Actions on the exact PR head:

```text
Current Preview Final Identity CI = success
Visual Story Engine CI = success
Visual Story Media CI = success
```

- [ ] **Step 5: Review the diff against protected invariants**

The PR must show:

```text
NO change to final-render request schema
NO change to Final authorization bundle schema
NO change to approved Renderer checkout identity
NO change to render-approved-current-final.ts
NO semantic/editorial file changes
NO second wake workflow
```

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/nasdaq-cafe-final-v2.yml scripts/test-final-v2-runner-readiness.py .github/workflows/current-preview-final-identity-ci.yml
git commit -m "fix: make Current Final own runner readiness"
```

## Task 5: Verify behavior without creating a new production semantic path

**Files:** none required beyond Task 4.

- [ ] **Step 1: Verify an already-completed fingerprint is idempotent**

Use the existing successful 2026-08-17 Final fingerprint through the existing validator/preflight tests. Expected behavior is `ALREADY_COMPLETED`; `wake-codespace` and self-hosted Final must both be skipped.

- [ ] **Step 2: Do not manufacture a second real Final solely to test wake**

The real new-Final wake path is verified in `2026-09-02-fresh-episode-production-qualification.md`, where a legitimate fresh episode provides a new Final fingerprint.

## Review / rollback

Rollback is one Renderer PR revert. Because the standalone Wake continues to use the same shared helper, rollback of Final ownership does not remove diagnostic Wake capability.

Block merge if:

- the helper changes Codespace selection semantics beyond extraction;
- Final can wake before authorization preflight succeeds;
- Final wakes for an already completed fingerprint;
- any Final render/semantic identity contract changes;
- the new regression did not demonstrate RED before implementation.
