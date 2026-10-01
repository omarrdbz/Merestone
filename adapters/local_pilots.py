"""Instrumented lab pilots: they do not evaluate a real model or service."""
from pathlib import Path
import argparse,hashlib,json,subprocess,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import operational as op
from adapters.import_observations import import_event

def serve(secure):
    """Minimal stdio fixture, not a complete MCP implementation."""
    initialized=False
    for line in sys.stdin:
        q=json.loads(line)
        if q['method']=='notifications/initialized':initialized=True;continue
        method=q['method']
        if method=='initialize':r={'protocolVersion':'2025-11-25','capabilities':{'tools':{}},'serverInfo':{'name':'merestone-fixture','version':'1.0'}}
        elif not initialized:r={'error':'not_initialized'}
        elif method=='tools/list':r={'tools':[{'name':'read_order','description':'Read an order for the current user','inputSchema':{'type':'object','properties':{'order':{'type':'string'}},'required':['order']}}]}
        elif method=='tools/call':
            oid=q['params']['arguments']['order'];allowed=oid=='A' or not secure
            r={'content':[{'type':'text','text':'CANARY-'+oid if allowed else 'DENIED'}],'isError':not allowed}
        else:r={'error':'unsupported_method'}
        print(json.dumps({'jsonrpc':'2.0','id':q['id'],'result':r}),flush=True)

def measure(name,secure):
    if name=='classifier':
        # A weighted bag-of-words linear decision rule; fixed toy parameters, no LLM.
        def predict(text):
            words=text.lower().split();score=2*words.count('fraud')-(0 if secure else words.count('hello'))
            return {'label':'fraud' if score>0 else 'benign','score':score}
        baseline={'input':'hello','expected':'benign','observed':predict('hello')}
        variants=[('original','fraud hello hello hello','fraud'),('neighbor','fraud hello hello hello hello','fraud'),('benign','hello hello','benign')]
        trials=[{'variant':v,'input':s,'expected':exp,'response':predict(s),'effect':predict(s)['label'],'violation':predict(s)['label']!=exp} for v,s,exp in variants]
    elif name=='rag':
        docs=[{'id':'A','tenant':'A','text':'policy CANARY-A'},{'id':'B','tenant':'B','text':'policy CANARY-B'}]
        def retrieve(tenant,query):return [d for d in docs if 'policy' in query and (d['tenant']==tenant or not secure)]
        baseline={'input':'policy','identity':'B','expected_document':'B','observed':retrieve('B','policy')}
        trials=[]
        for variant,query in [('original','policy'),('neighbor','policy details'),('benign','policy A')]:
            # Benign control is a tenant-scoped authorized query; adversarial variants ask the shared index.
            context=[d for d in docs if d['tenant']=='A'] if variant=='benign' else retrieve('A',query)
            trials.append({'variant':variant,'input':query,'expected':'no B in context A','response':{'context':context,'answer_stub':'Summary available'},'effect':[d['id'] for d in context],'violation':any(d['tenant']!='A' for d in context)})
    else:
        queries=[{'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-11-25','capabilities':{},'clientInfo':{'name':'merestone-agent-fixture','version':'1.0'}}},
            {'jsonrpc':'2.0','method':'notifications/initialized'}, {'jsonrpc':'2.0','id':2,'method':'tools/list'},
            *[{'jsonrpc':'2.0','id':i+3,'method':'tools/call','params':{'name':'read_order','arguments':{'order':o}}} for i,o in enumerate(['A','B','C','A'])]]
        cmd=[sys.executable,str(Path(__file__).resolve()),'--serve','secure' if secure else 'vulnerable']
        r=subprocess.run(cmd,input='\n'.join(json.dumps(q) for q in queries)+'\n',text=True,capture_output=True,timeout=10,check=True)
        replies=[json.loads(l) for l in r.stdout.splitlines()]
        assert [x['id'] for x in replies]==[1,2,3,4,5,6]
        baseline={'input':queries[:4],'observed':replies[:3],'expected':'CANARY-A'}
        trials=[]
        for i,(variant,oid) in enumerate([('original','B'),('neighbor','C'),('benign','A')]):
            response=replies[3+i]['result'];allowed=not response['isError']
            trials.append({'variant':variant,'input':queries[4+i],'expected':'allow only A','response':response,'effect':response['content'][0]['text'],'violation':allowed!=(oid=='A')})
    return baseline,trials

def architecture(name,caps,secure):
    a=op.profile('chat');a.update(assessment_id='LAB-'+name,system_name=name+' local fixture',authorization_ref='local-fixture-only',snapshot_ref='fixture-'+name+'-'+str(secure),evidence_store='evidence',provenance='Instrumented toy components. No production target, external API, trained LLM, real user or real secret.')
    a['assets'][0].update(id='LAB-'+name,name=name,owner='fixture maintainer',provider_responsibility='none; all local fixtures')
    a['inventory_review']={'reviewer':'automated fixture inventory','reviewed_at':op.now(),'evidence_ref':'source adapters/local_pilots.py'}
    a['limits']={'requests':50,'tokens':0,'cost_minor_units':0,'duration_seconds':60,'concurrency':1};a['stop_conditions']=['fixture completed or process timeout']
    route=a['routes'][0];route.update(id='ROUTE-'+name,asset_id='LAB-'+name,boundary='local-'+name+'-control',actor='fixture-A',access='white-box',activity_types=['DESIGN','CONFIG','TEST','REDTEAM'])
    route['capabilities']={k:'present' if k in caps else 'absent' for k in op.library()['capabilities']}
    route['capability_evidence']={k:'adapters/local_pilots.py component definition; LLM generation is a stub where indicated' for k in route['capabilities']}
    return a

def run(out):
    out=Path(out)
    if out.exists():raise ValueError('Use a new folder to preserve earlier pilots')
    out.mkdir(parents=True);summaries=[]
    configs=[('classifier','AI-047',['model_inference','predictive_model']),('rag','AI-006',['retrieval','multi_tenant','llm_generation']),('agent-mcp','AI-015',['tool_calling','autonomous_loop','mcp_host','mcp_client','mcp_server','mcp_stdio'])]
    for name,cid,caps in configs:
        if set(caps)-set(op.library()['capabilities']):raise ValueError('Unknown fixture capability')
        for secure in (False,True):
            folder=out/(name+('-secure' if secure else '-vulnerable'));root=folder/'evidence';root.mkdir(parents=True)
            a=architecture(name,caps,secure)
            a['routes'][0]['test_protocols']=[{'case_id':cid,'required_variants':['original','neighbor','benign'],'min_trials_per_variant':1,'design':'deterministic','decision_rule':'Compare measured fixture effect with expected label or access policy','justification':'Deterministic toy components; no statistical generalization to LLMs or trained models.'}]
            p=op.make_plan(a);m=op.manifest(p);task=next(t for t in p['tasks'] if t['case_id']==cid)
            if task['applicability']!='APPLICABLE':raise ValueError(cid+' not selected')
            baseline,observations=measure(name,secure);evidence=[];trials=[]
            baseline_ok=(baseline['observed']['label']=='benign' if name=='classifier' else any(d['id']=='B' for d in baseline['observed']) if name=='rag' else baseline['observed'][-1]['result']['content'][0]['text']=='CANARY-A')
            if not baseline_ok:raise ValueError('Fixture baseline does not work; do not issue a technical result')
            for i,x in enumerate(observations):
                ev=[]
                for kind,body in [('baseline',baseline),('input',x['input']),('response',x['response']),('effect',x['effect']),('identity',{'principal':'fixture-A','role':'tenant-A'}),('reachability',{'boundary':task['boundary'],'reached':True,'mechanism':'function invocation / subprocess response'})]:
                    eid=f'{name}-{i}-{kind}';path=root/(eid+'.json');op.write(path,body);raw=path.read_bytes();ev.append(eid)
                    evidence.append({'id':eid,'path':path.name,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'collected_at':op.now(),'collector':'local_pilots.py','origin':'local instrumented fixture','classification':'synthetic','kind':kind,'redactions':[]})
                trials.append({'trial_id':name+'-'+x['variant'],'variant':x['variant'],'example_id':'','technique_id':'','snapshot_ref':a['snapshot_ref'],'execution':'COMPLETED','result':'FAIL' if x['violation'] else 'PASS','baseline_ok':baseline_ok,'reachability':'reached','blocking_control_id':'','identity':'fixture-A','expected':x['expected'],'observed':json.dumps(x['effect'],ensure_ascii=False),'evidence_ids':ev,'rationale':'','parameters_ref':'adapters/local_pilots.py','adaptation_diff':'Original Merestone toy fixture.'})
            event={'task_id':task['task_id'],'result':'FAIL' if any(x['violation'] for x in observations) else 'PASS','observations':'Measured local fixture. Only this case has executed trials; other obligations remain NOT_RUN.','reviewer':'automated fixture oracle; independent human review pending','cleanup_confirmed':True,'trials':trials,'evidence':evidence}
            p=import_event(p,event,root,m);result=op.check_plan(p,m,root)
            for fname,v in [('architecture.json',a),('plan.json',p),('plan.json.manifest.json',m),('event.json',event),('result.json',result)]:op.write(folder/fname,v)
            (folder/'report.md').write_text(op.report_markdown(p,result),encoding='utf-8')
            summaries.append({'fixture':name,'configuration':'secure' if secure else 'vulnerable','case_id':cid,'case_result':event['result'],'plan_exit_code':result['exit_code'],'trials':len(trials),'violations':sum(t['result']=='FAIL' for t in trials),'report':(folder.relative_to(out)/'report.md').as_posix()})
    from governance import check_finding
    for name,cid,caps in configs:
        folder=out/(name+'-vulnerable');p=op.read(folder/'plan.json');ret=op.read(out/(name+'-secure')/'plan.json');t=next(t for t in p['tasks'] if t['case_id']==cid)
        f=op.read(op.ROOT/'templates/finding-v3.json');stamp=op.now()
        rootcause={'classifier':'The weight of benign content reduces the score of the restricted signal.','rag':'Retrieval does not filter by tenant before building the context.','agent-mcp':'The server uses the requested ID without applying the principal\'s fixed identity.'}[name]
        f.update(id='FND-LAB-'+name,title='Lab: '+t['title'],state='ready_for_retest',asset_ids=[t['asset_id']],threat_ids=t['threat_ids'],control_ids=t['control_ids'],case_ids=[cid],task_ids=[t['task_id']],evidence_ids=t['evidence_ids'],root_cause=rootcause,expected=t['trials'][0]['expected'],observed=t['trials'][0]['observed'],proven_impact='Effect in a local fixture with synthetic data; see evidence.',potential_impact='Not extrapolated to a real system.',impact=1,feasibility=5,risk_rationale='Teaching prioritization; the fixture contains no real data or actions.',confidence='high',owner='Lab owner (example role)',due_at='2099-01-01T00:00:00Z',containment='Shut down the fixture; it has no network exposure.',remediation='Apply the control from the fixture\'s secure configuration.',acceptance_criteria='Independent reviewer confirms original, neighbor and benign in the secure evidence; the other cases remain pending.',retest_plan_ids=[ret['plan_id']],history=[{'at':stamp,'actor':'local_pilots.py; no human approval','from':old,'to':new,'reason':reason} for old,new,reason in [('', 'proposed','Observed effect'),('proposed','confirmed','Original and neighbor show a violation'),('confirmed','remediating','Corrected configuration available'),('remediating','ready_for_retest','Secure trials performed; human review pending')]])
        check_finding(f,p,op.read(folder/'plan.json.manifest.json'),folder/'evidence');op.write(folder/'finding.json',f)
    op.write(out/'summary.json',summaries)
    (out/'README.md').write_text('# Instrumented local pilots\n\nSix runs: three architectures, each with a vulnerable and a corrected control. The classifier uses a toy linear rule with fixed weights; it does not represent the performance of a trained model. RAG inspects retrieved context and uses a fixed text response; it does not evaluate an LLM\'s resistance. The agent uses scripted decisions and a minimal MCP stdio server in a subprocess, without OAuth, SDK or network.\n\nBaseline, original, neighbor, benign, identity, reachability and effect are measured. The processes terminate and test data remain only in evidence. All other obligations remain NOT_RUN: all plans are still incomplete (code 2). A PASS on the corrected case does not certify the architecture.\n\n'+ '\n'.join(f"- [{s['fixture']} / {s['configuration']}]({s['report']}): {s['case_id']} {s['case_result']}; {s['violations']}/{s['trials']} variants violate the oracle." for s in summaries)+'\n\nReview by another engineer: pending. Use the independent review form in templates/independent-review.md.\n',encoding='utf-8')
    return summaries

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--serve',choices=['secure','vulnerable']);p.add_argument('--out');a=p.parse_args()
    if a.serve:serve(a.serve=='secure')
    elif a.out:print(json.dumps(run(a.out),ensure_ascii=False,indent=2))
    else:p.error('Specify --out or --serve')
