#!/usr/bin/env python3
"""Verify current request bytes are immutable from init through Final authorization."""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import run_daily_production_v12 as v12  # noqa: E402

DATE = "2099-04-01"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="nasdaq-current-request-") as temp:
        root = Path(temp)
        (root / "contracts").mkdir(parents=True)
        shutil.copyfile(
            ROOT / "contracts/renderer_binding.json",
            root / "contracts/renderer_binding.json",
        )
        binding = json.loads(
            (root / "contracts/renderer_binding.json").read_text(encoding="utf-8")
        )
        daily = root / "daily-inputs" / DATE / f"daily_source_package_{DATE}.md"
        daily.parent.mkdir(parents=True)
        daily.write_text("# synthetic current source\n", encoding="utf-8")
        freeze = root / "semantic-freezes" / f"{DATE}.json"
        freeze.parent.mkdir(parents=True)
        freeze.write_text(
            json.dumps({"contractVersion": "1.2.0", "episodeDate": DATE}) + "\n",
            encoding="utf-8",
        )

        module = v12.load_module()
        result = v12.init_request(
            module=module,
            workspace=root,
            date=DATE,
            daily_source=daily,
            requested_scope="preview",
            renderer_commit=binding["renderer"]["commit"],
            renderer_contract_version=binding["renderer"]["contractVersion"],
            visual_intelligence_bridge_version=binding["bridgeContractVersion"],
            semantic_freeze_path=freeze,
            semantic_freeze_sha256=module.sha256_file(freeze),
        )
        if result.get("status") != "created":
            raise AssertionError(result)
        request_path = module.request_path(root, DATE)
        before = request_path.read_bytes()
        request = json.loads(before)
        if request.get("visual_intelligence", {}).get("required") is not True:
            raise AssertionError("current request was not born with Visual Intelligence binding")
        if request.get("semantic_freeze", {}).get("sha256") != module.sha256_file(freeze):
            raise AssertionError("current request was not born with Semantic Freeze binding")
        if (
            request.get("renderer", {}).get("registry_snapshot_sha256")
            != binding["renderer"]["registrySnapshotSha256"]
        ):
            raise AssertionError("current request was not born with Registry binding")
        if request.get("approvals", {}).get("final_requested") is not False:
            raise AssertionError("Final must not be pre-authorized in the production request")

        state_path = module.state_path(root, DATE)
        state = module.load_json(state_path, "production state")
        request_sha = state["request_sha256"]
        state["current_state"] = "user_preview_approved"
        module.write_atomic(state_path, state)
        approval = root / "verification" / DATE / "approval.json"
        approval.parent.mkdir(parents=True)
        module.write_atomic(
            approval,
            {"episode_date": DATE, "status": "approved", "final_requested": True},
        )
        module.request_final(
            workspace=root,
            date=DATE,
            approval_record=approval,
            explicit_final=True,
        )
        after = request_path.read_bytes()
        final_state = module.load_json(state_path, "production state")
        if before != after:
            raise AssertionError("current production request changed after Final authorization")
        if final_state.get("request_sha256") != request_sha:
            raise AssertionError("current request SHA changed after Final authorization")
        if final_state.get("current_state") != "final_requested":
            raise AssertionError("Final authorization did not advance current state")
        final_request = json.loads(after)
        if final_request.get("approvals", {}).get("final_requested") is not False:
            raise AssertionError("Final authorization leaked back into immutable request bytes")

    print("current request immutability PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
