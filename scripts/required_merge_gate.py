#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Iterable

PASS = "PASS"
WAITING_FOR_WORKFLOW = "WAITING_FOR_WORKFLOW"
WAITING_FOR_COMPLETION = "WAITING_FOR_COMPLETION"
MIXED_REQUEST_PR = "MIXED_REQUEST_PR"
UNCLASSIFIED_CHANGE = "UNCLASSIFIED_CHANGE"
EXPECTED_WORKFLOW_FAILED = "EXPECTED_WORKFLOW_FAILED"
EXPECTED_WORKFLOW_TIMEOUT = "EXPECTED_WORKFLOW_TIMEOUT"


def load_policy(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("contractVersion") != "1.0.0":
        raise ValueError("required merge gate policy contractVersion must be 1.0.0")
    if value.get("unclassifiedNonDocs") != "FAIL":
        raise ValueError("required merge gate must fail closed for unclassified non-doc changes")
    return value


def _matches(path: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def _change_paths(change: dict) -> list[str]:
    paths = [str(change.get("filename", ""))]
    previous = change.get("previous_filename")
    if previous:
        paths.append(str(previous))
    return [path for path in paths if path]


def classify_changes(policy: dict, changes: list[dict]) -> dict:
    all_paths = [path for change in changes for path in _change_paths(change)]
    if not all_paths:
        return {"state": UNCLASSIFIED_CHANGE, "expectedWorkflows": [], "paths": []}

    request_matches: list[dict] = []
    for group in policy.get("requestOnlyGroups", []):
        if any(_matches(path, group.get("patterns", [])) for path in all_paths):
            request_matches.append(group)
    if request_matches:
        if len(changes) != 1 or len(request_matches) != 1 or not all(
            _matches(path, request_matches[0].get("patterns", [])) for path in all_paths
        ):
            return {"state": MIXED_REQUEST_PR, "expectedWorkflows": [], "paths": all_paths}
        return {
            "state": "REQUEST_ONLY",
            "expectedWorkflows": sorted(set(request_matches[0].get("workflows", []))),
            "paths": all_paths,
        }

    docs_patterns = policy.get("docsOnlyPatterns", [])
    if all(_matches(path, docs_patterns) for path in all_paths):
        return {"state": "DOCS_ONLY", "expectedWorkflows": [], "paths": all_paths}

    expected: set[str] = set()
    unmatched: list[str] = []
    groups = policy.get("workflowGroups", [])
    for path in all_paths:
        if _matches(path, docs_patterns):
            continue
        path_matched = False
        for group in groups:
            if _matches(path, group.get("patterns", [])):
                path_matched = True
                expected.update(str(name) for name in group.get("workflows", []))
        if not path_matched:
            unmatched.append(path)

    if unmatched:
        return {
            "state": UNCLASSIFIED_CHANGE,
            "expectedWorkflows": sorted(expected),
            "paths": all_paths,
            "unclassifiedPaths": sorted(set(unmatched)),
        }
    if not expected:
        return {"state": UNCLASSIFIED_CHANGE, "expectedWorkflows": [], "paths": all_paths}
    return {"state": "WORKFLOWS_REQUIRED", "expectedWorkflows": sorted(expected), "paths": all_paths}


def _run_key(run: dict) -> tuple[int, int, int]:
    return (int(run.get("run_number") or 0), int(run.get("run_attempt") or 0), int(run.get("id") or 0))


def select_latest_runs(expected: set[str], runs: list[dict], head_sha: str) -> dict[str, dict]:
    selected: dict[str, dict] = {}
    for run in runs:
        name = str(run.get("name") or "")
        if name not in expected:
            continue
        if run.get("head_sha") != head_sha or run.get("event") != "pull_request":
            continue
        current = selected.get(name)
        if current is None or _run_key(run) > _run_key(current):
            selected[name] = run
    return selected


def evaluate_latest_runs(expected: set[str], selected: dict[str, dict]) -> dict:
    missing = sorted(expected - set(selected))
    if missing:
        return {"state": WAITING_FOR_WORKFLOW, "missing": missing}

    pending: list[str] = []
    failed: list[dict] = []
    for name in sorted(expected):
        run = selected[name]
        if run.get("status") != "completed":
            pending.append(name)
            continue
        if run.get("conclusion") != "success":
            failed.append({"workflow": name, "conclusion": run.get("conclusion"), "runId": run.get("id")})
    if failed:
        return {"state": EXPECTED_WORKFLOW_FAILED, "failed": failed}
    if pending:
        return {"state": WAITING_FOR_COMPLETION, "pending": pending}
    return {"state": PASS, "runs": {name: selected[name].get("id") for name in sorted(expected)}}


def _github_json(url: str, token: str) -> dict | list:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "nasdaq-cafe-required-merge-gate",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _list_workflow_runs(repository: str, head_sha: str, token: str, request_fn: Callable[[str], dict] | None = None) -> list[dict]:
    request_fn = request_fn or (lambda url: _github_json(url, token))
    runs: list[dict] = []
    page = 1
    while True:
        query = urllib.parse.urlencode({"head_sha": head_sha, "event": "pull_request", "per_page": 100, "page": page})
        payload = request_fn(f"https://api.github.com/repos/{repository}/actions/runs?{query}")
        page_runs = list(payload.get("workflow_runs", []))
        runs.extend(page_runs)
        if len(page_runs) < 100:
            break
        page += 1
    return runs


def poll_expected_workflows(
    repository: str,
    head_sha: str,
    expected: set[str],
    token: str,
    *,
    request_fn: Callable[[str], dict] | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    monotonic_fn: Callable[[], float] = time.monotonic,
    timeout_seconds: int = 2700,
    poll_seconds: int = 10,
) -> dict:
    started = monotonic_fn()
    last = {"state": WAITING_FOR_WORKFLOW, "missing": sorted(expected)}
    while True:
        runs = _list_workflow_runs(repository, head_sha, token, request_fn=request_fn)
        selected = select_latest_runs(expected, runs, head_sha)
        last = evaluate_latest_runs(expected, selected)
        if last["state"] == PASS:
            return last
        if last["state"] == EXPECTED_WORKFLOW_FAILED:
            return last
        elapsed = monotonic_fn() - started
        if elapsed >= timeout_seconds:
            return {
                "state": EXPECTED_WORKFLOW_TIMEOUT,
                "lastState": last,
                "timeoutSeconds": timeout_seconds,
            }
        sleep_fn(min(poll_seconds, max(0.0, timeout_seconds - elapsed)))


def _list_pr_files(repository: str, pr_number: int, token: str) -> list[dict]:
    files: list[dict] = []
    page = 1
    while True:
        payload = _github_json(
            f"https://api.github.com/repos/{repository}/pulls/{pr_number}/files?per_page=100&page={page}", token
        )
        page_files = list(payload)
        files.extend(page_files)
        if len(page_files) < 100:
            break
        page += 1
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--pr-number", required=True, type=int)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--timeout-seconds", type=int, default=2700)
    parser.add_argument("--poll-seconds", type=int, default=10)
    args = parser.parse_args(argv)

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print(json.dumps({"state": "CONFIGURATION_ERROR", "error": "GH_TOKEN/GITHUB_TOKEN is required"}))
        return 2

    try:
        policy = load_policy(Path(args.policy))
        changes = _list_pr_files(args.repository, args.pr_number, token)
        classification = classify_changes(policy, changes)
        print(json.dumps({"classification": classification}, sort_keys=True))
        if classification["state"] in {MIXED_REQUEST_PR, UNCLASSIFIED_CHANGE}:
            return 1
        if classification["state"] == "DOCS_ONLY":
            print(json.dumps({"state": PASS, "reason": "DOCS_ONLY"}, sort_keys=True))
            return 0
        expected = set(classification["expectedWorkflows"])
        result = poll_expected_workflows(
            args.repository,
            args.head_sha,
            expected,
            token,
            timeout_seconds=args.timeout_seconds,
            poll_seconds=args.poll_seconds,
        )
        print(json.dumps(result, sort_keys=True))
        return 0 if result["state"] == PASS else 1
    except Exception as exc:
        print(json.dumps({"state": "CHECKER_ERROR", "error": str(exc)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
