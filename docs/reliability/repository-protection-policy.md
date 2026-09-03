# Current Production Repository Protection Policy

Verification date: 2026-09-03

## Required merge status

Both Current production repositories protect their default `main` branch with one repository ruleset named `current-production-main-v1`.

The only directly required status context is:

```text
Nasdaq Cafe Required Merge Gate
```

The required status is bound to GitHub Actions (`integration_id: 15368`). Path-filtered CI workflows are intentionally not required directly; the trusted base-branch merge gate observes the appropriate exact-head workflow set.

## Plot

```text
repository: saienjoy0/nasdaq-plot-creator-
ruleset id: 22159825
ruleset name: current-production-main-v1
enforcement: active
target: default branch / main
bypass actors: none
required status: Nasdaq Cafe Required Merge Gate
required status source: GitHub Actions (integration_id 15368)
require pull request: yes
required approving reviews: 0
require branch up to date: yes
restrict deletion: yes
block force pushes / non-fast-forward: yes
```

Post-activation verification:

```text
PR #188 initial head 34e196227ac76779035dc8c4184b6378b8ecb034
Validate Daily Production Package: failure
Nasdaq Cafe Required Merge Gate: failure

PR #188 repaired head fd4c073781e8723c47869f3bed0ebfba388c4346
Validate Daily Production Package: success
Story Engine v1.1 Gate: success
Nasdaq Cafe Required Merge Gate: success
PR closed without merge
```

## Renderer

```text
repository: saienjoy0/saienjoy0-nasdaq-cafe-remotion
ruleset id: 22160068
ruleset name: current-production-main-v1
enforcement: active
target: default branch / main
bypass actors: none
required status: Nasdaq Cafe Required Merge Gate
required status source: GitHub Actions (integration_id 15368)
require pull request: yes
required approving reviews: 0
require branch up to date: yes
restrict deletion: yes
block force pushes / non-fast-forward: yes
```

Post-activation verification:

```text
PR #221 initial head 8c3e60eb68dd6f41166d8f24a80c505a7395095d
Visual Story Engine CI: failure
Nasdaq Cafe Required Merge Gate: failure

PR #221 repaired head ac36da3667079ca124372081f34d9d33a70e1808
Visual Story Engine CI: success
Visual Story Media CI: success
Nasdaq Cafe Required Merge Gate: success
PR closed without merge
```

## Trust boundary

`Required Merge Gate Control Plane` runs through `pull_request_target`, checks out the pull request base SHA, and executes the checker/policy from that trusted base. PR-head code is treated only as change metadata and is never executed by the privileged gate. A PR that changes the gate cannot replace the judge evaluating that same PR.

Missing mapped workflows remain a wait state until the configured deadline. The newest exact-head workflow run/attempt is authoritative; only `success` passes. Unknown non-document changes fail closed.

## Operational rule

Do not add path-filtered workflows such as `Visual Story Engine CI` or `Validate Daily Production Package` directly to the repository ruleset. Keep `Nasdaq Cafe Required Merge Gate` as the single required status so skipped workflows cannot deadlock merges.
