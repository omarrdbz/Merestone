// Client regression tests: Node's standard library only, no browser dependencies.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const html = fs.readFileSync(path.join(__dirname, '../ui/app.html'), 'utf8');
const source = html.match(/<script nonce="__NONCE__">([\s\S]*?)<\/script>/)[1]
  .split('/* ================= start ================= */')[0];

function client() {
  const context = vm.createContext({
    document: {addEventListener() {}, querySelector() {return null}, querySelectorAll() {return []}},
    localStorage: {getItem() {return null}, setItem() {}},
    setTimeout() {}, clearTimeout() {}, window: {},
    btoa: s => Buffer.from(s, 'binary').toString('base64'),
  });
  const run = text => vm.runInContext(text, context);
  run(source);
  run(`
    render=()=>{}; toast=(...args)=>messages.push(args); busy=()=>{};
    const messages=[], calls=[], modals=[];
    openModal=(html)=>modals.push(html); closeModal=()=>{};
    api=async(action,body)=>{calls.push([action,body]);return {};};
    act=async(action,body)=>{calls.push([action,body]);return {};};
    refresh=async()=>{}; gotoTarget=(...args)=>calls.push(['goto',...args]);
    S={items:{authorization:{label:'Permission to test'}},access:['black-box','gray-box','white-box'],activities:{DESIGN:'Review design',TEST:'Tests'},cases:{},
      trust_changes:[{key:'permissions',label:'Permissions',hint:'p'},{key:'identity',label:'Identity',hint:'i'},{key:'authority',label:'Authority',hint:'a'},{key:'data_trust',label:'Data trust',hint:'d'}]};
    ST={workspace:{series:'plan-001'},arch:{
      authorization_ref:'AUTH',snapshot_ref:'v1',evidence_store:'evidence',
      inventory_review:{reviewer:'Reviewer',evidence_ref:'Doc'},assets:[{owner:'Owner'}],
      limits:{requests:10,duration_seconds:60,concurrency:1,tokens:0,cost_minor_units:0},
      threats:[{id:'TH-001',hypothesis:'Complete actor, access, boundary, effect and control',risk:'To be evaluated'}],
      routes:[{id:'ROUTE-1',actor:'User',boundary:'App -> Model',access:'white-box',scope:'in_scope',activity_types:['DESIGN'],test_protocols:[],capabilities:{},threat_ids:['TH-001']}]
    }};
  `);
  return run;
}

test('scope labels are readable and explain the pending obligations', () => {
  const run=client();
  run(`rform(ST.arch.routes[0]).scope='out_of_scope'`);
  const page=run('routeCard()');
  assert.match(page, />Out of scope<\/button>/);
  assert.match(page, /does not count as passing/);
  assert.doesNotMatch(page, />out of_scope</);
});

test('freeze refuses unsaved route edits without sending a plan request', async () => {
  const run=client();run(`rform(ST.arch.routes[0]).scope='out_of_scope'`);
  await run('A.freeze()');
  assert.equal(run(`calls.some(c=>c[0]==='plan')`), false);
  assert.equal(run('messages[0][0]'), 'Save your architecture edits before freezing.');
});

test('readiness, limits and protocols are checked for unsaved changes', () => {
  const run=client();assert.equal(run('unsavedArchitecture().length'),0);
  run(`setF('rd.authorization','NEW');setF('lim.requests','20');F['proto:ROUTE-1']={case:'AI-006',variants:['original'],min:1,design:'deterministic',rule:'rule',why:'why'}`);
  assert.equal(run('unsavedArchitecture().length'),3);
  run(`ST.arch.authorization_ref='NEW';ST.arch.limits.requests=20;ST.arch.routes[0].test_protocols=[{case_id:'AI-006',required_variants:['original'],min_trials_per_variant:1,design:'deterministic',decision_rule:'rule',justification:'why'}]`);
  assert.equal(run('unsavedArchitecture().length'),0);
});

test('invalid blank route edits are retained instead of reporting a false save', async () => {
  const run=client();run(`rform(ST.arch.routes[0]).actor=''`);
  await run(`A.saveRoute({dataset:{route:'ROUTE-1'}})`);
  assert.equal(run('calls.length'),0);
  assert.equal(run(`F['route:ROUTE-1'].actor`),'');
});

test('a valid route scope change is saved in one request with its internal value', async () => {
  const run=client();run(`rform(ST.arch.routes[0]).scope='out_of_scope'`);
  await run(`A.saveRoute({dataset:{route:'ROUTE-1'}})`);
  assert.equal(run('calls.length'),1);
  assert.equal(run('calls[0][0]'),'route');
  assert.equal(run('JSON.stringify(calls[0][1])'),JSON.stringify({op:'edit',route:'ROUTE-1',scope:'out_of_scope'}));
});

for (const phase of ['write', 'refresh']) {
  for (const latest of ['Second edit', '']) {
    test(`route edits during ${phase} survive saving, including reverting to ${JSON.stringify(latest)}`, async () => {
      const run=client();
      run(`
        rform(ST.arch.routes[0]).perms='First edit';
        let finishWrite, finishRefresh, submitted;
        api=(action,body)=>{submitted=body;return new Promise(resolve=>finishWrite=resolve)};
        refresh=async()=>{
          await new Promise(resolve=>finishRefresh=resolve);
          ST.arch.routes[0].actor_permissions=submitted.permissions;
          routeCard(); // refresh renders before the save handler resumes
        };
      `);
      const saving=run(`A.saveRoute({dataset:{route:'ROUTE-1'}})`);
      if (phase==='refresh') {run('finishWrite({})');await Promise.resolve();}
      run(`rform(ST.arch.routes[0]).perms=${JSON.stringify(latest)}`);
      if (phase==='write') {run('finishWrite({})');await Promise.resolve();}
      run('finishRefresh()');await saving;
      assert.equal(run('submitted.permissions'),'First edit');
      assert.equal(run('ST.arch.routes[0].actor_permissions'),'First edit');
      assert.equal(run('rform(ST.arch.routes[0]).perms'),latest);
      assert.equal(run('routeDirty(ST.arch.routes[0])'),true);
      assert.match(run('routeCard()'),/Unsaved: permissions/);
      assert.match(run('messages.at(-1)[1]'),/newer edits.*not saved/i);
      await run('A.freeze()');
      assert.equal(run(`calls.some(c=>c[0]==='plan')`),false);
    });
  }
}

test('a successful save without newer edits clears the draft and uses normalized saved values', async () => {
  const run=client();
  run(`rform(ST.arch.routes[0]).perms='  Read own documents  ';
    refresh=async()=>{ST.arch.routes[0].actor_permissions=calls[0][1].permissions;routeCard()};`);
  await run(`A.saveRoute({dataset:{route:'ROUTE-1'}})`);
  assert.equal(run('rform(ST.arch.routes[0]).perms'),'Read own documents');
  assert.equal(run('routeDirty(ST.arch.routes[0])'),false);
});

test('scope can be saved on a draft route whose actor is still unknown', async () => {
  const run=client();run(`ST.arch.routes[0].actor='to be identified';ST.arch.routes[0].boundary='to be identified';rform(ST.arch.routes[0]).scope='out_of_scope'`);
  await run(`A.saveRoute({dataset:{route:'ROUTE-1'}})`);
  assert.equal(run(`calls[0][1].scope`),'out_of_scope');
  assert.equal(run(`'actor' in calls[0][1] || 'path' in calls[0][1]`),false);
});

test('blocked scope points to scope on the correct route; no access has a separate label', () => {
  const run=client();run(`facts=()=>''`);
  const page=run(`workTab({route_id:'ROUTE-1',scope:'out_of_scope',access:'white-box',bucket:'TODO'})`);
  assert.match(page,/data-route="ROUTE-1" data-target="fld-scope"/);
  assert.equal(run(`accessLabel({scope:'in_scope',access:'none'})`),'No access');
  assert.equal(run(`accessLabel({scope:'in_scope',access:'unknown'})`),'Access unknown');
});

test('repeated submit events cannot issue duplicate writes', async () => {
  const run=client();run(`let release;let writes=0;A.record=()=>{writes++;return new Promise(r=>release=r)}`);
  const first=run(`dispatch({dataset:{act:'record'}})`);
  await run(`dispatch({dataset:{act:'record'}})`);
  assert.equal(run('writes'),1);
  run('release()');await first;
  run(`A.record=async()=>{writes++}`);
  await run(`dispatch({dataset:{act:'record'}})`);
  assert.equal(run('writes'),2);
});

test('a failed write releases the submit guard and reports the error', async () => {
  const run=client();run(`A.record=async()=>{throw new Error('Offline')}`);
  await run(`dispatch({dataset:{act:'record'}})`);
  assert.equal(run('writing'),false);
  assert.equal(run('messages[0][0]'),'Offline');
});

test('filter tab counts match the filtered task list', () => {
  const run=client();run(`
    ST.plan={series:'plan-001',created_at:'2026-10-13',tasks:[
      {alias:'AI-006@R1',case_id:'AI-006',title:'Retrieval ACL',module:'RAG',activity:'TEST',bucket:'TODO',access:'white-box',scope:'in_scope',trials:[]},
      {alias:'CORE-001@R1',case_id:'CORE-001',title:'Scope',module:'CORE',activity:'DESIGN',bucket:'TODO',access:'white-box',scope:'in_scope',trials:[]}
    ]};UI.module='RAG';
  `);
  const page=run('boardView()');
  assert.match(page,/Selected<span>1<\/span>/);
  assert.match(page,/To do<span>1<\/span>/);
  assert.doesNotMatch(page,/CORE-001@R1/);
});

test('evidence replaced while hashing keeps the latest file', async () => {
  const run=client();run(`let resolveOld;const old={name:'old.txt',size:1,arrayBuffer:()=>new Promise(r=>resolveOld=r)};const latest={name:'new.txt',size:1,arrayBuffer:async()=>new Uint8Array([2]).buffer}`);
  const first=run(`addFile('rec:AI-006','response',old)`);
  await run(`addFile('rec:AI-006','response',latest)`);
  run(`resolveOld(new Uint8Array([1]).buffer)`);await first;
  assert.equal(run(`F['rec:AI-006'].ev.response.name`),'new.txt');
});

test('oversized evidence does not leave an occupied hashing slot', async () => {
  const run=client();await run(`addFile('rec:AI-006','response',{name:'large.bin',size:41*1024*1024})`);
  assert.equal(run(`!!F['rec:AI-006']?.ev?.response`),false);
  assert.match(run('messages[0][0]'),/larger than 40 MB/);
});

test('all CSS theme variables used by the interface are defined', () => {
  const style=html.match(/<style>([\s\S]*?)<\/style>/)[1];
  const defined=new Set([...style.matchAll(/(--[\w-]+)\s*:/g)].map(m=>m[1]));
  for(const [,name] of html.matchAll(/var\((--[\w-]+)\)/g))assert.ok(defined.has(name),name);
});

/* ---------- route editor: flow, example, trust boundaries, preview and plan ---------- */

test('the example fills only the draft, never capabilities, and asks before replacing text', async () => {
  const run=client();run(`ST.arch.routes[0].capabilities={retrieval:'unknown'}`);
  run(`A.exLoad({dataset:{route:'ROUTE-1'}})`);                 // the route already has an actor and a path
  assert.equal(run('modals.length'),1);
  assert.match(run('modals[0]'),/Replace what this route says with the example/);
  assert.equal(run(`rform(ST.arch.routes[0]).actor`),'User'); // nothing replaced before confirming
  run(`A.exLoadGo({dataset:{route:'ROUTE-1'}})`);
  const f=run(`JSON.stringify(rform(ST.arch.routes[0]))`);
  assert.match(f,/Authenticated user of customer A/);
  assert.match(f,/Read only customer A documents/);
  assert.match(f,/Customer B documents are never retrieved/);
  assert.equal(run(`ST.arch.routes[0].capabilities.retrieval`),'unknown');
  assert.equal(run(`rform(ST.arch.routes[0]).access`),'white-box');   // access, activities and scope are not loaded
  assert.equal(run('calls.filter(c=>c[0]!==\'goto\').length'),0);       // nothing is written
  assert.match(run('routeCard()'),/Example loaded: illustrative values/);
  assert.equal(run('rdiff(rform(ST.arch.routes[0]),rbase(ST.arch.routes[0])).sort().join()'),'actor,check,hops,perms,trust');
});

test('the example loads at once into an empty route', () => {
  const run=client();run(`ST.arch.routes[0].actor='To be identified';ST.arch.routes[0].boundary='To be identified'`);
  run(`A.exLoad({dataset:{route:'ROUTE-1'}})`);
  assert.equal(run('modals.length'),0);
  assert.equal(run(`rform(ST.arch.routes[0]).hops.join(' > ')`),'App > Document search > Model > Answer');
});

test('connections are drawn as plain steps until a trust boundary is marked', () => {
  const run=client();run(`ST.arch.routes[0].boundary='App -> Search -> Model'`);
  let svg=run(`mapSvg(rform(ST.arch.routes[0]),'ROUTE-1')`);
  assert.doesNotMatch(svg,/class="stone/);
  assert.equal((svg.match(/class="hand/g)||[]).length,3);
  assert.match(svg,/not marked as a trust boundary/);
  run(`A.trust({dataset:{route:'ROUTE-1',j:'2',k:'data_trust'}})`);
  svg=run(`mapSvg(rform(ST.arch.routes[0]),'ROUTE-1')`);
  assert.equal((svg.match(/class="stone/g)||[]).length,1);
  assert.match(svg,/Search to Model: trust boundary 1, Data trust/);
  assert.match(run('routeCard()'),/1 marked of 3 steps/);
});

test('trust marks are saved by component name in the same request as the path', async () => {
  const run=client();run(`const f=rform(ST.arch.routes[0]);f.hops=['App','Search','Model'];f.trust=[{changes:['identity'],note:' session '},{changes:[],note:''},{changes:['data_trust'],note:''}]`);
  await run(`A.saveRoute({dataset:{route:'ROUTE-1'}})`);
  const body=JSON.parse(run('JSON.stringify(calls[0][1])'));
  assert.equal(body.path,'App -> Search -> Model');
  assert.deepEqual(body.trust,[{from:'actor',to:'App',changes:['identity'],note:'session'},{from:'Search',to:'Model',changes:['data_trust'],note:''}]);
});

test('saved marks round-trip without unsaved changes; stale marks are reported', () => {
  const run=client();run(`ST.arch.routes[0].trust_boundaries=[{from:'actor',to:'App',changes:['identity']},{from:'Gone',to:'Model',changes:['authority']}]`);
  assert.equal(run('routeDirty(ST.arch.routes[0])'),false);
  assert.equal(run(`rbase(ST.arch.routes[0]).trust.map(m=>m.changes.join()).join('|')`),'identity|');
  assert.equal(run('orphanMarks(ST.arch.routes[0]).length'),1);
  assert.match(run('routeCard()'),/1 saved mark does not match this path \(Gone → Model\)/);
});

test('removing a component clears the marks of the steps it joined', () => {
  const run=client();run(`const f=rform(ST.arch.routes[0]);f.hops=['A','B','C'];f.trust=[{changes:['identity'],note:''},{changes:['permissions'],note:''},{changes:['authority'],note:''}]`);
  run(`A.hopDel({dataset:{route:'ROUTE-1',i:'1'}})`);
  assert.equal(run(`rform(ST.arch.routes[0]).hops.join()`),'A,C');
  assert.equal(run(`rform(ST.arch.routes[0]).trust.map(m=>m.changes.join()).join('|')`),'identity|');
  assert.match(run('messages.at(-1)[0]'),/marks next to B were cleared/);
});

test('trust and permission edits block freezing until they are saved', async () => {
  const run=client();run(`A.trust({dataset:{route:'ROUTE-1',j:'0',k:'identity'}})`);
  assert.equal(run('unsavedArchitecture().length'),1);
  await run('A.freeze()');
  assert.equal(run(`calls.some(c=>c[0]==='plan')`),false);
  run(`delete F['route:ROUTE-1'];rform(ST.arch.routes[0]).perms='Read own documents'`);
  assert.equal(run('unsavedArchitecture()[0].label'),'Route ROUTE-1');
  assert.match(run('routeCard()'),/Unsaved: permissions/);
});

test('the check comes from the route threat; template text counts as empty', () => {
  const run=client();
  assert.equal(run('routeCheck(ST.arch.routes[0])'),'');
  run(`ST.arch.threats[0].hypothesis='Customer B documents are never retrieved'`);
  assert.equal(run('rbase(ST.arch.routes[0]).check'),'Customer B documents are never retrieved');
});

test('discarding restores the saved route without writing', () => {
  const run=client();run(`rform(ST.arch.routes[0]).actor='Someone else'`);
  run(`A.routeDiscard({dataset:{route:'ROUTE-1'}})`);
  assert.match(run('modals[0]'),/Discard unsaved changes on ROUTE-1/);
  run(`A.routeDiscardGo({dataset:{route:'ROUTE-1'}})`);
  assert.equal(run('routeDirty(ST.arch.routes[0])'),false);
  assert.equal(run('calls.length'),0);
});

test('the effect panel separates saved values from unsaved activities', () => {
  const run=client();run(`
    const sum=(n,a)=>({total:n,APPLICABLE:a,UNKNOWN:n-a,NOT_APPLICABLE:0,activities:{DESIGN:{APPLICABLE:a,UNKNOWN:n-a,NOT_APPLICABLE:0}},
      examples:[{alias:'CORE-001@ROUTE-1',title:'Scope',activity:'DESIGN',applicability:'APPLICABLE',why:{core:true}},{alias:'AI-006@ROUTE-1',title:'Retrieval ACL',activity:'TEST',applicability:'UNKNOWN',why:{unknown:['retrieval']}}]});
    ST.preview={'ROUTE-1':sum(9,9)};`);
  let card=run('routeCard()');
  assert.match(card,/Saved route/);assert.match(card,/<b class="big">9<\/b> tasks on ROUTE-1/);
  assert.match(card,/common core, needs no capability/);assert.match(card,/pending · <code>retrieval<\/code> unknown/);
  assert.equal(run('UI.pvReq'),null);                                  // no draft: no extra request
  run(`rform(ST.arch.routes[0]).activities=['DESIGN','TEST']`);
  card=run('routeCard()');
  assert.equal(run('UI.pvReq'),'ROUTE-1|DESIGN,TEST');                   // the engine is asked for the draft
  assert.match(card,/Includes unsaved activities/);assert.match(card,/Calculating with the engine/);
  run(`UI.pv['ROUTE-1|DESIGN,TEST']=sum(40,12)`);
  card=run('routeCard()');
  assert.match(card,/<h4>Saved<\/h4><p><b class="big">9<\/b>/);
  assert.match(card,/<h4>With your unsaved activities \(\+31 tasks\)<\/h4><p><b class="big">40<\/b>/);
});

test('a route in the frozen plan cannot be removed; out of scope is offered instead', () => {
  const run=client();run(`ST.arch.routes.push({...ST.arch.routes[0],id:'ROUTE-2'});ST.plan={series:'plan-001',tasks:[],routes:[{id:'ROUTE-1',capabilities:{}}]};ST.workspace.series='plan-001'`);
  run(`A.routeRemove({dataset:{route:'ROUTE-1'}})`);
  assert.match(run('modals[0]'),/ROUTE-1 is part of the frozen plan/);
  assert.match(run('modals[0]'),/data-act="routeOutOfScope"/);
  run(`A.routeOutOfScope({dataset:{route:'ROUTE-1'}})`);
  assert.equal(run(`rform(ST.arch.routes[0]).scope`),'out_of_scope');
  run(`A.routeRemove({dataset:{route:'ROUTE-2'}})`);
  assert.match(run('modals[1]'),/Remove ROUTE-2\?/);
  assert.match(run('modals[1]'),/No plan, result or evidence file is changed/);
  assert.equal(run('calls.filter(c=>c[0]===\'route\').length'),0);
});

test('a task explains why it is in the plan using the frozen route', () => {
  const run=client();run(`
    S.cases={'AI-006':{applies_if:[['retrieval','multi_tenant']]},'CORE-001':{applies_if:[[]]}};
    ST.plan={series:'plan-001',tasks:[],routes:[{id:'ROUTE-1',capabilities:{retrieval:'present',multi_tenant:'present'},actor_permissions:'Read own documents',trust_boundaries:[{from:'actor',to:'App',changes:['identity']}],check:'No B documents'}]};
    ST.arch.routes[0].capabilities={retrieval:'absent'};`);       // later edits must not rewrite the explanation
  const why=run(`whyTask({route_id:'ROUTE-1',case_id:'AI-006',activity:'TEST',applicability:'APPLICABLE',actor:'User',boundary:'App -> Model'})`);
  assert.match(why,/ROUTE-1 includes tests \(TEST\)/);
  assert.match(why,/<code>retrieval<\/code> \+ <code>multi_tenant<\/code> were marked present on ROUTE-1/);
  assert.match(why,/Read own documents/);assert.match(why,/Actor → App <span class="faint">\(identity\)/);assert.match(why,/No B documents/);
  assert.match(run(`whyTask({route_id:'ROUTE-1',case_id:'CORE-001',activity:'DESIGN',applicability:'APPLICABLE',actor:'User',boundary:'App'})`),/common core/);
});

test('adding a route validates the ID before writing', async () => {
  const run=client();run(`setF('radd.id','bad id!')`);
  await run('A.routeAddGo()');
  assert.equal(run('calls.length'),0);assert.match(run('messages[0][0]'),/letters, digits/);
  run(`setF('radd.id','route-1')`);await run('A.routeAddGo()');
  assert.equal(run('calls.length'),0);assert.match(run('messages[1][0]'),/already exists/);
  run(`setF('radd.id','orders')`);await run('A.routeAddGo()');
  assert.equal(run('JSON.stringify(calls[0])'),JSON.stringify(['route',{op:'add',route:'ORDERS',like:'ROUTE-1',copy_caps:false}]));
});

test('a protocol form that was only opened is not an unsaved change', () => {
  const run=client();
  run(`ns('proto:ROUTE-1',()=>({case:'AI-006',variants:['original','benign'],min:1,design:'deterministic',rule:'',why:''}))`);
  assert.equal(run('unsavedArchitecture().length'),0);
  run(`F['proto:ROUTE-1'].rule='No B chunk reaches the context'`);
  assert.equal(run('unsavedArchitecture()[0].label'),'Protocol AI-006');
});

test('a refused save keeps the draft and says why in the save status', async () => {
  const run=client();run(`rform(ST.arch.routes[0]).hops=['App','']`);
  await run(`A.saveRoute({dataset:{route:'ROUTE-1'}})`);
  assert.equal(run('calls.length'),0);
  assert.match(run('routeCard()'),/Not saved: Describe the actor and every component before saving\. Your edits are kept\./);
  run(`api=async()=>{throw Object.assign(new Error('Route ROUTE-1 changed elsewhere'),{hint:'Reload it'})};rform(ST.arch.routes[0]).hops=['App','Model2']`);
  await run(`A.saveRoute({dataset:{route:'ROUTE-1'}})`);
  assert.match(run('routeCard()'),/Not saved: Route ROUTE-1 changed elsewhere Reload it\. Your edits are kept\./);
  assert.equal(run(`rform(ST.arch.routes[0]).hops.join()`),'App,Model2');
});

test('the save status says whether the saved route matches the frozen plan', () => {
  const run=client();
  assert.match(run('routeCard()'),/<span class="ss ok">Saved<\/span>/);
  run(`ST.plan={series:'plan-001',tasks:[],routes:[{id:'ROUTE-1',actor:'User',boundary:'App -> Model',access:'white-box',scope:'in_scope',activity_types:['DESIGN'],capabilities:{},capability_evidence:{},test_protocols:[],trust_boundaries:[],actor_permissions:'',check:''}]};ST.workspace.series='plan-001'`);
  assert.match(run('routeCard()'),/Saved · matches plan-001/);
  run(`ST.arch.routes[0].actor_permissions='Read own documents'`);
  assert.match(run('routeCard()'),/Saved · differs from plan-001 until you freeze a revision/);
  run(`ST.plan.routes=[]`);
  assert.match(run('routeCard()'),/Saved · not in plan-001 until you freeze a revision/);
});

for (const edit of [
  `ST.arch.routes[0].actor_permissions='Read own documents'`,
  `ST.arch.routes[0].trust_boundaries=[{from:'actor',to:'App',changes:['identity']}]`,
  `ST.arch.threats[0].hypothesis='No cross-customer documents'`,
]) {
  test(`the effect panel reports descriptive changes without task changes: ${edit}`, () => {
    const run=client();
    run(`ST.plan={series:'plan-001',stale:false,tasks:[],routes:[{...JSON.parse(JSON.stringify(ST.arch.routes[0])),check:''}]};
      ST.revision={routes:{'ROUTE-1':{added:0,removed:0,changed:0,results:0}}};`);
    assert.match(run('routeCard()'),/The saved route matches it\./);
    run(`${edit};ST.plan.stale=true`);
    const page=run('routeCard()');
    assert.match(page,/Saved · differs from plan-001/);
    assert.match(page,/The tasks are unchanged, but saved route information differs/);
    assert.doesNotMatch(page,/The saved route matches it\./);
    run(`ST.revision.routes['ROUTE-1'].changed=2`);
    assert.match(run('routeCard()'),/update 2/);
    run(`ST.plan.routes=[];ST.revision.routes['ROUTE-1'].added=3`);
    assert.match(run('routeCard()'),/Not in plan-001 yet/);
  });
}
