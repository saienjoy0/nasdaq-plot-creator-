#!/usr/bin/env python3
from __future__ import annotations

import copy

import visual_intelligence_terminal_projection as terminal


def fixture() -> dict:
    return {
        "scenes": [
            {
                "sceneId": f"scene-{index:02d}",
                "transition": {"type": "fade", "durationMs": 220 + index},
                "visualBeats": [{"beatId": f"scene-{index:02d}-beat-001"}],
            }
            for index in range(1, 10)
        ]
    }


def main() -> None:
    source = fixture()
    before = copy.deepcopy(source)
    projected = terminal.normalize_terminal_transition(source)

    assert source == before, "terminal projection must never mutate producer input"
    assert projected["scenes"][:-1] == before["scenes"][:-1], (
        "only Scene 9 terminal transition may be normalized"
    )
    assert projected["scenes"][-1]["transition"] == {
        "type": "none",
        "durationMs": 0,
    }
    assert projected["scenes"][-1]["visualBeats"] == before["scenes"][-1]["visualBeats"]

    invalid = fixture()
    invalid["scenes"].pop()
    try:
        terminal.normalize_terminal_transition(invalid)
    except terminal.VisualIntelligenceTerminalProjectionError as exc:
        assert "E_VISUAL_TERMINAL_PROJECTION_SCENE_COUNT" in str(exc)
    else:
        raise AssertionError("non-nine-Scene input must fail closed")

    print("visual intelligence terminal transition projection tests passed")


if __name__ == "__main__":
    main()
