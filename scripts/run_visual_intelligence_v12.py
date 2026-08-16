#!/usr/bin/env python3
"""Execute the machine half of visual-intelligence-bridge/1.2.0.

The first invocation stops at DECISION_REQUIRED after Candidate generation.
With an AI-B Director selection present, the second invocation compiles the actual
visual output and warning report, then stops at REVIEW_REQUIRED. Only after AI-B
Critic reviews those exact outputs and records a bound PASS may the final package
validator run and produce visual_intelligence_valid evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import renderer_binding
import validate_visual_intelligence_package
import visual_intelligence_bridge_staged
import visual_intelligence_causal_inventory
import visual_intelligence_intraday_evidence
import visual_intelligence_object_references
import visual_intelligence_renderer_projection
import visual_intelligence_terminal_projection


STALE_DIRECTOR_MARKERS = (
    "selectedCandidateId is not a legal Candidate",
    "strongest alternative is invalid",
    "single legal Candidate must not invent an alternative",
    "E_VISUAL_REQUIRED_REALITY_ANCHOR_MISSING",
    "E_VISUAL_REALITY_ANCHOR_DEPENDENCY_INVALID",
    "E_VISUAL_REALITY_ANCHOR_DEPENDENCY_NOT_PRIOR",
    "E_VISUAL_REALITY_ANCHOR_DEPENDENCY_CROSS_SCENE",
)


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return value


def _restore_precomputed_financial_context(path: Path, original: bytes | None) -> None:
    """Keep the pre-Director financial provider immutable once registered as evidence.

    `visual_intelligence_story_context.py` creates this provider from the approved
    producer RenderSpec before Visual Requirements are authored. The staged bridge
    also materializes provider metadata from its projected Renderer input for legacy
    compatibility. That derived write must not replace the already-registered
    Visual-independent context, otherwise the production-state evidence SHA becomes
    stale even though Story and Visual semantics did not change.
    """
    if original is None:
        return
    if not path.is_file() or path.read_bytes() != original:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(original)


def _reject_legacy_source_evidence_authority(root: Path, date: str) -> None:
    """Keep generic source evidence under the single Visual Intelligence authority.

    The pre-v1.2 Financial Visual pipeline historically modeled Reuters/AP source
    receipts as `kind: source-evidence` and froze a preferred `source-receipt` before
    the Visual Director ran. Visual Intelligence v1.2 already owns source-document,
    verification, and text-only Candidate selection, so carrying that legacy selected
    path into v1.2 creates two competing visual authorities and stale financial traces.

    Genuine financial intents remain legal and continue through the Financial Recipe
    pipeline unchanged. Only legacy source-evidence intents are forbidden on v1.2.
    """
    path = root / "working" / date / "financial_final_episode_contract.json"
    if not path.is_file():
        return
    value = load_json(path)
    visuals = value.get("financialVisuals")
    if not isinstance(visuals, dict):
        return
    intents = visuals.get("intents")
    if not isinstance(intents, list):
        return
    legacy = [
        item.get("intentId", "<unknown>")
        for item in intents
        if isinstance(item, dict) and item.get("kind") == "source-evidence"
    ]
    if legacy:
        raise ValueError(
            "E_VISUAL_SOURCE_EVIDENCE_DUAL_AUTHORITY:"
            + ",".join(str(item) for item in legacy)
            + ": source evidence must be authored through Visual Requirements/Candidates, not the legacy Financial selected path"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--date", required=True)
    parser.add_argument("--render-spec", required=True, type=Path)
    parser.add_argument("--renderer-root", required=True, type=Path)
    args = parser.parse_args()
    root = args.root.resolve()
    renderer_root = args.renderer_root.resolve()
    report_path = root / "verification" / args.date / "visual_intelligence_validation.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        binding = renderer_binding.verify_renderer_checkout(root, renderer_root)
        producer_render = load_json(args.render_spec)
        _reject_legacy_source_evidence_authority(root, args.date)
        candidate_render = (
            visual_intelligence_renderer_projection.project_visual_intelligence_renderer_input(
                producer_render,
                repo_root=root,
                date=args.date,
            )
        )
        candidate_render = visual_intelligence_terminal_projection.normalize_terminal_transition(
            candidate_render
        )
        candidate_render = visual_intelligence_causal_inventory.materialize_causal_inventory(
            candidate_render
        )
        candidate_render = (
            visual_intelligence_object_references.reconcile_projected_object_references(
                producer_render,
                candidate_render,
            )
        )
        candidate_render = visual_intelligence_intraday_evidence.bind_verified_intraday_evidence(
            candidate_render,
            repo_root=root,
            date=args.date,
        )
        financial_context_path = (
            root
            / "working"
            / args.date
            / "visual-intelligence"
            / "financial_candidate_provider.json"
        )
        financial_context_before = (
            financial_context_path.read_bytes() if financial_context_path.is_file() else None
        )
        try:
            result = visual_intelligence_bridge_staged.prepare_and_compile(
                render=candidate_render,
                output_root=root,
                date=args.date,
                renderer_root=renderer_root,
                expected_renderer_commit=binding["renderer"]["commit"],
                plot_root=root,
            )
        finally:
            _restore_precomputed_financial_context(
                financial_context_path,
                financial_context_before,
            )
        validation = validate_visual_intelligence_package.validate(
            root=root,
            date=args.date,
            renderer_root=renderer_root,
        )
        report = {
            **validation,
            "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
            "candidateCatalog": str(result["catalog_path"].relative_to(root)),
            "compiledVisual": str(
                (
                    root
                    / "working"
                    / args.date
                    / "visual-intelligence"
                    / "visual_direction_compiled_render.json"
                ).relative_to(root)
            ),
        }
        code = 0
    except visual_intelligence_bridge_staged.VisualIntelligenceStageError as exc:
        text = str(exc)
        stale_director = text.startswith("E_VISUAL_DECISION_STALE:") or any(
            marker in text for marker in STALE_DIRECTOR_MARKERS
        )
        if "E_VISUAL_INTELLIGENCE_DECISION_REQUIRED" in text or stale_director:
            status = "DECISION_REQUIRED"
            code = 3
            if stale_director and not text.startswith("E_VISUAL_DECISION_STALE:"):
                text = "E_VISUAL_DECISION_STALE:" + text
        elif "E_VISUAL_INTELLIGENCE_REVIEW_REQUIRED" in text:
            status = "REVIEW_REQUIRED"
            code = 4
        else:
            status = "FAIL"
            code = 2
        report = {
            "status": status,
            "episodeDate": args.date,
            "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
            "errors": [text],
        }
        if status == "REVIEW_REQUIRED":
            vi = root / "working" / args.date / "visual-intelligence"
            compiled = vi / "visual_direction_compiled_render.json"
            warnings = vi / "visual_editorial_warning_report.json"
            if compiled.is_file():
                report["compiledVisual"] = str(compiled.relative_to(root))
                report["compiledVisualSha256"] = visual_intelligence_bridge_staged.base.sha256_file(compiled)
            if warnings.is_file():
                report["warningReport"] = str(warnings.relative_to(root))
                report["warningReportSha256"] = visual_intelligence_bridge_staged.base.sha256_file(warnings)
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        renderer_binding.RendererBindingError,
        validate_visual_intelligence_package.VisualIntelligencePackageError,
        visual_intelligence_causal_inventory.VisualIntelligenceCausalInventoryError,
        visual_intelligence_intraday_evidence.IntradayEvidenceBindingError,
        visual_intelligence_object_references.ObjectReferenceReconciliationError,
        visual_intelligence_renderer_projection.VisualIntelligenceRendererProjectionError,
        visual_intelligence_terminal_projection.VisualIntelligenceTerminalProjectionError,
    ) as exc:
        report = {
            "status": "FAIL",
            "episodeDate": args.date,
            "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
            "errors": [str(exc)],
        }
        code = 2
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
