#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import build_final_production_package_v12 as final_v12  # noqa: E402


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    date = "2099-07-07"
    with tempfile.TemporaryDirectory(prefix="nasdaq-v12-preflight-") as temp:
        root = Path(temp)
        (root / "contracts").mkdir(parents=True)
        shutil.copyfile(ROOT / "contracts/renderer_binding.json", root / "contracts/renderer_binding.json")
        binding = json.loads((root / "contracts/renderer_binding.json").read_text(encoding="utf-8"))
        verification = root / "verification" / date
        preflight = verification / "official_execution_preflight.json"
        integrity = verification / "visual_intelligence_post_pass_integrity.json"
        package = root / "working" / date / "visual-intelligence" / "visual_intelligence_package.json"
        render_spec = root / "render-specs" / date / "render_spec.json"
        verification.mkdir(parents=True)
        package.parent.mkdir(parents=True)
        render_spec.parent.mkdir(parents=True)
        preflight.write_text(json.dumps({
            "contract_version": "1.0.0",
            "episode_memory_hardening": {"pre_build": "pass", "public_artifacts": "pass"},
            "authorization": {"preview": True, "final": False},
        }, indent=2) + "\n", encoding="utf-8")
        package.write_text(json.dumps({
            "contractVersion": "1.0.0",
            "bridgeContractVersion": binding["bridgeContractVersion"],
            "episodeDate": date,
            "inputs": {
                "editorialSnapshotSha256": "1" * 64,
                "rendererCommit": binding["renderer"]["commit"],
                "registrySnapshotSha256": binding["renderer"]["registrySnapshotSha256"],
            },
            "final": {"status": "PASS"},
        }, indent=2) + "\n", encoding="utf-8")
        render_spec.write_text(json.dumps({"schemaVersion": "2.4.0"}, indent=2) + "\n", encoding="utf-8")
        validation = {
            "status": "PASS",
            "episodeDate": date,
            "packageSha256": sha256(package),
            "compiledVisualSha256": "2" * 64,
        }
        integrity.write_text(json.dumps({
            "contractVersion": "1.0.0",
            "bridgeContractVersion": binding["bridgeContractVersion"],
            "episodeDate": date,
            "status": "PASS",
            "approvedCompiledVisualSha256": validation["compiledVisualSha256"],
            "finalRenderSpecSha256": sha256(render_spec),
            "sceneCount": 9,
            "beatCount": 18,
            "beatIdentityPreserved": True,
            "semanticSurfacePreserved": True,
            "visualAuthorityPreserved": True,
            "secondDirectorInvoked": False,
        }, indent=2) + "\n", encoding="utf-8")
        record = final_v12._persist_visual_intelligence_preflight_binding(
            output_root=root,
            date=date,
            repo_root=root,
            validation=validation,
        )
        value = json.loads(preflight.read_text(encoding="utf-8"))
        if value["episode_memory_hardening"] != {"pre_build": "pass", "public_artifacts": "pass"}:
            raise AssertionError("episode-memory hardening was changed by convergence binding")
        if value["authorization"] != {"preview": True, "final": False}:
            raise AssertionError("Preview/Final authorization was changed by convergence binding")
        if value["visual_intelligence"] != record:
            raise AssertionError("Visual Intelligence preflight record was not persisted exactly")
        if record["status"] != "PASS":
            raise AssertionError(record)
        if record["packageSha256"] != validation["packageSha256"]:
            raise AssertionError("package SHA missing from preflight record")
        if record["rendererCommit"] != binding["renderer"]["commit"]:
            raise AssertionError("Renderer SHA missing from preflight record")
        if record["registrySnapshotSha256"] != binding["renderer"]["registrySnapshotSha256"]:
            raise AssertionError("Registry SHA missing from preflight record")
        if record["postPassIntegritySha256"] != sha256(integrity):
            raise AssertionError("post-PASS integrity SHA missing from preflight record")
        if value["artifacts"]["visual_intelligence_post_pass_integrity"] != sha256(integrity):
            raise AssertionError("post-PASS integrity artifact was not bound")
    print("visual intelligence preflight binding tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
