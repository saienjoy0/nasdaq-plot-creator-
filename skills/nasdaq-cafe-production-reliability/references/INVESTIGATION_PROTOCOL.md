# Investigation Protocol

Adapted to 朝のNASDAQカフェ from the evidence-first mechanics of investigation-mode.

## Triage order

1. Exact request identity and Current public entrypoint.
2. GitHub Actions run status.
3. First failed/blocked job.
4. First failed/blocked step.
5. Decoded job logs.
6. Boundary input/output artifacts and SHA lineage.
7. Only then inspect owning code and tests.

## Rules

- Do not start from a favorite hypothesis.
- Do not inspect downstream components after a confirmed upstream break.
- Prefer exact error lines, stable error codes, missing files, mismatched SHAs, and job conclusions over inference.
- Distinguish expected semantic pauses (`DECISION_REQUIRED`, author selection, human Preview approval) from machine failures.
- A timeout is not a diagnosis. Determine the last confirmed successful stage and the unresolved operation after it.
- Missing logs that prevent boundary identification are themselves a reliability defect.
- Never run the same unchanged check more than twice.

## Common Nasdaq Cafe failure families

### Contract ownership duplication

Symptoms:
- workflow and facade validate the same semantic fact differently;
- a sealed artifact is revalidated against mutable Current contracts;
- one repair exposes stale duplicate validation elsewhere.

Repair principle: one owner, other layers verify identity/receipt rather than re-authoring meaning.

### Path/import instability

Symptoms:
- tests pass from repository root but Actions fails from a nested working directory;
- dynamically loaded Python modules cannot import siblings;
- relative file paths depend on process cwd.

Repair principle: production code must resolve repository-relative paths from explicit workspace/module roots, and regression must launch from the failing working directory with incidental `PYTHONPATH` removed.

### Fixture/production divergence

Symptoms:
- unit tests pass but exact real-day request fails;
- fixtures omit Visual Source, Freeze, registry, or current contract fields present in production;
- synthetic test enters a lower-level script while production uses the Current facade.

Repair principle: add a characterization/E2E test that enters through the same public entrypoint and replays the real failing shape without changing semantic meaning.

### Stale immutable/mutable coupling

Symptoms:
- immutable Semantic Freeze becomes invalid only because a current contract SHA moved;
- rerunning unchanged production bytes changes validity.

Repair principle: verify sealed identity against its issuance evidence; evaluate Current compatibility in the designated Current compatibility layer, not by reissuing historical acceptance.

### State / artifact drift

Symptoms:
- state says a stage passed but expected output is absent or has another SHA;
- rerun silently overwrites a ChatGPT-authored semantic checkpoint;
- old render_spec or selection is reused for a new story snapshot.

Repair principle: fail closed on identity drift; preserve explicit post-authoring checkpoints only when their bound story/semantic snapshot is unchanged.

## Evidence template

```text
Checking:
Evidence:
Conclusion:
Next:
```

## Root-cause statement template

A valid root-cause statement names:

1. the owning component;
2. the exact violated assumption;
3. the evidence proving it;
4. why the existing gate/test allowed it to reach production.

Example form:

```text
The Current Story Engine loader assumed repository-root import resolution when Actions invokes it from scripts/story-engine; the decoded job log shows sibling import failure before Story projection, while existing tests inherited repository-root PYTHONPATH and therefore did not reproduce the production launch context.
```
