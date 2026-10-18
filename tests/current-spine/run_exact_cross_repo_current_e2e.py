#!/usr/bin/env python3
"""PR-0B exact-pinned current Cross-Repo E2E.

The test consumes the canonical Plot renderer binding, rejects any checkout or
registry mismatch, reuses the existing current Renderer fixture/Visual Intelligence
E2E, and proves the Plot Preview V4 request is accepted by the pinned Renderer
request validator.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_authoring_runtime_policy(renderer_root: Path) -> dict:
    """Qualify the authoring instructions against the already-bound runtime."""
    scripts = str(ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from canon_manifest import document_bytes, load_manifest

    manifest = load_manifest(ROOT)
    production_spec = next(item for item in manifest["documents"] if item["id"] == "03")
    text = document_bytes(ROOT, production_spec).decode("utf-8")
    profiles = json.loads((renderer_root / "config/voice-profiles.json").read_text(encoding="utf-8"))["profiles"]
    main = profiles["fox-main"]
    charon = profiles["gemini-charon"]
    for field in ("provider", "model", "voice", "provisional"):
        if main[field] != charon[field]:
            raise AssertionError(f"production voice profiles disagree: {field}")
    if main["provider"] != "gemini" or main["voice"] != "Charon" or main["provisional"]:
        raise AssertionError("pinned production voice is not the approved Gemini Charon profile")
    model_token = r"(?<![A-Za-z0-9_.-])gemini-\d[A-Za-z0-9_.-]*-tts(?:-preview)?(?![A-Za-z0-9_.-])"
    models = set(re.findall(model_token, text))
    if models != {main["model"]}:
        raise AssertionError(
            f"authoring/runtime TTS policy mismatch: canon03={sorted(models)} runtime={main['model']}"
        )
    voices = set(re.findall(r"音声\s*`([^`]+)`", text))
    voices.update(re.findall(rf"(?:{model_token})の([A-Za-z][A-Za-z0-9-]*)", text))
    voices.update(re.findall(r"Gemini TTSの([A-Za-z][A-Za-z0-9-]*)", text))
    if voices != {main["voice"]}:
        raise AssertionError(
            f"authoring/runtime voice policy mismatch: canon03={sorted(voices)} runtime={main['voice']}"
        )

    policy = (renderer_root / "scripts/duration-policy.ts").read_text(encoding="utf-8")
    seconds = {}
    for boundary in ("MIN", "MAX"):
        match = re.search(rf"export const STANDARD_DURATION_{boundary}_MS = ([\d_]+);", policy)
        if not match:
            raise AssertionError(f"cannot read pinned Renderer duration boundary: {boundary}")
        milliseconds = int(match.group(1).replace("_", ""))
        if milliseconds % 1000:
            raise AssertionError("authoring duration comparison requires whole-second runtime boundaries")
        seconds[boundary] = milliseconds // 1000
    duration_range = f"実音声{seconds['MIN']}〜{seconds['MAX']}秒"
    authored_ranges = {
        (int(lower), int(upper))
        for lower, upper in re.findall(r"(?:実音声|実測音声|通常回の合格範囲|通常回の)(\d+)〜(\d+)秒", text)
    }
    if f"**{duration_range}**" not in text or authored_ranges != {(seconds["MIN"], seconds["MAX"])}:
        raise AssertionError(f"authoring/runtime duration policy mismatch: canon03 must specify {duration_range}")
    shortened_bounds = {int(value) for value in re.findall(r"実(?:測)?音声(?:が)?(\d+)秒未満", text)}
    if shortened_bounds != {seconds["MIN"]}:
        raise AssertionError("canon03 shortened boundary differs from the pinned runtime")
    upper_bounds = {int(value) for value in re.findall(r"実(?:測)?音声が(\d+)秒を超えた", text)}
    if upper_bounds != {seconds["MAX"]}:
        raise AssertionError("canon03 upper boundary differs from the pinned runtime")
    writing_ranges = re.findall(r"^\| [1-9] \| (\d+)〜(\d+)秒 \|", text, re.MULTILINE)
    if len(writing_ranges) != 9:
        raise AssertionError("canon03 must contain nine Scene writing-budget ranges")
    writing_min = sum(int(lower) for lower, _ in writing_ranges)
    writing_max = sum(int(upper) for _, upper in writing_ranges)
    if f"合計{writing_min}〜{writing_max}秒" not in text:
        raise AssertionError(f"canon03 Scene writing-budget total mismatch: actual={writing_min}〜{writing_max}秒")
    return {
        "authoringRuntimePolicy": "PASS",
        "productionTtsModel": main["model"],
        "productionVoice": main["voice"],
        "standardDurationSeconds": [seconds["MIN"], seconds["MAX"]],
        "sceneWritingBudgetSeconds": [writing_min, writing_max],
    }


def load_cross_repo_module():
    path = ROOT / "tests/remotion-compat/run_visual_intelligence_v12_cross_repo.py"
    spec = importlib.util.spec_from_file_location("current_visual_intelligence_cross_repo", path)
    if not spec or not spec.loader:
        raise AssertionError(f"cannot load existing current Cross-Repo E2E: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def verify_authored_causal_path(renderer_root: Path, cross_repo) -> dict:
    """Exercise real Current VI stages with independent authored causal engines."""
    spec = cross_repo.generate_current_fixture(renderer_root)
    scene = spec["scenes"][5]
    beat = scene["visualBeats"][0]
    scene["nodes"] = [
        {"nodeId": "scene-06-node-002", "label": "TEST COMPANY REACTION"},
        {"nodeId": "scene-06-node-001", "label": "TEST COMPANY FACTOR"},
        {"nodeId": "scene-06-node-004", "label": "TEST MACRO REACTION"},
        {"nodeId": "scene-06-node-003", "label": "TEST MACRO FACTOR"},
    ]
    scene["arrows"] = [
        {"arrowId": "scene-06-arrow-002", "fromNodeId": "scene-06-node-003", "toNodeId": "scene-06-node-004", "label": "TEST MACRO EDGE"},
        {"arrowId": "scene-06-arrow-001", "fromNodeId": "scene-06-node-001", "toNodeId": "scene-06-node-002", "label": "TEST COMPANY EDGE"},
    ]
    scene["visualEvents"] = []
    scene["visualMode"] = "causal-diagram"
    beat.update({
        "visualTemplate": "causal-lane",
        "templateVariant": "left-to-right",
        "visualGrammarId": "causal",
        "visualMode": "causal-diagram",
        "screenState": "Data",
        "sequencePolicy": "static",
        "objectIds": ["scene-06-node-001", "scene-06-node-002", "scene-06-arrow-001", "scene-06-node-003", "scene-06-node-004", "scene-06-arrow-002"],
        "templateConfig": {
            "variant": "left-to-right",
            "comparisonBasis": None,
            "dataBasis": "synthetic authored causal path acceptance",
            "nodeOrder": ["scene-06-node-001", "scene-06-node-002", "scene-06-node-003", "scene-06-node-004"],
            "laneLabels": [],
            "outcomeNodeId": None,
        },
    })
    result = cross_repo.run(renderer_root, fixture_override=spec)
    if result.get("status") != "PASS" or result.get("semanticDiff") != "PASS":
        raise AssertionError("independent authored graph did not preserve identity through Current VI")
    return {
        "authoredIndependentCausalPaths": "PASS",
        "authoredGraphOrderAndNullableOutcome": "PASS",
        "authoredCausalGraphPackageValidation": result["packageValidation"],
    }


def verify_preview_request_contract(renderer_root: Path, renderer: dict[str, str]) -> dict[str, str]:
    validator = renderer_root / "scripts/validate-current-request.py"
    if not validator.is_file():
        raise AssertionError(f"pinned Renderer Current request validator is missing: {validator}")

    date = "2099-07-01"
    bundle_id = "a" * 64
    artifact_name = "nasdaq-cafe-handoff-2099-07-01-123"
    with tempfile.TemporaryDirectory(prefix="nasdaq-current-preview-request-") as tmp:
        temp = Path(tmp)
        manifest = temp / "handoff_manifest.json"
        manifest.write_text(
            json.dumps({"episodeDate": date, "bundleId": bundle_id}) + "\n",
            encoding="utf-8",
        )
        request = temp / "current_preview_request_v4.json"
        built = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/build_current_preview_request_v4.py"),
                "--root",
                str(ROOT),
                "--date",
                date,
                "--manifest",
                str(manifest),
                "--plot-run-id",
                "123",
                "--artifact-name",
                artifact_name,
                "--output",
                str(request),
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        if built.returncode != 0:
            raise AssertionError(
                f"Plot Preview V4 request builder failed: stdout={built.stdout!r} stderr={built.stderr!r}"
            )

        value = json.loads(request.read_text(encoding="utf-8"))
        expected_fields = {
            "contractVersion",
            "episodeDate",
            "plotRunId",
            "handoffArtifactName",
            "expectedBundleId",
            "expectedManifestSha256",
            "expectedRendererCommit",
            "expectedRendererContractVersion",
            "expectedRegistrySnapshotSha256",
            "confirmation",
        }
        if set(value) != expected_fields:
            raise AssertionError(f"Plot Preview V4 request fields drifted: {sorted(value)}")
        if value.get("contractVersion") != "2.1.0":
            raise AssertionError("Plot Preview V4 request must use Renderer contractVersion 2.1.0")
        if value.get("expectedRendererCommit") != renderer["commit"]:
            raise AssertionError("Plot Preview V4 request Renderer commit mismatch")
        if value.get("expectedRendererContractVersion") != renderer["contractVersion"]:
            raise AssertionError("Plot Preview V4 request Renderer contract mismatch")
        if value.get("expectedRegistrySnapshotSha256") != renderer["registrySnapshotSha256"]:
            raise AssertionError("Plot Preview V4 request Registry SHA mismatch")

        accepted = subprocess.run(
            [sys.executable, str(validator), "preview", str(request)],
            cwd=renderer_root,
            check=False,
            capture_output=True,
            text=True,
        )
        if accepted.returncode != 0:
            raise AssertionError(
                "pinned Renderer rejected Plot Preview V4 request: "
                f"stdout={accepted.stdout!r} stderr={accepted.stderr!r}"
            )
        return {
            "previewRequestContractVersion": value["contractVersion"],
            "previewRequestRendererValidation": "PASS",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--renderer-root", required=True, type=Path)
    args = parser.parse_args()

    renderer_root = args.renderer_root.resolve()
    binding = json.loads((ROOT / "contracts/renderer_binding.json").read_text(encoding="utf-8"))
    renderer = binding["renderer"]

    actual_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=renderer_root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual_commit != renderer["commit"]:
        raise AssertionError(
            f"Renderer checkout drift: expected={renderer['commit']} actual={actual_commit}"
        )

    registry_path = renderer_root / renderer["registrySnapshotPath"]
    if not registry_path.is_file():
        raise AssertionError(f"pinned Renderer registry is missing: {registry_path}")
    registry_sha = sha256(registry_path)
    if registry_sha != renderer["registrySnapshotSha256"]:
        raise AssertionError(
            "Renderer Registry snapshot drift: "
            f"expected={renderer['registrySnapshotSha256']} actual={registry_sha}"
        )

    authoring_policy = verify_authoring_runtime_policy(renderer_root)
    cross_repo = load_cross_repo_module()
    result = cross_repo.run(renderer_root)
    result.update(verify_authored_causal_path(renderer_root, cross_repo))
    expected = {
        "status": "PASS",
        "rendererCommit": renderer["commit"],
        "machinePausedBeforeDecision": True,
        "staleCatalogDecisionRejected": True,
        "machinePausedBeforeCritic": True,
        "criticBoundToCompiledVisual": True,
        "packageValidation": "PASS",
    }
    for key, value in expected.items():
        if result.get(key) != value:
            raise AssertionError(
                f"current Cross-Repo observable contract drifted: {key}: "
                f"expected={value!r} actual={result.get(key)!r}"
            )

    preview_request = verify_preview_request_contract(renderer_root, renderer)
    output = {
        **result,
        **preview_request,
        **authoring_policy,
        "bridgeContractVersion": binding["bridgeContractVersion"],
        "rendererContractVersion": renderer["contractVersion"],
        "registrySnapshotSha256": registry_sha,
        "exactPinnedRenderer": True,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
