from __future__ import annotations

import importlib

import pytest

resolve = importlib.import_module("resolve_visual_sources")
projection = importlib.import_module("visual_source_projection")


def test_private_and_local_urls_are_rejected() -> None:
    for url in (
        "http://127.0.0.1/x.png",
        "http://10.0.0.1/x.png",
        "http://169.254.169.254/latest/meta-data/",
        "http://localhost/x.png",
        "file:///etc/passwd",
    ):
        with pytest.raises(resolve.VisualSourceResolutionError):
            resolve.validate_external_url(url)


def test_visual_beat_aliases_are_deterministic() -> None:
    assert projection._beat_aliases("vb-02-01") == {
        "vb-02-01",
        "scene-02-beat-001",
    }
    assert projection._beat_aliases("scene-05-beat-002") == {
        "scene-05-beat-002",
        "vb-05-02",
    }


def test_wikimedia_page_id_uses_exact_page_without_search(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: list[str] = []

    def fake_json_exact(url: str):
        observed.append(url)
        return (
            url,
            {
                "query": {
                    "pages": [
                        {
                            "title": "File:Example.png",
                            "imageinfo": [
                                {
                                    "url": "https://upload.wikimedia.org/example.png",
                                    "extmetadata": {
                                        "Artist": {"value": "Example Author"},
                                        "LicenseShortName": {"value": "CC BY 4.0"},
                                        "LicenseUrl": {"value": "https://creativecommons.org/licenses/by/4.0/"},
                                    },
                                }
                            ],
                        }
                    ]
                }
            },
        )

    monkeypatch.setattr(resolve, "_json_exact", fake_json_exact)
    monkeypatch.setattr(resolve, "validate_external_url", lambda value: value)
    source_url, attribution = resolve._wikimedia_exact({"pageId": "Example.png"})
    assert source_url == "https://upload.wikimedia.org/example.png"
    assert attribution["Artist"] == "Example Author"
    assert attribution["LicenseShortName"] == "CC BY 4.0"
    assert len(observed) == 1
    assert "titles=File%3AExample.png" in observed[0]
    assert "search" not in observed[0].lower()
