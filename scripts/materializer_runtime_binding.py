#!/usr/bin/env python3
"""Resolve per-episode materializer runtime values without mutating source files."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
SHA256_RE = re.compile(r"[0-9a-f]{64}")


class MaterializerRuntimeBindingError(ValueError):
    """Raised when deterministic materializer runtime values cannot be resolved."""


@dataclass(frozen=True)
class MaterializerRuntimeBinding:
    episode_date: str
    market_date: str
    information_cutoff: str
    dossier_template_sha256: str

    @classmethod
    def from_workspace(cls, root: Path, episode_date: str) -> "MaterializerRuntimeBinding":
        if not DATE_RE.fullmatch(episode_date):
            raise MaterializerRuntimeBindingError(
                f"episode_date must be YYYY-MM-DD: {episode_date!r}"
            )
        authoring_path = root / "daily-authoring" / f"{episode_date}.json"
        try:
            authoring = json.loads(authoring_path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise MaterializerRuntimeBindingError(
                f"daily authoring missing: {authoring_path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise MaterializerRuntimeBindingError(
                f"daily authoring invalid JSON: {authoring_path}: {exc}"
            ) from exc
        if not isinstance(authoring, dict):
            raise MaterializerRuntimeBindingError(
                f"daily authoring root must be object: {authoring_path}"
            )

        market_date = authoring.get("marketDate")
        information_cutoff = authoring.get("informationCutoff")
        if not isinstance(market_date, str) or not DATE_RE.fullmatch(market_date):
            raise MaterializerRuntimeBindingError(
                f"daily authoring marketDate must be YYYY-MM-DD: {market_date!r}"
            )
        if not isinstance(information_cutoff, str) or not information_cutoff.strip():
            raise MaterializerRuntimeBindingError(
                "daily authoring informationCutoff must be a non-empty string"
            )

        dossier = (
            root
            / "research"
            / episode_date
            / "causal_research_dossier.template.json"
        )
        if not dossier.is_file():
            raise MaterializerRuntimeBindingError(
                f"causal dossier template missing: {dossier}"
            )
        dossier_sha = hashlib.sha256(dossier.read_bytes()).hexdigest()
        if not SHA256_RE.fullmatch(dossier_sha):
            raise MaterializerRuntimeBindingError(
                f"invalid dossier template SHA-256: {dossier_sha!r}"
            )

        return cls(
            episode_date=episode_date,
            market_date=market_date,
            information_cutoff=information_cutoff,
            dossier_template_sha256=dossier_sha,
        )

    def cli_args(self) -> list[str]:
        return [
            "--market-date",
            self.market_date,
            "--information-cutoff",
            self.information_cutoff,
            "--dossier-template-sha",
            self.dossier_template_sha256,
        ]
