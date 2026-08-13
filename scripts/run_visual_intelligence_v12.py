#!/usr/bin/env python3
"""Execute the machine half of visual-intelligence-bridge/1.2.0.

The first invocation is expected to stop with DECISION_REQUIRED after producing
CandidateInput/Capability/Catalog when AI-B has not authored its decision yet.
Once the AI-B decision exists, this command compiles, runs the strict package
validator, and writes the evidence used by `visual_intelligence_valid`.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import renderer_binding
import validate_visual_intelligence_package
import visual_intelligence_bridge
import visual_intelligence_renderer_projection


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
        producer_render = load_json(args.render_spec)
        candidate_render = (
            visual_intelligence_renderer_projection.project_visual_intelligence_renderer_input(
                producer_render,
                repo_root=root,
                date=args.date,
            )
        )
        result = visual_intelligence_bridge.prepare_and_compile(
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
        report = {
            **validation,
            "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
            "candidateCatalog": str(result["catalog_path"].relative_to(root)),
            "compiledVisual": str(
                (root / "working" / args.date / "visual-intelligence" / "visual_direction_compiled_render.json").relative_to(root)
            ),
        }
        code = 0
    except visual_intelligence_bridge.VisualIntelligenceBridgeError as exc:
        text = str(exc)
        status = "DECISION_REQUIRED" if "E_VISUAL_INTELLIGENCE_DECISION_REQUIRED" in text else "FAIL"
        report = {
            "status": status,
            "episodeDate": args.date,
            "bridgeContractVersion": renderer_binding.BRIDGE_CONTRACT_VERSION,
            "errors": [text],
        }
        code = 3 if status == "DECISION_REQUIRED" else 2
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        renderer_binding.RendererBindingError,
        validate_visual_intelligence_package.VisualIntelligencePackageError,
        visual_intelligence_renderer_projection.VisualIntelligenceRendererProjectionError,
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
