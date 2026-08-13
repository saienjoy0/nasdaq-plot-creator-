# Visual Patch Rules

## Allowed automatic patch

Only:

```text
candidate selection
```

A patch must name:

- `visualBeatId`
- old Candidate ID
- replacement Candidate ID
- finding being resolved
- why the replacement improves understanding

## Forbidden automatic patch

- narration rewrite
- Evidence addition/deletion
- Expected / Actual / Gap change
- causal scope or confidence change
- Scene reorder
- free-form shot authoring
- new Component creation
- machine eligibility override

## Maximum rounds

Two candidate patch + independent re-review rounds.

After round two:

- Story defect → `RETURN_TO_STORY`
- capability/evidence absence → `BLOCKED`
- otherwise fail closed

## Story return invalidation

If Story changes, invalidate all prior:

- Visual Intent
- Provisional Direction
- Candidate Catalog binding
- Director selection
- Critic PASS

Restart from Visual Intent against the new editorial snapshot.
