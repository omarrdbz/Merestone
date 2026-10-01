import copy,hashlib,json,tempfile,unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import operational as op

def architecture(present=(),activities=None):
    a=op.profile('chat');a.update(assessment_id='SYNTHETIC',system_name='Synthetic fixture',authorization_ref='fixture-auth',snapshot_ref='fixture-snapshot',evidence_store='local-fixture')
    a['inventory_review']={'reviewer':'fixture-reviewer','reviewed_at':'2026-09-28T00:00:00Z','evidence_ref':'fixture-inventory'}
    a['limits']={'requests':100,'tokens':0,'cost_minor_units':0,'duration_seconds':60,'concurrency':1};a['stop_conditions']=['fixture complete']
    r=a['routes'][0];r.update(boundary='fixture-boundary',actor='fixture-user',access='gray-box',activity_types=activities or ['DESIGN','CONFIG','TEST'])
    r['capabilities']={k:'present' if k in present else 'absent' for k in op.library()['capabilities']}
    r['capability_evidence']={k:'fixture-config' for k in r['capabilities']}
    r['test_protocols']=[{'case_id':c['id'],'required_variants':['fixture'],'min_trials_per_variant':1,'design':'deterministic','decision_rule':'Compare fixture effect to invariant','justification':'Test fixture only'} for c in op.library()['cases']+op.library()['scenarios'] if c['activity'] in ('TEST','REDTEAM')]
    return a

def add_evidence(plan,root,id,kind,body='fixture'):
    path=Path(root)/(id+'.txt');path.write_text(body,encoding='utf-8');raw=path.read_bytes()
    rec={'id':id,'path':path.name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'collected_at':'2026-09-28T00:00:00Z','collector':'fixture','origin':'local-test','classification':'synthetic','kind':kind,'redactions':[]}
    plan['evidence'].append(rec);return id

def complete(plan,root,result='PASS'):
    for i,t in enumerate(plan['tasks']):
        if t['applicability']!='APPLICABLE':continue
        t.update(execution='COMPLETED',result=result,observations='Fixture observed',reviewer='fixture-reviewer',cleanup_confirmed=True)
        if t['activity'] in ('DESIGN','CONFIG'):t['evidence_ids']=[add_evidence(plan,root,f'E{i}-review','review')]
        else:
            ids=[add_evidence(plan,root,f'E{i}-{k}',k) for k in ('baseline','input','response','effect','identity','reachability')]
            t['evidence_ids']=ids;t['trials']=[{'trial_id':f'TR{i}','variant':'fixture','example_id':'','technique_id':'','snapshot_ref':'fixture-snapshot','execution':'COMPLETED','result':result,'baseline_ok':True,'reachability':'reached','blocking_control_id':'','identity':'fixture-user','expected':'allow A; deny B','observed':'measured fixture','evidence_ids':ids,'rationale':'','parameters_ref':'fixture','adaptation_diff':'original synthetic fixture'}]
    return plan

class OperationalTests(unittest.TestCase):
    def test_unknown_is_not_absent(self):
        self.assertEqual(op.applies([['retrieval']],{}),'UNKNOWN')
        self.assertEqual(op.applies([['retrieval']],{'retrieval':'absent'}),'NOT_APPLICABLE')
        self.assertEqual(op.applies([['retrieval','llm_generation']],{'retrieval':'absent'}),'NOT_APPLICABLE')
    def test_rag_without_tools_sql_or_html(self):
        p=op.make_plan(architecture(['retrieval','llm_generation']))
        states={t['case_id']:t['applicability'] for t in p['tasks']}
        self.assertEqual(states['AI-006'],'APPLICABLE');self.assertEqual(states['AI-007'],'APPLICABLE');self.assertEqual(states['AI-009'],'APPLICABLE')
        for c in ('AI-012','AI-013','AI-014','AI-011','AI-019'):self.assertEqual(states[c],'NOT_APPLICABLE')
    def test_mcp_stdio_without_llm_oauth(self):
        p=op.make_plan(architecture(['mcp_server','mcp_stdio']))
        ids={t['case_id'] for t in p['tasks'] if t['applicability']=='APPLICABLE'}
        self.assertIn('AI-024',ids);self.assertNotIn('AI-001',ids);self.assertNotIn('AI-021',ids);self.assertNotIn('AI-040',ids)
    def test_all_capabilities_select_conditional_cases(self):
        caps=op.library()['capabilities'];p=op.make_plan(architecture(caps))
        ids={t['case_id'] for t in p['tasks'] if t['applicability']=='APPLICABLE'}
        self.assertTrue({'AI-005','AI-007','AI-009','AI-017','AI-026','AI-038','AI-040'}<=ids)
    def test_same_case_two_assets_allowed(self):
        a=architecture(['retrieval']);a['assets'].append(dict(a['assets'][0],id='B'))
        a['routes'].append(dict(copy.deepcopy(a['routes'][0]),id='ROUTE-B',asset_id='B'))
        p=op.make_plan(a);tasks=[t for t in p['tasks'] if t['case_id']=='AI-006']
        self.assertEqual(len(tasks),2);self.assertNotEqual(tasks[0]['task_id'],tasks[1]['task_id']);op.check_plan(p)
    def test_deleted_task_rejected(self):
        p=op.make_plan(architecture());p['tasks']=p['tasks'][:1]
        with self.assertRaisesRegex(ValueError,'Tasks deleted'):op.check_plan(p)
    def test_altered_case_rejected(self):
        p=op.make_plan(architecture());p['tasks'][0]['case_id']='AI-007'
        with self.assertRaises(ValueError):op.check_plan(p)
    def test_complete_documentary_review(self):
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(architecture(activities=['DESIGN'])),d)
            r=op.check_plan(p,op.manifest(p),d);self.assertEqual(r['exit_code'],0)
    def test_core_design_required(self):
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(architecture(activities=['TEST'])),d)
            r=op.check_plan(p,op.manifest(p),d)
            self.assertIn('core_design_missing',r['readiness_gaps']);self.assertEqual(r['exit_code'],2)
            self.assertFalse(any(t['case_id'].startswith('CORE-') for t in p['tasks']))
    def test_incomplete_evidence_never_green(self):
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(architecture(activities=['DESIGN'])),d)
            self.assertEqual(op.check_plan(p)['exit_code'],2)
            Path(d,p['evidence'][0]['path']).write_text('changed')
            with self.assertRaisesRegex(ValueError,'(?i)hash'):op.check_plan(p,op.manifest(p),d)
    def test_technical_fail_and_pass(self):
        for state,code in [('PASS',0),('FAIL',1)]:
            with self.subTest(state=state),tempfile.TemporaryDirectory() as d:
                p=complete(op.make_plan(architecture(['retrieval'])),d,state)
                self.assertEqual(op.check_plan(p,op.manifest(p),d)['exit_code'],code)
    def test_fail_cannot_be_hidden(self):
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(architecture(['retrieval'])),d,'FAIL')
            t=next(t for t in p['tasks'] if t['trials']);t['result']='PASS'
            with self.assertRaisesRegex(ValueError,'FAIL'):op.check_plan(p,op.manifest(p),d)
    def test_unreached_input_not_pass(self):
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(architecture(['retrieval'])),d)
            next(t for t in p['tasks'] if t['trials'])['trials'][0]['reachability']='not_reached'
            with self.assertRaisesRegex(ValueError,'Reachability'):op.check_plan(p,op.manifest(p),d)
    def test_duplicate_trial_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(architecture(['retrieval'])),d);t=next(t for t in p['tasks'] if t['trials']);t['trials']*=2
            with self.assertRaisesRegex(ValueError,'(?i)duplicate'):op.check_plan(p,op.manifest(p),d)
    def test_unknown_cannot_be_completed(self):
        p=op.make_plan(op.profile('rag'));t=next(t for t in p['tasks'] if t['applicability']=='UNKNOWN');t.update(execution='COMPLETED',result='PASS')
        with self.assertRaises(ValueError):op.check_plan(p)
    def test_external_manifest_pins_scope(self):
        p=op.make_plan(architecture());m=op.manifest(p);m['architecture_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'manifest'):op.check_plan(p,m)
    def test_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=complete(op.make_plan(architecture(activities=['DESIGN'])),d);p['evidence'][0]['path']='../outside.txt'
            with self.assertRaises(ValueError):op.check_plan(p,op.manifest(p),d)
    def test_profile_drafts_not_green(self):
        for profile in ('chat','rag','agent','mcp','ml-pipeline','full'):
            self.assertEqual(op.check_plan(op.make_plan(op.profile(profile)))['exit_code'],2)
    def test_markdown_contains_evidence_oracles_originals(self):
        text=op.plan_markdown(op.make_plan(architecture(['llm_generation'])))
        for value in ('Oracle','PI-06','Evidence','Walkthroughs','NOT_RUN'):self.assertIn(value,text)
    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'plan.json';p.write_text('user content')
            self.assertEqual(op.main(['plan','--profile','rag','--out',str(p)]),2);self.assertEqual(p.read_text(),'user content')
    def test_source_boundaries_and_ids(self):
        lib=op.library();self.assertTrue({f'AI-{i:03d}' for i in range(1,41)}<={c['id'] for c in lib['cases']})
        self.assertTrue({f'EX-ORIG-{i:03d}' for i in range(1,45)}<={e['id'] for e in lib['examples']})
        self.assertTrue(all(e['id'].startswith('EX-') for e in lib['examples']))

if __name__=='__main__':unittest.main()
