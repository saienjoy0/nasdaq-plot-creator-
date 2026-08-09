#!/usr/bin/env python3
"""Resolve pre-approved Visual Source candidates without performing discovery.

The resolver processes the Primary and Approved Fallback candidates already
stored in the Final Episode Contract. It never searches for alternatives and
never chooses which candidate is used in production.
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import os
import shutil
import socket
import subprocess
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_IMAGE_FORMATS = {"PNG", "JPEG", "WEBP"}


class VisualSourceResolutionError(ValueError):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise VisualSourceResolutionError(f"{label} invalid: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualSourceResolutionError(f"{label} root must be an object")
    return value


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    tmp = path.with_name(f".{path.name}.visual-source.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def safe_relative_file(root: Path, relative: str, label: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise VisualSourceResolutionError(f"{label}: unsafe relative path: {relative}")
    root = root.resolve()
    resolved = (root / path).resolve()
    if resolved != root and root not in resolved.parents:
        raise VisualSourceResolutionError(f"{label}: path escapes root: {relative}")
    if not resolved.is_file() or resolved.stat().st_size == 0:
        raise VisualSourceResolutionError(f"{label}: missing or empty file: {relative}")
    return resolved


def _ensure_output_root(repo_root: Path, asset_root: Path) -> Path:
    root = repo_root.resolve()
    resolved = asset_root.resolve()
    if resolved != root and root not in resolved.parents:
        raise VisualSourceResolutionError(
            f"E_VISUAL_SOURCE_OUTPUT_INVALID: asset root escapes repository: {resolved}"
        )
    return resolved


def _host_is_public(hostname: str) -> bool:
    if not hostname or hostname.lower() in {"localhost", "localhost.localdomain"}:
        return False
    try:
        literal = ipaddress.ip_address(hostname.strip("[]"))
        return not (
            literal.is_private
            or literal.is_loopback
            or literal.is_link_local
            or literal.is_multicast
            or literal.is_reserved
            or literal.is_unspecified
        )
    except ValueError:
        pass
    try:
        addresses = socket.getaddrinfo(hostname, None, proto=socket.IPPROTO_TCP)
    except OSError:
        return False
    if not addresses:
        return False
    for item in addresses:
        address = ipaddress.ip_address(item[4][0])
        if (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_multicast
            or address.is_reserved
            or address.is_unspecified
        ):
            return False
    return True


def validate_external_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in {"http", "https"}:
        raise VisualSourceResolutionError("E_VISUAL_SOURCE_REDIRECT_FORBIDDEN: URL scheme")
    if parsed.username is not None or parsed.password is not None:
        raise VisualSourceResolutionError("E_VISUAL_SOURCE_REDIRECT_FORBIDDEN: credential URL")
    if not parsed.hostname or not _host_is_public(parsed.hostname):
        raise VisualSourceResolutionError("E_VISUAL_SOURCE_REDIRECT_FORBIDDEN: non-public host")
    return value


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_external_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _open_exact(url: str):
    validate_external_url(url)
    opener = urllib.request.build_opener(SafeRedirectHandler())
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "NasdaqCafeVisualSource/1.0 (+auditable exact-locator resolver)"},
    )
    try:
        return opener.open(request, timeout=25)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise VisualSourceResolutionError(f"E_VISUAL_SOURCE_FETCH_FAILED: {exc}") from exc


def download_exact(url: str, target: Path) -> tuple[str, str | None]:
    with _open_exact(url) as response:
        final_url = validate_external_url(response.geturl())
        content_type = response.headers.get_content_type()
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_DOWNLOAD_BYTES:
            raise VisualSourceResolutionError("E_VISUAL_SOURCE_TOO_LARGE")
        target.parent.mkdir(parents=True, exist_ok=True)
        received = 0
        try:
            with target.open("wb") as handle:
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    received += len(chunk)
                    if received > MAX_DOWNLOAD_BYTES:
                        raise VisualSourceResolutionError("E_VISUAL_SOURCE_TOO_LARGE")
                    handle.write(chunk)
        except OSError as exc:
            raise VisualSourceResolutionError(f"E_VISUAL_SOURCE_FETCH_FAILED: {exc}") from exc
    return final_url, content_type


def _json_exact(url: str) -> tuple[str, dict[str, Any]]:
    with _open_exact(url) as response:
        final_url = validate_external_url(response.geturl())
        length = response.headers.get("Content-Length")
        if length and int(length) > 2 * 1024 * 1024:
            raise VisualSourceResolutionError("E_VISUAL_SOURCE_TOO_LARGE")
        raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise VisualSourceResolutionError("E_VISUAL_SOURCE_TOO_LARGE")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise VisualSourceResolutionError(f"E_VISUAL_SOURCE_FETCH_FAILED: invalid JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise VisualSourceResolutionError("E_VISUAL_SOURCE_FETCH_FAILED: JSON root must be object")
    return final_url, value


def _normalize_image(source: Path, output: Path) -> tuple[int, int, str]:
    try:
        with Image.open(source) as image:
            image.load()
            if image.format not in ALLOWED_IMAGE_FORMATS:
                raise VisualSourceResolutionError(
                    f"E_VISUAL_SOURCE_MIME_INVALID: unsupported image format {image.format}"
                )
            width, height = image.size
            if width < 16 or height < 16 or width > 10000 or height > 10000:
                raise VisualSourceResolutionError(
                    f"E_VISUAL_SOURCE_OUTPUT_INVALID: invalid image dimensions {width}x{height}"
                )
            normalized = image.convert("RGB") if image.mode not in {"RGB", "RGBA"} else image.copy()
            output.parent.mkdir(parents=True, exist_ok=True)
            normalized.save(output, format="PNG")
            return width, height, "image/png"
    except VisualSourceResolutionError:
        raise
    except Exception as exc:
        raise VisualSourceResolutionError(f"E_VISUAL_SOURCE_OUTPUT_INVALID: {exc}") from exc


def _collector_document(
    *, collector_root: Path, episode_date: str, locator: dict[str, Any], capture: str
) -> Path:
    if isinstance(locator.get("localPath"), str):
        return safe_relative_file(collector_root, locator["localPath"], "collector localPath")
    document_id = locator.get("documentId")
    if not isinstance(document_id, str) or not document_id:
        raise VisualSourceResolutionError("E_VISUAL_SOURCE_LOCATOR_MISSING: documentId")
    if "/" in document_id or "\\" in document_id or document_id in {".", ".."}:
        raise VisualSourceResolutionError("E_VISUAL_SOURCE_LOCATOR_MISSING: unsafe documentId")
    base = collector_root / "output" / episode_date / "raw" / "articles"
    if capture == "pdf-page-render":
        candidates = [base / f"{document_id}.pdf"]
    else:
        candidates = [
            base / f"{document_id}.png",
            base / f"{document_id}.jpg",
            base / f"{document_id}.jpeg",
            base / f"{document_id}.webp",
            base / f"{document_id}.pdf",
            base / f"{document_id}.html",
        ]
    existing = [path for path in candidates if path.is_file() and path.stat().st_size > 0]
    if len(existing) != 1:
        raise VisualSourceResolutionError(
            f"E_VISUAL_SOURCE_LOCATOR_MISSING: expected exactly one archive file for {document_id}; found={len(existing)}"
        )
    return existing[0]


def _render_pdf_page(source_pdf: Path, page_number: int, output: Path) -> tuple[int, int, str]:
    tool = shutil.which("pdftoppm")
    if tool is None:
        raise VisualSourceResolutionError(
            "E_VISUAL_SOURCE_FETCH_FAILED: pdftoppm is required for pdf-page-render"
        )
    with tempfile.TemporaryDirectory(prefix="nasdaq-cafe-pdf-") as temp_dir:
        prefix = Path(temp_dir) / "page"
        command = [
            tool,
            "-f",
            str(page_number),
            "-l",
            str(page_number),
            "-singlefile",
            "-png",
            "-r",
            "144",
            str(source_pdf),
            str(prefix),
        ]
        completed = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if completed.returncode != 0:
            raise VisualSourceResolutionError(
                "E_VISUAL_SOURCE_PDF_PAGE_INVALID: " + completed.stderr.strip()[:500]
            )
        rendered = prefix.with_suffix(".png")
        if not rendered.is_file():
            raise VisualSourceResolutionError("E_VISUAL_SOURCE_PDF_PAGE_INVALID: page output missing")
        return _normalize_image(rendered, output)


def _capture_webpage(
    *, url: str, capture_spec: dict[str, Any], output: Path
) -> tuple[str, int, int, str]:
    validate_external_url(url)
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise VisualSourceResolutionError(
            "E_VISUAL_SOURCE_FETCH_FAILED: playwright==1.61.0 is required for webpage capture"
        ) from exc

    viewport = capture_spec.get("viewport") or {"width": 1440, "height": 900}
    width = int(viewport.get("width", 1440))
    height = int(viewport.get("height", 900))
    selector = capture_spec.get("selector")
    with tempfile.TemporaryDirectory(prefix="nasdaq-cafe-web-capture-") as temp_dir:
        raw = Path(temp_dir) / "capture.png"
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={"width": width, "height": height},
                    reduced_motion="reduce",
                    color_scheme="dark",
                    locale="en-US",
                    user_agent="NasdaqCafeVisualSource/1.0 exact-locator capture",
                )

                def route_guard(route, request):
                    request_url = request.url
                    if request_url.startswith(("data:", "blob:", "about:")):
                        route.continue_()
                        return
                    try:
                        validate_external_url(request_url)
                    except VisualSourceResolutionError:
                        route.abort()
                        return
                    route.continue_()

                context.route("**/*", route_guard)
                page = context.new_page()
                response = page.goto(url, wait_until="domcontentloaded", timeout=25000)
                final_url = validate_external_url(page.url)
                if response is not None and response.status >= 400:
                    raise VisualSourceResolutionError(
                        f"E_VISUAL_SOURCE_FETCH_FAILED: HTTP {response.status}"
                    )
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except PlaywrightTimeoutError:
                    pass
                page.add_style_tag(
                    content="""
                    *, *::before, *::after {
                      animation-duration: 0s !important;
                      animation-delay: 0s !important;
                      transition-duration: 0s !important;
                      caret-color: transparent !important;
                    }
                    html { scroll-behavior: auto !important; }
                    """
                )
                page.wait_for_timeout(250)
                if isinstance(selector, str) and selector.strip():
                    selected = page.locator(selector).first
                    selected.wait_for(state="visible", timeout=5000)
                    selected.screenshot(path=str(raw), animations="disabled")
                else:
                    page.screenshot(
                        path=str(raw),
                        full_page=False,
                        animations="disabled",
                        caret="hide",
                    )
                browser.close()
        except VisualSourceResolutionError:
            raise
        except (PlaywrightTimeoutError, PlaywrightError, OSError) as exc:
            raise VisualSourceResolutionError(
                f"E_VISUAL_SOURCE_FETCH_FAILED: webpage capture failed: {exc}"
            ) from exc
        image_width, image_height, mime = _normalize_image(raw, output)
        return final_url, image_width, image_height, mime


def _wikimedia_exact(locator: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    url = locator.get("url")
    if isinstance(url, str) and url:
        return validate_external_url(url), {}
    page_id = locator.get("pageId")
    if not isinstance(page_id, str) or not page_id.strip():
        raise VisualSourceResolutionError("E_VISUAL_SOURCE_LOCATOR_MISSING: Wikimedia pageId/url")
    title = page_id.strip()
    if not title.startswith("File:"):
        title = f"File:{title}"
    query = urllib.parse.urlencode(
        {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "prop": "imageinfo",
            "iiprop": "url|mime|size|extmetadata",
            "titles": title,
        }
    )
    api_url = f"https://commons.wikimedia.org/w/api.php?{query}"
    _, payload = _json_exact(api_url)
    query_obj = payload.get("query")
    pages = query_obj.get("pages") if isinstance(query_obj, dict) else None
    if not isinstance(pages, list) or len(pages) != 1:
        raise VisualSourceResolutionError("E_VISUAL_SOURCE_FETCH_FAILED: Wikimedia page response invalid")
    page = pages[0]
    infos = page.get("imageinfo") if isinstance(page, dict) else None
    if not isinstance(infos, list) or len(infos) < 1 or not isinstance(infos[0], dict):
        raise VisualSourceResolutionError("E_VISUAL_SOURCE_FETCH_FAILED: Wikimedia imageinfo missing")
    info = infos[0]
    source_url = info.get("url")
    if not isinstance(source_url, str):
        raise VisualSourceResolutionError("E_VISUAL_SOURCE_FETCH_FAILED: Wikimedia image URL missing")
    metadata = info.get("extmetadata") if isinstance(info.get("extmetadata"), dict) else {}
    attribution = {}
    for key in ("Artist", "Credit", "LicenseShortName", "LicenseUrl", "UsageTerms"):
        value = metadata.get(key)
        if isinstance(value, dict) and isinstance(value.get("value"), str):
            attribution[key] = value["value"]
    return validate_external_url(source_url), attribution


def _resolve_candidate(
    *,
    repo_root: Path,
    collector_root: Path | None,
    episode_date: str,
    intent_id: str,
    path_name: str,
    candidate: dict[str, Any],
    asset_root: Path,
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    result: dict[str, Any] = {
        "intentId": intent_id,
        "path": path_name,
        "candidateId": candidate["candidateId"],
        "assetId": candidate["assetId"],
        "sourceKind": candidate["sourceKind"],
        "captureMethod": candidate["captureMethod"],
        "sourceLocator": candidate["sourceLocator"],
        "rightsStatus": candidate["rightsStatus"],
        "status": "technical-failure",
        "retrievedAt": now,
        "resolvedSource": None,
        "sourceSha256": None,
        "outputPath": None,
        "outputSha256": None,
        "mimeType": None,
        "width": None,
        "height": None,
        "attribution": {},
        "failureCode": None,
        "failureReason": None,
    }
    try:
        source_kind = candidate["sourceKind"]
        capture = candidate["captureMethod"]
        locator = candidate["sourceLocator"]
        output = asset_root / episode_date / f"{candidate['assetId']}.png"

        if source_kind == "existing-asset":
            result.update(
                status="ready",
                resolvedSource=f"renderer-registry:{candidate['assetId']}",
                mimeType="renderer-registry",
            )
            return result

        if capture in {"webpage-screenshot", "social-capture"} and source_kind in {
            "official-url",
            "web-page",
            "social-post",
        }:
            resolved_source, width, height, mime = _capture_webpage(
                url=locator["url"],
                capture_spec=candidate.get("captureSpec") or {},
                output=output,
            )
            result.update(
                status="ready",
                resolvedSource=resolved_source,
                outputPath=output.relative_to(repo_root).as_posix(),
                outputSha256=sha256_file(output),
                mimeType=mime,
                width=width,
                height=height,
            )
            return result

        if source_kind == "wikimedia" and capture == "mediawiki-fetch":
            source_url, attribution = _wikimedia_exact(locator)
            with tempfile.TemporaryDirectory(prefix="nasdaq-cafe-wikimedia-") as temp_dir:
                downloaded = Path(temp_dir) / "source-image"
                resolved_source, declared_type = download_exact(source_url, downloaded)
                if declared_type and not (
                    declared_type.startswith("image/") or declared_type == "application/octet-stream"
                ):
                    raise VisualSourceResolutionError(
                        f"E_VISUAL_SOURCE_MIME_INVALID: declared {declared_type}"
                    )
                result["sourceSha256"] = sha256_file(downloaded)
                width, height, mime = _normalize_image(downloaded, output)
            result.update(
                status="ready",
                resolvedSource=resolved_source,
                outputPath=output.relative_to(repo_root).as_posix(),
                outputSha256=sha256_file(output),
                mimeType=mime,
                width=width,
                height=height,
                attribution=attribution,
            )
            return result

        source_file: Path | None = None
        resolved_source: str | None = None
        declared_type: str | None = None
        temporary: tempfile.TemporaryDirectory[str] | None = None
        try:
            if source_kind == "generated-image":
                source_file = safe_relative_file(
                    repo_root, locator["localPath"], f"{intent_id}.{path_name}.localPath"
                )
                resolved_source = source_file.relative_to(repo_root).as_posix()
            elif source_kind == "collector-document":
                if collector_root is None:
                    raise VisualSourceResolutionError(
                        "E_VISUAL_SOURCE_LOCATOR_MISSING: collector root is not configured"
                    )
                source_file = _collector_document(
                    collector_root=collector_root,
                    episode_date=episode_date,
                    locator=locator,
                    capture=capture,
                )
                resolved_source = source_file.as_posix()
            elif source_kind == "official-url":
                temporary = tempfile.TemporaryDirectory(prefix="nasdaq-cafe-url-")
                parsed = urllib.parse.urlsplit(locator["url"])
                suffix = Path(parsed.path).suffix or ".bin"
                downloaded = Path(temporary.name) / f"source{suffix}"
                resolved_source, declared_type = download_exact(locator["url"], downloaded)
                source_file = downloaded
            else:
                raise VisualSourceResolutionError(
                    f"E_VISUAL_SOURCE_FETCH_FAILED: unsupported sourceKind/capture {source_kind}/{capture}"
                )

            if source_file is None:
                raise VisualSourceResolutionError("E_VISUAL_SOURCE_OUTPUT_INVALID: source file missing")
            result["sourceSha256"] = sha256_file(source_file)
            result["resolvedSource"] = resolved_source

            if capture == "pdf-page-render":
                capture_spec = candidate.get("captureSpec") or {}
                width, height, mime = _render_pdf_page(
                    source_file, int(capture_spec["pageNumber"]), output
                )
            elif capture in {"local-file-validation", "archive-file", "direct-download"}:
                if declared_type and not (
                    declared_type.startswith("image/") or declared_type == "application/octet-stream"
                ):
                    raise VisualSourceResolutionError(
                        f"E_VISUAL_SOURCE_MIME_INVALID: declared {declared_type}"
                    )
                width, height, mime = _normalize_image(source_file, output)
            else:
                raise VisualSourceResolutionError(
                    f"E_VISUAL_SOURCE_FETCH_FAILED: captureMethod {capture} is not implemented"
                )
            result.update(
                status="ready",
                outputPath=output.relative_to(repo_root).as_posix(),
                outputSha256=sha256_file(output),
                mimeType=mime,
                width=width,
                height=height,
            )
            return result
        finally:
            if temporary is not None:
                temporary.cleanup()
    except VisualSourceResolutionError as exc:
        message = str(exc)
        code = message.split(":", 1)[0] if message.startswith("E_") else "E_VISUAL_SOURCE_FETCH_FAILED"
        result["failureCode"] = code
        result["failureReason"] = message
        return result
    except Exception as exc:
        result["failureCode"] = "E_VISUAL_SOURCE_FETCH_FAILED"
        result["failureReason"] = str(exc)
        return result


def resolve_all(
    *,
    contract_path: Path,
    repo_root: Path,
    output_path: Path,
    asset_root: Path,
    collector_root: Path | None,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    asset_root = _ensure_output_root(repo_root, asset_root)
    contract = load_json(contract_path, "Final Episode Contract")
    visual_sources = contract.get("visualSources") or {"contractVersion": "1.0.0", "intents": []}
    if visual_sources.get("contractVersion") != "1.0.0":
        raise VisualSourceResolutionError("Visual Source contractVersion must be 1.0.0")
    results: list[dict[str, Any]] = []
    for intent in visual_sources["intents"]:
        for path_name in ("primary", "fallback"):
            results.append(
                _resolve_candidate(
                    repo_root=repo_root,
                    collector_root=collector_root.resolve() if collector_root else None,
                    episode_date=contract["episodeDate"],
                    intent_id=intent["intentId"],
                    path_name=path_name,
                    candidate=intent[path_name],
                    asset_root=asset_root,
                )
            )
    document = {
        "contractVersion": "1.0.0",
        "episodeDate": contract["episodeDate"],
        "finalEpisodeContractSha256": sha256_file(contract_path),
        "status": "resolved" if all(item["status"] == "ready" for item in results) else "partial",
        "results": results,
    }
    write_json_atomic(output_path, document)
    return document


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--asset-root", type=Path, default=Path("daily-assets"))
    parser.add_argument("--collector-root", type=Path)
    args = parser.parse_args(argv)
    try:
        result = resolve_all(
            contract_path=args.contract,
            repo_root=args.repo_root,
            output_path=args.output,
            asset_root=(args.repo_root / args.asset_root),
            collector_root=args.collector_root
            or (Path(os.environ["NASDAQ_CAFE_COLLECTOR_ROOT"]) if os.environ.get("NASDAQ_CAFE_COLLECTOR_ROOT") else None),
        )
        code = 0
    except (VisualSourceResolutionError, OSError, KeyError, json.JSONDecodeError) as exc:
        result = {"status": "fail", "errors": str(exc).splitlines()}
        code = 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
