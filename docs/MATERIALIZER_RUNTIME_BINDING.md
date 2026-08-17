# Materializer Runtime Binding

Step 2 of the reliability hardening removes runtime Python source rewriting from daily production.

Canonical production now resolves the episode-specific values from already-materialized daily authoring and the date-scoped causal dossier template, freezes them in an immutable `MaterializerRuntimeBinding`, and passes them to `scripts/materialize_daily_episode.py` as explicit CLI arguments:

- `--market-date`
- `--information-cutoff`
- `--dossier-template-sha`

The materializer source file is not edited at runtime. Separate episode dates therefore do not share mutable source state.

This change is intentionally semantic-neutral: Story Engine materialization/projection, Visual Intelligence, market causality, narration, Primary/Fallback selection, and Final authorization are unchanged.
