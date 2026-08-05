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

scenes = []
markdown = ["# Episode Package 2026-07-31", "", "04審問反映後の最終版。", ""]
for number in range(1, 10):
    scene_id = f"scene-{number:02d}"
    beat_ids = [f"vb-{number:02d}-01"]
    if number == 4:
        beat_ids.append("vb-04-02")
    beats = []
    markdown.append(f"## Scene {number}")
    for beat_id in beat_ids:
        markdown.append(f"<!--VISUAL_BEAT:{scene_id}:{beat_id}-->")
        markdown.append(f"### Visual Beat {beat_id}")
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
            }
        else:
            beat = {
                "visualBeatId": beat_id,
                "headline": f"Scene {number} headline",
                "screenQuestion": f"Scene {number} question",
                "startCue": f"Scene {number} start",
                "endCue": f"Scene {number} end",
                "returnTarget": f"Scene {number} return",
                "fallbackHeadline": f"Scene {number} fallback headline",
                "fallbackQuestion": f"Scene {number} fallback question",
            }
        beats.append(beat)
        markdown.append(beat["headline"])
        markdown.append("")
    scenes.append({"sceneId": scene_id, "visualBeats": beats})

markdown.extend([
    "## Financial Visual Usage Annex",
    "",
    "<!--BEGIN_FINANCIAL_VISUAL_ANNEX-->",
    "```json",
    json.dumps(financial, ensure_ascii=False, indent=2),
    "```",
    "<!--END_FINANCIAL_VISUAL_ANNEX-->",
    "",
])
package_text = "\n".join(markdown)
package_rel = "tests/final-episode-contract/fixtures/episode_package_2026-07-31.md"
package_path = ROOT / package_rel
package_path.write_text(package_text, encoding="utf-8")
sha = hashlib.sha256(package_path.read_bytes()).hexdigest()

contract = {
    "contractVersion": "1.0.0",
    "episodeDate": "2026-07-31",
    "episodePackage": {"path": package_rel, "sha256": sha},
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
print(sha)
