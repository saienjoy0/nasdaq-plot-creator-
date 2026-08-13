# Visual Plan Critic Rules

The Critic must run independently from the Director context.

## Inputs

- Editorial Snapshot
- Visual Intent
- Candidate Catalog
- Director Selection
- Compiled Visual Plan
- Mechanical Warning Report
- Visual Editorial Principles
- Recent Approved Pattern Context only when available

## Review order

1. Story-preservation check
2. Beat-level Information Gain
3. selected vs strongest alternative comparison
4. Reality Anchor check
5. repetition / economy check
6. Visual Turn check
7. episode-level progression
8. Scene 4 → 8 delta
9. Scenes 6–8 deletion test
10. recent-pattern staleness when Phase 2 is available
11. status decision

## Findings

### `VISUAL_NO_INFORMATION_GAIN`
The visual adds no meaningful ability to compare, verify, sequence, delimit, or understand.

### `VISUAL_RECEIPT_ONLY`
The visual merely repeats narration. Do not issue if it materially confirms provenance or exposes a meaningful comparison/boundary.

### `MISSED_REALITY_ANCHOR`
A legal Reality Anchor would materially improve understanding, but an abstract option was selected instead.

### `DECORATIVE_NOVELTY`
A new component/image/motion is visually different without changing understanding.

### `UNJUSTIFIED_REPETITION`
Repeated visual function hides meaningful Story/Evidence progression. Do not issue for justified stable comparison.

### `UNNECESSARY_VISUAL_CHANGE`
A change interrupts useful continuity but adds no explanatory function.

### `OVERDIRECTED_VISUALS`
Direction competes with narration or creates more attentional work than explanatory gain.

### `CROSS_EPISODE_PATTERN_STALENESS`
Recent approved functional pattern repeats by inertia when a strong today-specific legal alternative exists.

### `WEAK_VISUAL_TURN`
Visual function does not reflect the Story's understanding transition.

### `NO_VISUAL_PROGRESS`
Across the episode, visuals accumulate surfaces without materially advancing the viewer model.

### `CANDIDATE_SELECTION_UNJUSTIFIED`
The Director does not show why selected beats the strongest legal alternative, or the rationale relies on ordering/novelty rather than meaning.

## Status mapping

- `PASS`: no unresolved major finding.
- `REVISE`: candidate selection alone can resolve the major finding.
- `RETURN_TO_STORY`: the visual defect is downstream evidence of a Story meaning/progression defect.
- `BLOCKED`: no legal candidate/fallback can perform the required understanding function.

Never make an editorial finding a Hard Validator error.
