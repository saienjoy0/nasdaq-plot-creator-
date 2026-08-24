# Observability and Regression Contract

## Observability principle

Every meaningful stage transition must make the last successful boundary and first failed/missing boundary discoverable from machine evidence.

Minimum stage event fields:

```text
stage
request_id / run_id
episode_date
input_sha(s)
output_sha(s)
started_at
finished_at
duration_ms
status
stable_error_code
```

At external or asynchronous boundaries, emit entry and exit/failure events. Do not log secrets, tokens, raw credentials, or unnecessary private data.

## Stable failure identity

Prefer stable error codes to prose-only exceptions. A useful code names the owning boundary and failure class, for example:

```text
SEMANTIC_FREEZE_IDENTITY_MISMATCH
CURRENT_ENTRYPOINT_VIOLATION
VISUAL_SOURCE_SELECTION_REQUIRED
ASSET_REFERENCE_MISSING
RENDER_SPEC_VALIDATION_FAILED
TTS_GENERATION_FAILED
REMOTION_RENDER_FAILED
PREVIEW_ARTIFACT_MISSING
```

Expected semantic/human pauses should use explicit non-error states where possible.

## Regression requirement

Every durable production bug repair should answer:

```text
What exact assumption failed?
What test would have caught it before production?
Does the new test exercise the production launch context and public entrypoint where relevant?
```

A regression must not simply assert the patched implementation detail. It should reproduce the violated contract boundary.

## Cascade policy

Record `CASCADE_DETECTED` when the same immutable request reveals two or more different first-broken boundaries after successive repairs.

Before the next repair, inspect:

- duplicate ownership/gates;
- current-vs-sealed contract coupling;
- production-vs-test entrypoint differences;
- cwd/import/path assumptions;
- real-day-vs-fixture shape differences;
- missing boundary observability;
- workflow-level bypasses or duplicate checks.

## Incident ledger

Recommended append-only location:

```text
reliability/incidents/YYYY-MM-DD/<incident_id>.json
```

Minimum record:

```json
{
  "incident_id": "...",
  "episode_date": "YYYY-MM-DD",
  "production_request_sha": "...",
  "first_failed_boundary": "...",
  "error_signature": "...",
  "root_cause": "...",
  "why_tests_missed_it": "...",
  "fix_commit": "...",
  "regression_test": "...",
  "e2e_result": "...",
  "preview_result": "...",
  "recurrence_signature": "..."
}
```

Prior incidents are diagnostic leads only. Current evidence must reconfirm recurrence.
