# Reliability-First Visual Upgrade — Qualification and Migration Design

**Status:** REVIEW_REQUIRED  
**Classification:** `ARCHITECTURE_REVIEW_REQUIRED`  
**Date:** 2026-09-05  
**Builds on:** `docs/reliability/plans/2026-09-02-current-production-reliability-closure-design.md`  
**Related qualification:** `docs/reliability/plans/2026-09-02-fresh-episode-production-qualification.md`

## 1. Purpose

This design separates two concerns that must not be debugged at the same time:

1. proving that the repaired Current production architecture is reliable on the existing production contract; and
2. introducing the new visual-development toolchain and RenderSpec `2.5.0` semantic-scope contract.

The intended outcome is not merely to make the current draft PRs mergeable. The outcome is a production path where a new visual capability can be introduced without making it ambiguous whether a later failure came from the existing Current production control plane or from the new visual contract.

The governing rule is therefore:

> **Qualify the existing Current production path first. Then migrate visual-development capability and RenderSpec semantics in independently reviewable steps. Re-qualify after the migration.**

## 2. Current verified state

### 2.1 Current production reliability is not presently blocked by an unknown machine failure

The fresh episode qualification for 2026-09-03 has reached committed semantic authority / Semantic Freeze in Plot PR `#192`.

That PR explicitly does **not** publish a Preview request and cannot start Preview or Final. Therefore the present stop is an intentional qualification boundary, not evidence that the Current production path is currently broken.

The next reliability action is to continue the existing qualification plan from the first unexecuted production boundary rather than invent a new request or start a second production path.

### 2.2 Plot PR `#191` is exact-head merge-gate GREEN but cross-repo production binding is incomplete

Plot PR `#191` introduces explicit visual `semanticScope`, projects Current authoring to RenderSpec `2.5.0`, and transports the field into Renderer-oriented source material.

Its trusted required merge status is GREEN.

However, on the same branch, `contracts/renderer_binding.json` still binds Renderer commit `83db1e9e204269c941f743e71c6d3ed34d8f334e` with contract version `2.4.0`.

Therefore PR `#191` is not yet production-ready as a cross-repository change even though its repository-local merge gate is GREEN. It must not be merged until an actual Renderer `2.5.0` compatible commit is merged and Plot is rebound to that exact immutable commit and contract version.

### 2.3 Renderer PR `#223` is exact-head merge-gate GREEN

Renderer PR `#223` adds `2.5.0` compatibility while retaining `2.4.0` compatibility and carries `semanticScope` through the Candidate Input, Candidate Catalog, Visual Director compile, and relevant validation/timing surfaces.

Its dedicated semantic-scope regression verifies:

- `2.5.0` parses;
- authored `semanticScope` survives Candidate Input and Candidate Catalog;
- Visual Director compile preserves the exact authored scope;
- tampered candidate scope fails closed; and
- legacy `2.4.0` remains supported.

The trusted required merge status is GREEN.

### 2.4 Renderer PR `#220` failed for control-plane ownership classification, not because its Skill contract CI failed

Renderer PR `#220` integrates pinned visual-development Agent Skill sources and routing rules. Its relevant functional CI, including Agent Skills Contract CI, Visual Story Engine CI, and Visual Story Media CI, succeeded on the exact PR head.

The trusted Required Merge Gate failed because the PR adds `config/agent-skills.lock.json`, while the trusted base policy in `contracts/required_merge_gate_policy.json` does not classify that path. The policy is fail-closed for unclassified non-doc changes.

This is the authoritative root cause for `#220`.

A previous timing/race hypothesis is superseded by the ownership-classification evidence and must not be recorded as the repair target.

### 2.5 Why existing tests did not prevent the `#220` failure

The existing Required Merge Gate tests correctly assert that an unknown non-doc path fails closed. That behavior is desirable and must remain.

The missing protection is different: when a new persistent control/config path is introduced, there is no regression requiring that the path receive an explicit merge-policy owner at the same architectural change boundary.

The repair must therefore add **ownership registration**, not weaken fail-closed classification.

## 3. Protected invariants

All implementation under this design MUST preserve the following:

- `scripts/current_production_facade_v12.py` remains the sole public Current production facade in Plot.
- GitHub Actions remains mechanical; it does not decide market causality, narration, scene order, visual meaning, Candidate choice, Critic decision, or Primary/Fallback adoption.
- No production runtime or GitHub Actions job fetches external Agent Skill repositories.
- External Skill sources are pinned to exact commits and are development-time inputs only.
- `render_spec.json` remains the renderer-side daily editorial source of truth.
- RenderSpec `2.4.0` remains supported during the migration window until `2.5.0` is proven across the real Current path.
- `semanticScope` is authored upstream and may not be inferred, broadened, narrowed, or rewritten by Renderer Candidate generation or Visual Director compile.
- A Renderer binding is always an exact repository + commit + contract tuple; Plot does not bind a floating branch.
- Required Merge Gate remains fail-closed for unclassified non-doc changes.
- The trusted merge decision remains generated from protected base code rather than code from the PR being judged.
- Preview must be visually reviewed by the user before any Final authorization.
- Final remains prohibited without explicit user approval of the exact Preview identity.
- No qualification success may be claimed after patching forward across an uninvestigated first broken machine boundary.

## 4. Approaches considered

### A. Merge all visual PRs first, then run one new qualification

Merge `#220`, `#223`, and `#191`, then run a fresh episode through the resulting system.

**Rejected as primary approach.** It minimizes the number of qualification cycles but combines control-plane reliability, new development tooling, Renderer contract migration, and Plot contract migration into one fault domain. If the fresh episode fails, diagnosis must disentangle multiple newly changed boundaries.

### B. Reliability-first staged migration — SELECTED

1. Complete the already-started fresh Current production qualification on the existing production contract.
2. Repair the trusted ownership policy required by `#220` through a separate control-plane PR based on main.
3. Re-evaluate and merge `#220` only after the base policy recognizes its exact persistent control path.
4. Merge Renderer `#223` before Plot `#191`, retaining `2.4.0` compatibility.
5. Rebind Plot `#191` to the exact merged Renderer commit and contract `2.5.0`.
6. Run cross-repository contract verification.
7. Run a different fresh episode through Preview under the migrated path; only proceed to Final after user Preview approval.

**Selected because:** it keeps every failure attributable to one migration layer, preserves rollback points, and proves the old production path before changing the daily RenderSpec contract.

### C. Close reliability qualification and postpone all visual changes

Complete the fresh Current qualification and leave `#220`, `#223`, and `#191` unmerged indefinitely.

**Rejected as target architecture.** It is safe but does not accomplish the visual-upgrade objective.

## 5. Target migration architecture

```text
PHASE 0 — CURRENT CONTRACT QUALIFICATION
real source
  -> Current semantic authority / Semantic Freeze
  -> existing Current prepare / Director / Critic / compile PASS
  -> one Plot PREVIEW request
  -> one Renderer Preview
  -> user visual review
  -> explicit Final authorization only if approved
  -> one Final
  -> reliability qualification evidence PASS

PHASE 1 — SKILL CONTROL-PLANE OWNERSHIP
Renderer main
  -> small trusted policy PR classifies exact Agent Skill control paths
  -> regression proves new owned path + unknown path still FAIL
  -> merge policy PR
  -> #220 exact-head gate re-evaluates against new trusted base
  -> #220 merge

PHASE 2 — RENDERER 2.5 COMPATIBILITY
Renderer #223
  -> retain 2.4 support
  -> add 2.5 + semanticScope transport/protection
  -> exact-head CI + Required Merge Gate PASS
  -> merge
  -> capture immutable merged Renderer SHA

PHASE 3 — PLOT 2.5 PRODUCER MIGRATION
Plot #191
  -> update renderer_binding.json to exact merged Renderer SHA
  -> renderer contractVersion = 2.5.0
  -> preserve semanticScope from Current authoring to strict projection
  -> cross-repo tests use exact bound Renderer
  -> exact-head gate PASS
  -> merge

PHASE 4 — POST-MIGRATION QUALIFICATION
new legitimate fresh episode
  -> Current semantics
  -> RenderSpec 2.5.0
  -> semanticScope preserved at every boundary
  -> one Preview
  -> user review
  -> Final only on explicit approval
  -> no infrastructure/control-plane retries
```

## 6. Phase 0 — finish existing reliability qualification before migration

### 6.1 Qualification episode

Continue the existing 2026-09-03 qualification lineage from Plot PR `#192` because it already contains the real source binding and Semantic Freeze evidence.

Do not manufacture a 2026-09-05 production request merely to create activity. A date becomes a formal production identity only when its Current semantic package is complete and the normal production readiness boundary is satisfied.

### 6.2 Required success evidence

Use the existing `2026-09-02-fresh-episode-production-qualification.md` evidence contract unchanged.

At minimum, Phase 0 must prove:

- one formal Plot Preview request after semantic/Visual Intelligence PASS;
- one immutable handoff;
- one Renderer Preview request and successful Preview;
- explicit user visual approval before Final;
- one Plot Final authorization and one Renderer Final request if approved;
- Final V2 runner readiness occurs inside the normal Final path;
- no normal Final requires a separate Wake request;
- no infrastructure/control-plane `retry-*` production identity is created; and
- exact Preview/Final identity lineage is preserved.

If a new machine-boundary failure occurs, Phase 0 stops and returns to Reliability `DIAGNOSE`. Visual migration does not start until the current architecture is qualified.

## 7. Phase 1 — repair `#220` ownership classification without weakening fail-closed behavior

### 7.1 Why the repair must be separate from `#220`

The Required Merge Gate executes trusted base/main policy through `pull_request_target`. A policy edit contained only in `#220` cannot authorize the same PR because the gate intentionally does not trust that PR's changed control-plane code.

Therefore the ownership repair must first land in Renderer `main` through a separate, narrowly scoped control-plane PR.

### 7.2 Policy change

Do **not** classify `config/**` broadly.

Register the smallest exact set of persistent Agent Skill control files that require a trusted CI owner. At minimum this includes:

```text
config/agent-skills.lock.json
```

The preferred ownership is the existing `visual-story-engine` workflow group if the file semantically participates in the Visual Story development contract and that workflow remains the authoritative broad contract test owner.

If a dedicated `agent-skills` workflow group is added instead, it must be justified by an existing exact-head CI workflow and must not create a second overlapping required-status control plane. The trusted Required Merge Gate remains the single required repository status.

### 7.3 Regression requirements

Add tests proving all of the following:

```text
config/agent-skills.lock.json -> WORKFLOWS_REQUIRED with explicit expected owner workflow
mystery/unowned-control.json  -> UNCLASSIFIED_CHANGE
unknown config path           -> UNCLASSIFIED_CHANGE unless explicitly registered
```

The test must preserve the current fail-closed guarantee; no wildcard escape hatch may be introduced.

### 7.4 `#220` acceptance

After the control-plane repair is merged into Renderer `main`:

- update/rebase/synchronize `#220` as needed so it is evaluated against the new trusted base;
- require Agent Skills Contract CI PASS;
- require Visual Story Engine CI / other policy-selected exact-head workflows PASS;
- require `Nasdaq Cafe Required Merge Gate = success`;
- then merge `#220`.

Skill synchronization remains development-only after merge.

## 8. Phase 2 — merge Renderer `2.5.0` compatibility before Plot produces `2.5.0`

Renderer must be upgraded first because a producer must not emit a contract the bound consumer cannot parse.

`#223` acceptance requires:

- RenderSpec schema accepts `2.4.0` and `2.5.0`;
- `semanticScope` uses only the reviewed enum vocabulary;
- Candidate Input preserves scope exactly;
- Candidate Catalog preserves scope exactly;
- compile rejects semantic-scope drift;
- timing/preflight paths operate on `2.5.0`;
- legacy `2.4.0` regression remains GREEN;
- exact-head Required Merge Gate is success.

After merge, record the actual Renderer merge SHA. The hypothetical PR merge SHA or branch head is not a production binding authority.

## 9. Phase 3 — rebind and merge Plot `#191`

Before Plot `#191` may merge:

1. replace its stale Renderer binding with the exact merged Renderer SHA from Phase 2;
2. set the bound Renderer contract version to `2.5.0`;
3. update any registry/interface SHA only if the merged Renderer changed those authorities;
4. verify the exact bound Renderer can be fetched and used by the Plot Current closure tests;
5. prove RenderSpec `2.5.0` survives strict projection without removing `semanticScope`;
6. prove no unsupported contract downgrade silently rewrites `2.5.0` back to `2.4.0`; and
7. require exact-head Required Merge Gate success.

The Plot migration may continue to read historical `2.4.0` artifacts where existing compatibility explicitly permits it, but all newly materialized Current v2 production RenderSpec after the migration uses the approved `2.5.0` contract.

## 10. Phase 4 — post-migration fresh-episode qualification

The first post-migration qualification must use a legitimate episode different from the Phase 0 qualification episode.

Its purpose is to prove both production reliability and semantic-scope preservation in a date/content-independent case.

In addition to the normal reliability evidence contract, record a semantic-scope trace for every Visual Beat:

```text
sceneId
beatId
authored semanticScope
materialized Plot RenderSpec semanticScope
strict Renderer projection semanticScope
Renderer Candidate Input semanticScope
Candidate Catalog semanticScope
compiled RenderSpec semanticScope
```

All values for a Beat must be identical.

Any inferred replacement, missing field, or scope drift is a contract failure and must stop qualification.

A Preview rejection by the user for visual/editorial quality is not a machine reliability failure. It returns to the owning visual/editorial design layer. Final remains prohibited until the exact Preview is explicitly approved.

## 11. Failure ownership and rollback

### Phase 0 failure

Owner: existing Current production reliability.

Action: stop at first broken machine boundary and return to `DIAGNOSE`. Do not begin visual migration.

### Phase 1 failure

Owner: Required Merge Gate policy / Agent Skill control-file ownership.

Rollback: policy PR only. No runtime production behavior is changed.

### Phase 2 failure

Owner: Renderer `2.5.0` compatibility.

Rollback: do not merge `#223`; Plot remains bound to `2.4.0` and current production remains unchanged.

### Phase 3 failure

Owner: Plot producer migration or cross-repo binding.

Rollback: do not merge `#191`; Renderer may safely retain backward-compatible `2.5.0` support while Plot continues producing the existing contract.

### Phase 4 failure

Owner depends on the first broken boundary.

The prior Phase 0 qualification provides a known-good production baseline. This makes it possible to distinguish migration-induced regressions from pre-existing production failures.

## 12. Merge order

The merge / execution order is mandatory:

```text
0. Finish current-contract fresh qualification
1. Renderer trusted policy ownership repair
2. Renderer #220 visual-development Skill integration
3. Renderer #223 RenderSpec 2.5 compatibility
4. Update Plot #191 exact Renderer binding
5. Plot #191
6. Post-migration fresh Preview qualification
7. Explicit user review
8. Post-migration Final only if explicitly approved
```

Do not merge `#191` before the actual Renderer `2.5.0` merge SHA exists.

Do not treat `#220`, `#223`, and `#191` as one atomic mega-change.

## 13. Test strategy

### Control-plane tests

- Required Merge Gate path classification regression for the exact Agent Skill lock path.
- Unknown non-doc and unknown config paths still fail closed.
- Trusted base/main execution model remains unchanged.

### Skill integration tests

- pinned 40-hex upstream commits;
- deterministic materialization receipts;
- no runtime network fetch requirement;
- routing contract preserves Visual Director ownership.

### Renderer contract tests

- `2.4.0` compatibility;
- `2.5.0` parse and schema validation;
- semanticScope exact transport;
- semanticScope tamper detection;
- timing/preflight coverage.

### Plot contract tests

- Current authoring requires explicit semanticScope;
- RenderSpec materialization emits `2.5.0`;
- renderer source normalization preserves the actual schema version;
- strict projection preserves semanticScope;
- exact renderer binding identifies the merged `2.5.0` consumer.

### Cross-repo tests

- Plot exact binding checkout succeeds;
- producer `2.5.0` validates in the exact bound Renderer;
- Candidate/Director semantic-scope trace is lossless;
- no fallback to an older Renderer commit occurs.

### Real production tests

Two separate proofs are required by this design:

1. pre-migration Current production qualification; and
2. post-migration different-date Current production qualification.

The second proof must not replace the first.

## 14. Completion definition

This design is complete only when all of the following are true:

- current production has one fresh real-day qualification PASS before visual migration;
- `#220` no longer depends on an unowned persistent config path;
- Required Merge Gate still fails closed on unknown paths;
- Agent Skills are installed as pinned development tools without production-time fetches;
- Renderer main supports both `2.4.0` and `2.5.0` at the migration boundary;
- Plot main is bound to the exact merged Renderer `2.5.0` commit before it emits new `2.5.0` production RenderSpec;
- every authored semanticScope survives unchanged through Plot, strict projection, Candidate Input, Candidate Catalog, and compile;
- a different fresh episode reaches successful Preview under the migrated path without infrastructure/control-plane retry identities;
- the user reviews that exact Preview;
- Final is produced only if the user explicitly requests it; and
- post-migration qualification evidence records no unresolved machine boundary.

## 15. Non-goals

This design does not:

- redesign market causality or the nine-scene editorial structure;
- let Agent Skills author production semantics;
- add new speculative visual templates;
- replace the Current facade;
- create a new orchestration engine;
- auto-approve Preview or Final;
- broaden merge-policy wildcards merely to make a draft PR pass; or
- treat a GREEN repository-local PR as sufficient evidence of cross-repository production compatibility.
