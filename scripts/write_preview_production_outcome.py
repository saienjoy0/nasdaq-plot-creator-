#!/usr/bin/env python3
"""Normalize Preview production completion or safe-pause into one machine-readable outcome."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ACTION_TO_STATE = {
    "AUTHOR_VISUAL_REQUIREMENTS": "WAITING_FOR_VISUAL_REQUIREMENTS",
    "AUTHOR_VISUAL_SOURCE_SELECTION": "WAITING_FOR_VISUAL_SOURCE_SELECTION",
    "AUTHOR_VISUAL_INTELLIGENCE_DECISION": "WAITING_FOR_VISUAL_INTELLIGENCE_DECISION",
    "RESELECT_VISUAL_CANDIDATES": "WAITING_FOR_VISUAL_RESELECTION",
}


def _load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return value


def build_outcome(args: argparse.Namespace) -> dict:
    base = {
        "contractVersion": "1.1.0",
        "episodeDate": args.episode_date,
        "canonicalWorkflow": ".github/workflows/chatgpt-daily-preview-production.yml",
        "plotCommit": args.plot_commit,
        "rendererCommit": args.renderer_commit,
        "previewHandoffReady": False,
        "previewPublicationReady": False,
        "finalRendered": False,
    }

    if not args.closure_gate.is_file():
        return {
            **base,
            "state": "FAILED",
            "reason": f"renderer closure gate missing: {args.closure_gate}",
        }

    gate = _load_object(args.closure_gate)
    closure_status = gate.get("status")
    required_action = gate.get("requiredAction")
    reason = gate.get("reason") or gate.get("error")
    outcome = {**base, "closureStatus": closure_status}
    if isinstance(required_action, str) and required_action:
        outcome["requiredAction"] = required_action
    if isinstance(reason, str) and reason:
        outcome["reason"] = reason

    if closure_status == "PASS":
        if (
            args.handoff_upload_outcome == "success"
            and args.handoff_artifact_name
            and args.request_publication_outcome == "success"
            and args.request_publication_receipt
            and args.renderer_request_path
        ):
            outcome.update(
                {
                    "state": "PREVIEW_PUBLICATION_READY",
                    "previewHandoffReady": True,
                    "previewPublicationReady": True,
                    "handoffArtifactName": args.handoff_artifact_name,
                    "requestPublicationReceipt": args.request_publication_receipt,
                    "rendererRequestPath": args.renderer_request_path,
                }
            )
            for key, value in (
                ("handoffArtifactId", args.handoff_artifact_id),
                ("handoffArtifactUrl", args.handoff_artifact_url),
                ("handoffArtifactDigest", args.handoff_artifact_digest),
            ):
                if value:
                    outcome[key] = value
            return outcome
        if args.handoff_upload_outcome != "success" or not args.handoff_artifact_name:
            reason = "semantic closure passed but immutable Preview handoff was not uploaded successfully"
        else:
            reason = "immutable Preview handoff was uploaded but its deterministic Renderer publication receipt was not published successfully"
        outcome.update({"state": "FAILED", "reason": reason})
        return outcome

    if closure_status == "REVIEW_REQUIRED":
        outcome["state"] = "WAITING_FOR_VISUAL_REVIEW"
        return outcome

    if closure_status == "PREPARED":
        outcome["state"] = ACTION_TO_STATE.get(str(required_action), "SAFE_PAUSED")
        return outcome

    if closure_status == "FAIL":
        outcome["state"] = "FAILED"
        if "reason" not in outcome:
            outcome["reason"] = "renderer closure reported FAIL"
        return outcome

    outcome.update(
        {
            "state": "FAILED",
            "reason": f"unexpected renderer closure status: {closure_status!r}",
        }
    )
    return outcome


def main() -> int:
    import jsonschema

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--closure-gate", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--episode-date", required=True)
    parser.add_argument("--plot-commit", required=True)
    parser.add_argument("--renderer-commit", required=True)
    parser.add_argument("--handoff-upload-outcome", default="skipped")
    parser.add_argument("--handoff-artifact-name", default="")
    parser.add_argument("--handoff-artifact-id", default="")
    parser.add_argument("--handoff-artifact-url", default="")
    parser.add_argument("--handoff-artifact-digest", default="")
    parser.add_argument("--request-publication-outcome", default="skipped")
    parser.add_argument("--request-publication-receipt", default="")
    parser.add_argument("--renderer-request-path", default="")
    args = parser.parse_args()

    outcome = build_outcome(args)
    schema = _load_object(args.schema)
    jsonschema.Draft202012Validator(schema).validate(outcome)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(outcome, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
