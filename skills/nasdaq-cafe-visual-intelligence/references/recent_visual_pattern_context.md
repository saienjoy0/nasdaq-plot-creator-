# Recent Approved Visual Pattern Context — Phase 2 Policy

This reference defines how the LLM interprets machine-generated recent pattern context. It does not fetch or create that context.

## Eligibility

Only episodes with `verification/YYYY-MM-DD/human_preview_review.json` where:

- `status` is `approved`
- stored Preview SHA matches the reviewed Preview exactly

may be used.

The LLM never self-approves a Preview.

## Initial retrieval size

Up to about five recent approved episodes is sufficient as context. This is not a Hard quota.

Inspect function, not only template names:

- visual function sequence
- Reality Anchor placement
- document/chart/card role
- opening understanding function
- late payoff display
- closing assembly function

## Staleness rule

Similarity alone is not a defect.

Use `CROSS_EPISODE_PATTERN_STALENESS` only when:

1. multiple recent approved episodes share substantially the same functional pattern,
2. today's Evidence has a strong legal alternative expression,
3. repeating the old pattern has weak today-specific justification.

If context is absent, mark this check `unassessed`.
