from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import renderer_binding
import validate_visual_intelligence_package as validator
import visual_director_bridge as bridge

DATE = "2099-01-02"
RENDERER_COMMIT = "5" * 40


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def argument(arguments: list[str], name: str) -> str:
    return arguments[arguments.index(name) + 1]


def render() -> dict:
    return {
        "schemaVersion": "2.4.0",
        "episode": {"targetDate": DATE},
        "scenes": [
            {
                "sceneId": "scene-01",
                "visualBeats": [
                    {"beatId": "vb-01-01", "visualTemplate": "text-focus"}
                ],
            }
        ],
    }


def fake_runner(renderer_root: Path, command: str, arguments: list[str]) -> None:
    del renderer_root
    spec_path = Path(argument(arguments, "--spec"))
    if command == "build":
        assert argument(arguments, "--candidate-builder") == "vnext"
        editorial_sha = argument(arguments, "--editorial-snapshot-sha256")
        assert editorial_sha == sha(spec_path)
        candidate_input_path = Path(argument(arguments, "--candidate-input"))
        write_json(
            candidate_input_path,
            {
                "contractVersion": "1.0.0",
                "episodeDate": DATE,
                "editorialSnapshotSha256": editorial_sha,
                "beats": [{"visualBeatId": "vb-01-01"}],
            },
        )
        inventory_path = Path(argument(arguments, "--capability-inventory"))
        write_json(
            inventory_path,
            {
                "contractVersion": "1.0.0",
                "episodeDate": DATE,
                "visualCandidateInputSha256": sha(candidate_input_path),
                "beats": [
                    {"visualBeatId": "vb-01-01", "capabilities": ["text-only"]}
                ],
            },
        )
        write_json(
            Path(argument(arguments, "--catalog")),
            {
                "contractVersion": "1.0.0",
                "episodeDate": DATE,
                "sourceRenderSpecSha256": editorial_sha,
                "candidates": [
                    {
                        "visualBeatId": "vb-01-01",
                        "candidateId": "vc-vb-01-01-01",
                    },
                    {
                        "visualBeatId": "vb-01-01",
                        "candidateId": "vc-vb-01-01-02",
                    },
                ],
            },
        )
        return

    assert command == "compile"
    compiled = json.loads(spec_path.read_text(encoding="utf-8"))
    write_json(Path(argument(arguments, "--output")), compiled)
    write_json(
        Path(argument(arguments, "--report")),
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "sourceRenderSpecSha256": sha(spec_path),
            "semanticDiff": "PASS",
            "warnings": [{"code": "LOW_VISUAL_VARIETY"}],
        },
    )


def prepare_fixture(root: Path, renderer_root: Path) -> Path:
    work = root / f"working/{DATE}/visual-intelligence"
    write_json(
        work / "visual_intent.json",
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "beats": [
                {
                    "visualBeatId": "vb-01-01",
                    "purpose": "矛盾を固定する",
                    "audienceBeliefBefore": "方向だけ見えている",
                    "audienceBeliefAfter": "何が矛盾か分かる",
                    "visualInformationGain": "比較対象を同時に見られる",
                    "preferredEvidenceModes": ["text-only"],
                    "realityAnchorPreference": "neutral",
                    "editorialReason": "理解対象を先に固定する",
                }
            ],
        },
    )
    write_json(
        work / "provisional_visual_direction.json",
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "requirements": [
                {
                    "visualBeatId": "vb-01-01",
                    "requiredModes": ["text-only"],
                    "imageRequirement": "not-required",
                    "reason": "画像は理解を増やさない",
                }
            ],
        },
    )
    write_json(root / f"verification/{DATE}/asset_resolution_log.json", {"status": "pass"})
    principles = root / "skills/nasdaq-cafe-visual-intelligence/references/VISUAL_EDITORIAL_INTELLIGENCE.md"
    principles.parent.mkdir(parents=True, exist_ok=True)
    principles.write_text("Visual change is not editorial progress.\n", encoding="utf-8")
    registry = renderer_root / "contracts/visual_component_registry_snapshot.json"
    write_json(registry, {"contractVersion": "1.0.0", "components": []})
    return work


def run_bridge(root: Path, renderer_root: Path):
    return bridge.prepare_and_compile(
        render=render(),
        output_root=root,
        date=DATE,
        renderer_root=renderer_root,
        expected_renderer_commit=RENDERER_COMMIT,
        runner=fake_runner,
        renderer_head=lambda _: RENDERER_COMMIT,
    )


def test_checkpointed_vnext_convergence_and_lineage(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    renderer_root = tmp_path / "renderer"
    work = prepare_fixture(root, renderer_root)

    with pytest.raises(bridge.VisualDirectorBridgeError, match="SELECTION_REQUIRED"):
        run_bridge(root, renderer_root)
    assert (work / "visual_candidate_input.json").is_file()
    assert (work / "visual_capability_inventory.json").is_file()
    assert (work / "visual_candidate_catalog.json").is_file()
    assert not (work / "visual_direction_plan.json").exists()

    write_json(
        work / "visual_editorial_selection.json",
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "round": 1,
            "selections": [
                {
                    "visualBeatId": "vb-01-01",
                    "selectedCandidateId": "vc-vb-01-01-02",
                    "strongestAlternativeCandidateId": "vc-vb-01-01-01",
                    "whySelected": "理解差が大きい",
                    "whyNotAlternative": "対抗は情報進展が弱い",
                }
            ],
        },
    )
    with pytest.raises(bridge.VisualDirectorBridgeError, match="REVIEW_REQUIRED"):
        run_bridge(root, renderer_root)
    assert (work / "visual_direction_plan.json").is_file()
    assert (work / "visual_editorial_warning_report.json").is_file()

    write_json(
        work / "visual_direction_review.json",
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "round": 1,
            "status": "PASS",
            "sourceEditorialSnapshotSha256": sha(work / "editorial_snapshot.json"),
            "sourceCandidateCatalogSha256": sha(work / "visual_candidate_catalog.json"),
            "sourceVisualDirectionPlanSha256": sha(work / "visual_direction_plan.json"),
            "sourceCompileReportSha256": sha(work / "visual_direction_compile_report.json"),
            "findings": [],
        },
    )
    result = run_bridge(root, renderer_root)
    assert result["package_path"].is_file()
    package = json.loads(result["package_path"].read_text(encoding="utf-8"))
    assert package["bridgeContractVersion"] == "visual-intelligence-bridge/1.2.0"
    assert package["final"]["status"] == "PASS"
    assert package["director"]["selections"][0]["selectedCandidateId"] == "vc-vb-01-01-02"

    source_root = Path(__file__).resolve().parents[2]
    (root / "contracts").mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        source_root / "contracts/visual_intelligence_package.schema.json",
        root / "contracts/visual_intelligence_package.schema.json",
    )
    binding = {
        "contractVersion": "1.0.0",
        "rendererRepository": "saienjoy0/saienjoy0-nasdaq-cafe-remotion",
        "rendererCommit": RENDERER_COMMIT,
        "rendererContractVersion": "2.4.0",
        "visualIntelligenceBridge": "visual-intelligence-bridge/1.2.0",
        "candidateBuilder": "vnext",
        "registrySnapshotPath": "contracts/visual_component_registry_snapshot.json",
    }
    write_json(root / "contracts/renderer_binding.json", binding)
    validated = validator.validate_package(
        repo_root=root,
        date=DATE,
        renderer_root=renderer_root,
    )
    assert validated["status"] == "PASS"
    assert validated["selectionCount"] == 1


def test_multiple_candidates_require_strongest_alternative(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    renderer_root = tmp_path / "renderer"
    work = prepare_fixture(root, renderer_root)
    with pytest.raises(bridge.VisualDirectorBridgeError, match="SELECTION_REQUIRED"):
        run_bridge(root, renderer_root)
    write_json(
        work / "visual_editorial_selection.json",
        {
            "contractVersion": "1.0.0",
            "episodeDate": DATE,
            "round": 1,
            "selections": [
                {
                    "visualBeatId": "vb-01-01",
                    "selectedCandidateId": "vc-vb-01-01-01",
                    "strongestAlternativeCandidateId": None,
                    "whySelected": "理由",
                    "whyNotAlternative": "",
                }
            ],
        },
    )
    with pytest.raises(bridge.VisualDirectorBridgeError, match="strongest alternative"):
        run_bridge(root, renderer_root)


def test_renderer_commit_mismatch_is_fail_closed(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    renderer_root = tmp_path / "renderer"
    prepare_fixture(root, renderer_root)
    with pytest.raises(bridge.VisualDirectorBridgeError, match="SHA mismatch"):
        bridge.prepare_and_compile(
            render=render(),
            output_root=root,
            date=DATE,
            renderer_root=renderer_root,
            expected_renderer_commit=RENDERER_COMMIT,
            runner=fake_runner,
            renderer_head=lambda _: "6" * 40,
        )


def test_canonical_renderer_binding_is_vnext() -> None:
    root = Path(__file__).resolve().parents[2]
    binding = renderer_binding.load_renderer_binding(root)
    assert binding["candidateBuilder"] == "vnext"
    assert binding["visualIntelligenceBridge"] == "visual-intelligence-bridge/1.2.0"
    assert binding["rendererCommit"] == "5391967099fbd7a0a2569c6c82b94d90aa889d64"
