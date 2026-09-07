# Reliability-First Visual Upgrade — Qualification and Migration Design

**Status:** REVIEW_REQUIRED  
**Classification:** `ARCHITECTURE_REVIEW_REQUIRED`  
**Date:** 2026-09-05  
**Builds on:** `docs/reliability/plans/2026-09-02-current-production-reliability-closure-design.md`  
**Related qualification:** `docs/reliability/plans/2026-09-02-fresh-episode-production-qualification.md`

## 1. Purpose

This design separates two concerns that must not be debugged at the same time:

1. proving that the repaired Current production architecture is reliable on the existing production contract; and
2. introducing the visual-development Agent Skills plus RenderSpec `2.5.0` semantic-scope contract.

The governing rule is:

> **Qualify the existing Current production path first. Then migrate visual-development capability and RenderSpec semantics in independently reviewable steps. Re-qualify after the migration.**

The objective is not merely to make draft PRs mergeable. The objective is to preserve a known-good baseline so a later failure can be attributed to one migration layer instead of triggering another cascade of unrelated patches.

## 2. Verified current state

### 2.1 Current production is at an intentional qualification boundary

The 2026-09-03 fresh qualification lineage exists in Plot PR `#192` and has reached committed semantic authority / Semantic Freeze.

PR `#192` explicitly does not publish a Preview request and cannot render Preview or Final. The present stop is therefore not evidence of an unknown machine failure. The correct next action is to continue the existing qualification plan from its first unexecuted production boundary.

Do not manufacture a 2026-09-05 production request merely to create activity.

### 2.2 Plot PR `#191` is repository-local GREEN but not cross-repo production-ready

Plot PR `#191` introduces explicit `semanticScope`, emits RenderSpec `2.5.0`, and transports the field through Plot projection code. Its trusted Required Merge Gate is GREEN.

However, the same branch still binds Renderer commit `83db1e9e204269c941f743e71c6d3ed34d8f334e` with Renderer contract `2.4.0` in `contracts/renderer_binding.json`.

Therefore `#191` MUST NOT merge until an actual Renderer `2.5.0` compatible commit has merged and Plot is rebound to that exact immutable commit and contract version.

### 2.3 Renderer PR `#223` is repository-local GREEN and backward-compatible

Renderer PR `#223` adds `2.5.0` support while retaining `2.4.0` support. Its semantic-scope regression proves that:

- `2.5.0` parses;
- Candidate Input preserves authored `semanticScope`;
- Candidate Catalog preserves authored `semanticScope`;
- Visual Director compile preserves authored `semanticScope`;
- tampered scope fails closed; and
- legacy `2.4.0` remains supported.

Its trusted Required Merge Gate is GREEN.

### 2.4 Renderer PR `#220` failed because its new persistent config path has no trusted policy owner

Renderer PR `#220` integrates pinned visual-development Agent Skills. Its Agent Skills Contract CI, Visual Story Engine CI, and Visual Story Media CI succeeded on the exact PR head.

The trusted Required Merge Gate failed because `#220` adds:

```text
config/agent-skills.lock.json
```

while trusted base `contracts/required_merge_gate_policy.json` does not classify that path and `unclassifiedNonDocs` is `FAIL`.

This is the authoritative root cause. The earlier timing/race hypothesis is superseded and is not a repair target.

### 2.5 Existing gate tests behaved correctly

Existing Required Merge Gate tests deliberately prove that unknown non-doc files fail closed. That behavior must remain.

The missing regression is an architectural ownership rule: a new persistent control/config path must receive an explicit policy owner. The repair is ownership registration, not a wildcard or fail-open exception.

## 3. Protected invariants

Implementation under this design MUST preserve all of the following:

- `scripts/current_production_facade_v12.py` remains the sole public Current production facade in Plot.
- GitHub Actions remains mechanical and does not decide market causality, narration, Scene order, Visual Beat meaning, Candidate choice, Critic decision, or Primary/Fallback adoption.
- No production runtime or GitHub Actions job fetches external Agent Skill repositories.
- Agent Skill sources are pinned to exact commits and are development-time inputs only.
- `render_spec.json` remains the Renderer-side daily editorial source of truth.
- Renderer retains RenderSpec `2.4.0` compatibility through the migration window.
- `semanticScope` is authored upstream and may not be inferred, broadened, narrowed, or rewritten by Renderer Candidate generation or Visual Director compile.
- A Renderer binding is an exact repository + commit + contract tuple; Plot never binds a floating branch.
- Required Merge Gate remains fail-closed for unclassified non-doc paths.
- The required merge decision continues to run from protected trusted base code.
- Preview requires user visual review before Final authorization.
- Final remains prohibited without explicit user approval of the exact Preview identity.
- A qualification run stops at the first newly broken machine boundary and returns to Reliability `DIAGNOSE`.

## 4. Approaches considered

### A. Merge all visual PRs first and qualify once

Merge `#220`, `#223`, and `#191`, then run one fresh episode.

**Rejected.** This combines control-plane ownership, development tooling, Renderer contract migration, and Plot producer migration into one fault domain.

### B. Reliability-first staged migration — SELECTED

1. Finish the already-started Current production qualification on the existing production contract.
2. Land a narrow Renderer control-plane prerequisite that explicitly owns `config/agent-skills.lock.json`.
3. Re-evaluate and merge `#220`.
4. Merge backward-compatible Renderer `#223`.
5. Rebind Plot `#191` to the actual merged Renderer `2.5.0` SHA, verify cross-repo compatibility, then merge it.
6. Run a different fresh episode under the migrated `2.5.0` path.
7. Stop at Preview for user review; Final occurs only after explicit approval.

**Selected because:** every migration boundary has a known owner and rollback point.

### C. Finish reliability only and postpone visual work

**Rejected as the target.** Safe, but it does not accomplish the visual-upgrade objective.

## 5. Mandatory architecture and order

```text
PHASE 0 — EXISTING CONTRACT QUALIFICATION
2026-09-03 real source / semantic freeze
  -> Current prepare
  -> ChatGPT Director
  -> compile / Critic
  -> compile PASS
  -> ONE Plot PREVIEW request
  -> ONE Renderer Preview
  -> user review
  -> explicit Final authorization only if approved
  -> ONE Final
  -> reliability evidence PASS

PHASE 1 — #220 CONTROL-PLANE PREREQUISITE
Renderer main
  -> classify exact config/agent-skills.lock.json path
  -> owner workflow = Agent Skills Contract CI
  -> unknown config paths remain unclassified
  -> merge prerequisite
  -> #220 re-evaluates against new trusted base
  -> #220 merge

PHASE 2 — RENDERER 2.5
Renderer #223
  -> keep 2.4 compatibility
  -> add 2.5 + exact semanticScope transport/protection
  -> merge
  -> capture actual merged Renderer SHA

PHASE 3 — PLOT 2.5
Plot #191
  -> renderer_binding.json = actual merged Renderer SHA
  -> renderer contractVersion = 2.5.0
  -> cross-repo exact-binding verification
  -> merge

PHASE 4 — POST-MIGRATION QUALIFICATION
new legitimate different-date episode
  -> RenderSpec 2.5.0
  -> semanticScope trace remains identical at every boundary
  -> ONE Preview
  -> user review
  -> Final only on explicit approval
```

The merge / execution order is mandatory:

```text
0. Finish current-contract fresh qualification
1. Renderer trusted policy ownership prerequisite
2. Renderer #220
3. Renderer #223
4. Update Plot #191 exact Renderer binding
5. Plot #191
6. Post-migration fresh Preview qualification
7. Explicit user review
8. Post-migration Final only if explicitly approved
```

`#220`, `#223`, and `#191` are not one atomic mega-change.

## 6. Phase 0 — finish the existing qualification before migration

Continue the 2026-09-03 lineage from Plot PR `#192`. Use the evidence contract already defined by `2026-09-02-fresh-episode-production-qualification.md` unchanged.

Phase 0 PASS requires, at minimum:

- one formal Plot Preview request created only after semantic/Visual Intelligence PASS;
- one immutable Plot handoff;
- one Renderer Preview request and one successful Preview;
- explicit user review of the exact Preview;
- one Plot Final authorization and one Renderer Final request only if the user approves;
- Final V2 runner readiness inside the normal Final path;
- no separate Wake request for a normal Final;
- no infrastructure/control-plane `retry-*` production identity; and
- exact Preview/Final lineage preservation.

If a new machine failure appears, Phase 0 stops. Visual migration does not start until the current architecture is qualified.

## 7. Phase 1 — repair `#220` ownership without weakening fail-closed behavior

### 7.1 Separate prerequisite is mandatory

Required Merge Gate evaluates the PR with trusted base/main policy via `pull_request_target`. A policy change inside `#220` cannot authorize the same PR.

Therefore a separate Renderer control-plane prerequisite PR must merge first.

### 7.2 Exact ownership decision

Do NOT classify `config/**` broadly.

Add an exact workflow group to trusted `contracts/required_merge_gate_policy.json`:

```json
{
  "name": "agent-skills",
  "patterns": [
    "config/agent-skills.lock.json"
  ],
  "workflows": [
    "Agent Skills Contract CI"
  ]
}
```

This is the selected owner. Do not substitute Visual Story Engine CI as the only owner of the lock file: the dedicated Agent Skills Contract CI is the workflow that validates pinned Skill source and synchronization/routing contract behavior.

The Required Merge Gate remains the single repository-required status. `Agent Skills Contract CI` is evidence consumed by that trusted gate, not a second branch-protection authority.

### 7.3 Why the owner may be named before it exists on main

`#220` itself introduces `Agent Skills Contract CI` and its `pull_request` path filter includes `config/agent-skills.lock.json`. Required Merge Gate already polls exact-head `pull_request` workflow runs and waits for missing/pending expected workflows. After the prerequisite policy is on main, a synchronized `#220` supplies and runs the named exact-head workflow; the trusted gate waits for its result.

The prerequisite PR itself does not add the lock file, so it does not require `Agent Skills Contract CI` for its own merge.

### 7.4 Regression contract

Add Required Merge Gate unit tests proving exactly:

```text
config/agent-skills.lock.json -> WORKFLOWS_REQUIRED
expected workflow             -> Agent Skills Contract CI
config/unknown.json           -> UNCLASSIFIED_CHANGE
mystery/unowned-control.json  -> UNCLASSIFIED_CHANGE
```

No wildcard escape hatch is allowed.

### 7.5 `#220` acceptance

After the prerequisite merges:

- synchronize/rebase `#220` against the new trusted base as required;
- require Agent Skills Contract CI PASS;
- require every other workflow selected by existing changed-path policy PASS;
- require `Nasdaq Cafe Required Merge Gate = success`;
- merge `#220`.

Production runtime and GitHub Actions still do not fetch external Skill repositories.

## 8. Phase 2 — merge Renderer `#223` before Plot emits `2.5.0`

Renderer must be upgraded first because a producer must not emit a contract the bound consumer cannot parse.

`#223` acceptance requires:

- RenderSpec schema accepts `2.4.0` and `2.5.0`;
- `semanticScope` is limited to the reviewed enum vocabulary;
- Candidate Input preserves scope exactly;
- Candidate Catalog preserves scope exactly;
- Visual Director compile rejects scope drift;
- timing/preflight paths work on `2.5.0`;
- legacy `2.4.0` regression remains GREEN; and
- exact-head Required Merge Gate succeeds.

After merge, record the **actual merged Renderer commit SHA**. A draft head SHA or hypothetical merge SHA is not a production binding authority.

## 9. Phase 3 — rebind and merge Plot `#191`

Before `#191` may merge:

1. update `contracts/renderer_binding.json` to the exact merged Renderer SHA from Phase 2;
2. set bound Renderer `contractVersion` to `2.5.0`;
3. update registry/interface hashes only if the merged Renderer actually changed those authorities;
4. fetch and test the exact bound Renderer, not `main`;
5. prove Plot materialization emits RenderSpec `2.5.0`;
6. prove strict projection preserves `semanticScope` and does not silently downgrade the schema version;
7. prove the exact bound Renderer accepts the projected result; and
8. require exact-head Required Merge Gate success.

Renderer may continue supporting `2.4.0`; that backward compatibility is the rollback boundary if Plot migration is delayed or rejected.

## 10. Phase 4 — post-migration different-date qualification

Use a legitimate episode different from the Phase 0 episode.

In addition to the normal reliability evidence, record this trace for every Visual Beat:

```text
sceneId
beatId
authored semanticScope
Plot materialized RenderSpec semanticScope
strict Renderer projection semanticScope
Renderer Candidate Input semanticScope
Candidate Catalog semanticScope
compiled RenderSpec semanticScope
```

Every value for the same Beat must be identical. Missing scope, inferred replacement, or scope drift is a contract failure and stops qualification.

The migrated path must also prove one Preview without infrastructure/control-plane retry identities.

A user rejection of the Preview for editorial/visual quality is not a machine reliability failure. It returns to the owning visual/editorial process. Final remains prohibited until the exact Preview is explicitly approved.

## 11. Failure ownership and rollback

### Phase 0 failure

Owner: existing Current production reliability.  
Action: return to Reliability `DIAGNOSE`; do not begin migration.

### Phase 1 failure

Owner: trusted Required Merge Gate policy / Agent Skill path ownership.  
Rollback: prerequisite PR only; no runtime behavior has changed.

### Phase 2 failure

Owner: Renderer `2.5.0` compatibility.  
Rollback: do not merge `#223`; Plot remains on the existing contract.

### Phase 3 failure

Owner: Plot producer migration or exact cross-repo binding.  
Rollback: do not merge `#191`; Renderer can safely retain backward-compatible `2.5.0` support.

### Phase 4 failure

Owner: the first broken boundary shown by evidence.  
The Phase 0 qualification is the known-good pre-migration baseline.

## 12. Test strategy

### Control plane

- exact Agent Skill lock path classification;
- unknown config remains fail-closed;
- unknown non-doc remains fail-closed;
- trusted base execution model unchanged.

### Agent Skills

- exact 40-hex pinned upstream commits;
- deterministic materialization receipts;
- routing contract preserves Visual Director authority;
- no production-time network fetch.

### Renderer

- `2.4.0` compatibility;
- `2.5.0` validation;
- semanticScope exact transport;
- semanticScope tamper detection;
- timing/preflight compatibility.

### Plot

- explicit semanticScope required in Current authoring;
- new Current materialization emits `2.5.0`;
- renderer-source normalization preserves the actual schema version;
- strict projection preserves semanticScope;
- exact Renderer binding points to the merged `2.5.0` consumer.

### Cross-repo

- exact bound Renderer checkout succeeds;
- Plot `2.5.0` validates in that exact Renderer;
- Candidate/Director semantic-scope trace is lossless;
- no floating/fallback Renderer is used.

### Real production

Two separate real-day proofs are required:

1. pre-migration Current production qualification; and
2. post-migration different-date qualification.

The second does not replace the first.

## 13. Completion definition

The migration is complete only when:

- a fresh real-day Current production qualification passes before visual migration;
- `config/agent-skills.lock.json` has the explicit trusted `Agent Skills Contract CI` owner;
- unknown paths still fail closed;
- `#220` merges with pinned development-only Skill behavior and no runtime fetch;
- Renderer main supports both `2.4.0` and `2.5.0` at the migration boundary;
- Plot is rebound to the exact merged Renderer `2.5.0` commit before new `2.5.0` production materialization reaches main;
- every authored semanticScope survives unchanged through Plot, strict projection, Candidate Input, Candidate Catalog, and compile;
- a different fresh episode reaches successful Preview without infrastructure/control-plane retry identities;
- the user reviews the exact Preview; and
- Final is produced only if the user explicitly requests it.

## 14. Non-goals

This design does not:

- redesign market causality or the nine-scene editorial structure;
- let Agent Skills author production semantics;
- create speculative visual templates;
- replace the Current facade;
- create a new orchestration engine;
- auto-approve Preview or Final;
- weaken merge-policy classification to make a draft PR pass; or
- treat repository-local GREEN status as sufficient evidence of cross-repository production compatibility.
