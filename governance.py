"""Plan changes and finding lifecycle. Does not authenticate approvers."""
from pathlib import Path
import argparse,json,sys
import operational as op

TRANSITIONS={
 '':{'proposed'},'proposed':{'confirmed','false_positive','duplicate'},
 'confirmed':{'assigned','remediating','risk_accepted'},'assigned':{'remediating','risk_accepted'},
 'remediating':{'ready_for_retest','risk_accepted'},'ready_for_retest':{'closed','remediating','risk_accepted'},
 'closed':{'confirmed'},'risk_accepted':{'confirmed','remediating'},'duplicate':{'confirmed'},'false_positive':{'confirmed'}}

def check_finding(f,plan,manifest,evidence_root,retests=()):
    if manifest is None or evidence_root is None:raise ValueError('Finding requires a manifest and a verifiable store')
    op.validate(f,op.read(op.ROOT/'schemas/finding-v3.schema.json'))
    op.check_plan(plan,manifest,evidence_root)
    maps={'asset_ids':{a['id'] for a in plan['architecture']['assets']},
      'threat_ids':{a['id'] for a in plan['architecture']['threats']},
      'task_ids':{t['task_id'] for t in plan['tasks']},'evidence_ids':{e['id'] for e in plan['evidence']},
      'case_ids':{t['case_id'] for t in plan['tasks']},'control_ids':{c for t in plan['tasks'] for c in t['control_ids']}}
    for k,known in maps.items():
        if set(f[k])-known:raise ValueError('Finding with unknown reference: '+k)
    tasks=[t for t in plan['tasks'] if t['task_id'] in f['task_ids']]
    if not set(f['case_ids'])<={t['case_id'] for t in tasks}:raise ValueError('Cases not linked to the finding tasks')
    if not set(f['evidence_ids'])<={e for t in tasks for e in t['evidence_ids']}:raise ValueError('Evidence unrelated to the finding tasks')
    if f['state'] not in ('proposed','duplicate','false_positive') and not any(t['result']=='FAIL' for t in tasks):raise ValueError('Confirmed finding without a documented violation')
    state='';last=None
    for h in f['history']:
        d=op.timestamp(h['at'])
        if last and d<last:raise ValueError('History out of order')
        if h['from']!=state or h['to'] not in TRANSITIONS.get(state,set()):raise ValueError('Invalid finding transition')
        state=h['to'];last=d
    if state!=f['state']:raise ValueError('State does not match history')
    op.timestamp(f['due_at'])
    if state=='risk_accepted':
        for k,v in f['risk_acceptance'].items():op.nonempty(v,'risk_acceptance.'+k)
        if op.timestamp(f['risk_acceptance']['expires_at'])<=op.timestamp(op.now()):raise ValueError('Risk acceptance expired')
    if state=='closed':
        closure=f.get('closure',{})
        for k in ('reviewer','change_evidence_ref'):op.nonempty(closure.get(k),'closure.'+k)
        if f['impact']*f['feasibility']>=10 and closure['reviewer']==f['owner']:raise ValueError('Closing a high/critical finding requires a reviewer different from the correction owner')
        if not closure.get('criteria_met'):raise ValueError('Closure criteria not satisfied')
        indexed={p['plan_id']:(p,m,r) for p,m,r in retests}
        if not f['retest_plan_ids'] or set(f['retest_plan_ids'])-set(indexed):raise ValueError('Missing verifiable retest plan')
        if plan['plan_id'] in f['retest_plan_ids']:raise ValueError('Revalidation requires a new plan')
        passed=set();evidence=set();trials=set()
        original_keys={tuple(t[k] for k in ('case_id','asset_id','route_id','actor','activity')) for t in tasks}
        for pid in f['retest_plan_ids']:
            p,m,r=indexed[pid]
            if m is None or r is None:raise ValueError('Retest requires a manifest and a store')
            op.check_plan(p,m,r)
            evidence.update(e['id'] for e in p['evidence'])
            for t in p['tasks']:
                if t['result']=='PASS' and t['execution']=='COMPLETED' and tuple(t[k] for k in ('case_id','asset_id','route_id','actor','activity')) in original_keys:
                    passed.add((t['case_id'],t['asset_id'],t['route_id'],t['actor'],t['activity']))
                    trials.update(x['trial_id'] for x in t['trials'] if x['result']=='PASS')
        for t in tasks:
            key=tuple(t[k] for k in ('case_id','asset_id','route_id','actor','activity'))
            if t['result']=='FAIL' and key not in passed:raise ValueError('Retest without PASS at the original boundary')
        if closure['change_evidence_ref'] not in evidence:raise ValueError('Change evidence missing')
        if any(t['activity'] in ('TEST','REDTEAM') for t in tasks):
            refs=[closure.get(k) for k in ('original_trial_ref','neighbor_trial_ref','benign_trial_ref')]
            if len(set(refs))!=3 or any(x not in trials for x in refs):raise ValueError('Retest requires three distinct trials: original, neighbor and benign')
        elif closure.get('review_evidence_ref') not in evidence:raise ValueError('Documentary retest requires review evidence')
    return {'id':f['id'],'state':state,'priority_local':f['impact']*f['feasibility'],'confidence':f['confidence'],'validated':True,
      'note':'Validates consistency and referenced evidence; the judgment and the reviewer identity require human review.'}

def revise_plan(previous,architecture,reason,approver):
    op.nonempty(reason,'reason for change');op.nonempty(approver,'change owner')
    plan=op.make_plan(architecture)
    plan['amendments']=previous['amendments']+[{'previous_plan_id':previous['plan_id'],'reason':reason,'approver':approver,'at':op.now()}]
    return plan

def compare_plans(old,new):
    before={t['task_id']:t for t in old['tasks']};after={t['task_id']:t for t in new['tasks']}
    fields=('case_revision','applicability','scope','access','control_ids','threat_ids','technique_ids','test_protocol')
    return {'previous_plan_id':old['plan_id'],'new_plan_id':new['plan_id'],
      'catalog_changed':old['catalog_sha256']!=new['catalog_sha256'],
      'architecture_changed':old['architecture_sha256']!=new['architecture_sha256'],
      'added':sorted(after.keys()-before.keys()),'removed':sorted(before.keys()-after.keys()),
      'changed':{k:[f for f in fields if before[k][f]!=after[k][f]] for k in sorted(before.keys()&after.keys()) if any(before[k][f]!=after[k][f] for f in fields)},
      'result_transfer':'none; repeat or justify evidence reuse through explicit review'}

def load_retests(bundle):
    if not bundle:return []
    b=Path(bundle)
    return [(op.read(b.parent/r['plan']),op.read(b.parent/r['manifest']),b.parent/r['evidence_root']) for r in op.read(b)]

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);s=p.add_subparsers(dest='command',required=True)
    q=s.add_parser('revise');q.add_argument('--plan',required=True);q.add_argument('--architecture',required=True)
    for key in ('reason','approver','out'):q.add_argument('--'+key,required=True)
    q=s.add_parser('compare');q.add_argument('old');q.add_argument('new')
    q=s.add_parser('check-finding')
    for key in ('finding','plan','manifest','evidence-root'):q.add_argument('--'+key,required=True)
    q.add_argument('--retest-bundle',help='JSON array: plan, manifest, evidence_root paths, relative to this bundle')
    a=p.parse_args(argv)
    try:
        if a.command=='revise':
            old=op.read(a.plan);new=revise_plan(old,op.read(a.architecture),a.reason,a.approver)
            out=Path(a.out);m=out.with_suffix(out.suffix+'.manifest.json')
            if out.exists() or m.exists():raise ValueError('Do not overwrite plan/manifest')
            op.write(out,new);op.write(m,op.manifest(new));print(json.dumps(compare_plans(old,new),ensure_ascii=False,indent=2))
        elif a.command=='compare':print(json.dumps(compare_plans(op.read(a.old),op.read(a.new)),ensure_ascii=False,indent=2))
        else:
            retests=load_retests(a.retest_bundle)
            print(json.dumps(check_finding(op.read(a.finding),op.read(a.plan),op.read(a.manifest),a.evidence_root,retests),ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as e:print('ERROR: '+str(e),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
