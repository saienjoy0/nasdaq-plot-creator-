# PR2 implementation notes

`designs/PR2_SAFE_MEMORY_PROMOTION.md` is the governing design. This implementation adds the deterministic two-phase write layer described there.

## Commands

Dry-run only:

```bash
python scripts/plan_memory_promotion.py \
  production/publication_record_YYYY-MM-DD.json \
  --output working/memory-promotion/YYYY-MM-DD
```

Explicit apply, including one Git commit for all memory-file changes:

```bash
python scripts/apply_memory_promotion.py \
  working/memory-promotion/YYYY-MM-DD/promotion_plan.json \
  --apply
```

The compatibility wrapper is dry-run by default:

```bash
python scripts/promote_episode_memory.py production/publication_record_YYYY-MM-DD.json
```

It only applies when `--apply` is also provided.

## Safety behavior

- Source paths must resolve inside the repository.
- Approval, source artifacts, source hashes, date consistency, and formal validator PASS are checked before staging.
- A completed episode is stored under immutable `v001`, `v002`, ... revisions.
- Changed same-date input requires explicit next revision, correction reason, and superseded revision.
- Same source fingerprint is a no-op.
- Claim, alias, thread, and status-transition conflicts block apply.
- Plan and staged hashes are rechecked under an exclusive lock.
- Apply uses backups and rollback to prevent partial memory updates.
- Git apply stages only planned memory paths and creates one commit.
- `--no-commit` exists only for isolated CI tests.
