# Unified Story Engine

Shadow-mode implementation of `designs/STORY_ENGINE_UNIFIED_FINAL_DESIGN_v1.1.md`.

```bash
python -m unittest discover -s tests/story-engine -p 'test_*.py'
python skills/nasdaq-cafe-story-engine/validators/validate_story_engine_hardening.py \
  --repo-root . --package path/to/story_engine_package.json
```

The validator checks contract structure, repository-relative hashes, independent Author/Critic invocations, Claim Ledger references, nine-Scene progression, open-loop limits, review lineage, unresolved Critical findings, causality preservation and final binding. It does not score subjective quality.
