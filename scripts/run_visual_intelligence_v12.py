#!/usr/bin/env python3
"""Execute the staged machine half of visual-intelligence-bridge/1.2.0.

Stages are data-driven by artifact presence:
1. no Director decision -> Candidate Catalog then DECISION_REQUIRED (exit 3)
2. Director decision, no final Critic PASS -> compile + warnings then REVIEW_REQUIRED (exit 4)
3. final Critic PASS -> package validation PASS (exit 0)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import renderer_binding
import validate_visual_intelligence_package
import visual_intelligence_bridge_staged as staged
import visual_intelligence_renderer_input


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"JSON root must be object: {path}")
    return value


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
        canonical = visual_intelligence_renderer_input.canonicalize_for_visual_director(
            render=load_json(args.render_spec),
            output_root=root,
            date=args.date,
        )
        result = staged.prepare_and_compile(
            render=canonical,
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
        report = {
            **validation,
            "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
            "candidateCatalog": str(result["catalog_path"].relative_to(root)),
            "compiledVisual": str(
                (root / "working" / args.date / "visual-intelligence" / "visual_direction_compiled_render.json").relative_to(root)
            ),
        }
        code = 0
    except staged.VisualIntelligenceStageError as exc:
        text = str(exc)
        if "E_VISUAL_INTELLIGENCE_DECISION_REQUIRED" in text:
            status, code = "DECISION_REQUIRED", 3
        elif "E_VISUAL_INTELLIGENCE_REVIEW_REQUIRED" in text:
            status, code = "REVIEW_REQUIRED", 4
        else:
            status, code = "FAIL", 2
        report = {
            "status": status,
            "episodeDate": args.date,
            "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
            "errors": [text],
        }
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        renderer_binding.RendererBindingError,
        validate_visual_intelligence_package.VisualIntelligencePackageError,
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
