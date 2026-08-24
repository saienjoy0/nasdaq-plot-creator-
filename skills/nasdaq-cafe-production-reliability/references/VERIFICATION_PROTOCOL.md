# Verification Protocol

Adapted to 朝のNASDAQカフェ from full-story verification.

## Verification target

The unit of verification is the complete Current production story, not an isolated function:

```text
production request
→ current_production_facade_v12.py
→ semantic/editorial verification
→ Story projection
→ Visual Requirements / Visual Source planning
→ asset resolution
→ Visual Intelligence
→ episode package / render spec
→ validators / handoff
→ GitHub Actions
→ TTS
→ Remotion
→ Preview artifact
```

## Baseline before repair

Capture:

- exact request identity and SHA;
- branch/commit;
- first failed boundary;
- first failed job/step/log line;
- relevant input/output artifact SHAs;
- relevant existing tests that passed despite the production failure.

This baseline is the comparison point after the repair.

## Verification ladder

1. Regression reproduces the original failure before the fix when practical.
2. Regression passes after the fix.
3. Existing tests for the owning boundary pass.
4. Current-entrypoint characterization / contract E2E passes.
5. Exact previously failing real-day request passes the old broken boundary.
6. Production continues until Preview or the next first broken boundary.

Do not claim full recovery at step 2 or 3.

## Boundary table

For the verified attempt, maintain:

| Boundary | Status | Evidence |
|---|---|---|
| Request identity | PASS/FAIL | request path/SHA |
| Current entrypoint | PASS/FAIL | facade invocation |
| Semantic/editorial | PASS/FAIL | receipt/freeze evidence |
| Story projection | PASS/FAIL | report/SHA |
| Visual planning | PASS/WAIT/FAIL | requirements/source decision |
| Asset resolution | PASS/FAIL | resolver/package evidence |
| Visual Intelligence | PASS/WAIT/FAIL | catalog/decision/critic |
| Package/render spec | PASS/FAIL | validator report |
| Handoff | PASS/FAIL | immutable bundle/preflight |
| GitHub Actions | PASS/FAIL | run/job/step |
| TTS | PASS/FAIL | generated audio evidence |
| Remotion | PASS/FAIL | exit code/log |
| Preview artifact | PASS/FAIL | artifact id/file |

## Intentional pauses

The following may be valid WAIT states rather than failures when required by the contracts:

- ChatGPT Visual Director / Critic decision required;
- Visual Source selection required;
- generated image human acceptance/rejection;
- user Preview review;
- explicit Final authorization.

A verifier must not bypass a semantic or human pause to obtain a green machine run.

## Future-change resilience

After a reliability repair that affects shared infrastructure, add at least one test that varies the input shape rather than replaying only one date when practical. Candidate dimensions:

- different episode date;
- changed Scene text with same contracts;
- Visual Source intents empty vs non-empty;
- different legal Candidate count;
- asset fallback selected;
- process launched from a different working directory;
- changed current contract SHA while sealed historical identity remains constant where architecture requires separation.

The purpose is to prove the fix is structural rather than hard-coded to one daily episode.
