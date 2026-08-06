from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FIX = Path(__file__).resolve().parent / "fixtures"
FIX.mkdir(parents=True, exist_ok=True)

metrics = [
    {
        "metricId": "aws-expected",
        "label": "AWS revenue expected",
        "role": "expected",
        "valueText": "$42.3B",
        "numericValue": 42.3,
        "unit": "billion",
        "currency": "USD",
        "period": "2026 Q2",
        "entityId": "amazon-aws",
        "sessionDate": None,
        "sourceIds": ["source-001"],
    },
    {
        "metricId": "aws-actual",
        "label": "AWS revenue actual",
        "role": "actual",
        "valueText": "$43.0B",
        "numericValue": 43.0,
        "unit": "billion",
        "currency": "USD",
        "period": "2026 Q2",
        "entityId": "amazon-aws",
        "sessionDate": None,
        "sourceIds": ["source-001"],
    },
    {
        "metricId": "aws-gap",
        "label": "AWS revenue gap",
        "role": "gap",
        "valueText": "+$0.7B",
        "numericValue": 0.7,
        "unit": "billion",
        "currency": "USD",
        "period": "2026 Q2",
        "entityId": "amazon-aws",
        "sessionDate": None,
        "sourceIds": ["source-001"],
    },
]

preferred = {
    "planVersion": "1.0.0",
    "planId": "fvp-aws-gap-preferred",
    "intentId": "fvi-aws-expectation-gap",
    "path": "preferred",
    "recipeId": "earnings-surprise",
    "visualTemplateId": "earnings-surprise",
    "templateVariant": "zero-baseline",
    "sceneId": "scene-04",
    "visualBeatId": "vb-04-02",
    "screenState": "Chart",
    "metricIds": ["aws-expected", "aws-actual", "aws-gap"],
    "causalStepIds": [],
    "displayOrder": ["aws-expected", "aws-actual", "aws-gap"],
    "comparisonBasis": "AWS revenue, same quarter and currency",
    "highlightObjectIds": ["aws-gap"],
    "headlineRef": "episode://scene-04/vb-04-02/headline",
    "screenQuestionRef": "episode://scene-04/vb-04-02/screenQuestion",
    "startCueRef": "episode://scene-04/vb-04-02/startCue",
    "endCueRef": "episode://scene-04/vb-04-02/endCue",
    "returnTargetRef": "episode://scene-04/vb-04-02/returnTarget",
    "sourceIds": ["source-001"],
}

fallback = {
    "planVersion": "1.0.0",
    "planId": "fvp-aws-gap-fallback",
    "intentId": "fvi-aws-expectation-gap",
    "path": "fallback",
    "recipeId": "expected-anchor",
    "visualTemplateId": "expected-actual-bullet",
    "templateVariant": "zero-baseline",
    "sceneId": "scene-04",
    "visualBeatId": "vb-04-02",
    "screenState": "Chart",
    "metricIds": ["aws-expected", "aws-actual"],
    "causalStepIds": [],
    "displayOrder": ["aws-expected", "aws-actual"],
    "comparisonBasis": "AWS revenue, same quarter and currency",
    "highlightObjectIds": ["aws-actual"],
    "headlineRef": "episode://scene-04/vb-04-02/fallbackHeadline",
    "screenQuestionRef": "episode://scene-04/vb-04-02/fallbackQuestion",
    "startCueRef": "episode://scene-04/vb-04-02/startCue",
    "endCueRef": "episode://scene-04/vb-04-02/endCue",
    "returnTargetRef": "episode://scene-04/vb-04-02/returnTarget",
    "sourceIds": ["source-001"],
}

intent = {
    "intentContractVersion": "1.1.0",
    "intentId": "fvi-aws-expectation-gap",
    "kind": "expectation-gap",
    "target": {"sceneId": "scene-04", "visualBeatId": "vb-04-02"},
    "metrics": metrics,
    "causalSteps": [],
    "sourceIds": ["source-001"],
    "dataPrecision": "derived-difference",
    "chartPolicy": "no-series",
    "preferredPlanId": preferred["planId"],
    "fallbackPlanId": fallback["planId"],
    "status": "approved",
    "editorialNote": "Expected, Actual, and Gap were confirmed by the editor before compilation.",
    "selectionState": {
        "compilerSelection": "not-run",
        "selectedPlanId": None,
        "selectedRecipeId": None,
        "selectedVisualTemplateId": None,
        "compilerReasonCodes": [],
        "fallbackDiversityRecheck": "not-run",
    },
}
financial = {
    "annexVersion": "1.0.0",
    "intents": [intent],
    "candidatePlans": [preferred, fallback],
}

scene_grammars = {
    1: [("contradiction", "major-shift")],
    2: [("entity", "major-shift"), ("comparison", "continuation")],
    3: [("evidence", "major-shift")],
    4: [("gap", "major-shift"), ("analogy", "return")],
    5: [("causal", "major-shift")],
    6: [("reaction", "major-shift"), ("evidence", "continuation")],
    7: [("comparison", "major-shift")],
    8: [("verification", "major-shift")],
    9: [("assembly", "closing")],
}

scenes = []
sidecar_scenes = []
markdown = ["# Episode Package 2026-07-31", "", "04審問反映後の最終版。", ""]
for number in range(1, 10):
    scene_id = f"scene-{number:02d}"
    beats = []
    sidecar_beats = []
    markdown.append(f"## Scene {number}")
    for index, (grammar_id, transition_role) in enumerate(
        scene_grammars[number], start=1
    ):
        beat_id = f"vb-{number:02d}-{index:02d}"
        return_target = "vb-04-01" if transition_role == "return" else None
        visual_grammar = {
            "contractVersion": "1.0.0",
            "grammarId": grammar_id,
            "transitionRole": transition_role,
            "returnTargetBeatId": return_target,
        }
        if beat_id == "vb-04-02":
            beat = {
                "visualBeatId": beat_id,
                "headline": "AWSは予想を上回った",
                "screenQuestion": "それでも市場が見た差は何か",
                "startCue": "Expectedを説明し始める",
                "endCue": "Gapの意味を言い切る",
                "returnTarget": "狐の通常画面へ戻る",
                "fallbackHeadline": "AWSの予想と実績",
                "fallbackQuestion": "確認できた二つの数字は何か",
                "visualGrammar": visual_grammar,
            }
        else:
            beat = {
                "visualBeatId": beat_id,
                "headline": f"Scene {number} headline {index}",
                "screenQuestion": f"Scene {number} question {index}",
                "startCue": f"Scene {number} start {index}",
                "endCue": f"Scene {number} end {index}",
                "returnTarget": f"Scene {number} return {index}",
                "fallbackHeadline": f"Scene {number} fallback headline {index}",
                "fallbackQuestion": f"Scene {number} fallback question {index}",
                "visualGrammar": visual_grammar,
            }
        beats.append(beat)
        sidecar_beats.append(
            {"visualBeatId": beat_id, "visualGrammar": visual_grammar}
        )
        markdown.extend(
            [
                f"<!--VISUAL_BEAT:{scene_id}:{beat_id}-->",
                f"### Visual Beat {beat_id}",
                beat["headline"],
                "",
            ]
        )
    scenes.append({"sceneId": scene_id, "visualBeats": beats})
    sidecar_scenes.append({"sceneId": scene_id, "visualBeats": sidecar_beats})

sidecar = {
    "episodeDate": "2026-07-31",
    "visualGrammarContractVersion": "1.0.0",
    "expectedConfirmed": True,
    "scene5CausalExceptionReason": None,
    "scenes": sidecar_scenes,
}

markdown.extend(
    [
        "## Visual Grammar Annex",
        "",
        "<!--BEGIN_VISUAL_GRAMMAR_ANNEX-->",
        "```json",
        json.dumps(sidecar, ensure_ascii=False, indent=2),
        "```",
        "<!--END_VISUAL_GRAMMAR_ANNEX-->",
        "",
        "## Financial Visual Usage Annex",
        "",
        "<!--BEGIN_FINANCIAL_VISUAL_ANNEX-->",
        "```json",
        json.dumps(financial, ensure_ascii=False, indent=2),
        "```",
        "<!--END_FINANCIAL_VISUAL_ANNEX-->",
        "",
    ]
)

package_rel = "tests/final-episode-contract/fixtures/episode_package_2026-07-31.md"
package_path = ROOT / package_rel
package_path.parent.mkdir(parents=True, exist_ok=True)
package_path.write_text("\n".join(markdown), encoding="utf-8")
package_sha = hashlib.sha256(package_path.read_bytes()).hexdigest()

sidecar_rel = "tests/final-episode-contract/fixtures/visual_grammar_sidecar.valid.json"
sidecar_path = ROOT / sidecar_rel
sidecar_path.write_text(
    json.dumps(sidecar, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
sidecar_sha = hashlib.sha256(sidecar_path.read_bytes()).hexdigest()

contract = {
    "contractVersion": "1.1.0",
    "episodeDate": "2026-07-31",
    "episodePackage": {"path": package_rel, "sha256": package_sha},
    "visualGrammarSidecar": {"path": sidecar_rel, "sha256": sidecar_sha},
    "visualGrammarContractVersion": "1.0.0",
    "expectedConfirmed": True,
    "scene5CausalExceptionReason": None,
    "review": {
        "verdict": "approved-with-changes",
        "postInquisitionFinal": True,
        "approvedForProduction": True,
    },
    "sourceRegistry": [
        {
            "sourceId": "source-001",
            "title": "Amazon Q2 2026 results",
            "publisher": "Amazon",
            "sourceType": "company",
        }
    ],
    "scenes": scenes,
    "financialVisuals": financial,
}
(FIX / "final_episode_contract.valid.json").write_text(
    json.dumps(contract, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(package_sha)
