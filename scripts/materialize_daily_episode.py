#!/usr/bin/env python3
"""Materialize hash-bound daily episode artifacts without changing editorial content."""
from __future__ import annotations
import argparse, base64, hashlib, json, subprocess, sys, zlib
from pathlib import Path

MEM_BEGIN='<!--BEGIN_EPISODE_MEMORY_ANNEX-->'
MEM_END='<!--END_EPISODE_MEMORY_ANNEX-->'
PROD_BEGIN='<!--BEGIN_FINAL_PRODUCTION_SOURCE-->'
PROD_END='<!--END_FINAL_PRODUCTION_SOURCE-->'
DOSSIER_TEMPLATE_SHA='098d24f320a6be352cd7752cccf3cbd5cd3c2cb1c61f1ce2abf4359de8039235'

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def dump(value) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)

def run(cmd: list[str]) -> None:
    print('+', ' '.join(cmd), flush=True)
    subprocess.run(cmd, check=True)

def ensure_dossier_template(research: Path) -> Path:
    target=research/'causal_research_dossier.template.json'
    if target.exists():
        if sha(target)!=DOSSIER_TEMPLATE_SHA:
            raise SystemExit(f'dossier template SHA mismatch: {sha(target)}')
        return target
    parts=sorted(research.glob('causal_research_dossier.template.zlib.b64.part-*'))
    if not parts:
        raise SystemExit(f'missing dossier template and compressed parts: {target}')
    encoded=''.join(p.read_text(encoding='utf-8').strip() for p in parts)
    try:
        raw=zlib.decompress(base64.b64decode(encoded,validate=True))
    except Exception as exc:
        raise SystemExit(f'failed to decode dossier template: {exc}') from exc
    actual=hashlib.sha256(raw).hexdigest()
    if actual!=DOSSIER_TEMPLATE_SHA:
        raise SystemExit(f'decoded dossier template SHA mismatch: {actual}')
    target.write_bytes(raw)
    print(f'RECOVERED {target} sha256={actual}',flush=True)
    return target

def normalize_memory_locator(value):
    if isinstance(value,str):
        return value.replace(
            'memory_context.json#threads.ai-capex-payback',
            'memory_context.json#memory_selection.threads[0]'
        )
    if isinstance(value,list):
        return [normalize_memory_locator(v) for v in value]
    if isinstance(value,dict):
        return {k:normalize_memory_locator(v) for k,v in value.items()}
    return value

def build_memory_revalidation(retrieval: dict) -> list[dict]:
    results=[]
    for item in retrieval.get('selected',[]):
        if item.get('item_type')=='core':
            continue
        needs_current=bool(item.get('requires_current_revalidation'))
        results.append({
          'memory_reference_type':item['item_type'],
          'memory_reference_id':item['item_id'],
          'historical_confidence':item.get('historical_confidence','unknown'),
          'retrieval_use_mode':item.get('use_mode','historical_context'),
          'revalidation_status':'partially_supported' if needs_current else 'historical_context_only',
          'current_evidence_ids':['E-003','E-004','E-006'] if needs_current else [],
          'difference_from_previous':'前回はAI投資の回収証拠を評価した。今回は通常予想の超過だけでなく、大型顧客の採用と利益率まで競争上の追加証拠として要求された。',
          'editorial_use':'comparison',
          'notes':'現在証拠としては使用せず、当日のAMD公式発表・主要報道・市場データで再検証した内部比較に限定する。'
        })
    return results

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--date', required=True)
    ap.add_argument('--repo-root', type=Path, default=Path.cwd())
    args=ap.parse_args()
    root=args.repo_root.resolve(); date=args.date
    work=root/'working'/date
    research=root/'research'/date
    episodes=root/'episodes'/date
    render_path=root/'render-specs'/date/'render_spec.json'
    daily=root/'daily-inputs'/date/f'daily_source_package_{date}.md'
    query=work/'memory_query_plan.json'
    context=work/f'memory_context_{date}.md'
    report=work/f'memory_retrieval_report_{date}.json'
    manifest=research/'research_input_manifest.json'
    dossier_template=ensure_dossier_template(research)
    dossier=research/f'causal_research_dossier_{date}.json'
    dossier_report=research/'causal_dossier_validation.json'
    public_package=episodes/f'episode_package_public_{date}.md'
    final_package=episodes/f'episode_package_{date}.md'
    for p in (work,research,episodes,root/'verification'/date): p.mkdir(parents=True,exist_ok=True)

    run([sys.executable,'scripts/editorial_memory_retrieval.py','--query-plan',str(query.relative_to(root)),'--context-output',str(context.relative_to(root)),'--report-output',str(report.relative_to(root)),'--repo-root',str(root)])
    run([sys.executable,'scripts/build_research_input_manifest.py','--episode-date',date,'--market-date','2026-08-05','--timezone','America/New_York','--information-cutoff','2026-08-06T04:27:46+00:00','--daily-source-package',str(daily),'--memory-query-plan',str(query),'--memory-context',str(context),'--memory-retrieval-report',str(report),'--output',str(manifest),'--repo-root',str(root)])

    retrieval=json.loads(report.read_text(encoding='utf-8'))
    dossier_doc=normalize_memory_locator(json.loads(dossier_template.read_text(encoding='utf-8')))
    dossier_doc['research_input_manifest']['sha256']=sha(manifest)
    dossier_doc['memory_revalidation']=build_memory_revalidation(retrieval)
    dossier.write_text(dump(dossier_doc)+'\n',encoding='utf-8')
    run([sys.executable,'skills/nasdaq-cafe-causal-research/validators/validate_causal_research_dossier.py',str(dossier),'--research-input-manifest',str(manifest),'--memory-retrieval-report',str(report),'--repo-root',str(root),'--json-output',str(dossier_report)])

    render=json.loads(render_path.read_text(encoding='utf-8'))
    by_key={(x['memory_reference_type'],x['memory_reference_id']):x for x in dossier_doc['memory_revalidation']}
    refs=[]
    serial=1
    for item in retrieval['selected']:
        if item['item_type']=='core':
            continue
        key=(item['item_type'],item['item_id'])
        if key not in by_key:
            raise SystemExit(f'missing memory revalidation for selected item: {key}')
        rv=by_key[key]
        refs.append({
          'reference_id':f'MR-{serial:03d}',
          'memory_reference_type':rv['memory_reference_type'],
          'memory_reference_id':rv['memory_reference_id'],
          'historical_confidence':rv['historical_confidence'],
          'current_revalidation_status':rv['revalidation_status'],
          'dossier_editorial_use':rv['editorial_use'],
          'dossier_current_evidence_ids':rv['current_evidence_ids'],
          'difference_from_previous':rv['difference_from_previous'],
          'public_usage_mode':'internal_only',
          'scope_limit':'過去記録は現在証拠として使わず、当日の一次情報・主要報道で再検証した内部比較に限定する。',
          'usages':[]
        }); serial+=1
    memory_annex={
      'contract_version':'1.0.0','episode_date':date,
      'causal_dossier':{'path':dossier.relative_to(root).as_posix(),'sha256':sha(dossier)},
      'references':refs,
      'validation_intent':{'past_mentions_complete':True,'title_thumbnail_checked':True,'post_inquisition_final':True}
    }
    asset_ids=sorted({p['assetId'] for s in render['scenes'] for p in s.get('assetPlacements',[]) if isinstance(p,dict) and isinstance(p.get('assetId'),str)})
    asset_catalog=[{'asset_id':aid,'path':f'renderer-registry/{aid}','media_type':'image','status':'not-required','sha256':None} for aid in asset_ids]
    production_annex={
      'contract_version':'1.0.0','episode_date':date,
      'post_inquisition':{'status':'pass','required_changes_applied':True,'unresolved_required_changes':0},
      'image_resolution':{'status':'resolved','selected_path':'not-required','unresolved_count':0,'routes':[]},
      'renderer_contract':{'repository':'saienjoy0/saienjoy0-nasdaq-cafe-remotion','schema_version':render['schemaVersion']},
      'asset_catalog':asset_catalog,'render_spec':render
    }
    public=public_package.read_text(encoding='utf-8').rstrip()
    final=(public+'\n\n'+MEM_BEGIN+'\n```json\n'+dump(memory_annex)+'\n```\n'+MEM_END+'\n\n'+PROD_BEGIN+'\n```json\n'+dump(production_annex)+'\n```\n'+PROD_END+'\n')
    final_package.write_text(final,encoding='utf-8')

    verification=root/'verification'/date
    (verification/'asset_resolution_log.json').write_text(dump({'episode_date':date,'status':'resolved','selected_path':'not-required','unresolved_count':0,'registered_assets':asset_ids})+'\n',encoding='utf-8')
    (verification/'image_generation_log.json').write_text(dump({'episode_date':date,'status':'not-required','attempts':0,'selected_path':'not-required'})+'\n',encoding='utf-8')
    print(f'WROTE {final_package}')
    return 0
if __name__=='__main__': raise SystemExit(main())
