import copy,tempfile,unittest
from pathlib import Path
import operational as op
import governance as gov
from adapters.import_observations import import_event
from test_operational import architecture,complete

def finding(plan):
    t=next(t for t in plan['tasks'] if t['result']=='FAIL')
    f=op.read(op.ROOT/'templates/finding-v3.json')
    f.update(title='Synthetic control failure',state='confirmed',asset_ids=[t['asset_id']],threat_ids=t['threat_ids'],control_ids=t['control_ids'],case_ids=[t['case_id']],task_ids=[t['task_id']],evidence_ids=t['evidence_ids'],root_cause='fixture faulty predicate',expected='deny B',observed='allowed B',proven_impact='fixture only',potential_impact='',impact=4,feasibility=4,risk_rationale='Synthetic high impact fixture',confidence='high',owner='fixture maintainer',due_at='2099-01-01T00:00:00Z',containment='disable fixture',remediation='fix predicate',acceptance_criteria='original, neighbor and benign pass',history=[{'at':'2026-09-28T00:00:00Z','actor':'fixture analyst','from':'','to':'proposed','reason':'observed fixture'},{'at':'2026-09-28T00:00:01Z','actor':'fixture analyst','from':'proposed','to':'confirmed','reason':'reproduced fixture'}])
    return f

class GovernanceTests(unittest.TestCase):
    def test_changed_depth_invalidates_manifest(self):
        p=op.make_plan(architecture(['retrieval']));m=op.manifest(p)
        a=copy.deepcopy(p['architecture']);a['routes'][0]['test_protocols'][0]['min_trials_per_variant']=20
        new=gov.revise_plan(p,a,'more sampling','reviewer')
        with self.assertRaises(ValueError):op.check_plan(new,m)
        self.assertEqual(new['amendments'][-1]['previous_plan_id'],p['plan_id'])
        self.assertTrue(gov.compare_plans(p,new)['changed']);self.assertFalse(any(t['result'] for t in new['tasks']))
    def test_reduced_sample_rejected(self):
        a=architecture(['retrieval'])
        for x in a['routes'][0]['test_protocols']:x['min_trials_per_variant']=2
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(a),d)
            with self.assertRaisesRegex(ValueError,'sample'):op.check_plan(p,op.manifest(p),d)
    def test_missing_planned_variant_rejected(self):
        a=architecture(['retrieval'])
        for x in a['routes'][0]['test_protocols']:x['required_variants'].append('cache-warm')
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(a),d)
            with self.assertRaisesRegex(ValueError,'variants'):op.check_plan(p,op.manifest(p),d)
    def test_unplanned_protocol_never_pass(self):
        a=architecture(['retrieval']);a['routes'][0]['test_protocols']=[]
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(a),d)
            with self.assertRaisesRegex(ValueError,'depth'):op.check_plan(p,op.manifest(p),d)
    def test_earlier_block_not_downstream_pass(self):
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(architecture(['retrieval'])),d);t=next(t for t in p['tasks'] if t['trials'])
            t['trials'][0].update(reachability='blocked_by_control',blocking_control_id='OTHER')
            with self.assertRaisesRegex(ValueError,'earlier block'):op.check_plan(p,op.manifest(p),d)
    def test_wrong_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(architecture(['retrieval'])),d);next(t for t in p['tasks'] if t['trials'])['trials'][0]['snapshot_ref']='different'
            with self.assertRaisesRegex(ValueError,'snapshot'):op.check_plan(p,op.manifest(p),d)
    def test_import_event_verifies_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p=op.make_plan(architecture(['retrieval']));done=complete(copy.deepcopy(p),d,'FAIL');t=next(t for t in done['tasks'] if t['trials']);e={k:t[k] for k in ('task_id','result','observations','reviewer','cleanup_confirmed','trials')};e['evidence']=[x for x in done['evidence'] if x['id'] in t['evidence_ids']]
            imported=import_event(p,e,d,op.manifest(p));self.assertEqual(op.check_plan(imported,op.manifest(p),d)['failures'],1)
            Path(d,e['evidence'][0]['path']).write_text('corrupt')
            with self.assertRaisesRegex(ValueError,'(?i)hash'):import_event(p,e,d,op.manifest(p))
    def test_finding_history_and_references(self):
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(architecture()),d,'FAIL');f=finding(p)
            self.assertTrue(gov.check_finding(f,p,op.manifest(p),d)['validated'])
            f['history'][-1]['from']='closed'
            with self.assertRaisesRegex(ValueError,'transition'):gov.check_finding(f,p,op.manifest(p),d)
    def test_expired_risk_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(architecture()),d,'FAIL');f=finding(p);f['state']='risk_accepted'
            f['history'].append({'at':'2026-09-28T00:00:02Z','actor':'fixture owner','from':'confirmed','to':'risk_accepted','reason':'fixture'})
            f['risk_acceptance']={'approver':'fixture owner','reason':'fixture','expires_at':'2020-01-01T00:00:00Z','compensation':'fixture'}
            with self.assertRaisesRegex(ValueError,'expired'):gov.check_finding(f,p,op.manifest(p),d)
    def test_no_closure_without_retest(self):
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(architecture()),d,'FAIL');f=finding(p)
            for i,(old,new) in enumerate([('confirmed','remediating'),('remediating','ready_for_retest'),('ready_for_retest','closed')]):f['history'].append({'at':f'2026-09-28T00:00:0{i+2}Z','actor':'fixture reviewer','from':old,'to':new,'reason':'fixture'})
            f['state']='closed';f['closure'].update(reviewer='fixture reviewer',change_evidence_ref='change',criteria_met=True)
            with self.assertRaisesRegex(ValueError,'retest plan'):gov.check_finding(f,p,op.manifest(p),d)
    def test_documentary_closure_does_not_require_attack_trials(self):
        with tempfile.TemporaryDirectory() as d,tempfile.TemporaryDirectory() as r:
            a=architecture(activities=['DESIGN']);p=complete(op.make_plan(a),d,'FAIL');f=finding(p);ret=complete(gov.revise_plan(p,a,'correction','fixture reviewer'),r)
            for i,(old,new) in enumerate([('confirmed','remediating'),('remediating','ready_for_retest'),('ready_for_retest','closed')]):f['history'].append({'at':f'2026-09-28T00:00:0{i+2}Z','actor':'fixture reviewer','from':old,'to':new,'reason':'fixture'})
            f['state']='closed';f['retest_plan_ids']=[ret['plan_id']];eid=ret['evidence'][0]['id']
            f['closure'].update(reviewer='fixture reviewer',change_evidence_ref=eid,review_evidence_ref=eid,criteria_met=True)
            self.assertTrue(gov.check_finding(f,p,op.manifest(p),d,[(ret,op.manifest(ret),r)])['validated'])
    def test_module_coverage_retains_nonapplicable(self):
        p=op.make_plan(architecture());r=op.check_plan(p)
        self.assertEqual(sum(sum(v.values()) for v in r['coverage_by_module'].values()),len(p['tasks']))
    def test_report_includes_verified_findings(self):
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(architecture()),d,'FAIL');f=finding(p);r=op.check_plan(p,op.manifest(p),d)
            text=op.report_markdown(p,r,[f]);self.assertIn(f['root_cause'],text);self.assertIn('Proven impact',text);self.assertIn('local priority',text)
            with self.assertRaisesRegex(ValueError,'store'):gov.check_finding(f,p,None,None)

if __name__=='__main__':unittest.main()
