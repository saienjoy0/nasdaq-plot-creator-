# Current Production Reliability Closure — Repair Design

**Status:** REVIEW_REQUIRED  
**Classification:** `CASCADE_DETECTED` / `ARCHITECTURE_REVIEW_REQUIRED`  
**Coordinator:** `skills/nasdaq-cafe-production-reliability/SKILL.md`  
**Protocol:** `skills/nasdaq-cafe-production-reliability/references/REPAIR_DESIGN_PROTOCOL.md`

## Problem statement

The 2026-08-17 Current production path eventually produced a valid Final, but successive attempts exposed multiple different first broken boundaries: cross-repo Artifact authentication, TTS block identity inference, Final control-plane/version drift, sleeping self-hosted Codespace runner, approved-byte restore assumptions, checkout ordering, and legacy Final approval coupling. Those individual defects are repaired, but architecture review finds two remaining reliability gaps:

1. Current Final V2 still depends on a separately-triggered Codespace Wake request when the self-hosted runner is asleep.
2. Plot and Renderer `main` are not repository-enforced fail-closed branches; source PR gates exist, but GitHub currently permits direct/bypassed updates because no active ruleset protects `main`.

A third verification gap remains: the Exact Cross-Repo Current E2E is synthetic by design, while the only complete real-day Preview→Final closure proven after the repairs is 2026-08-17. A fresh episode must prove date/content independence.

## Protected invariants

The repair MUST preserve all of the following:

- `scripts/current_production_facade_v12.py` remains the sole public Current production facade in Plot.
- GitHub Actions remains mechanical and MUST NOT author market causality, narration, Scene order, Visual Beat meaning, Candidate choice, Critic decision, or image adoption.
- Formal main Preview remains compile-only after semantic readiness PASS.
- Final MUST NOT start before explicit user Final approval and a valid Plot Final authorization bundle.
- No second Current state machine, second Renderer handoff, hidden fallback, or synthetic legacy approval evidence may be introduced.
- Immutable Preview identity, Renderer commit, Registry SHA, RenderSpec SHA, TTS input SHA, block-audio SHA, and Final fingerprint remain exact authorities.
- Existing standalone Codespace Wake remains available for diagnostics/manual recovery, but lifecycle API logic has one code owner.
- Existing path-specific CI remains the test owner; merge enforcement must not create a path-filter deadlock.
- The required merge decision for a PR must be produced by trusted base/main code, not by gate code that the same PR can modify.
- Collector behavior and editorial/Visual Intelligence semantics are out of scope.

## Approaches considered

### A. Keep manual Wake and rely on operator discipline

Keep `nasdaq-cafe-codespace-wake.yml` separate, wake Final manually when needed, keep current unprotected branches, and rely on human discipline around CI.

**Rejected:** both remaining machine prerequisites stay human-dependent.

### B. Assign runner readiness and merge safety to their owning layers — SELECTED

- Extract Codespace lifecycle logic into one Renderer helper.
- Reuse that helper from standalone diagnostic Wake and Current Final V2.
- Current Final V2 wakes the runner only after authorization preflight proves a new Final is required.
- Add a trusted merge-control plane per repository using `pull_request_target`; it executes only protected base code, inspects PR changes as data, waits for the path-specific exact-head workflows required by policy, and writes one fixed commit-status context to the PR head.
- Protect `main` in both repositories with a ruleset requiring PRs and that fixed trusted status context. Do not require path-filtered workflows directly.
- Run a fresh real-day episode through the unchanged canonical production path. Qualification succeeds only if Preview and Final complete without a manual Wake request or infrastructure retry request.

**Selected because:** it repairs ownership without creating a second production engine, makes machine prerequisites mechanical, and moves merge enforcement to a base-trusted layer that the PR being judged cannot rewrite.

### C. Replace Current production with one monolithic orchestration workflow

Combine readiness, Plot publication, Renderer Preview, user approval, Codespace lifecycle, and Final in one new workflow.

**Rejected:** it would duplicate/compete with the Current facade and authority boundaries, increase mutable coupling, and blur intentional human/semantic pauses with machine failures.

## Target architecture

```text
ChatGPT semantic authoring / Visual Intelligence
        |
        v
Plot PR
  |        trusted Plot main gate observes exact-head CI
  |        and writes "Nasdaq Cafe Required Merge Gate"
  v
Plot protected main
        |
        v
Plot compile-only production --> immutable handoff / Preview request
        |
        v
Renderer request-only PR
  |        trusted Renderer main gate observes exact-head CI
  |        and writes "Nasdaq Cafe Required Merge Gate"
  v
Renderer protected main
        |
        v
Preview --> human visual approval
        |
        v
Plot Final authorization --> Renderer Final request-only PR
        |
        v
Renderer Final V2 preflight
        |
        +-- existing Final outcome? --> PASS / no runner wake
        |
        +-- new Final required --> shared Codespace readiness helper
                                      |
                                      v
                              self-hosted Final render
                                      |
                                      v
                         immutable Final receipt/artifact
```

## Ownership decisions

### Runner readiness

Owner: Renderer Current Final control-plane (`.github/workflows/nasdaq-cafe-final-v2.yml`).

Reason: only this layer knows that explicit approval and Plot Final authorization have passed and a new self-hosted render is actually required. Waking earlier wastes compute; waking outside this path requires manual orchestration.

The GitHub Codespaces REST/polling implementation itself belongs to one shared Renderer helper.

### Merge enforcement

Owner: repository ruleset + base-trusted merge-control workflow.

Reason: source CI cannot prevent direct pushes by itself, and a gate executed from a PR head can be weakened by that same PR. The trusted control plane therefore runs from protected base/main (`pull_request_target`), never executes PR code, evaluates the PR as data plus exact-head workflow results, and writes the required head-commit status `Nasdaq Cafe Required Merge Gate`. Rulesets require that status.

Path-filtered CI remains authoritative test evidence but is not itself required directly, because skipped required workflows can otherwise remain pending and deadlock unrelated PRs.

### Real-day qualification

Owner: reliability verification, not production semantics.

Reason: synthetic Exact Cross-Repo E2E proves contract behavior but intentionally does not promote historical real-day artifacts into a current fixture. One fresh episode is required after the architecture repair to prove the actual environment and date-varying inputs.

## Work decomposition

Implementation is split into three independently reviewable plans:

1. `2026-09-02-final-v2-runner-readiness-integration.md`
2. `2026-09-02-required-main-merge-gates.md`
3. `2026-09-02-fresh-episode-production-qualification.md`

Order is mandatory: 1 → 2 → 3.

## Completion definition

Architecture closure is not complete until all three plans pass their gates and a fresh real-day episode proves:

- one canonical Plot PREVIEW request, with no production-request churn at intentional semantic pauses;
- one canonical Renderer Preview request;
- explicit user approval before Final;
- one canonical Final request, with no `retry-*` generated for infrastructure/control-plane reasons;
- no separate `codespace-wake-requests/*` change required during normal Final;
- exact Preview identity and Final authorization lineage preserved;
- one successful Final outcome per fingerprint;
- trusted required merge status is generated by protected base code for both repositories;
- both repository `main` branches reject updates that do not satisfy the active ruleset.
