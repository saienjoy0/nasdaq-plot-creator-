# 2026-08-25 Current-v2 parity cascade

- incident_id: `current-v2-parity-cascade-2026-08-17`
- episode_date: `2026-08-17`
- classification: `CASCADE_DETECTED / ARCHITECTURE_REVIEW_REQUIRED`
- latest_first_failed_boundary: `VALIDATOR`
- error_signature: `verification-matrix + templateConfig.variant=default is not registered`
- root_cause_family: `Current-v2 projection / final contract parity gaps not exercised by exact pre-merge production validation`
- previous_exposed_boundaries:
  - integrated 04 heading canonicalization missing
  - `current_final_production_source.json` sidecar missing
  - `terminal_assembly_bindings.json` missing
  - Renderer Candidate template/variant legality gap
- repair_plan: `docs/reliability/plans/2026-08-25-renderer-candidate-variant-contract.md`
- why_tests_missed_it: `Candidate tests did not assert template-specific variant registry membership; Visual Intelligence compile did not invoke official visual-story validation before PASS.`
- preview_result: `not produced yet`
- recurrence_signature: `current-v2 passes local projection/VI checks but fails at a later exact Renderer contract boundary`
