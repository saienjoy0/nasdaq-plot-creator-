---
name: nasdaq-cafe-production-reliability
version: 1.0.0
description: Diagnose, repair, and verify 朝のNASDAQカフェ Current production failures from the first broken boundary through Preview, without creating a second production engine.
---

# Nasdaq Cafe Production Reliability

## Purpose

This skill is the single reliability layer for stuck, failing, looping, or repeatedly patched Current production. It adapts the strongest mechanics from investigation-mode, verification, and observability to the Nasdaq Cafe production architecture.

It does not create editorial meaning, rewrite narration, select market causality, choose Visual Candidates, or replace the Current production state machine.

The goal is not "fix one error". The goal is:

```text
find the first broken boundary with evidence
→ identify the root cause
→ explain why existing tests/gates missed it
→ apply the smallest durable repair
→ add a regression that would have caught it
→ re-run the real Current path
→ prove Preview readiness or report the next first broken boundary
```

## Authority and entrypoint

Always obey `AGENTS.md` and the project source-of-truth order.

Current production has one public entrypoint:

```text
scripts/current_production_facade_v12.py
```

The reliability skill observes and repairs that existing path. It must never introduce a second facade, second state machine, second semantic validator chain, or second Renderer handoff.

## Trigger conditions

Use this skill when the user says or implies:

- where is it stuck / what is blocking it;
- it keeps failing / loops / never finishes;
- why did the previous fix not solve it;
- make the pipeline stable;
- diagnose and fix the Current production path;
- verify the entire production flow after a repair;
- repeated real-day requests fail at successive boundaries.

## Mandatory modes

### DIAGNOSE

Do not guess. Inspect the real Current production evidence in this order:

1. Confirm the exact production request / episode / branch / commit under investigation.
2. Confirm the Current public entrypoint is used.
3. Inspect the latest relevant GitHub Actions run.
4. Find the first failed or blocked job.
5. Find the first failed or blocked step.
6. Read that job's decoded logs.
7. Inspect the input artifact(s), state evidence, SHAs, and output artifact(s) for that boundary.
8. Classify the failure boundary.
9. Stop root-cause search when a high-confidence specific cause is found.
10. If two consecutive checks provide no signal, classify this as an observability gap and add evidence before further guessing.

Do not continue downstream after the first confirmed broken boundary. Downstream failures are not primary evidence until the earlier boundary passes.

### REPAIR

After a high-confidence root cause:

1. State the root cause in one sentence.
2. Identify why the existing test/gate did not catch it.
3. Apply the smallest repair at the owning layer.
4. Do not modify editorial meaning to satisfy machine contracts.
5. Add or strengthen a regression test reproducing the real failure mode.
6. Prefer fixing ownership, entrypoint, lineage, path stability, contract drift, or missing observability over adding another bypass.

### VERIFY

A repair is not complete because a unit test passes.

Verify in this order:

1. New regression test.
2. Existing affected test suite.
3. Current-entrypoint characterization / contract E2E relevant to the changed boundary.
4. The real-day canary or exact previously failing request.
5. GitHub Actions through the next production boundary.
6. Continue until Preview is produced or a new first broken boundary is found.

If a new first broken boundary appears, return to DIAGNOSE for that boundary. Do not call the whole production path fixed yet.

## Failure taxonomy

Classify the first broken boundary as one of:

```text
REQUEST_IDENTITY
CURRENT_ENTRYPOINT
CAUSAL_DOSSIER
DAILY_AUTHORING
EDITORIAL_ACCEPTANCE
SEMANTIC_FREEZE
STORY_PROJECTION
VISUAL_REQUIREMENTS
VISUAL_SOURCE_SELECTION
ASSET_RESOLUTION
VISUAL_INTELLIGENCE
EPISODE_PACKAGE
RENDER_SPEC
VALIDATOR
HANDOFF
GITHUB_ACTIONS
TTS
REMOTION
PREVIEW_ARTIFACT
HUMAN_REVIEW_WAIT
OBSERVABILITY_GAP
UNKNOWN
```

Use the owning layer to decide what may be changed. Do not fix a `RENDER_SPEC` contract issue inside Remotion, and do not fix a `SEMANTIC_FREEZE` identity issue by changing story meaning.

## Cascading failure rule

If the same immutable production request encounters two or more different first broken boundaries across successive repair attempts, mark:

```text
CASCADE_DETECTED
```

Then perform pipeline-boundary analysis before another patch:

- Why was the newly exposed failure not caught by pre-merge tests?
- Did tests use a different entrypoint from production?
- Did fixtures freeze stale contracts or paths?
- Is the same semantic fact validated by multiple owners?
- Is a mutable Current dependency being revalidated against an immutable Freeze?
- Is a runtime import/path assumption different between tests and Actions?
- Did a workflow duplicate a gate already owned by the facade?
- Is the real-day canary materially different from synthetic fixtures?

A cascade is evidence that the missing test or ownership boundary matters as much as the latest local bug.

## Investigation reporting contract

For every diagnostic step, record:

```text
Checking: what boundary/evidence is being inspected
Evidence: exact run/job/step/log/artifact/SHA result
Conclusion: what the evidence proves or does not prove
Next: only the next most informative check
```

Do not silently cycle through checks.

## Observability baseline

Every production stage should expose enough information to locate the stop point:

```text
stage
run_id / request_id
episode_date
input_sha(s)
output_sha(s)
start
finish
duration
status
stable error_code
```

At async/external boundaries, log entry and exit. The last successful boundary plus the first missing/failed boundary must be determinable without reading speculative code paths.

If logs are insufficient to distinguish two plausible causes, improving observability is the next repair.

## Specialist delegation

Keep this skill as coordinator, not as a duplicate expert implementation.

- Editorial / market causality → existing editorial and causal-research authority.
- Visual semantics / Candidate choice → `nasdaq-cafe-visual-intelligence`.
- Remotion-specific markup/render/API behavior → installed Remotion skills.
- GitHub Actions evidence → workflow run, job, step, log, and artifact APIs.

The coordinator must first prove the failure is inside a specialist's boundary before delegating.

## Stop conditions

Diagnosis stops when:

- a specific high-confidence root cause is supported by evidence; or
- two consecutive evidence layers produce no useful signal, in which case report `OBSERVABILITY_GAP` and fix measurement first.

Repair verification stops when:

- the real Current path reaches Preview; or
- a new first broken boundary is identified with evidence; or
- the production is intentionally waiting for human input such as Visual Source selection or Preview approval.

Never re-run the same unchanged failing check more than twice.

## Reliability completion definition

Do not say "fixed" unless all are true:

- root cause identified;
- ownership boundary identified;
- why-old-tests-missed-it recorded;
- durable minimal repair applied;
- regression added or an explicit reason why not possible;
- affected tests pass;
- exact Current entrypoint is exercised;
- previously failing real-day request passes that boundary;
- no unresolved hidden fallback/bypass was added;
- Preview is produced, or the next stop is an intentional human/semantic pause rather than a machine failure.

## Incident memory

For repeated production incidents, maintain an append-only reliability record containing at least:

```text
incident_id
production_request_sha
first_failed_boundary
error_signature
root_cause
why_tests_missed_it
fix_commit
regression_test
e2e_result
preview_result
recurrence_signature
```

Use prior incidents only as diagnostic leads. Reconfirm the current failure with current logs and artifacts before declaring recurrence.
