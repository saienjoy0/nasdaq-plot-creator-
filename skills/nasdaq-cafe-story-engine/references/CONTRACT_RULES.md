# Story Engine Contract Rules

- One Skill contains Pass A–G; Daily Production states are not expanded in the shadow phase.
- Facts, Expected / Actual / Gap, chronology, causal scope, confidence and counterevidence are immutable editorial baseline fields.
- The Author draft is frozen by SHA before Critic review.
- Every Critical finding identifies Scenes, field paths, viewer effect, required fix and Claim/Evidence preservation requirements.
- Rewrite patches must reference existing findings and may not silently regenerate the whole episode.
- Review rounds are sequential and limited to two.
- Open loops are limited to two and must close or become evidence-backed unresolved by Scene 8.
- A deterministic validator proves structure and lineage, not entertainment quality.
- `logical_shadow` is not production independence. It requires `production_eligible=false` and emits `W_LOGICAL_SHADOW_CRITIC`.
- Production requires `critic_isolation_mode=separate_invocation`, a passing final review and explicit user acceptance.
