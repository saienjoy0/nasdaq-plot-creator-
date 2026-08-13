#!/usr/bin/env python3
"""Authoritative guarded entry point for final production artifact generation."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class HardenedBuildError(ValueError):
    pass


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if not spec or not spec.loader:
        raise HardenedBuildError(f"cannot import {name}: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _real_gate(repo_root: Path, package: Path, artifacts: list[Path]):
    module = _load_module(
        "episode_memory_hardening_gate",
        repo_root / "skills/nasdaq-cafe-episode-package-memory/validators/validate_episode_package_memory_hardening.py",
    )
    return module.validate_hardening(
        repo_root=repo_root, episode_package=package, public_artifacts=artifacts,
    )


def _real_builder(package: Path, output_root: Path, schema: Path):
    module = _load_module(
        "final_production_base_builder", ROOT / "scripts/build_final_production_package.py"
    )
    return module.build(package, output_root, schema)


def _real_renderer_finalizer(*, output_root: Path, date: str, renderer_root: Path):
    module = _load_module(
        "renderer_package_finalizer_compat",
        ROOT / "scripts/finalize_renderer_package_compat.py",
    )
    intraday = _load_module(
        "renderer_intraday_series_attachment",
        ROOT / "scripts/remotion_intraday_series.py",
    )
    visual_intelligence_validator = _load_module(
        "visual_intelligence_package_validator",
        ROOT / "scripts/validate_visual_intelligence_package.py",
    )
    render_spec_path = output_root / "render-specs" / date / "render_spec.json"
    runtime_registry = module.base._build_validation_runtime_asset_registry(
        output_root=output_root,
        date=date,
        render_spec_path=render_spec_path,
    )
    previous_registry = os.environ.get("NASDAQ_CAFE_RUNTIME_ASSET_REGISTRY")
    if runtime_registry is not None:
        os.environ["NASDAQ_CAFE_RUNTIME_ASSET_REGISTRY"] = str(runtime_registry)

    # Keep the legacy canonical projection untouched. The production-only hardened
    # entry point decorates its existing call so explicitly bound full minute data is
    # attached immediately after projection and therefore before referential checks,
    # the pinned Renderer validator, and all persisted preflight hashes.
    original_canonicalize = module.remotion_240_projection.canonicalize_render_spec
    attachment_result: dict[str, Any] = {}

    def canonicalize_with_bound_intraday(
        render: dict[str, Any],
        *,
        episode_date: str,
        reaction_bindings_path: Path,
    ) -> None:
        original_canonicalize(
            render,
            episode_date=episode_date,
            reaction_bindings_path=reaction_bindings_path,
        )
        result = intraday.attach_bound_intraday_series(
            render,
            output_root=output_root,
            episode_date=episode_date,
            reaction_bindings_path=reaction_bindings_path,
        )
        attachment_result.clear()
        attachment_result.update(result)

    module.remotion_240_projection.canonicalize_render_spec = canonicalize_with_bound_intraday
    validation_path = output_root / "verification" / date / "visual_intelligence_validation.json"
    transaction_paths = module._transaction_paths(output_root, date) + [validation_path]
    outer_snapshot = module._snapshot(transaction_paths)
    try:
        finalized = module.finalize(
            output_root=output_root, date=date, renderer_root=renderer_root
        )
        visual_direction = finalized.get("visualDirection")
        if isinstance(visual_direction, dict):
            visual_validation = visual_intelligence_validator.validate_package(
                repo_root=output_root,
                date=date,
                renderer_root=renderer_root,
            )
            module.base.write_atomic(validation_path, visual_validation)
            package_path = (
                output_root
                / "working"
                / date
                / "visual-intelligence"
                / "visual_intelligence_package.json"
            )
            preflight_path = output_root / "verification" / date / "official_execution_preflight.json"
            preflight = module.base.load_json(preflight_path, "official execution preflight")
            artifacts = preflight.setdefault("artifacts", {})
            artifacts["visual_intelligence_package"] = module.base.sha256_file(package_path)
            artifacts["visual_intelligence_validation"] = module.base.sha256_file(validation_path)
            preflight["visual_intelligence_validation"] = {
                "status": "pass",
                "package_sha256": module.base.sha256_file(package_path),
                "report_sha256": module.base.sha256_file(validation_path),
            }
            module.base.write_atomic(preflight_path, preflight)
            finalized.setdefault("paths", {})["visual_intelligence_validation"] = str(validation_path)
            finalized.setdefault("hashes", {})["visual_intelligence_package"] = module.base.sha256_file(package_path)
            finalized["hashes"]["visual_intelligence_validation"] = module.base.sha256_file(validation_path)
            finalized["hashes"]["preflight"] = module.base.sha256_file(preflight_path)
            finalized["visualIntelligenceValidation"] = visual_validation
        if attachment_result:
            finalized["intradaySeriesAttachment"] = dict(attachment_result)
        return finalized
    except Exception:
        module._restore(outer_snapshot)
        raise
    finally:
        module.remotion_240_projection.canonicalize_render_spec = original_canonicalize
        if previous_registry is None:
            os.environ.pop("NASDAQ_CAFE_RUNTIME_ASSET_REGISTRY", None)
        else:
            os.environ["NASDAQ_CAFE_RUNTIME_ASSET_REGISTRY"] = previous_registry


def _errors(result: Any) -> list[str]:
    value = getattr(result, "errors", None)
    if isinstance(value, list):
        return list(value)
    if isinstance(result, dict) and result.get("status") == "fail":
        errors = result.get("errors", [])
        return list(errors) if isinstance(errors, list) else [str(errors)]
    return []


def _safe_output_root(repo_root: Path, output_root: Path) -> Path:
    root = repo_root.resolve()
    output = output_root.resolve()
    if output != root and root not in output.parents:
        raise HardenedBuildError(f"output root escapes repository root: {output_root}")
    return output


def _cleanup_generated(result: dict[str, Any]) -> None:
    paths = result.get("paths", {})
    if not isinstance(paths, dict):
        return
    for value in paths.values():
        if not isinstance(value, str):
            continue
        path = Path(value)
        try:
            if path.is_file():
                path.unlink()
        except OSError:
            pass


def _persist_preflight_hardening(preflight_path: Path) -> None:
    try:
        value = json.loads(preflight_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HardenedBuildError(
            f"cannot persist episode-memory hardening in preflight: {exc}"
        ) from exc
    if not isinstance(value, dict) or value.get("status") != "pass":
        raise HardenedBuildError(
            "preflight must be a PASS object before hardening can be persisted"
        )
    value["episode_memory_hardening"] = {
        "pre_build": "pass", "public_artifacts": "pass",
    }
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = preflight_path.with_name(preflight_path.name + ".hardening.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(preflight_path)


def _production_date(paths: dict[str, Any]) -> str:
    value = paths.get("render_spec")
    if not isinstance(value, str):
        raise HardenedBuildError("base builder omitted render_spec path")
    date = Path(value).parent.name
    if not DATE_RE.fullmatch(date):
        raise HardenedBuildError(f"cannot derive episode date from {value}")
    return date


def _merge_finalizer_result(result: dict[str, Any], finalized: dict[str, Any]) -> None:
    if not isinstance(finalized, dict) or finalized.get("status") != "pass":
        raise HardenedBuildError("renderer finalizer did not return PASS")
    final_paths = finalized.get("paths", {})
    if not isinstance(final_paths, dict):
        raise HardenedBuildError("renderer finalizer omitted paths")
    result.setdefault("paths", {}).update(final_paths)
    final_hashes = finalized.get("hashes", {})
    if isinstance(final_hashes, dict):
        result.setdefault("hashes", {}).update(final_hashes)
    result["renderer_finalization"] = {
        "status": "pass", "renderer_validation": "pass",
    }
    intraday_attachment = finalized.get("intradaySeriesAttachment")
    if isinstance(intraday_attachment, dict):
        result["intraday_series_attachment"] = intraday_attachment
    visual_direction = finalized.get("visualDirection")
    if isinstance(visual_direction, dict):
        result["visual_direction"] = visual_direction
    visual_intelligence_validation = finalized.get("visualIntelligenceValidation")
    if isinstance(visual_intelligence_validation, dict):
        result["visual_intelligence_validation"] = visual_intelligence_validation


def build_hardened(
    package: Path,
    output_root: Path,
    schema: Path,
    *,
    repo_root: Path = ROOT,
    gate: Callable[[Path, Path, list[Path]], Any] = _real_gate,
    builder: Callable[[Path, Path, Path], dict[str, Any]] = _real_builder,
    renderer_finalizer: Callable[..., dict[str, Any]] = _real_renderer_finalizer,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    package = package.resolve()
    output_root = _safe_output_root(repo_root, output_root)
    pre = gate(repo_root, package, [])
    pre_errors = _errors(pre)
    if pre_errors:
        raise HardenedBuildError(
            "episode-memory pre-build gate failed:\n" + "\n".join(pre_errors)
        )
    result = builder(package, output_root, schema)
    if not isinstance(result, dict) or result.get("status") != "pass":
        raise HardenedBuildError("base final production builder did not return PASS")

    paths = result.get("paths", {})
    required = ("spoken_script", "asset_manifest", "render_spec")
    artifacts: list[Path] = []
    for key in required:
        value = paths.get(key) if isinstance(paths, dict) else None
        if not isinstance(value, str):
            _cleanup_generated(result)
            raise HardenedBuildError(f"base builder omitted required artifact path: {key}")
        artifacts.append(Path(value))

    renderer_root_value = os.environ.get("NASDAQ_CAFE_RENDERER_ROOT")
    date: str | None = None
    if renderer_root_value:
        date = _production_date(paths if isinstance(paths, dict) else {})
        try:
            finalized = renderer_finalizer(
                output_root=output_root, date=date,
                renderer_root=Path(renderer_root_value),
            )
            _merge_finalizer_result(result, finalized)
        except Exception:
            _cleanup_generated(result)
            raise
    else:
        render_value = paths.get("render_spec") if isinstance(paths, dict) else None
        if isinstance(render_value, str) and DATE_RE.fullmatch(Path(render_value).parent.name):
            date = Path(render_value).parent.name
            request_exists = (
                output_root / "working" / date / "production_request.json"
            ).is_file()
            if request_exists:
                _cleanup_generated(result)
                raise HardenedBuildError(
                    "NASDAQ_CAFE_RENDERER_ROOT is required for production renderer validation"
                )

    paths = result.get("paths", {})
    artifacts = [Path(paths[key]) for key in required]
    post = gate(repo_root, package, artifacts)
    post_errors = _errors(post)
    if post_errors:
        _cleanup_generated(result)
        raise HardenedBuildError(
            "episode-memory public-artifact gate failed:\n" + "\n".join(post_errors)
        )
    preflight_value = paths.get("preflight") if isinstance(paths, dict) else None
    if not isinstance(preflight_value, str):
        _cleanup_generated(result)
        raise HardenedBuildError("base builder omitted required artifact path: preflight")
    try:
        _persist_preflight_hardening(Path(preflight_value))
    except Exception:
        _cleanup_generated(result)
        raise
    result["episode_memory_hardening"] = {
        "pre_build": "pass", "public_artifacts": "pass",
        "preflight_persisted": "pass",
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--episode-package", required=True, type=Path)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument(
        "--schema", type=Path,
        default=ROOT / "skills/nasdaq-cafe-final-production/contracts/final_production_source_annex.schema.json",
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    try:
        result = build_hardened(
            args.episode_package, args.output_root, args.schema, repo_root=args.repo_root,
        )
        code = 0
    except (OSError, HardenedBuildError, ValueError, json.JSONDecodeError) as exc:
        result = {"status": "fail", "errors": [str(exc)]}
        code = 1
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
