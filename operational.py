"""Merestone 0.3: offline planning and verification; does not execute attacks or use the network."""
from __future__ import annotations
import argparse, copy, hashlib, json, sys, uuid
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
import jsonutil
from jsonutil import validate

ROOT=Path(__file__).resolve().parent
VERSION='0.3.0'
ACTIVITIES=('DESIGN','CONFIG','TEST','REDTEAM')
def digest(v):return hashlib.sha256(jsonutil.canonical(v)).hexdigest()
def read(p):return jsonutil.read_json(p)
def write(p,v):
    p=Path(p)
    if p.exists():raise ValueError('Existing file; preserve history: '+str(p))
    jsonutil.write_json(p,v)
def now():return datetime.now(timezone.utc).isoformat()
def nonempty(v,label):
    if not isinstance(v,str) or not v.strip():raise ValueError('Missing '+label)
def unique(rows,key,label):
    ids=[r[key] for r in rows]
    if len(ids)!=len(set(ids)):raise ValueError(label+' duplicate')
def timestamp(value):
    nonempty(value,'ISO date');d=datetime.fromisoformat(value.replace('Z','+00:00'))
    if d.tzinfo is None:raise ValueError('Date without time zone')
    return d

def library():
    names=('cases','controls','techniques','examples','scenarios')
    data={n:read(ROOT/'catalog'/n/'index.json') for n in names}
    data['capabilities']=read(ROOT/'catalog/capabilities.json')['capabilities']
    for name in names:unique(data[name],'id',name)
    ids={n:{x['id'] for x in data[n]} for n in names}
    for c in data['cases']:
        for k,n in [('control_ids','controls'),('technique_ids','techniques'),('example_ids','examples')]:
            if set(c[k])-ids[n]:raise ValueError(c['id']+': unknown reference '+k)
        if c['activity'] not in ACTIVITIES:raise ValueError('Invalid activity')
        if not c['procedure'] or not all(c['success_criteria'].values()):raise ValueError('Case without procedure/oracle')
        for clause in c['applies_if']:
            if set(clause)-set(data['capabilities']):raise ValueError('Unknown capability')
    for name in names:
        contract=ROOT/'schemas'/(name+'-v3.schema.json')
        if contract.exists():validate(data[name],read(contract))
    for e in data['examples']:
        if set(e['technique_ids'])-ids['techniques']:raise ValueError('Example with unknown technique')
    for t in data['techniques']+data['cases']:
        if set(t.get('related_cases',[]))-ids['cases']:raise ValueError('Technique with unknown case')
    for s in data['scenarios']:
        if set(s['case_ids'])-ids['cases']:raise ValueError('Scenario with unknown case')
    data['sha256']=digest({n:data[n] for n in names+('capabilities',)})
    return data

def applies(rule,caps):
    """OR of AND predicates; missing capability remains UNKNOWN."""
    uncertain=False
    for clause in rule:
        values=[caps.get(k,'unknown') for k in clause]
        if all(v=='present' for v in values):return 'APPLICABLE'
        if 'absent' not in values:uncertain=True
    return 'UNKNOWN' if uncertain else 'NOT_APPLICABLE'

def validate_architecture(a,lib=None):
    lib=lib or library();validate(a,read(ROOT/'schemas/architecture-v3.schema.json'))
    unique(a['assets'],'id','Asset');unique(a['routes'],'id','Route');unique(a['threats'],'id','Threat')
    assets={x['id'] for x in a['assets']};threats={x['id'] for x in a['threats']}
    for r in a['routes']:
        if r['asset_id'] not in assets or set(r['threat_ids'])-threats:raise ValueError('Route with unknown asset/threat')
        if set(r['capabilities'])-set(lib['capabilities']):raise ValueError('Unknown capability; register the extension in the catalog')
        if any(v not in ('present','absent','unknown') for v in r['capabilities'].values()):raise ValueError('Invalid capability state')
        if len(set(r['activity_types']))!=len(r['activity_types']):raise ValueError('Duplicate activity type')
        unique(r.get('test_protocols',[]),'case_id','Protocol')
        for protocol in r.get('test_protocols',[]):
            if protocol['case_id'] not in {c['id'] for c in lib['cases']+lib['scenarios']}:raise ValueError('Protocol with unknown case')
    return a

def profile(name):return read(ROOT/'templates/architectures'/f'{name}.json')
def task_spec(c,r):
    key=[c['id'],r['asset_id'],r['id'],r['actor'],c['activity']]
    protocol=next((x for x in r.get('test_protocols',[]) if x['case_id']==c['id']),None)
    return {'task_id':'TASK-'+digest(key)[:16],'case_id':c['id'],'case_revision':c['revision'],
      'title':c['title'],'module':c['module'],'activity':c['activity'],'asset_id':r['asset_id'],
      'route_id':r['id'],'boundary':r['boundary'],'actor':r['actor'],'threat_ids':r['threat_ids'],
      'control_ids':c['control_ids'],'technique_ids':c['technique_ids'],'example_ids':c['example_ids'],
      'applicability':applies(c['applies_if'],r['capabilities']),
      'scope':r['scope'],'access':r['access'],'test_protocol':protocol}
def expected_tasks(a,lib):
    specs=[]
    for r in a['routes']:
        for c in lib['cases']:
            if c['activity'] in r['activity_types']:specs.append(task_spec(c,r))
        if 'REDTEAM' in r['activity_types']:
            for sc in lib['scenarios']:
                c=dict(sc,module='SCENARIOS',control_ids=sorted({ctl for x in lib['cases'] if x['id'] in sc['case_ids'] for ctl in x['control_ids']}),technique_ids=[],example_ids=[])
                specs.append(task_spec(c,r))
    return specs
def make_plan(architecture):
    lib=library();a=validate_architecture(copy.deepcopy(architecture),lib);specs=expected_tasks(a,lib)
    plan={'schema_version':'3.0','framework_version':VERSION,'plan_id':str(uuid.uuid4()),'created_at':now(),
      'catalog_sha256':lib['sha256'],'architecture':a,'architecture_sha256':digest(a),
      'obligations_sha256':digest(specs),'amendments':[],'evidence':[],'tasks':[]}
    for spec in specs:plan['tasks'].append(dict(spec,execution='NOT_RUN',result='',rationale='',observations='',reviewer='',evidence_ids=[],trials=[],cleanup_confirmed=False,exclusion=None))
    return plan
def manifest(plan):return {k:plan[k] for k in ('schema_version','plan_id','catalog_sha256','architecture_sha256','obligations_sha256')}
def verified_file(entry,root):
    rel=Path(entry['path'])
    if rel.is_absolute() or '..' in rel.parts or ':' in str(rel):raise ValueError('Evidence path must be relative to the store')
    base=Path(root).resolve();p=(base/rel).resolve()
    if not p.is_relative_to(base) or not p.is_file():raise ValueError('Evidence missing or outside the store: '+entry['id'])
    data=p.read_bytes()
    if len(data)!=entry['bytes'] or hashlib.sha256(data).hexdigest()!=entry['sha256']:raise ValueError('Invalid evidence hash/size: '+entry['id'])
def ready(a):
    errors=[]
    for k in ('authorization_ref','snapshot_ref','evidence_store'):
        if not a[k].strip():errors.append(k)
    for k in ('reviewer','reviewed_at','evidence_ref'):
        if not a['inventory_review'][k].strip():errors.append('inventory_review.'+k)
    if a['inventory_review']['reviewed_at']:timestamp(a['inventory_review']['reviewed_at'])
    if not a['stop_conditions']:errors.append('stop_conditions')
    # The common core (CORE-001…008) is only generated on routes with DESIGN; without any, the assessment cannot close green.
    if not any('DESIGN' in r['activity_types'] for r in a['routes']):errors.append('core_design_missing')
    # Zero tokens/cost is a valid prohibition for offline ML or documentary reviews.
    if any(a['limits'][k]<=0 for k in ('requests','duration_seconds','concurrency')):errors.append('limits')
    for r in a['routes']:
        for k,v in r['capabilities'].items():
            if v!='unknown' and not r['capability_evidence'].get(k,'').strip():errors.append(r['id']+':evidence:'+k)
    return errors

def check_plan(plan,approved_manifest=None,evidence_root=None):
    lib=library();validate(plan,read(ROOT/'schemas/plan-v3.schema.json'))
    if plan['catalog_sha256']!=lib['sha256']:raise ValueError('Different catalog snapshot; keep the original or migrate explicitly')
    a=validate_architecture(plan['architecture'],lib)
    if digest(a)!=plan['architecture_sha256']:raise ValueError('Architecture modified without migration')
    expected=expected_tasks(a,lib)
    if digest(expected)!=plan['obligations_sha256']:raise ValueError('Obligations do not match the selection')
    if approved_manifest is not None and manifest(plan)!=approved_manifest:raise ValueError('The plan differs from the approved external manifest')
    unique(plan['tasks'],'task_id','Task');unique(plan['evidence'],'id','Evidence')
    lookup={s['task_id']:s for s in expected}
    if set(lookup)!={t['task_id'] for t in plan['tasks']}:raise ValueError('Tasks deleted or added outside the frozen plan')
    ev={x['id']:x for x in plan['evidence']}
    for x in ev.values():
        timestamp(x['collected_at'])
        if evidence_root is not None:verified_file(x,evidence_root)
    seen_trials=set();unresolved=[];counts=Counter();coverage=defaultdict(Counter);decided=0;excluded=0;failures=0
    example_ids={e['id'] for e in lib['examples']}
    technique_ids={t['id'] for t in lib['techniques']}
    for task in plan['tasks']:
        for k,v in lookup[task['task_id']].items():
            if task.get(k)!=v:raise ValueError('Frozen field modified: '+task['task_id']+':'+k)
        state=task['execution'];result=task['result'];app=task['applicability']
        if set(task['evidence_ids'])-ev.keys():raise ValueError('Unregistered evidence reference')
        if task['exclusion'] is not None:
            ex=task['exclusion']
            for k in ('reason','approver','approved_at','expires_at','residual_risk'):nonempty(ex.get(k),'exclusion.'+k)
            if timestamp(ex['expires_at'])<=datetime.now(timezone.utc):raise ValueError('Exclusion expired')
            if timestamp(ex['approved_at'])>timestamp(ex['expires_at']):raise ValueError('Invalid exclusion dates')
            if task['trials'] or result or state!='NOT_RUN':raise ValueError('An exclusion cannot hide trials or results')
            excluded+=1;counts['EXCLUDED']+=1;coverage[task['module']]['EXCLUDED']+=1;unresolved.append(task['task_id']+':EXCLUDED');continue
        if app=='NOT_APPLICABLE':
            if result or task['trials'] or state!='NOT_RUN':raise ValueError('Not applicable with execution/result')
            counts[app]+=1;coverage[task['module']][app]+=1;continue
        if app=='UNKNOWN' or task['scope']!='in_scope' or task['access'] in ('unknown','none'):
            if state=='COMPLETED':raise ValueError('Do not complete with pending applicability, access or scope')
        if state in ('ERROR','BLOCKED') or result=='INCONCLUSIVE':nonempty(task['rationale'],'reason for pending result')
        if state!='COMPLETED' and result:raise ValueError('Result without complete execution')
        if state=='COMPLETED' and not result:raise ValueError('Execution without result')
        for trial in task['trials']:
            tid=trial['trial_id']
            if tid in seen_trials:raise ValueError('Duplicate trial')
            seen_trials.add(tid)
            if trial['example_id'] and trial['example_id'] not in example_ids:raise ValueError('Unknown trial example')
            if trial['technique_id'] and trial['technique_id'] not in technique_ids:raise ValueError('Unknown trial technique')
            if task['activity']!='REDTEAM' and trial['technique_id'] and trial['technique_id'] not in task['technique_ids']:raise ValueError('Technique not linked to the case')
            if task['activity']!='REDTEAM' and trial['example_id'] and trial['example_id'] not in task['example_ids']:raise ValueError('Example not linked to the case')
            if not trial['example_id'] and not trial['adaptation_diff'].strip():raise ValueError('Own input requires describing adaptation/provenance')
            if set(trial['evidence_ids'])-ev.keys():raise ValueError('Unknown trial evidence')
            if trial['execution']!='COMPLETED' and trial['result']:raise ValueError('Trial not run with a result')
            if trial['execution']=='COMPLETED' and not trial['result']:raise ValueError('Completed trial without result')
            if trial['execution'] in ('BLOCKED','ERROR') or trial['result']=='INCONCLUSIVE':nonempty(trial['rationale'],'reason for the trial')
            if trial['result'] in ('PASS','FAIL'):
                for k in ('variant','snapshot_ref','identity','reachability','expected','observed'):nonempty(trial[k],k)
                if not trial['baseline_ok'] or not trial['evidence_ids']:raise ValueError('Trial without baseline/evidence')
                kinds={ev[x]['kind'] for x in trial['evidence_ids']}
                if not {'baseline','input','response','effect','identity','reachability'}<=kinds:raise ValueError('Incomplete technical evidence')
                if trial['reachability'] not in ('reached','blocked_by_control'):raise ValueError('Reachability not verifiable')
                if trial['reachability']=='blocked_by_control' and not trial['blocking_control_id']:raise ValueError('Missing observed blocking control')
                if trial['result']=='PASS' and trial['reachability']=='blocked_by_control' and trial['blocking_control_id'] not in task['control_ids']:raise ValueError('An earlier block does not demonstrate this task\'s control')
                if trial['snapshot_ref']!=a['snapshot_ref']:raise ValueError('Trial with a snapshot different from the plan')
        trial_results=[t['result'] for t in task['trials']]
        if 'FAIL' in trial_results and result!='FAIL':raise ValueError('Do not hide a FAIL trial')
        if result in ('PASS','FAIL'):
            if not task['evidence_ids']:raise ValueError('Task without evidence')
            nonempty(task['observations'],'observations');nonempty(task['reviewer'],'reviewer')
            if task['activity'] in ('DESIGN','CONFIG'):
                if not any(ev[x]['kind']=='review' for x in task['evidence_ids']):raise ValueError('Review without documentary evidence')
                if task['trials']:raise ValueError('A review does not accept attack trials')
            else:
                if not task['trials'] or not task['cleanup_confirmed']:raise ValueError('Test without trials/cleanup')
                protocol=task['test_protocol']
                if not protocol:raise ValueError('Decided test without frozen depth/variants')
                valid=Counter(t['variant'] for t in task['trials'] if t['execution']=='COMPLETED' and t['result'] in ('PASS','FAIL'))
                missing=[v for v in protocol['required_variants'] if valid[v]<protocol['min_trials_per_variant']]
                if missing and result=='PASS':raise ValueError('PASS with incomplete planned sample or variants')
                if missing:unresolved.append(task['task_id']+':SAMPLING')
                if result=='PASS' and (any(r!='PASS' for r in trial_results) or any(t['execution']!='COMPLETED' for t in task['trials'])):raise ValueError('PASS with incomplete or failed variants')
                if result=='FAIL' and 'FAIL' not in trial_results:raise ValueError('FAIL without a failed trial')
                if not set(x for t in task['trials'] for x in t['evidence_ids'])<=set(task['evidence_ids']):raise ValueError('The task must keep all the evidence of its trials')
                if any(t['execution']!='COMPLETED' or t['result']=='INCONCLUSIVE' for t in task['trials']):unresolved.append(task['task_id']+':VARIANT')
            decided+=1;failures+=result=='FAIL'
        else:unresolved.append(task['task_id']+':'+(app if app=='UNKNOWN' else state+':'+result))
        label=result or (app if app=='UNKNOWN' else state)
        counts[label]+=1;coverage[task['module']][label]+=1
    readiness=ready(a);technical_code=2 if unresolved or not decided else 1 if failures else 0
    integrity_verified=approved_manifest is not None and evidence_root is not None
    code=2 if readiness or not integrity_verified else technical_code
    return {'plan_id':plan['plan_id'],'counts':dict(counts),'coverage_by_module':{k:dict(v) for k,v in coverage.items()},
      'activity_types_selected':sorted({t['activity'] for t in plan['tasks']}),
      'coverage_by_activity':{act:dict(Counter(t['result'] or ('EXCLUDED' if t['exclusion'] else t['applicability'] if t['applicability']!='APPLICABLE' else t['execution']) for t in plan['tasks'] if t['activity']==act)) for act in sorted({t['activity'] for t in plan['tasks']})},
      'scope_and_access':dict(Counter('out_of_scope' if t['scope']!='in_scope' else 'no_access' if t['access']=='none' else 'access_unknown' if t['access']=='unknown' else 'accessible' for t in plan['tasks'] if t['applicability']!='NOT_APPLICABLE')),
      'trials_by_task_and_variant':{t['task_id']:{v:dict(Counter(x['result'] or x['execution'] for x in t['trials'] if x['variant']==v)) for v in sorted({x['variant'] for x in t['trials']})} for t in plan['tasks'] if t['trials']},
      'applicable_obligations':sum(t['applicability']=='APPLICABLE' for t in plan['tasks']),
      'unknown_obligations':sum(t['applicability']=='UNKNOWN' for t in plan['tasks']),
      'decided_obligations':decided,'excluded_obligations':excluded,'failures':failures,
      'unresolved':unresolved,'readiness_gaps':readiness,'integrity_verified':integrity_verified,
      'technical_exit_code':technical_code,'exit_code':code,
      'note':'Hashes verify integrity, not authenticity or the validity of the judgment. Case coverage, not system certification.'}

def render_case(c,lib=None):
    lib=lib or library();ts={t['id']:t for t in lib['techniques']}
    lines=[f"# {c['id']} — {c['title']}",f"\nRevision {c['revision']} · {c['module']} · {c['activity']}\n",
      '## Objective and risk\n',c['objective'],c['potential_impact'],'\nControls: '+', '.join(c['control_ids']),
      '\n## Applicability\n','One alternative must be satisfied: '+ ' **o** '.join(' + '.join(x) or 'common core' for x in c['applies_if']),
      '\nActor: '+c['actor']+'\n\nAccess: '+c['access_required'],'\n## Preparation\n']
    lines+=['- '+s for s in c['preconditions']]
    lines+=['\nAllowed baseline: '+c['baseline']['allowed'],'\nRestricted control: '+c['baseline']['denied'],'\n## Procedure\n']
    lines+=[f'{i}. {s}' for i,s in enumerate(c['procedure'],1)]
    lines+=['\n## Techniques and examples\n']
    for tid in c['technique_ids']:
        t=ts[tid];lines+=[f"\n### {tid} — {t['title']}\n",'````text\n'+t['example']+'\n````\n']
        lines+=[f'{i}. {s}' for i,s in enumerate(t['steps'],1)]
        lines+=['\nOracle: '+t['validation'],'\nFalse positives: '+t['false_positive_checks']]
    fams=sorted({ts[tid].get('family','') for tid in c['technique_ids'] if ts[tid].get('family')})
    if fams:
        lines+=['\nWalkthroughs: step-by-step application of the technique families used here.']
        for fam in fams:
            lines.append(f"- [{fam} walkthrough](../walkthroughs/{fam}.md)")
    lines+=['\n## Evidence\n']+['- '+s for s in c['evidence']]
    lines+=['\n## Result\n','- FAIL: '+c['success_criteria']['attack_success'],'- PASS: '+c['success_criteria']['control_pass'],'- INCONCLUSIVE: '+c['success_criteria']['inconclusive'],
      '\n## Variants and metrics\n',', '.join(c['variants']) or 'Routes and roles present.',json.dumps(c['metrics'],ensure_ascii=False),
      '\n## Stop, cleanup and retest\n','; '.join(c['stop_conditions']),c['cleanup']]+['- '+s for s in c['retest']]
    lines+=['\n## Recommendations\n']+['- '+s for s in c['mitigations']]
    lines+=['\n## References\n']
    for m in c['mappings']:lines.append(f"- {m['framework']} {m['version']} {m['id']}: {m['relation']}. {m['rationale']}")
    lines+=['\nLimits: '+' '.join(c['limitations']),'\nIndependent review: '+c['review']['independent_review']+'. The fieldcard does not imply execution against a real system.']
    return '\n'.join(lines)+'\n'
def plan_markdown(plan,out_path=None):
    lib=library();cs={x['id']:x for x in lib['cases']};lines=['# Merestone operational plan',f"\nPlan: {plan['plan_id']} · {VERSION}",
      '\nComplete authorization and inventory before running. Unknown and non-applicable obligations are kept.\n']
    for t in plan['tasks']:
        lines+=[f"\n## {t['task_id']} · {t['case_id']} · {t['title']}\n",f"Asset: {t['asset_id']} · route: {t['route_id']} · boundary: {t['boundary']}",
          f"Applicability: {t['applicability']} · {t['activity']} · {t['execution']} · {t['result'] or 'pending'}"]
        if t['applicability']=='NOT_APPLICABLE':continue
        c=cs.get(t['case_id'])
        if c:lines+=['\n'+render_case(c,lib).replace('\n#','\n##').lstrip('#').strip()]
        lines+=['\nRecord snapshot, variant, baseline, reachability, identity, expected/observed, evidence, reviewer and cleanup.']
    rendered='\n'.join(lines)+'\n'
    return rendered
CATALOG_NOTE=('## How to read the CORE module\n\n'
  'The CORE module groups three kinds of fieldcards: (1) unconditional common-core reviews, CORE-001…008 (DESIGN) and CFG-001/002 (CONFIG); '
  '(2) CONFIG reviews conditioned by capability, CFG-003…006; and (3) cross-cutting cases that do not belong to a single module, AI-004, AI-050, AI-054 and AI-061, activated by capability. '
  'Unconditional reviews are only generated on routes that declare DESIGN or CONFIG in `activity_types`; `check-plan` records the gap `core_design_missing` and does not issue code 0 or 1 if no route declares DESIGN. '
  'Declare CONFIG when there is deployed configuration to review.\n\n'
  'Numbering: AI-060 is retired (it was reserved during construction and dropped to avoid duplicating AI-038). It is not reused.\n')

FAMILY_NAMES={'REC':'Reconnaissance','PI':'Prompt injection','JB':'Jailbreaks','OUT':'Output handling',
  'MCP':'MCP (host, client, server, transport)','DATA':'Data and training','APP':'Application and platform',
  'AGENT':'Agents, memory and delegation','RAG':'Retrieval (RAG)','PLATFORM':'Platform and supply chain',
  'MODEL':'Model inference and privacy','TOOLS':'Tools and function calling','LLM':'LLM guardrails',
  'CORE':'Common core','MULTIMODAL':'Multimodal'}

def render_walkthroughs(lib):
    """Generate one walkthrough per technique family from the catalog."""
    from collections import defaultdict
    base=ROOT/'playbook/walkthroughs';base.mkdir(parents=True,exist_ok=True)
    fams=defaultdict(list)
    for t in lib['techniques']:
        if t.get('family'):fams[t['family']].append(t)
    exbytech=defaultdict(list)
    for e in lib['examples']:
        for tid in e.get('technique_ids',[]):exbytech[tid].append(e)
    for fam in sorted(fams):
        title=FAMILY_NAMES.get(fam,fam)
        L=[f'# {fam} — {title}: walkthrough','',
           'This walkthrough applies each technique of the family against an authorized fixture '
           'with a reserved canary. Keep authorization, limits '
           'and telemetry per the field guide, and record every adaptation.','']
        for t in sorted(fams[fam],key=lambda x:x['id']):
            L+=[f"## {t['id']} — {t['title']}",'',f"**Objective:** {t['objective']}",'']
            if t.get('preconditions'):L+=['**Preparation:** '+'; '.join(t['preconditions']),'']
            L+=['**Steps:**','']+[f"{i}. {s}" for i,s in enumerate(t.get('steps',[]),1)]+['']
            exs=exbytech.get(t['id'],[])
            if exs:
                L+=['**Example inputs (Merestone fixtures):**','']
                for e in exs:
                    if e.get('payload'):L.append(f"- `{e['id']}`: {e['payload']}")
                L+=['']
            L+=[f"**Oracle:** {t.get('validation','')}",'']
            if t.get('false_positive_checks'):L+=[f"**Avoid false positives:** {t['false_positive_checks']}",'']
            if t.get('variants'):L+=['**Variants:** '+', '.join(t['variants']),'']
            if t.get('mitigations'):L+=['**Mitigations:** '+'; '.join(t['mitigations']),'']
            if t.get('related_cases'):
                L+=['**Fieldcards:** '+', '.join(f"[{cid}](../fieldcards/{cid}.md)" for cid in t['related_cases']),'']
        (base/(fam+'.md')).write_text('\n'.join(L).rstrip()+'\n',encoding='utf-8')
    idx=['# Walkthroughs','','Step-by-step application of each technique family, with Merestone fixtures.','','| Family | Techniques |','|---|---|']
    for fam in sorted(fams):
        idx.append(f"| [{fam} — {FAMILY_NAMES.get(fam,fam)}]({fam}.md) | {len(fams[fam])} |")
    (base/'README.md').write_text('\n'.join(idx)+'\n',encoding='utf-8')

def render_all():
    lib=library();base=ROOT/'playbook/fieldcards';base.mkdir(parents=True,exist_ok=True)
    for c in lib['cases']:(base/(c['id']+'.md')).write_text(render_case(c,lib),encoding='utf-8')
    lines=['# Operational catalog\n','View generated from `catalog/cases/index.json`.\n',CATALOG_NOTE,'| Case | Module | Activity | Controls |','|---|---|---|---|']
    for c in lib['cases']:lines.append(f"| [{c['id']} — {c['title']}](fieldcards/{c['id']}.md) | {c['module']} | {c['activity']} | {', '.join(c['control_ids'])} |")
    (ROOT/'playbook/catalog.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    lines=['# Technique library\n','Mechanisms are reused in boundary cases. Relating a technique is not the same as running a test. Merestone\'s own inputs are in the fieldcards and the step-by-step application in the [walkthroughs](walkthroughs/).\n','| Technique | Family / stage | Associated cases |','|---|---|---|']
    for t in lib['techniques']:
        links=', '.join(f"[{cid}](fieldcards/{cid}.md)" for cid in t['related_cases'])
        lines.append(f"| {t['id']} — {t['title']} | {t.get('family','')} / {t.get('stage','')} | {links} |")
    (ROOT/'playbook/techniques.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    render_walkthroughs(lib)
    for s in lib['scenarios']:
        p=ROOT/'playbook/scenarios'/(s['id']+'.md');p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text('# '+s['id']+' — '+s['title']+'\n\n'+s['objective']+'\n\nActor: '+s['actor']+'\n\nApplicability: '+str(s['applies_if'])+'\n\nPreparation:\n\n'+'\n'.join('- '+x for x in s['preconditions'])+'\n\nSteps:\n\n'+
          '\n'.join(f"{x['order']}. [{x['case_id']}](../fieldcards/{x['case_id']}.md): {x['observe']}" for x in s['steps'])+
          '\n\nSuccess: '+s['success_criteria']+'\n\nStop: '+'; '.join(s['stop_conditions'])+'\n\nCleanup: '+s['cleanup']+'\n\n'+s['reporting']+'\n',encoding='utf-8')
def report_markdown(plan,result,findings=()):
    lines=['# Merestone report','\nSystem: '+plan['architecture']['system_name'],'\nPlan: '+plan['plan_id'],
      '\n'+result['note'],'\n## Scope\n','Authorization: '+plan['architecture']['authorization_ref'],'Snapshot: '+plan['architecture']['snapshot_ref'],
      '\n## Coverage\n',
      f"Applicable obligations: {result['applicable_obligations']}; unknown: {result['unknown_obligations']}; decided: {result['decided_obligations']}; excluded: {result['excluded_obligations']}; FAIL: {result['failures']}. Record status: code {result['exit_code']} (0 complete without FAIL; 1 complete with FAIL; 2 incomplete/unverified).",
      '\n| Module | States of its obligations |','|---|---|']
    for mod,counts in sorted(result['coverage_by_module'].items()):lines.append('| '+mod+' | '+', '.join(f'{k}: {v}' for k,v in counts.items())+' |')
    lines+=['\n| Activity | States |','|---|---|']
    for act,counts in result['coverage_by_activity'].items():lines.append('| '+act+' | '+', '.join(f'{k}: {v}' for k,v in counts.items())+' |')
    lines+=['\nAccess and scope: '+json.dumps(result['scope_and_access'],ensure_ascii=False),
      '\nPending readiness: '+(', '.join(result['readiness_gaps']) or 'no declared gaps'),
      '\n## Results per boundary\n','| Case | Asset/route | Activity | Applicability | Execution | Result | Evidence |','|---|---|---|---|---|---|---|']
    for t in plan['tasks']:lines.append('| '+' | '.join(str(x).replace('|','\\|').replace('\n',' ') for x in [t['case_id'],t['asset_id']+'/'+t['route_id'],t['activity'],t['applicability'],t['execution'],t['result'],', '.join(t['evidence_ids'])])+' |')
    lines+=['\n## Trials per variant\n','| Task | Variant | Results |','|---|---|---|']
    for task,variants in result['trials_by_task_and_variant'].items():
        for variant,counts in variants.items():lines.append('| '+task+' | '+variant.replace('|','\\|')+' | '+', '.join(f'{k}: {v}' for k,v in counts.items())+' |')
    lines+=['\nBenign trials are utility controls; do not add them to the adversarial ASR denominator. Do not aggregate snapshots or adaptive exploration as a fixed sample.\n',
      '\n## Findings and treatment\n']
    if not findings:lines+=['No finding records were attached to this view. Earlier FAILs remain in force; consolidate them by cause/correction with the finding-v3 template. A documentary deficiency does not demonstrate exploitation.']
    for f in findings:
        lines+=['\n### '+f['id']+' — '+f['title']+'\n',
          f"Status: {f['state']}; local priority I×F: {f['impact']}×{f['feasibility']}; confidence: {f['confidence']}.",
          '\nCause: '+f['root_cause'],'\nExpected: '+f['expected'],'\nObserved: '+f['observed'],
          '\nProven impact: '+f['proven_impact'],'\nPotential impact: '+f['potential_impact'],
          '\nContainment: '+f['containment'],'\nCorrection: '+f['remediation'],
          '\nOwner: '+f['owner']+'; deadline: '+f['due_at'],
          '\nClosure: '+f['acceptance_criteria'],'\nEvidence: '+', '.join(f['evidence_ids'])]
    lines+=['\n## Decisions and limitations\n','Record residual risk, exclusions and acceptance with expiry; do not close because counts improved. The tool does not certify independent review or the authorization of the judgment.',
      '\n### Pending\n']+['- '+x for x in result['unresolved']]
    return '\n'.join(lines)+'\n'

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    s.add_parser('validate-library');s.add_parser('render')
    q=s.add_parser('list');q.add_argument('--family');q.add_argument('--module')
    q=s.add_parser('init');q.add_argument('--profile',choices=['chat','rag','agent','mcp','ml-pipeline','full'],required=True);q.add_argument('--out',required=True)
    q=s.add_parser('plan');g=q.add_mutually_exclusive_group(required=True);g.add_argument('--architecture');g.add_argument('--profile',choices=['chat','rag','agent','mcp','ml-pipeline','full']);q.add_argument('--format',choices=['json','md'],default='json');q.add_argument('--out',required=True)
    for name in ('check-plan','report'):
        q=s.add_parser(name);q.add_argument('path');q.add_argument('--manifest');q.add_argument('--evidence-root')
        if name=='report':q.add_argument('--out',required=True);q.add_argument('--findings',nargs='*',default=[]);q.add_argument('--retest-bundle')
    args=p.parse_args(argv)
    try:
        if args.command=='validate-library':
            lib=library();print(json.dumps({k:len(lib[k]) for k in ('cases','controls','techniques','examples','scenarios')}));return 0
        if args.command=='render':render_all();return 0
        if args.command=='list':
            lib=library()
            if args.family:
                for t in lib['techniques']:
                    if t['family']==args.family and (not args.module or any(c['module']==args.module and c['id'] in t['related_cases'] for c in lib['cases'])):print(t['id']+' | '+t['title'])
            else:
                for c in lib['cases']:
                    if not args.module or c['module']==args.module:print(c['id']+' | '+c['title'])
        elif args.command=='init':write(args.out,profile(args.profile))
        elif args.command=='plan':
            a=read(args.architecture) if args.architecture else profile(args.profile);plan=make_plan(a);out=Path(args.out);side=out.with_suffix(out.suffix+'.manifest.json')
            if out.exists() or side.exists():raise ValueError('Existing output/manifest; do not overwrite the log')
            out.parent.mkdir(parents=True,exist_ok=True)
            if args.format=='json':write(out,plan)
            else:out.write_text(plan_markdown(plan,out),encoding='utf-8')
            write(side,manifest(plan));print(f"{len(plan['tasks'])} obligations; review UNKNOWN and scope.")
        else:
            plan=read(args.path);man=read(args.manifest) if args.manifest else None;result=check_plan(plan,man,args.evidence_root)
            if args.command=='report':
                findings=[read(f) for f in args.findings]
                if findings:
                    from governance import check_finding,load_retests
                    for f in findings:check_finding(f,plan,man,args.evidence_root,load_retests(args.retest_bundle))
                out=Path(args.out)
                if out.exists():raise ValueError('Existing report; use a new revision')
                out.parent.mkdir(parents=True,exist_ok=True);out.write_text(report_markdown(plan,result,findings),encoding='utf-8')
            else:print(json.dumps(result,ensure_ascii=False,indent=2))
            return result['exit_code']
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:print('ERROR: '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
