#!/usr/bin/env python3
"""One-shot deterministic PR-1 migration.

Every replacement is guarded by exact occurrence/marker checks. The workflow removes
this script after successful application; it is not a production entrypoint.
"""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def replace_between(text: str, start_marker: str, end_marker: str, replacement: str, label: str) -> str:
    start = text.find(start_marker)
    if start < 0:
        raise SystemExit(f"{label}: start marker missing")
    end = text.find(end_marker, start)
    if end < 0:
        raise SystemExit(f"{label}: end marker missing")
    if text.find(start_marker, start + 1) >= 0:
        raise SystemExit(f"{label}: start marker is not unique")
    return text[:start] + replacement + text[end:]


v12_path = ROOT / "scripts/run_daily_production_v12.py"
v12 = v12_path.read_text(encoding="utf-8")
v12 = replace_once(
    v12,
    "import build_final_production_package_v12 as final_v12\nimport renderer_binding\nimport run_daily_production_hardened as hardened\n",
    "import build_final_production_package_v12 as final_v12\nimport current_daily_mechanisms_v12 as current_mechanisms\nimport renderer_binding\n",
    "current policy import",
)
v12 = replace_once(
    v12,
    "def load_module():\n    return hardened.load_hardened_daily_module()\n",
    "def load_module():\n    return current_mechanisms.load_module()\n",
    "current policy loader",
)

new_init = '''def init_request(
    *,
    module: Any,
    workspace: Path,
    date: str,
    daily_source: Path,
    requested_scope: str,
    renderer_commit: str,
    renderer_contract_version: str,
    visual_intelligence_bridge_version: str,
    semantic_freeze_path: Path,
    semantic_freeze_sha256: str,
) -> dict[str, Any]:
    workspace = workspace.resolve()
    if visual_intelligence_bridge_version != renderer_binding.BRIDGE_CONTRACT_VERSION:
        raise module.DailyProductionError(
            module.ERROR_CODES["renderer"], "unsupported Visual Intelligence bridge version"
        )
    canonical = renderer_binding.load_binding(workspace)
    renderer = canonical["renderer"]
    if (
        renderer_commit != renderer["commit"]
        or renderer_contract_version != renderer["contractVersion"]
    ):
        raise module.DailyProductionError(
            module.ERROR_CODES["renderer"],
            "request Renderer does not match canonical binding",
        )

    daily_source = module.safe_path(workspace, daily_source, "daily source")
    module.validate_date_in_name(date, daily_source, "daily source")
    if daily_source.stat().st_size == 0:
        raise module.DailyProductionError(
            module.ERROR_CODES["stale"], "daily source must be non-empty"
        )
    if requested_scope not in {"package", "preview"}:
        raise module.DailyProductionError(
            module.ERROR_CODES["final"],
            "initial requested_scope may only be package or preview",
        )
    freeze = module.safe_path(workspace, semantic_freeze_path, "semantic freeze")
    actual_freeze_sha = module.sha256_file(freeze)
    if semantic_freeze_sha256 != actual_freeze_sha:
        raise module.DailyProductionError(
            module.ERROR_CODES["stale"],
            "semantic freeze SHA does not match request input",
        )

    req_path = module.request_path(workspace, date)
    st_path = module.state_path(workspace, date)
    if req_path.exists() or st_path.exists():
        existing = status(module=module, workspace=workspace, date=date)
        if existing["validation"]["status"] != "pass":
            raise module.DailyProductionError(
                module.ERROR_CODES["stale"],
                "existing current request/state is stale or invalid",
            )
        request = _request(module, workspace, date)
        _validate_vi_binding(module, request)
        expected_freeze = {
            "path": freeze.relative_to(workspace).as_posix(),
            "sha256": actual_freeze_sha,
        }
        if request.get("semantic_freeze") != expected_freeze:
            raise module.DailyProductionError(
                module.ERROR_CODES["stale"],
                "existing current request binds a different Semantic Freeze",
            )
        return {"status": "noop", **existing}

    request = {
        "contract_version": "1.2.0",
        "episode_date": date,
        "requested_scope": requested_scope,
        "daily_source": {
            "path": daily_source.relative_to(workspace).as_posix(),
            "sha256": module.sha256_file(daily_source),
        },
        "semantic_freeze": {
            "path": freeze.relative_to(workspace).as_posix(),
            "sha256": actual_freeze_sha,
        },
        "renderer": {
            "repository": renderer_binding.RENDERER_REPOSITORY,
            "commit": renderer_commit,
            "contract_version": renderer_contract_version,
            "registry_snapshot_sha256": renderer["registrySnapshotSha256"],
        },
        "visual_director": {"required": True, "contract_version": "1.0.0"},
        "visual_intelligence": {
            "required": True,
            "bridge_contract_version": renderer_binding.BRIDGE_CONTRACT_VERSION,
            "frozen_interface_sha256": renderer_binding.FROZEN_INTERFACE_SHA256,
        },
        "approvals": {
            "preview_requested": requested_scope == "preview",
            "final_requested": False,
            "memory_promotion_requested": False,
        },
    }
    module.write_atomic(req_path, request)
    request_sha = module.sha256_file(req_path)
    state = {
        "contract_version": "1.2.0",
        "episode_date": date,
        "current_state": "intake_ready",
        "request_sha256": request_sha,
        "daily_source_sha256": request["daily_source"]["sha256"],
        "invalidated": False,
        "transitions": [
            {
                "state": "intake_ready",
                "evidence": [
                    request["daily_source"],
                    {
                        "path": req_path.relative_to(workspace).as_posix(),
                        "sha256": request_sha,
                    },
                    request["semantic_freeze"],
                ],
            }
        ],
    }
    module.write_atomic(st_path, state)
    return {
        "status": "created",
        "request_path": str(req_path),
        "state_path": str(st_path),
        "current_state": "intake_ready",
    }


'''
v12 = replace_between(
    v12,
    "def _rebind_request_sha(",
    "def status(",
    new_init,
    "current-native request writer",
)

new_status = '''def status(*, module: Any, workspace: Path, date: str) -> dict[str, Any]:
    workspace = workspace.resolve()
    req_path = module.request_path(workspace, date)
    st_path = module.state_path(workspace, date)
    request = module.load_json(req_path, "production request")
    state = module.load_json(st_path, "production state")
    errors: list[str] = []
    if request.get("episode_date") != date or state.get("episode_date") != date:
        errors.append("request/state episode date mismatch")
    if module.sha256_file(req_path) != state.get("request_sha256"):
        errors.append("production request SHA changed")
    try:
        _validate_vi_binding(module, request)
    except module.DailyProductionError as exc:
        errors.append(exc.message)

    try:
        daily_source = module.safe_path(
            workspace,
            request.get("daily_source", {}).get("path", ""),
            "daily source",
        )
        daily_sha = module.sha256_file(daily_source)
        if daily_sha != request.get("daily_source", {}).get("sha256"):
            errors.append("daily source SHA changed from production request")
        if daily_sha != state.get("daily_source_sha256"):
            errors.append("daily source SHA changed from production state")
        freeze = module.safe_path(
            workspace,
            request.get("semantic_freeze", {}).get("path", ""),
            "semantic freeze",
        )
        if module.sha256_file(freeze) != request.get("semantic_freeze", {}).get("sha256"):
            errors.append("Semantic Freeze SHA changed from production request")
    except module.DailyProductionError as exc:
        errors.append(exc.message)

    try:
        canonical = renderer_binding.load_binding(workspace)
        renderer = canonical["renderer"]
        requested_renderer = request.get("renderer", {})
        if requested_renderer.get("commit") != renderer["commit"]:
            errors.append("production request Renderer commit drifted from canonical binding")
        if requested_renderer.get("contract_version") != renderer["contractVersion"]:
            errors.append("production request Renderer contract drifted from canonical binding")
        if (
            requested_renderer.get("registry_snapshot_sha256")
            != renderer["registrySnapshotSha256"]
        ):
            errors.append("production request Registry SHA drifted from canonical binding")
    except renderer_binding.RendererBindingError as exc:
        errors.append(str(exc))

    for t_index, transition in enumerate(state.get("transitions", [])):
        for e_index, evidence in enumerate(transition.get("evidence", [])):
            try:
                path = module.safe_path(
                    workspace,
                    evidence.get("path", ""),
                    f"transitions[{t_index}].evidence[{e_index}]",
                )
            except module.DailyProductionError as exc:
                errors.append(exc.message)
                continue
            if module.sha256_file(path) != evidence.get("sha256"):
                errors.append(
                    f"transitions[{t_index}].evidence[{e_index}] SHA mismatch: "
                    f"{evidence.get('path')}"
                )

    current = state.get("current_state")
    next_state = (
        VI_STATES[VI_STATES.index(current) + 1]
        if current in VI_STATES and current != VI_STATES[-1]
        else None
    )
    return {
        "episode_date": date,
        "current_state": current,
        "next_state": next_state,
        "requested_scope": request.get("requested_scope"),
        "validation": {
            "status": "pass" if not errors and not state.get("invalidated") else "fail",
            "errors": errors,
        },
        "visual_intelligence_bridge": renderer_binding.BRIDGE_CONTRACT_VERSION,
    }


'''
v12 = replace_between(
    v12,
    "def status(",
    "def _evidence_by_name",
    new_status,
    "current status policy",
)
v12 = v12.replace("hardened._load_module", "current_mechanisms.load_external_module")
if "hardened._load_module" in v12:
    raise SystemExit("legacy external loader remained in current policy")
v12 = replace_once(
    v12,
    '''    request = _request(module, workspace, date)
    if not _is_vi_request(request):
        return module.add_transition(
            workspace=workspace,
            date=date,
            new_state=new_state,
            evidence_paths=evidence_paths,
            allow_multi_step=False,
        )
''',
    '''    request = _request(module, workspace, date)
    if not _is_vi_request(request):
        raise module.DailyProductionError(
            module.ERROR_CODES["stale"],
            "current-v1.2 control plane requires Visual Intelligence binding",
        )
''',
    "current-only transition policy",
)
v12 = replace_once(
    v12,
    '    p_init.add_argument("--visual-intelligence-bridge-version", required=True)\n',
    '    p_init.add_argument("--visual-intelligence-bridge-version", required=True)\n'
    '    p_init.add_argument("--semantic-freeze-path", required=True, type=Path)\n'
    '    p_init.add_argument("--semantic-freeze-sha256", required=True)\n',
    "current init CLI fields",
)
v12 = replace_once(
    v12,
    '''                visual_intelligence_bridge_version=args.visual_intelligence_bridge_version,
            )
''',
    '''                visual_intelligence_bridge_version=args.visual_intelligence_bridge_version,
                semantic_freeze_path=args.semantic_freeze_path,
                semantic_freeze_sha256=args.semantic_freeze_sha256,
            )
''',
    "current init CLI call",
)
if "run_daily_production_hardened" in v12 or "_rebind_request_sha" in v12:
    raise SystemExit("legacy current policy dependency or request SHA rebind remained")
v12_path.write_text(v12, encoding="utf-8")

closure_path = ROOT / "scripts/run_daily_renderer_closure_v12.py"
closure = closure_path.read_text(encoding="utf-8")
closure = replace_once(
    closure,
    '''    run(
        root, "python3", "scripts/run_daily_production_v12.py", "--workspace", ".", "init",
        "--episode-date", date, "--daily-source-package", f"daily-inputs/{date}/daily_source_package_{date}.md",
        "--requested-scope", "preview", "--renderer-commit", renderer["commit"],
        "--renderer-contract-version", renderer["contractVersion"],
        "--visual-intelligence-bridge-version", binding["bridgeContractVersion"], env=env,
    )
''',
    '''    run(
        root, "python3", "scripts/run_daily_production_v12.py", "--workspace", ".", "init",
        "--episode-date", date, "--daily-source-package", f"daily-inputs/{date}/daily_source_package_{date}.md",
        "--requested-scope", "preview", "--renderer-commit", renderer["commit"],
        "--renderer-contract-version", renderer["contractVersion"],
        "--visual-intelligence-bridge-version", binding["bridgeContractVersion"],
        "--semantic-freeze-path", str(freeze.relative_to(root)),
        "--semantic-freeze-sha256", env.get("NASDAQ_CAFE_SEMANTIC_FREEZE_SHA256", ""),
        env=env,
    )
''',
    "semantic freeze request binding",
)
closure_path.write_text(closure, encoding="utf-8")

state_test_path = ROOT / "tests/remotion-compat/test_visual_intelligence_v12_state.py"
state_test = state_test_path.read_text(encoding="utf-8")
if state_test.count("v12.hardened._load_module") != 6:
    raise SystemExit(
        "v1.2 state test hardened-loader occurrence drift: "
        f"{state_test.count('v12.hardened._load_module')}"
    )
state_test = state_test.replace(
    "v12.hardened._load_module",
    "v12.current_mechanisms.load_external_module",
)
state_test_path.write_text(state_test, encoding="utf-8")

character_path = ROOT / "tests/current-spine/test_current_spine_characterization.py"
character = character_path.read_text(encoding="utf-8")
character = replace_once(
    character,
    '''def require(source: str, needle: str, label: str) -> None:
    if needle not in source:
        raise AssertionError(f"current characterization drifted: {label}: {needle!r}")


''',
    '''def require(source: str, needle: str, label: str) -> None:
    if needle not in source:
        raise AssertionError(f"current characterization drifted: {label}: {needle!r}")


def forbid(source: str, needle: str, label: str) -> None:
    if needle in source:
        raise AssertionError(f"resolved divergence regressed: {label}: {needle!r}")


''',
    "characterization forbid helper",
)
old_character_block = '''    # CURRENT_POLICY still inherits policy from the hardened/legacy stack.
    require(current, "import run_daily_production_hardened as hardened", "current -> hardened policy dependency")
    require(current, "return hardened.load_hardened_daily_module()", "v1.2 control-plane loader")

    # Current request is not born complete yet: VI binding is appended and the
    # request/state lineage is repaired after the initial request write.
    require(current, "def _rebind_request_sha", "post-hoc request SHA repair helper")
    require(current, 'request["visual_intelligence"] = {', "post-init Visual Intelligence binding")
    require(current, "_rebind_request_sha(module, workspace, date)", "post-init request SHA rebind")

    # The base request is also mutated when Final is requested, including evidence
    # SHA rewrite. PR-1 must make the current request immutable for the full attempt.
    require(base, 'request["approvals"]["final_requested"] = True', "base request mutation at Final request")
    require(base, 'evidence["sha256"] = state["request_sha256"]', "request evidence SHA rewrite")
'''
new_character_block = '''    # PR-1 resolves Current -> legacy policy inheritance. Shared hardened stage
    # executors remain behind the dedicated mechanism module only.
    require(current, "import current_daily_mechanisms_v12 as current_mechanisms", "current mechanisms dependency")
    forbid(current, "run_daily_production_hardened", "current -> hardened policy dependency")

    # Current request is now born complete and immutable for the attempt.
    forbid(current, "def _rebind_request_sha", "post-hoc request SHA repair helper")
    require(current, '"semantic_freeze": {', "Semantic Freeze bound at request creation")
    require(current, '"registry_snapshot_sha256":', "Registry identity bound at request creation")

    # Legacy/base still mutates its own request. That is permitted only outside the
    # current path and remains visible until PR-8 legacy isolation documentation.
    require(base, 'request["approvals"]["final_requested"] = True', "legacy request mutation at Final request")
    require(base, 'evidence["sha256"] = state["request_sha256"]', "legacy request evidence SHA rewrite")
'''
character = replace_once(
    character,
    old_character_block,
    new_character_block,
    "PR-1 characterization expectations",
)
character_path.write_text(character, encoding="utf-8")

immutability_test = '''#!/usr/bin/env python3
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
        binding = json.loads((root / "contracts/renderer_binding.json").read_text(encoding="utf-8"))
        daily = root / "daily-inputs" / DATE / f"daily_source_package_{DATE}.md"
        daily.parent.mkdir(parents=True)
        daily.write_text("# synthetic current source\n", encoding="utf-8")
        freeze = root / "semantic-freezes" / f"{DATE}.json"
        freeze.parent.mkdir(parents=True)
        freeze.write_text(json.dumps({"contractVersion": "1.2.0", "episodeDate": DATE}) + "\n", encoding="utf-8")

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
        if request.get("renderer", {}).get("registry_snapshot_sha256") != binding["renderer"]["registrySnapshotSha256"]:
            raise AssertionError("current request was not born with Registry binding")

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

    print("current request immutability PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''
immutability_path = ROOT / "tests/current-spine/test_current_request_immutability.py"
if immutability_path.exists():
    raise SystemExit("immutability test unexpectedly already exists")
immutability_path.write_text(immutability_test, encoding="utf-8")

print("PR-1 deterministic migration applied")
