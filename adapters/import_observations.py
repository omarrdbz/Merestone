"""Imports measured records; does not invoke the target or execute test inputs."""
from pathlib import Path
import argparse,copy,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import operational as op

def import_event(plan,event,evidence_root,approved_manifest):
    op.check_plan(plan,approved_manifest,evidence_root)
    required={'task_id','result','observations','reviewer','cleanup_confirmed','trials','evidence'}
    if set(event)!=required:raise ValueError('Unexpected or incomplete import fields')
    result=copy.deepcopy(plan)
    task=next((t for t in result['tasks'] if t['task_id']==event['task_id']),None)
    if task is None:raise ValueError('Task not selected')
    if task['applicability']!='APPLICABLE' or task['scope']!='in_scope':raise ValueError('Task not applicable/in scope')
    if event['result'] not in ('PASS','FAIL','INCONCLUSIVE'):raise ValueError('Invalid result')
    known={e['id']:e for e in result['evidence']}
    for e in event['evidence']:
        op.validate(e,op.read(op.ROOT/'schemas/evidence-v3.schema.json'))
        op.verified_file(e,evidence_root)
        if e['id'] in known and e!=known[e['id']]:raise ValueError('Do not overwrite evidence')
        if e['id'] not in known:result['evidence'].append(e);known[e['id']]=e
    task['trials']+=event['trials']
    task['evidence_ids']=sorted(set(task['evidence_ids'])|{e['id'] for e in event['evidence']})
    task['execution']='COMPLETED';task['result']='FAIL' if task['result']=='FAIL' or any(t['result']=='FAIL' for t in task['trials']) else event['result']
    task['observations']+='\n'+event['observations'];task['reviewer']=event['reviewer'];task['cleanup_confirmed']=event['cleanup_confirmed']
    if event['result']=='INCONCLUSIVE':task['rationale']=event['observations']
    op.check_plan(result,approved_manifest,evidence_root)
    return result

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('plan','event','manifest','evidence-root','out'):p.add_argument('--'+k,required=True)
    a=p.parse_args(argv)
    try:
        result=import_event(op.read(a.plan),op.read(a.event),a.evidence_root,op.read(a.manifest));op.write(a.out,result);return 0
    except (ValueError,OSError,KeyError,TypeError) as e:print('ERROR: '+str(e),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
