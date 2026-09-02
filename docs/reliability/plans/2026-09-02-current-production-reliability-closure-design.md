# Current Production Reliability Closure — Repair Design

**Status:** REVIEW_REQUIRED  
**Classification:** `CASCADE_DETECTED` / `ARCHITECTURE_REVIEW_REQUIRED`  
**Coordinator:** `skills/nasdaq-cafe-production-reliability/SKILL.md`  
**Protocol:** `skills/nasdaq-cafe-production-reliability/references/REPAIR_DESIGN_PROTOCOL.md`

## Problem statement

The 2026-08-17 Current production path eventually produced a valid Final, but successive attempts exposed multiple different first broken boundaries: cross-repo Artifact authentication, TTS block identity inference, Final control-plane/version drift, sleeping self-hosted Codespace runner, approved-byte restore assumptions, checkout ordering, and legacy Final approval coupling. Those individual defects are now repaired, but the architecture review found two remaining reliability gaps:

1. Current Final V2 still depends on a separately-triggered Codespace Wake request when the self-hosted runner is asleep.
2. Plot and Renderer `main` are not repository-enforced fail-closed branches; PR gates exist in source, but GitHub currently permits direct/bypassed updates because no branch ruleset/required check protects `main`.

A third verification gap remains: the Exact Cross-Repo Current E2E is synthetic by design, while the only complete real-day Preview→Final closure proven after the repairs is 2026-08-17. A fresh episode must prove date/content independence.

## Protected invariants

The repair MUST preserve all of the following:

- `scripts/current_production_facade_v12.py` remains the sole public Current production facade in Plot.
- GitHub Actions remains mechanical and MUST NOT author market causality, narration, Scene order, Visual Beat meaning, Candidate choice, Critic decision, or image adoption.
- Formal main Preview remains compile-only after semantic readiness PASS.
- Final MUST NOT start before explicit user Final approval and a valid Plot Final authorization bundle.
- No second Current state machine, second Renderer handoff, hidden fallback, or synthetic legacy approval evidence may be introduced.
- Immutable Preview identity, Renderer commit, Registry SHA, RenderSpec SHA, TTS input SHA, block-audio SHA, and Final fingerprint remain exact authorities.
- Existing standalone Codespace Wake remains available for diagnostics/manual recovery, but lifecycle API logic must have one code owner.
- Existing path-specific CI remains useful as fast feedback; repository protection must not create a path-filter deadlock.
- Collector behavior and editorial/Visual Intelligence semantics are out of scope.

## Approaches considered

### A. Keep manual Wake and rely on operator discipline

Keep `nasdaq-cafe-codespace-wake.yml` separate and document that an operator must wake the runner after Final queues. Keep current unprotected branches and continue merging only after visually checking CI.

**Rejected:** this preserves both remaining human-dependent failure modes. It does not meet the durability goal.

### B. Assign runner readiness and merge safety to their owning layers — SELECTED

- Extract Codespace lifecycle logic into one Renderer helper.
- Reuse that helper from the existing standalone Wake workflow and from Current Final V2.
- Current Final V2 wakes the runner only after Final authorization preflight says a render is actually required, then allows the self-hosted render job to start.
- Add one always-on `Required Merge Gate` per repository. It classifies PR type and reuses existing suites; it always emits one stable final check name.
- Protect `main` in both repositories with a GitHub ruleset requiring PRs plus only the stable `Required Merge Gate`, avoiding path-filtered required-check deadlocks.
- Run a fresh real-day episode through the unchanged canonical path. Qualification succeeds only if Preview and Final complete without a manual Wake request or retry Final request.

**Selected because:** it repairs ownership without creating a second production engine, makes machine prerequisites mechanical, and makes repository policy enforce the CI contract already expected by the project.

### C. Replace the Current workflows with one monolithic orchestration workflow

Combine readiness, Plot publication, Renderer Preview, user approval state, Codespace lifecycle, and Final into one workflow.

**Rejected:** this would duplicate/compete with the Current facade and existing authority boundaries, increase mutable coupling, and make semantic/human pauses easier to misclassify as machine failures.

## Target architecture

```text
ChatGPT semantic authoring / Visual Intelligence
        |
        v
Plot PR -- Required Merge Gate --> protected main
        |
        v
Plot compile-only production --> immutable handoff / Preview request
        |
        v
Renderer request-only PR -- Required Merge Gate --> protected main
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

Reason: only this layer knows that user approval and Plot Final authorization have already passed and that a new self-hosted render is actually required. Waking earlier wastes compute; waking outside this path requires human orchestration.

The GitHub Codespaces API implementation itself is owned by a shared Renderer helper, not duplicated in workflows.

### Merge enforcement

Owner: repository configuration, with an always-on workflow contract in each repository.

Reason: source CI can describe desired policy but cannot stop direct pushes by itself. A branch ruleset must enforce the stable merge-gate check. Individual path-filtered workflows MUST NOT be required directly because request-only/docs-only PRs would leave absent checks permanently pending.

### Real-day qualification

Owner: reliability verification, not production semantics.

Reason: synthetic Exact Cross-Repo E2E proves contract behavior but intentionally does not promote a historical real-day artifact into a current fixture. One fresh episode is required after the architecture repair to prove the actual environment and date-varying inputs.

## Work decomposition

Implementation is intentionally split into three independently reviewable plans:

1. `2026-09-02-final-v2-runner-readiness-integration.md`
2. `2026-09-02-required-main-merge-gates.md`
3. `2026-09-02-fresh-episode-production-qualification.md`

Order is mandatory: 1 → 2 → 3.

## Completion definition

Architecture closure is not complete until all three plans pass their own gates and a fresh real-day episode proves:

- one canonical Plot PREVIEW request, no semantic request churn at intentional pauses;
- one canonical Renderer Preview request;
- explicit user approval before Final;
- one canonical Final request, with no `retry-*` request generated for infrastructure reasons;
- no separate `codespace-wake-requests/*` change required during the normal Final path;
- exact Preview identity and Final authorization lineage preserved;
- one successful Final outcome per fingerprint;
- both repository `main` branches reject un-gated direct updates according to the installed ruleset.
