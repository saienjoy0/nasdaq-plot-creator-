# Reliability-First Visual Upgrade Sequencing — Design

**Status:** REVIEW_REQUIRED  
**Classification:** `ARCHITECTURAL` / `RELIABILITY_QUALIFICATION_REQUIRED`  
**Date:** 2026-09-05  
**Scope:** Current production reliability qualification, Agent Skill merge ownership, RenderSpec 2.5 semanticScope cross-repo rollout  
**Predecessor:** `docs/reliability/plans/2026-09-02-current-production-reliability-closure-design.md`

## Decision summary

Do **not** merge the open visual-upgrade PRs as one undifferentiated batch.

The production path will be advanced in two isolated stages:

1. **Prove the repaired Current 2.4 production path first** with the already-frozen 2026-09-03 qualification episode through Preview and, only after explicit user approval, Final.
2. **Then introduce the visual-upgrade development changes** in dependency order: merge-control ownership repair for the Agent Skill lock path, Agent Skill integration, Renderer 2.5 compatibility, Plot 2.5 authoring/binding, then a fresh cross-repo regression.

This sequencing preserves causal isolation: a failure before the visual upgrade is a reliability defect; a failure introduced after RenderSpec 2.5 is a visual-contract rollout defect.

## Current evidence and diagnosis

### Current production is not presently stuck on a machine failure

The 2026-09-03 qualification PR has already proven Collector binding, Current Authoring v2 closure, Editorial Semantic Boundary, Semantic Freeze creation, and strict Semantic Freeze verification. Its scope intentionally stops before Preview publication. Therefore the current production state is an **intentional qualification boundary**, not evidence of a new production outage.

### PR #220 is a merge-control ownership problem, not a failed visual Skill implementation

Renderer PR #220 adds `config/agent-skills.lock.json` and the Agent Skill routing/sync contract. Its dedicated Agent Skills CI and the existing Visual Story Engine / Media workflows succeed.

The trusted required-merge policy on Renderer main is fail-closed for unclassified non-doc paths. The new `config/agent-skills.lock.json` path is not owned by the current policy, so the trusted gate can reject the PR even though the relevant Skill tests pass.

This is the intended fail-closed behavior exposing a missing ownership registration. The repair must register the exact new control path and add a regression proving future control files cannot silently bypass policy.

### PR #191 and PR #223 are not the same failure class as #220

Plot PR #191 and Renderer PR #223 both have successful trusted Required Merge Gate status on their current heads.

Renderer #223 already carries RenderSpec 2.5 `semanticScope` through Renderer parsing, Candidate input/catalog, Visual Director compilation, and timing/preflight while retaining 2.4 compatibility.

Plot #191 authors `semanticScope` and emits RenderSpec 2.5, but its branch still binds to a Renderer 2.4 commit/contract. Therefore it is not cross-repo production-complete until the actual merged Renderer 2.5 commit is known and the Plot binding is updated to that exact immutable commit and contract version.

## Protected invariants

All existing Current production invariants remain in force:

- `scripts/current_production_facade_v12.py` remains the sole public Plot Current production facade.
- GitHub Actions, Codex, and Remotion remain mechanical executors; they do not rewrite narration, market causality, Scene order, Visual Beat meaning, Candidate choice, counter-evidence, confidence, or image-adoption decisions.
- Preview remains compile-only after semantic readiness PASS.
- Final remains impossible before explicit user Final approval and valid authorization lineage.
- Preview identity, Renderer commit, Registry SHA, RenderSpec SHA, TTS identity, audio hashes, and Final fingerprint remain immutable authorities.
- No second Current state machine, hidden compatibility path, silent downgrade, or auto-Final path may be introduced.
- RenderSpec 2.4 remains supported during the 2.5 rollout until fresh cross-repo qualification passes.
- Agent Skill repositories are development-time inputs only; normal production and GitHub Actions do not fetch or execute external Skill repositories.
- External visual Skills may improve diagnosis, visual translation, motion, and implementation guidance, but may not override approved editorial semantics or the Visual Director ownership model.
- Main protection remains fail-closed. New control paths must be explicitly classified rather than covered by a broad permissive wildcard solely to make a PR pass.

## Approaches considered

### A. Reliability-first staged rollout — SELECTED

1. Complete the existing 2026-09-03 Current 2.4 qualification through Preview.
2. Require human visual inspection.
3. Proceed to Final only after an explicit user Final request.
4. Record the Current 2.4 path as qualified if no infrastructure/control-plane retry or manual wake workaround is required.
5. Repair the Renderer merge-control ownership gap for the Agent Skill lock path in a small trusted-base change.
6. Re-evaluate and merge the Agent Skill integration.
7. Merge Renderer 2.5 backward-compatible semanticScope support.
8. Update Plot 2.5 binding to the exact merged Renderer commit, then complete Plot 2.5 rollout.
9. Run a different fresh episode through the 2.5 cross-repo path and compare with the qualified 2.4 baseline.

**Why selected:** failures remain attributable to one layer, rollback remains cheap, and the existing repaired production spine is proven before interface expansion.

### B. Visual-first combined rollout

Merge the Skill and 2.5 changes before the first fresh qualification, then qualify once.

**Rejected:** a subsequent failure cannot be cleanly attributed to reliability infrastructure versus the new visual contract.

### C. Freeze all visual work until a later project

Finish reliability qualification and defer #220/#223/#191 indefinitely.

**Rejected:** safest operationally but does not advance the stated goal of improving the visual system once the baseline is proven.

## Target sequence

```text
PHASE 0 — BASELINE QUALIFICATION (no 2.5 changes)
2026-09-03 frozen semantic authority
        |
        v
Current 2.4 Preview request
        |
        v
Renderer Preview
        |
        v
USER VISUAL REVIEW
        |
        +-- not approved --> stop; no Final
        |
        +-- explicit Final request
                 |
                 v
        Plot Final authorization
                 |
                 v
        Renderer Final V2
                 |
                 v
        Reliability qualification receipt

PHASE 1 — DEVELOPMENT CONTROL OWNERSHIP
small Renderer control-plane PR
  exact ownership for config/agent-skills.lock.json
  + regression for new control-path classification
        |
        v
trusted main merge
        |
        v
re-evaluate PR #220 on new trusted base
        |
        v
merge Agent Skill integration

PHASE 2 — RENDERER CONTRACT FIRST
Renderer PR #223
  2.4 + 2.5 compatibility
  semanticScope transport/protection
        |
        v
merge and capture exact Renderer SHA

PHASE 3 — PLOT CONTRACT + IMMUTABLE BINDING
Plot PR #191
  author semanticScope
  emit 2.5
  bind exact merged Renderer SHA
  bind contractVersion 2.5.0
        |
        v
cross-repo contract verification
        |
        v
merge Plot

PHASE 4 — FRESH 2.5 QUALIFICATION
new date/content episode
        |
        v
Collector -> authoring -> freeze -> compile -> Preview
        |
        v
human visual review
        |
        +-- explicit Final request only --> Final
        |
        v
2.5 qualification / regression report
```

## Phase 0 — Current 2.4 baseline qualification

### Input authority

Use the existing 2026-09-03 qualification semantic authority. Do not silently regenerate the episode from newer news or alter editorial meaning merely to make the pipeline easier to run.

### Required proof

Qualification succeeds only if the canonical production route demonstrates:

- one semantic-authority lineage;
- one canonical Plot Preview publication path;
- one canonical Renderer Preview request;
- successful Preview artifact generation;
- no infrastructure `retry-*` request churn;
- no separate manual Codespace wake required for the normal Final path;
- explicit user approval before any Final request;
- exact Preview identity preserved into Final authorization;
- one successful Final outcome for the approved fingerprint, if Final is explicitly requested.

If the user does not request Final, Phase 0 may prove Preview reliability but **must not be recorded as full Preview→Final qualification**.

## Phase 1 — Agent Skill merge-control ownership repair

### Root cause

The trusted merge controller correctly rejects unclassified non-doc changes. `config/agent-skills.lock.json` is a new control file whose owner is absent from the current trusted policy.

### Repair boundary

Create a **small, separate Renderer control-plane PR** from current trusted main. It must:

1. classify the exact Agent Skill lock path under the appropriate existing or new workflow group;
2. require the exact-head workflow evidence that owns the lock/routing contract;
3. add a policy regression that demonstrates:
   - the known Agent Skill lock path is classified and requires its owner workflow;
   - an unknown sibling control path still fails closed;
4. avoid a broad `config/**` allow rule unless every config path truly shares the same owner and test contract;
5. make no production rendering or visual-semantic behavior changes.

### Why #220 cannot self-repair this safely

The Required Merge Gate intentionally checks the PR using trusted base/main code. A policy edit inside #220 cannot be treated as trusted authority for evaluating #220 itself. The control-plane ownership repair must first land on main; only then should #220 be re-evaluated against the new trusted base.

## Phase 2 — Renderer 2.5 compatibility first

Renderer is the downstream consumer, so backward-compatible acceptance must exist before Plot publishes 2.5 as a production contract.

The Renderer merge must prove:

- `2.4.0` remains accepted;
- `2.5.0` is accepted;
- `semanticScope` accepts only the reviewed enum;
- authored scope survives Candidate input and Candidate Catalog;
- Visual Director compilation cannot mutate semantic scope;
- tampered/drifted scope fails closed;
- timing, static layout, Visual Story validation, and media tests remain GREEN;
- no Renderer AI logic is introduced to infer semantic scope when the producer omits it.

After merge, record the exact Renderer commit SHA. This SHA becomes the only valid target for Plot binding in Phase 3.

## Phase 3 — Plot 2.5 authoring and exact Renderer binding

Plot may emit 2.5 only after the compatible Renderer commit is merged and immutable.

Before Plot merge:

- update `contracts/renderer_binding.json` to the exact merged Renderer SHA;
- set the bound Renderer contract version to `2.5.0`;
- refresh any frozen interface/registry hashes only from the exact bound Renderer source and only through the existing authoritative process;
- ensure authoring requires explicit `semanticScope` rather than inferring it from template, ticker, Scene number, or narration;
- ensure renderer-source normalization and strict projection preserve 2.5 rather than silently downgrading to 2.4;
- run exact cross-repo contract verification using the same Renderer SHA written into the binding.

A GREEN Plot PR with a stale 2.4 Renderer binding is insufficient for production merge.

## Phase 4 — Fresh 2.5 regression qualification

Use a different date/content episode from the 2026-09-03 baseline. The purpose is to prove the new field is date/content independent and does not work only because fixtures were authored around one known episode.

Required observations:

- semanticScope is explicitly authored for every production Visual Beat;
- no scope is invented by GitHub Actions or Renderer runtime;
- Candidate selection remains semantically compatible with scope;
- Preview completes without new manual compatibility steps;
- representative frames are reviewed for screen meaning, not just schema validity;
- 2.4 regression remains GREEN in CI during the qualification window;
- Final occurs only after a separate explicit user request.

## Failure handling and rollback

### Phase 0 failure

Treat as a Current reliability defect. Do not proceed to the 2.5 rollout. Diagnose the first broken production boundary under the reliability protocol.

### Phase 1 failure

Keep #220 unmerged. Repair only trusted merge-control ownership/tests. Do not weaken fail-closed behavior globally.

### Phase 2 failure

Keep Renderer main on 2.4. Plot #191 remains unmergeable as a production 2.5 publisher.

### Phase 3 failure

Keep Plot main on the qualified 2.4 contract. Do not point Plot at an unmerged Renderer branch or floating ref.

### Phase 4 failure

The qualified 2.4 baseline remains the operational reference. Revert or hold the specific 2.5 rollout layer that introduced the regression; do not rewrite the episode semantics to hide the failure.

## Test ownership

The rollout must use the smallest authoritative tests per boundary:

- trusted merge-policy classification tests own control-path ownership;
- Agent Skills Contract CI owns lock/source/routing materialization rules;
- Renderer semantic-scope regression owns 2.4/2.5 parsing and scope transport/protection;
- existing Visual Story Engine / Media CI own Renderer visual/runtime regressions;
- Plot Current Authoring parity and semantic-boundary tests own explicit authoring and projection;
- exact cross-repo verification owns immutable Plot→Renderer binding compatibility;
- real-day qualification owns environment/date independence and production orchestration behavior.

No new monolithic test suite should duplicate all of these owners.

## Completion definition

This design is complete only when all of the following are true:

1. The repaired Current 2.4 path has a fresh qualification result clearly labeled Preview-only or Preview→Final depending on explicit user Final approval.
2. Agent Skill control-path ownership is encoded in trusted Renderer main and unknown control paths remain fail-closed.
3. PR #220 (or its replacement) passes the trusted gate from the repaired base and merges without production runtime Skill fetching.
4. Renderer 2.5 support merges first and its exact commit SHA is recorded.
5. Plot 2.5 binding points to that exact Renderer SHA and contract 2.5.0 before Plot merge.
6. Exact cross-repo verification passes on those exact merged authorities.
7. A different fresh episode proves the 2.5 path through Preview without retry churn or manual compatibility intervention.
8. Human review remains the Preview→Final boundary; no automatic Final is introduced.
9. Existing 2.4 compatibility tests remain GREEN until 2.5 fresh qualification is accepted.

## Explicit non-goals

- Rewriting the 9-scene editorial structure.
- Changing market causality or episode narration while qualifying infrastructure.
- Allowing GitHub Actions or Renderer runtime to choose semantic scope.
- Replacing the Current production facade.
- Introducing a second visual state machine.
- Auto-updating external Agent Skills from floating branches/tags.
- Auto-rendering Final after Preview.
- Broadly weakening required merge policy to make development PRs easier to merge.
