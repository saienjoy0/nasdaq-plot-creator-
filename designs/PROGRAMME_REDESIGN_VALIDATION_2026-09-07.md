# Programme remediation implementation receipt

## Actual changes

- Current Visual Intelligence validates explicit causal nodes/arrows/config only. No card-order inference, event fan-out or outcome selection. Invalid input returns precise JSON paths and RETURN_TO_STORY. Explicit disconnected company/macro graphs are preserved. Legacy compatibility helper remains only for legacy replay; Current final production suppresses legacy materialization.
- Causal Research, Story Plan, Story Authoring, Visual Intelligence and Entertainment Critic strengthened in place. No new standalone Skill. Structural East Asia screening is independent from chronological cross-market transmission. Image generation remains a conceptual production capability with Primary/Fallback and source boundaries.
- Canon02 updated to 2.6.0 with manifest SHA/rawBytes and snapshot test. Historical freezes are not rewritten. Existing 03/04 remain unchanged, and variable scene production is not claimed.

## Validation on final source changes

- `python scripts/canon_manifest.py verify`: PASS.
- `python -m pytest -q tests/canon-manifest/test_canon_manifest.py`: 5 passed.
- `python tests/remotion-compat/test_visual_intelligence_causal_inventory.py`: PASS.
- `python tests/remotion-compat/test_visual_intelligence_object_references.py`: PASS.
- `python -m unittest discover -s tests/current-spine -p 'test_*.py'`: 19 passed.
- `python -m unittest tests/remotion-compat/test_remotion_compat.py`: 8 passed.
- Related Visual Intelligence compatibility scripts: PASS; scripts requiring local module imports ran with `PYTHONPATH=scripts`.
- Independent causal review: no blocking findings. Independent editorial review found the old Section8 NASDAQ-path rule conflicted with structural context; the rule was scoped to market-causation claims and canon integrity rechecked.
- Generic skill-creator quick_validate is incompatible with the repository's pre-existing top-level `version` metadata and rejects all five Skills for that field. This patch retains the repository convention and does not claim generic validation success.

## Not completed / rollout boundaries

This change does not reauthor the historical 2026-08-17 producer package or render a replacement MP4. Its card-only causal Beat now returns to editorial authoring if replayed through Current. Reauthor explicit supported graph objects in a new attempt; do not mutate an old approved bundle or label an inferred graph approved. New Story/Visual freezes must bind the updated canon; old approvals do not authorize new semantics or pixels.

The coordinated 5–12-scene migration is designed in PROGRAMME_REDESIGN_2026-09-07.md but not enabled. No TTS or Current Preview/Final request is published by this code PR. No audience retention or continuous audio/motion approval is claimed. Broader quality improvement still requires a newly authored episode, actual preview review and real audience feedback.

Renderer companion: https://github.com/saienjoy0/saienjoy0-nasdaq-cafe-remotion/pull/224 . It fixes subtitle token breaks, with 26 test entrypoints plus typecheck/build passing. Whole Renderer lint has the same pre-existing 30 errors/3warnings at baseline and patched tree.
