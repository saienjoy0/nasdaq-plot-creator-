#!/usr/bin/env python3
"""Execute the machine half of visual-intelligence-bridge/1.2.0.

Current order is immutable and explicit:
Requirements semantic -> canonical Requirements -> Candidate Catalog -> Director
semantic -> canonical Director -> Compile/Warnings -> Critic semantic -> canonical
Critic -> VI Package. Semantic drafts never become production evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import renderer_binding
import validate_visual_intelligence_package
import visual_intelligence_causal_inventory
import visual_intelligence_intraday_evidence
import visual_intelligence_object_references
import visual_intelligence_pipeline_v12 as pipeline
import visual_intelligence_read_set_v12
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
    "E_VISUAL_DECISION_STALE",
)


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return value


def _reject_legacy_source_evidence_authority(root: Path, date: str) -> None:
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
        candidate_render = visual_intelligence_renderer_projection.project_visual_intelligence_renderer_input(
            producer_render,
            repo_root=root,
            date=args.date,
        )
        candidate_render = visual_intelligence_terminal_projection.normalize_terminal_transition(
            candidate_render
        )
        candidate_render = visual_intelligence_causal_inventory.materialize_causal_inventory(
            candidate_render
        )
        candidate_render = visual_intelligence_object_references.reconcile_projected_object_references(
            producer_render,
            candidate_render,
        )
        candidate_render = visual_intelligence_intraday_evidence.bind_verified_intraday_evidence(
            candidate_render,
            repo_root=root,
            date=args.date,
        )
        result = pipeline.prepare_and_compile(
            render=candidate_render,
            output_root=root,
            date=args.date,
            renderer_root=renderer_root,
            expected_renderer_commit=binding["renderer"]["commit"],
            plot_root=root,
        )
        validation = validate_visual_intelligence_package.validate(
            root=root,
            date=args.date,
            renderer_root=renderer_root,
        )
        direct_read_sets = visual_intelligence_read_set_v12.build(
            root=root,
            date=args.date,
            renderer_root=renderer_root,
        )
        stale = visual_intelligence_read_set_v12.verify(
            root, direct_read_sets, renderer_root=renderer_root
        )
        if stale:
            raise visual_intelligence_read_set_v12.VisualIntelligenceReadSetError(
                "E_VISUAL_READ_SET_STALE:" + ";".join(stale)
            )
        report = {
            **validation,
            "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
            "candidateCatalog": str(result["catalog_path"].relative_to(root)),
            "visualDirectorDecision": str(result["director_path"].relative_to(root)),
            "visualCriticReview": str(result["critic_path"].relative_to(root)),
            "compiledVisual": str(
                (root / "working" / args.date / "visual-intelligence" / "visual_direction_compiled_render.json").relative_to(root)
            ),
            "directReadSets": direct_read_sets,
        }
        code = 0
    except pipeline.VisualIntelligenceStageError as exc:
        text = str(exc)
        stale_director = any(marker in text for marker in STALE_DIRECTOR_MARKERS)
        if "E_VISUAL_INTELLIGENCE_DECISION_REQUIRED" in text or stale_director:
            status = "DECISION_REQUIRED"
            code = 3
            if stale_director and not text.startswith("E_VISUAL_DECISION_STALE"):
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
            director = vi / "visual_director_decision.json"
            if compiled.is_file():
                report["compiledVisual"] = str(compiled.relative_to(root))
                report["compiledVisualSha256"] = pipeline.base.sha256_file(compiled)
            if warnings.is_file():
                report["warningReport"] = str(warnings.relative_to(root))
                report["warningReportSha256"] = pipeline.base.sha256_file(warnings)
            if director.is_file():
                report["visualDirectorDecision"] = str(director.relative_to(root))
                report["visualDirectorDecisionSha256"] = pipeline.base.sha256_file(director)
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        renderer_binding.RendererBindingError,
        validate_visual_intelligence_package.VisualIntelligencePackageError,
        visual_intelligence_causal_inventory.VisualIntelligenceCausalInventoryError,
        visual_intelligence_intraday_evidence.IntradayEvidenceBindingError,
        visual_intelligence_object_references.ObjectReferenceReconciliationError,
        visual_intelligence_read_set_v12.VisualIntelligenceReadSetError,
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
