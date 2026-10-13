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
    document: {addEventListener() {}},
    localStorage: {getItem() {return null}, setItem() {}},
    setTimeout() {}, clearTimeout() {}, window: {},
    btoa: s => Buffer.from(s, 'binary').toString('base64'),
  });
  const run = text => vm.runInContext(text, context);
  run(source);
  run(`
    render=()=>{}; toast=(...args)=>messages.push(args); busy=()=>{};
    const messages=[], calls=[];
    api=async(action,body)=>{calls.push([action,body]);return {};};
    act=async(action,body)=>{calls.push([action,body]);return {};};
    refresh=async()=>{}; gotoTarget=(...args)=>calls.push(['goto',...args]);
    S={items:{authorization:{label:'Permission to test'}},access:['black-box','gray-box','white-box'],activities:{DESIGN:'Review design'},cases:{}};
    ST={workspace:{series:'plan-001'},arch:{
      authorization_ref:'AUTH',snapshot_ref:'v1',evidence_store:'evidence',
      inventory_review:{reviewer:'Reviewer',evidence_ref:'Doc'},assets:[{owner:'Owner'}],
      limits:{requests:10,duration_seconds:60,concurrency:1,tokens:0,cost_minor_units:0},
      routes:[{id:'ROUTE-1',actor:'User',boundary:'App -> Model',access:'white-box',scope:'in_scope',activity_types:['DESIGN'],test_protocols:[],capabilities:{}}]
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

test('a valid route scope change is persisted with its internal value', async () => {
  const run=client();run(`rform(ST.arch.routes[0]).scope='out_of_scope'`);
  await run(`A.saveRoute({dataset:{route:'ROUTE-1'}})`);
  assert.equal(run(`calls[0][1].value`),'out_of_scope');
  assert.equal(run(`calls[0][1].route`),'ROUTE-1');
});

test('scope can be saved on a draft route whose actor is still unknown', async () => {
  const run=client();run(`ST.arch.routes[0].actor='to be identified';ST.arch.routes[0].boundary='to be identified';rform(ST.arch.routes[0]).scope='out_of_scope'`);
  await run(`A.saveRoute({dataset:{route:'ROUTE-1'}})`);
  assert.equal(run(`calls[0][1].field`),'scope');
  assert.equal(run(`calls[0][1].value`),'out_of_scope');
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
