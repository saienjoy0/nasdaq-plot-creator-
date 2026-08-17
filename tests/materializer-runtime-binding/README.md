# Materializer runtime binding regression

This suite locks the Step 2 acceptance criteria:

- two episode dates resolve independent runtime values;
- resolving those values does not change the SHA-256 of `scripts/materialize_daily_episode.py`;
- the canonical and legacy closure scripts no longer call `bind_legacy_materializer`;
- the materializer no longer contains the frozen 2026-08-05 market date, cutoff, or a source-level dossier SHA constant;
- production passes market date, information cutoff, and dossier template SHA through explicit CLI arguments.
