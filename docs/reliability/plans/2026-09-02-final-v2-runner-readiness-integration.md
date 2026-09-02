# Current Final V2 Runner Readiness Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `nasdaq-cafe-production-reliability` as coordinator and `superpowers:test-driven-development` for every code task. Use `superpowers:verification-before-completion` before any success claim.

**Goal:** Make an explicitly authorized Current Final progress from successful authorization preflight to the self-hosted Renderer without a separate human/ChatGPT Codespace Wake request.

**Architecture:** Current Final V2 owns the decision that a new Final actually needs runner readiness. One shared Renderer Python helper owns GitHub Codespaces lifecycle API behavior; the standalone diagnostic Wake workflow and Current Final V2 both call it. The Final render procedure, approved Renderer commit, Preview identity, RenderSpec, TTS bytes, and Final fingerprint remain unchanged.

**Tech Stack:** GitHub Actions YAML, Python 3.12 stdlib, GitHub Codespaces REST API, existing Renderer Current Final V2.

**Spec:** `docs/reliability/plans/2026-09-02-current-production-reliability-closure-design.md`

## Global Constraints

- Final MUST NOT start before explicit user Final approval and valid Plot Final authorization.
- Do not change narration, Scene order, Visual Beat meaning, RenderSpec bytes, TTS bytes, Registry identity, Renderer binding, or Final fingerprint semantics.
- Do not create a second Final workflow/state machine.
- Codespace REST/polling behavior has one code owner.
- Existing standalone `Nasdaq Cafe Codespace Wake` remains available for diagnostics/manual recovery.
- Missing `CODESPACE_LIFECYCLE_TOKEN`, no matching repository Codespace, timeout, or non-409 HTTP failure must fail closed before the self-hosted Final job.
- An already-completed Final fingerprint must not wake a Codespace.

---

**Root cause:** Current Final V2 schedules the Final job directly on `[self-hosted, linux, x64, nasdaq-cafe-codespace]` but does not own runner readiness. When the Codespace sleeps, an otherwise authorized Final waits indefinitely until a separate wake request is merged.

**First broken boundary:** `GITHUB_ACTIONS` — self-hosted runner readiness.

**Evidence:** authorized Final runs remained queued after successful preflight; the same queued Final acquired its runner immediately after the standalone Wake workflow made the repository Codespace `Available`.

**Why existing tests missed it:** tests proved the standalone Wake gateway and Final identity/control-plane contracts separately, but no regression required Current Final V2 to own the boundary between authorization preflight and the self-hosted job.

## Current code path

```text
.github/workflows/nasdaq-cafe-final-request-v2.yml
  resolve
    -> scripts/validate-current-request.py final
  final (reusable)
    -> .github/workflows/nasdaq-cafe-final-v2.yml
       preflight (ubuntu)
         -> existing Final outcome lookup
         -> Plot Final authorization Artifact verification
       [MISSING RUNNER READINESS OWNER]
       final (self-hosted nasdaq-cafe-codespace)
         -> approved Preview restore
         -> exact TTS re-verification
         -> approved Renderer cache-only compile
         -> render-approved-current-final.ts
```

## Working analogue

- `.github/workflows/nasdaq-cafe-final-request.yml` already has `wake-codespace` before its Final execution.
- `.github/workflows/nasdaq-cafe-codespace-wake.yml` already proves the desired lifecycle semantics: select the most recently used Codespace for the repository, start it when needed, tolerate start HTTP 409, poll to `Available`, and fail on timeout/other API failures.

The repair extracts and reuses this behavior; it does not invent another lifecycle protocol.

## Repair hypothesis

I think the remaining Final queue failure is caused by runner readiness being owned outside Current Final V2, because the exact queued Final proceeds after the standalone Wake reaches `Available`; moving the proven readiness behavior behind a shared helper and invoking it after successful Final preflight should eliminate the manual boundary without changing Final authorization or render semantics.

## File map

| File | Action | Responsibility |
|---|---|---|
| Renderer `scripts/wake_repository_codespace.py` | create | sole Codespaces REST + polling implementation |
| Renderer `scripts/test_wake_repository_codespace.py` | create | selection/start/poll/error unit regression |
| Renderer `scripts/test_final_v2_runner_readiness.py` | create | Final V2 orchestration regression |
| Renderer `.github/workflows/nasdaq-cafe-codespace-wake.yml` | modify | use shared helper, preserve diagnostic request/receipt contract |
| Renderer `.github/workflows/nasdaq-cafe-final-v2.yml` | modify | add runner-readiness job after preflight and before self-hosted Final |
| Renderer `.github/workflows/current-preview-final-identity-ci.yml` | modify | run new tests and syntax checks |

## Shared helper interface

Create `scripts/wake_repository_codespace.py` with these exact public functions:

```python
def request_json(method: str, url: str, token: str) -> dict | None:
    """Call GitHub Codespaces REST API; return decoded JSON or None for empty body.

    Raise CodespaceApiError(status_code, response_text) on HTTP failure.
    Never print or return the token.
    """


def select_repository_codespace(listing: dict, repository: str) -> dict:
    """Return the matching repository Codespace with the newest last_used_at/updated_at.

    Raise CodespaceWakeError if no matching Codespace exists.
    """


def ensure_available(
    repository: str,
    token: str,
    *,
    request_fn=request_json,
    sleep_fn=time.sleep,
    monotonic_fn=time.monotonic,
    timeout_seconds: int = 420,
    poll_seconds: int = 7,
) -> str:
    """Return Codespace name only after its state is Available."""
```

Define:

```python
class CodespaceApiError(RuntimeError):
    def __init__(self, status_code: int, response_text: str): ...

class CodespaceWakeError(RuntimeError):
    pass
```

CLI contract:

```text
python3 scripts/wake_repository_codespace.py \
  --repository "$GITHUB_REPOSITORY" \
  --github-output "$GITHUB_OUTPUT"
```

`CODESPACE_LIFECYCLE_TOKEN` is read from the environment. On success append exactly:

```text
name=<actual Codespace name>
state=Available
```

to the provided GitHub output file.

## Task 1: RED — capture the missing Final V2 readiness owner

**Files:**
- Create Renderer `scripts/test_final_v2_runner_readiness.py`
- Modify Renderer `.github/workflows/current-preview-final-identity-ci.yml`

- [ ] **Step 1: Write workflow-contract assertions**

The test reads `.github/workflows/nasdaq-cafe-final-v2.yml` and `.github/workflows/nasdaq-cafe-codespace-wake.yml` and requires:

```text
Final V2 has a wake-codespace job
wake-codespace needs preflight
wake is suppressed when preflight says already_completed=true
Final self-hosted job needs [preflight, wake-codespace]
Final self-hosted job requires wake-codespace success
both workflows call scripts/wake_repository_codespace.py
neither workflow contains the Codespaces REST URL or urllib implementation
```

Before implementation, the first assertion must raise:

```text
AssertionError: Current Final V2 does not own Codespace readiness
```

- [ ] **Step 2: Add the test to Current Preview Final Identity CI**

Add both new test paths to the workflow `pull_request.paths`, run:

```bash
python3 scripts/test_final_v2_runner_readiness.py
```

and include both new Python files in `python3 -m py_compile` when they exist.

- [ ] **Step 3: Run RED**

```bash
python3 scripts/test_final_v2_runner_readiness.py
```

Expected: the exact assertion above.

- [ ] **Step 4: Commit RED only**

```bash
git add scripts/test_final_v2_runner_readiness.py .github/workflows/current-preview-final-identity-ci.yml
git commit -m "test: require Current Final runner readiness"
```

## Task 2: RED/GREEN — extract the single Codespace lifecycle owner

**Files:**
- Create Renderer `scripts/wake_repository_codespace.py`
- Create Renderer `scripts/test_wake_repository_codespace.py`

- [ ] **Step 1: Write unit tests using injected fake transport/time functions**

Cover exactly:

```text
newest matching repository Codespace is selected
already Available -> no POST, return name
Shutdown -> POST start_url, poll until Available
POST CodespaceApiError(409, ...) -> tolerate and continue polling
no matching repository -> CodespaceWakeError
poll deadline exceeded -> CodespaceWakeError
non-409 CodespaceApiError -> propagated/fails
```

Fake `request_fn(method, url, token)` records calls and returns deterministic dicts; fake `monotonic_fn` advances deterministically so the timeout test has no real sleep.

- [ ] **Step 2: Run helper RED**

```bash
python3 scripts/test_wake_repository_codespace.py
```

Expected: import/file-not-found failure because `wake_repository_codespace.py` is not yet present.

- [ ] **Step 3: Implement minimal helper using the existing standalone semantics**

Exact endpoints/behavior:

```text
GET  https://api.github.com/user/codespaces?per_page=100
POST selected.start_url, or https://api.github.com/user/codespaces/{name}/start when state != Available
GET  https://api.github.com/user/codespaces/{name} while waiting
poll interval = 7 seconds
timeout = 420 seconds
HTTP 409 from POST = tolerated
other HTTP errors = fail
PASS only when state == Available
```

Use only Python stdlib (`urllib.request`, `urllib.error`, `json`, `time`, `argparse`, `os`).

- [ ] **Step 4: Run helper GREEN**

```bash
python3 scripts/test_wake_repository_codespace.py
python3 -m py_compile scripts/wake_repository_codespace.py scripts/test_wake_repository_codespace.py
```

- [ ] **Step 5: Commit**

```bash
git add scripts/wake_repository_codespace.py scripts/test_wake_repository_codespace.py
git commit -m "refactor: share Codespace readiness helper"
```

## Task 3: Route standalone Wake through the helper

**Files:**
- Modify Renderer `.github/workflows/nasdaq-cafe-codespace-wake.yml`
- Modify Renderer `scripts/test_codespace_wake_gateway.py`

- [ ] **Step 1: Change the existing gateway test first**

Require this command in the workflow:

```bash
python3 scripts/wake_repository_codespace.py \
  --repository "$GITHUB_REPOSITORY" \
  --github-output "$GITHUB_OUTPUT"
```

Forbid inline `https://api.github.com/user/codespaces` and `urllib.request` in the YAML.

- [ ] **Step 2: Run RED**

```bash
python3 scripts/test_codespace_wake_gateway.py
```

Expected: shared helper invocation missing.

- [ ] **Step 3: Replace only the existing inline Codespaces Python block**

Keep request validation, receipt generation, Artifact name, retention, and workflow trigger unchanged. The wake step becomes:

```yaml
- name: Start the most recently used repository Codespace
  id: wake
  shell: bash
  env:
    CODESPACE_LIFECYCLE_TOKEN: ${{ secrets.CODESPACE_LIFECYCLE_TOKEN }}
  run: |
    set -euo pipefail
    python3 scripts/wake_repository_codespace.py \
      --repository "$GITHUB_REPOSITORY" \
      --github-output "$GITHUB_OUTPUT"
```

- [ ] **Step 4: Run GREEN**

```bash
python3 scripts/test_codespace_wake_gateway.py
python3 scripts/test_wake_repository_codespace.py
```

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/nasdaq-cafe-codespace-wake.yml scripts/test_codespace_wake_gateway.py
git commit -m "refactor: route Wake gateway through shared helper"
```

## Task 4: Insert readiness into Current Final V2 at the owning boundary

**Files:**
- Modify Renderer `.github/workflows/nasdaq-cafe-final-v2.yml`
- Modify Renderer `scripts/test_final_v2_runner_readiness.py`

- [ ] **Step 1: Add `wake-codespace` after `preflight`**

Use:

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
        python3 scripts/wake_repository_codespace.py \
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

- [ ] **Step 2: Gate self-hosted Final on successful preflight + wake**

Use:

```yaml
needs: [preflight, wake-codespace]
if: >-
  always() &&
  needs.preflight.result == 'success' &&
  needs.preflight.outputs.already_completed != 'true' &&
  needs.wake-codespace.result == 'success'
```

Do not change any Final render/restore/TTS/receipt steps.

- [ ] **Step 3: Run local GREEN**

```bash
python3 scripts/test_final_v2_runner_readiness.py
python3 scripts/test-current-preview-final-identity-contract.py
python3 scripts/test-final-control-plane-renderer-boundary.py
python3 scripts/test_wake_repository_codespace.py
python3 scripts/test_codespace_wake_gateway.py
npm ci
npm run typecheck
```

- [ ] **Step 4: Require exact PR-head CI GREEN**

```text
Current Preview Final Identity CI = success
Visual Story Engine CI = success
Visual Story Media CI = success
```

- [ ] **Step 5: Review the actual diff**

Block merge if the diff changes any of:

```text
Final request schema
Final authorization bundle schema
approved Renderer checkout identity
render-approved-current-final.ts
narration/Scene/Visual semantics
Preview/Final SHA authority
```

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/nasdaq-cafe-final-v2.yml scripts/test_final_v2_runner_readiness.py .github/workflows/current-preview-final-identity-ci.yml
git commit -m "fix: make Current Final own runner readiness"
```

## Task 5: Idempotence verification without manufacturing another historical Final

- [ ] **Step 1: Exercise the existing successful 2026-08-17 fingerprint through current preflight tests**

Expected state:

```text
ALREADY_COMPLETED
wake-codespace skipped
self-hosted Final skipped
```

- [ ] **Step 2: Do not create a new 2026-08-17 Final merely to exercise wake**

The real new-Final wake path is proven in `2026-09-02-fresh-episode-production-qualification.md` with a legitimate fresh fingerprint.

## Review / rollback

Rollback is one Renderer source PR revert. The standalone diagnostic Wake remains available because it uses the same helper. If the shared helper itself is the defect, revert the helper extraction and both workflow call sites together.

Block merge if:

- the helper changes Codespace selection semantics beyond the proven standalone behavior;
- Final can wake before authorization preflight succeeds;
- Final wakes for an already-completed fingerprint;
- Final render/semantic identity changes;
- RED was not observed before implementation;
- the exact PR-head affected suites are not GREEN.
