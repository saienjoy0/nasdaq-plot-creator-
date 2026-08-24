# Repair Design Protocol

Purpose: turn a confirmed production root cause into an exact, reviewable, test-first implementation design before touching production code.

This protocol adapts the strongest mechanics of obra/superpowers `systematic-debugging`, `writing-plans`, `test-driven-development`, `requesting-code-review`, and `verification-before-completion` to the existing Nasdaq Cafe Current production architecture. It does not replace the Current facade, state machine, editorial authorities, Visual Intelligence, or Remotion specialists.

## Entry condition

Do not enter REPAIR_DESIGN until DIAGNOSE has produced all of:

- exact failing production request / run / job / step;
- first broken boundary;
- reproducible failure signature;
- one high-confidence root-cause statement;
- owning layer;
- evidence explaining why the existing test/gate missed it.

If any item is missing, return to DIAGNOSE.

## 1. Map the real code path

Read the actual production path, not only the failing function.

For the failing boundary, identify:

```text
public entrypoint
→ immediate caller
→ owning stage
→ downstream consumer
→ status / artifact contract
→ existing tests and canaries
```

Record exact files and functions. Follow the real GitHub Actions path when production differs from local tests.

For Current production, begin from `scripts/current_production_facade_v12.py` and the triggering workflow, then trace only as far as needed to own the confirmed failure.

## 2. Find a working analogue

Before designing a fix, search the same repository for the closest working pattern.

Examples:

- another intentional semantic pause handled as `PREPARED`;
- another Current facade caller handling `NORMAL_PAUSE`;
- a canary that correctly separates prepare and compile;
- another immutable request preflight gate;
- another regression that launches the exact production entrypoint.

Read the reference implementation completely enough to understand its assumptions. List material differences between working and failing paths.

## 3. State one repair hypothesis

Write exactly one sentence:

```text
I think <specific ownership / control-flow defect> is the root cause because <current evidence>, and changing <smallest owning behavior> should make <observable failing case> become <expected state> without changing <protected semantics>.
```

Do not bundle unrelated cleanup.

If three or more prior fixes on the same immutable production attempt exposed different failures, mark `ARCHITECTURE_REVIEW_REQUIRED` and explicitly evaluate whether ownership or orchestration is wrong before another local patch.

## 4. Define protected invariants

List what the repair must not change. At minimum consider:

- 01–04 editorial meaning;
- Semantic Freeze bytes / identity unless the root cause owns Freeze creation;
- narration, Scene order, Visual Beat meaning;
- Candidate selection ownership remains ChatGPT/AI-B;
- GitHub Actions remains mechanical;
- no automatic Final;
- no second Current facade or state machine;
- no hidden fallback / bypass;
- Renderer binding remains exact unless Renderer ownership is proven.

## 5. Produce an exact file map

Before code changes, write a file responsibility table:

| File | Action | Responsibility | Why this file owns the change |
|---|---|---|---|
| exact/path | modify/create/delete | one sentence | evidence |

Do not propose broad refactors without a demonstrated ownership reason.

## 6. Design the regression first

For a bug fix, the plan must start with a failing reproduction that would have caught the real incident.

The test must specify:

- exact fixture/request shape;
- exact command or public function exercised;
- expected pre-fix failure;
- expected post-fix result;
- protected negative cases;
- whether GitHub Actions parity or real-day canary coverage is also required.

Prefer a test that exercises the same public entrypoint as production. A unit test on an internal helper is insufficient when the bug is orchestration or caller/callee mismatch.

Required red/green evidence during implementation:

```text
RED: new regression fails for the real reason
GREEN: minimal repair makes it pass
SUITE: affected existing tests still pass
E2E: exact Current path passes the repaired boundary
```

## 7. Write implementation tasks

Each task must be independently testable and contain:

- exact files;
- exact functions / workflow steps;
- interfaces consumed and produced;
- test command;
- expected failing output before repair;
- minimal code behavior required;
- expected passing output after repair;
- compatibility / rollback note.

Do not use placeholders such as `TBD`, `handle appropriately`, `add tests`, or `similar to above`.

## 8. Risk review before implementation

Check the design for:

### Ownership risk
Is the change made at the layer that owns the meaning/control flow?

### Duplicate-control risk
Does the fix add a second gate already owned elsewhere?

### Staleness risk
Could immutable historical artifacts be revalidated against mutable Current contracts?

### Test-parity risk
Does CI test a different entrypoint, environment, path, or phase than production?

### Human-boundary risk
Could a missing ChatGPT/human decision be misclassified as machine failure?

### Loop risk
Could the repair merely expose the next known mandatory input without a preflight that predicts it?

## 9. Review gate

Before merge, review the diff against:

1. the confirmed root-cause statement;
2. the repair design;
3. protected invariants;
4. red/green regression evidence;
5. affected-suite evidence;
6. exact Current E2E evidence.

Critical or important deviations block merge.

## 10. Completion gate

Never claim the repair is complete from code inspection alone.

A repair may be called complete only with fresh evidence that:

- the regression failed before the fix and passes after it;
- affected tests pass;
- the real Current entrypoint exercises the repaired path;
- the previously failing production request passes that boundary;
- any subsequent stop is either a newly identified first broken boundary or an intentional semantic/human pause;
- no protected invariant changed.

## Repair design output format

Save consequential repair designs under:

```text
docs/reliability/plans/YYYY-MM-DD-<incident-or-boundary>.md
```

Use this structure:

```markdown
# <Repair> Implementation Plan

**Root cause:** ...
**First broken boundary:** ...
**Evidence:** ...
**Why existing tests missed it:** ...
**Goal:** ...
**Protected invariants:** ...

## Current code path
...

## Working analogue
...

## Repair hypothesis
...

## File map
...

## Task 1: Regression reproduction
...

## Task 2: Minimal owning-layer repair
...

## Task 3: Affected-suite and Current E2E verification
...

## Review / rollback
...
```
