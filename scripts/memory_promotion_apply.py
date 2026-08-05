#!/usr/bin/env python3
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from memory_promotion_common import (
    CONTRACT_VERSION, ConflictError, PromotionError, StalePlanError,
    digest_file, file_sha_or_none, plan_digest, read_json, resolve_repo_path,
    sha256_file, utc_now, validate_json_schema, write_json,
)

def verify_plan_and_staging(plan_path: Path, repo_root: Path, contracts_dir: Path) -> tuple[dict[str, Any], Path]:
    repo_root = repo_root.resolve()
    plan_path = resolve_repo_path(str(plan_path), repo_root)
    plan = read_json(plan_path)
    validate_json_schema(plan, contracts_dir / "memory_promotion_plan.schema.json")
    if plan.get("mode") != "apply" or plan.get("execution_state") != "planned":
        raise StalePlanError("promotion plan is not in planned apply state")
    if not plan.get("safe_to_apply") or plan.get("conflicts"):
        raise ConflictError("promotion plan has unresolved conflicts")
    if plan.get("plan_digest") != plan_digest(plan):
        raise StalePlanError("promotion plan digest mismatch")

    run_dir = resolve_repo_path(str(plan["run_directory"]), repo_root)
    if plan_path != run_dir / "promotion_plan.json":
        raise StalePlanError("plan path does not match its declared run directory")
    dry_run_report = run_dir / "dry_run_report.md"
    if not dry_run_report.is_file() or dry_run_report.stat().st_size <= 0:
        raise StalePlanError("dry-run report is missing or empty")

    report = read_json(resolve_repo_path(str(plan["conflict_report_path"]), repo_root))
    validate_json_schema(report, contracts_dir / "memory_conflict_report.schema.json")
    if report.get("unresolved_count") != 0 or not report.get("safe_to_apply"):
        raise ConflictError("conflict report is not safe to apply")

    preflight = read_json(resolve_repo_path(str(plan["source_preflight_path"]), repo_root))
    validate_json_schema(preflight, contracts_dir / "memory_source_preflight.schema.json")
    record_path = resolve_repo_path(str(plan["publication_record_path"]), repo_root)
    current_record_digest = digest_file(record_path, repo_root)
    if current_record_digest.sha256 != preflight["publication_record"]["sha256"]:
        raise StalePlanError("publication record changed after plan creation")
    record = read_json(record_path)
    source_paths = record["source_paths"]
    for key, expected in preflight["source_artifacts"].items():
        current = digest_file(resolve_repo_path(str(source_paths[key]), repo_root), repo_root)
        if current.sha256 != expected["sha256"] or current.bytes != expected["bytes"]:
            raise StalePlanError(f"source artifact changed after plan creation: {key}")

    staged_root = run_dir / "staged"
    for operation in plan["operations"]:
        target = resolve_repo_path(operation["path"], repo_root, must_exist=False)
        current_before = file_sha_or_none(target)
        if current_before != operation["before_sha256"]:
            raise StalePlanError(f"memory target changed after plan creation: {operation['path']}")
        staged = staged_root / operation["path"]
        if not staged.is_file():
            raise StalePlanError(f"missing staged file: {operation['path']}")
        if sha256_file(staged) != operation["after_sha256"] or staged.stat().st_size != operation["bytes"]:
            raise StalePlanError(f"staged file hash/size mismatch: {operation['path']}")
    return plan, run_dir


def run_git(repo_root: Path, args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo_root), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def ensure_git_targets_clean(repo_root: Path, relative_paths: list[str]) -> None:
    if not (repo_root / ".git").exists():
        raise PromotionError("apply requires a Git repository; use --no-commit only in isolated tests")
    if not relative_paths:
        return
    result = run_git(repo_root, ["status", "--porcelain", "--", *relative_paths])
    if result.stdout.strip():
        raise StalePlanError("target memory paths have uncommitted changes before apply")


def acquire_lock(lock_path: Path) -> int:
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise PromotionError(f"another memory promotion holds the lock: {lock_path}") from exc
    os.write(fd, f"pid={os.getpid()} created_at={utc_now()}\n".encode("utf-8"))
    return fd


def apply_plan(
    plan_path: Path,
    repo_root: Path,
    contracts_dir: Path,
    *,
    commit: bool = True,
    fail_after: int | None = None,
) -> dict[str, Any]:
    plan, run_dir = verify_plan_and_staging(plan_path, repo_root, contracts_dir)
    report_path = run_dir / "promotion_report.json"
    if report_path.exists():
        previous = read_json(report_path)
        if previous.get("status") in {"applied", "noop"}:
            raise PromotionError("promotion plan was already applied")

    if plan.get("noop"):
        report = {
            "contract_version": CONTRACT_VERSION,
            "status": "noop",
            "episode_date": plan["episode_date"],
            "revision": plan["revision"],
            "plan_digest": plan["plan_digest"],
            "changed_paths": [],
            "git_commit": None,
            "applied_at": utc_now(),
        }
        validate_json_schema(report, contracts_dir / "memory_promotion_report.schema.json")
        write_json(report_path, report)
        return report

    operations = [operation for operation in plan["operations"] if operation["action"] != "noop"]
    relative_paths = [str(operation["path"]) for operation in operations]
    if commit:
        ensure_git_targets_clean(repo_root, relative_paths)

    lock_path = repo_root / "working" / "memory-promotion" / ".apply.lock"
    lock_fd = acquire_lock(lock_path)
    backup_root = Path(tempfile.mkdtemp(prefix="memory-promotion-rollback-"))
    created: set[str] = set()
    replaced: list[str] = []
    staged_root = run_dir / "staged"
    commit_sha: str | None = None
    try:
        # Recheck under lock so concurrent plans cannot slip between validation and mutation.
        verify_plan_and_staging(plan_path, repo_root, contracts_dir)
        for index, operation in enumerate(operations, start=1):
            relative = str(operation["path"])
            target = resolve_repo_path(relative, repo_root, must_exist=False)
            staged = staged_root / relative
            if target.exists():
                backup = backup_root / relative
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, backup)
            else:
                created.add(relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + f".promotion-{os.getpid()}.tmp")
            shutil.copy2(staged, temporary)
            os.replace(temporary, target)
            replaced.append(relative)
            if fail_after is not None and index >= fail_after:
                raise RuntimeError("simulated apply failure")

        if commit and relative_paths:
            run_git(repo_root, ["add", "--", *relative_paths])
            result = run_git(
                repo_root,
                [
                    "commit",
                    "-m",
                    f"memory: promote {plan['episode_date']} {plan['revision']}",
                    "--",
                    *relative_paths,
                ],
            )
            commit_sha = run_git(repo_root, ["rev-parse", "HEAD"]).stdout.strip()

        report = {
            "contract_version": CONTRACT_VERSION,
            "status": "applied",
            "episode_date": plan["episode_date"],
            "revision": plan["revision"],
            "plan_digest": plan["plan_digest"],
            "changed_paths": relative_paths,
            "git_commit": commit_sha,
            "applied_at": utc_now(),
        }
        validate_json_schema(report, contracts_dir / "memory_promotion_report.schema.json")
        write_json(report_path, report)
        return report
    except Exception:
        if commit and relative_paths and (repo_root / ".git").exists():
            run_git(repo_root, ["reset", "--", *relative_paths], check=False)
        for relative in reversed(replaced):
            target = repo_root / relative
            backup = backup_root / relative
            if backup.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup, target)
            elif relative in created and target.exists():
                target.unlink()
        raise
    finally:
        shutil.rmtree(backup_root, ignore_errors=True)
        try:
            os.close(lock_fd)
        finally:
            lock_path.unlink(missing_ok=True)
