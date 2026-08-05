#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).with_name("apply-fvu-r3-renderer-compatibility.py")
text = path.read_text(encoding="utf-8")
old = '''    if '\"compatibility_matrix_sha256\": compatibility_matrix_sha' not in text:
        anchor = ''' + "'''" + '''        \"fallback_diversity\": diversity_status,
        \"unresolved_states\": 0,
    }
''' + "'''" + '''
        replacement = ''' + "'''" + '''        \"fallback_diversity\": diversity_status,
        \"compatibility_matrix_id\": compatibility_matrix[\"matrixId\"],
        \"compatibility_matrix_sha256\": compatibility_matrix_sha,
        \"unresolved_states\": 0,
    }
''' + "'''" + '''
        text = replace_once(text, anchor, replacement, \"production consistency compatibility binding\")
'''
new = '''    if '\"compatibility_matrix_sha256\": compatibility_matrix_sha' not in text:
        anchor = ''' + "'''" + '''    consistency[\"financial_visuals\"] = {
        \"status\": \"pass\",
        \"final_episode_contract_sha256\": sha256_file(final_contract_path),
        \"financial_recipe_plan_sha256\": recipe_plan_sha,
        \"render_spec_sha256\": render_sha,
        \"selection_count\": len(traces),
        \"fallback_count\": sum(trace[\"selectedPath\"] == \"fallback\" for trace in traces),
        \"fallback_diversity\": diversity_status,
        \"unresolved_states\": 0,
    }
''' + "'''" + '''
        replacement = ''' + "'''" + '''    consistency[\"financial_visuals\"] = {
        \"status\": \"pass\",
        \"final_episode_contract_sha256\": sha256_file(final_contract_path),
        \"financial_recipe_plan_sha256\": recipe_plan_sha,
        \"render_spec_sha256\": render_sha,
        \"selection_count\": len(traces),
        \"fallback_count\": sum(trace[\"selectedPath\"] == \"fallback\" for trace in traces),
        \"fallback_diversity\": diversity_status,
        \"compatibility_matrix_id\": compatibility_matrix[\"matrixId\"],
        \"compatibility_matrix_sha256\": compatibility_matrix_sha,
        \"unresolved_states\": 0,
    }
''' + "'''" + '''
        text = replace_once(text, anchor, replacement, \"production consistency compatibility binding\")
'''
if old not in text:
    raise SystemExit("temporary bootstrap anchor block not found")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("fixed temporary R3 bootstrap anchor")
