# Editorial canon gate ownership rollout

The required merge gate previously treated changes under `source-of-truth/` and
`designs/` as unclassified. This could block a valid canon or design pull request
even when its validation workflow had passed.

The ownership registry now assigns every `source-of-truth/**` change, along with
the existing canon schema, validator, materializer, semantic-freeze validator,
canon tests, and canon workflow, to the editorial-canon group. That group requires
both **Verify editorial canon** and **Validate Daily Production Package** at the
pull request's exact head commit. Design changes require the daily-production
baseline. Both workflows have matching pull-request path triggers.

Unknown paths still fail closed. Final-authorization requests remain request-only,
and a request mixed with a canon change is rejected. The trusted-base checkout,
exact-head matching, status publication, and branch protection are unchanged.

This prerequisite change must be reviewed and merged through the normal green
gate before the programme PR #198 base is refreshed. Do not use an administrator
bypass or let PR #198 authorize itself.
