"""merestone: workspace-based command line for Merestone.

A friendly layer over the frozen engine (operational.py, governance.py and the
observation importer). Every command reads and writes the same JSON records,
and check-plan remains the source of truth: this module never relaxes a rule,
it only removes manual bookkeeping (paths, hashes, IDs, JSON editing).
Standard library only; no network access.
"""
from __future__ import annotations
import argparse, difflib, getpass, hashlib, json, os, re, shutil, sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jsonutil
import operational as op
import governance as gov
from adapters.import_observations import import_event

WS_FILE = 'merestone.json'
PROFILES = ('chat', 'rag', 'agent', 'mcp', 'ml-pipeline', 'full')
TECH_KINDS = ('baseline', 'input', 'response', 'effect', 'identity', 'reachability')
EVIDENCE_KINDS = TECH_KINDS + ('review', 'configuration', 'snapshot', 'metric')
ACCESS = ('black-box', 'gray-box', 'white-box', 'unknown', 'none')
DESIGNS = ('deterministic', 'stochastic-fixed', 'adaptive-exploration')
YES = {'y', 'yes', 's', 'si', 'sí', 'present', 'p', 'true'}
NO = {'n', 'no', 'absent', 'a', 'false'}
UNK = {'', '?', 'u', 'unknown', 'dk', "don't know", 'ns'}

# Plain-language interview: each answer sets the listed capabilities.
GUIDE = [
    ('Does it generate text with a language model (LLM)?', ['llm_generation', 'model_inference']),
    ('Does it search documents or a knowledge base to answer (RAG)?', ['retrieval']),
    ('Do several customers, teams or tenants share the same system?', ['multi_tenant']),
    ('Can it call tools, functions or APIs by itself?', ['tool_calling']),
    ('Can those tools change things (send messages, write data, pay)?', ['effectful_operations']),
    ('Does a human have to approve some actions before they run?', ['human_approval']),
    ('Does it remember information between conversations or sessions?', ['persistent_memory', 'conversation_storage']),
    ('Does it work autonomously in loops or delegate to other agents?', ['autonomous_loop', 'delegation']),
    ('Does it connect to MCP servers (as a client or host)?', ['mcp_client', 'mcp_host']),
    ('Does it expose its own MCP server?', ['mcp_server']),
    ('Is its output rendered as HTML in a browser?', ['html_rendering']),
    ('Is its output turned into SQL queries?', ['text_to_sql']),
    ('Is its output executed as code?', ['code_execution']),
    ('Does it accept images, audio or uploaded files?', ['multimodal_input']),
    ('Does it fetch URLs or otherwise reach the internet?', ['network_egress']),
    ('Do you train or fine-tune models for it?', ['training', 'fine_tuning']),
]

FIX = {  # readiness gap -> command that resolves it
    'authorization_ref': 'merestone set authorization "<ticket or signed scope>"',
    'snapshot_ref': 'merestone set snapshot "<app, model, prompt and index versions>"',
    'evidence_store': 'merestone set evidence-store "<where evidence is kept>"',
    'inventory_review.reviewer': 'merestone set reviewer "<who reviewed the inventory>"   (also records the date)',
    'inventory_review.reviewed_at': 'merestone set reviewer "<who reviewed the inventory>"   (also records the date)',
    'inventory_review.evidence_ref': 'merestone set inventory-evidence "<document or interview>"',
    'stop_conditions': 'merestone set stop "<when testing must stop>"',
    'limits': 'merestone set limits requests=200 duration=3600 concurrency=1',
    'core_design_missing': 'merestone set activities DESIGN,CONFIG,TEST',
}
ENGINE_HINTS = [
    (r'Existing file|do not overwrite|Existing output', 'Merestone never overwrites records. Use a new name or folder.'),
    (r'Architecture modified without migration', 'Freeze a revision: merestone plan --reason "<why>" --approver "<who>"'),
    (r'pending applicability, access or scope', 'Set the route access (merestone set access gray-box) and freeze a revision with merestone plan --reason ... --approver ...'),
    (r'snapshot different from the plan', 'Trials must use the plan snapshot. Set it before planning: merestone set snapshot "..."'),
    (r'PASS with incomplete planned sample', 'Record every required variant first; see: merestone show <task>'),
    (r'Incomplete technical evidence', 'A decided trial needs baseline, input, response, effect, identity and reachability evidence.'),
    (r'Invalid evidence hash/size', 'An evidence file changed after it was recorded. Restore it; record new material as a new trial.'),
    (r'Decided test without frozen depth', 'Define a test protocol before planning: merestone protocol <case> --variants ... --rule ... --why ...'),
    (r'Test without trials/cleanup', 'Confirm cleanup with --cleanup-confirmed when deciding.'),
    (r'Different catalog snapshot', 'The catalog changed since this plan. Keep the original framework version or start a new plan.'),
]


class UserError(Exception):
    def __init__(self, msg, hint=''):
        super().__init__(msg); self.hint = hint


# ---------- output ----------
class Style:
    on = False
    @classmethod
    def c(cls, code, s): return f'\033[{code}m{s}\033[0m' if cls.on else str(s)
    bold = classmethod(lambda cls, s: cls.c('1', s)); dim = classmethod(lambda cls, s: cls.c('2', s))
    red = classmethod(lambda cls, s: cls.c('31', s)); green = classmethod(lambda cls, s: cls.c('32', s))
    yellow = classmethod(lambda cls, s: cls.c('33', s)); teal = classmethod(lambda cls, s: cls.c('36', s))

S = Style
def out(s=''): print(s)
def heading(s): out(S.bold(s))
def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def safe(s): return re.sub(r'[^A-Za-z0-9._-]+', '-', s).strip('-')
def code_label(code): return {0: S.green('0  complete, no FAIL'), 1: S.red('1  complete, with FAIL'), 2: S.yellow('2  incomplete or unverified')}[code]
def state(v):
    v = v.strip().lower()
    if v in YES: return 'present'
    if v in NO: return 'absent'
    if v in UNK: return 'unknown'
    raise UserError(f'Not a capability state: "{v}"', 'Use present/absent/unknown (or yes/no/?).')


# ---------- workspace ----------
class Workspace:
    def __init__(self, root):
        self.root = Path(root).resolve(); self.cfg = op.read(self.root / WS_FILE)
    @classmethod
    def find(cls, start=None):
        p = Path(start or os.getcwd()).resolve()
        for d in [p, *p.parents]:
            if (d / WS_FILE).is_file(): return cls(d)
        children = sorted(c.name for c in p.iterdir() if c.is_dir() and (c / WS_FILE).is_file()) if p.is_dir() else []
        if children:
            raise UserError('This folder is not a workspace, but it contains: ' + ', '.join(children),
                            f'Enter it first:  cd {children[0]}   (or pass --workspace {children[0]})')
        raise UserError('No Merestone workspace found in this folder or its parents.',
                        'Create one: merestone new <folder> --profile rag --guided   (or pass --workspace <folder>)')
    def p(self, rel):
        q = Path(rel); return q if q.is_absolute() else self.root / q
    @property
    def evidence_root(self): return self.p(self.cfg['evidence_dir'])
    def arch(self): return op.read(self.p(self.cfg['architecture']))
    def save_arch(self, a):
        op.validate_architecture(a); jsonutil.write_json(self.p(self.cfg['architecture']), a)
    def save(self): jsonutil.write_json(self.root / WS_FILE, self.cfg)
    def log(self, action, file=''):
        self.cfg.setdefault('history', []).append({'at': now(), 'action': action, 'file': file}); self.save()
    def has_plan(self): return bool(self.cfg.get('plan'))
    def plan(self):
        if not self.has_plan(): raise UserError('This workspace has no plan yet.', 'Freeze one: merestone plan')
        return op.read(self.p(self.cfg['plan']))
    def manifest(self): return op.read(self.p(self.cfg['manifest']))
    def check(self, plan=None):
        plan = plan or self.plan(); return plan, op.check_plan(plan, self.manifest(), self.evidence_root)
    def staging(self, task_id):
        return self.root / 'staging' / (task_id + '.json')
    def next_record(self, series):
        n = 1 + sum(1 for x in (self.root / 'plans').glob(series + '.r*.json'))
        return f'plans/{series}.r{n:03d}.json'


def ws_from(a): return Workspace(a.workspace) if a.workspace else Workspace.find()
def routes_of(arch, route):
    if route:
        r = [x for x in arch['routes'] if x['id'] == route]
        if not r: raise UserError(f'Unknown route {route}.', 'Routes: ' + ', '.join(x['id'] for x in arch['routes']))
        return r
    return arch['routes']


# ---------- task aliases ----------
def alias(t): return f"{t['case_id']}@{t['route_id']}"
def resolve(plan, key):
    tasks = plan['tasks']
    hit = [t for t in tasks if key in (t['task_id'], alias(t))]
    if not hit: hit = [t for t in tasks if t['case_id'] == key]
    if len(hit) == 1: return hit[0]
    if len(hit) > 1: raise UserError(f'"{key}" matches {len(hit)} tasks.', 'Use CASE@ROUTE, e.g. ' + ', '.join(alias(t) for t in hit[:3]))
    close = difflib.get_close_matches(key, sorted({alias(t) for t in tasks} | {t['case_id'] for t in tasks}), n=3)
    raise UserError(f'No task "{key}" in this plan.', ('Did you mean: ' + ', '.join(close)) if close else 'List them: merestone tasks')
def task_state(t):
    if t.get('exclusion'): return 'EXCLUDED'
    if t['result']: return t['result']
    if t['applicability'] != 'APPLICABLE': return t['applicability']
    return t['execution']


# ---------- commands: setup ----------
def guided(arch, ask=None):
    ask = ask or (lambda prompt: input(prompt))
    out(S.bold('\nA few questions about the system. Answer y (yes), n (no) or ? (not sure).'))
    out(S.dim('Unsure answers stay "unknown" and remain in the plan: unknown is not absent.\n'))
    caps = {}
    for q, keys in GUIDE:
        while True:
            try: v = state(ask(f'  {q} [y/n/?] ')); break
            except UserError: out(S.yellow('    Please answer y, n or ?'))
        for k in keys: caps[k] = v
    source = ask('\n  Where do these answers come from? (e.g. "architecture doc v2", "interview with the owner") ').strip()
    name = ask('  System name (optional): ').strip()
    for r in arch['routes']:
        for k, v in caps.items():
            r['capabilities'][k] = v
            if v != 'unknown' and source: r['capability_evidence'][k] = source
            elif v == 'unknown': r['capability_evidence'].pop(k, None)
    if name: arch['system_name'] = name
    return caps


def cmd_new(a):
    root = Path(a.folder)
    fw = op.ROOT.resolve(); target = root.resolve()
    if (target == fw or fw in target.parents) and not a.inside_framework:
        raise UserError('Workspaces hold evidence, so they should live outside the framework folder (and never be committed).',
                        f'Use a folder outside it, e.g.:  merestone new "{fw.parent / "assessments" / root.name}" --profile {a.profile}'
                        '   (or --inside-framework to override)')
    if root.exists() and any(root.iterdir()):
        raise UserError(f'"{root}" already exists and is not empty.', 'Choose a new folder: Merestone never overwrites assessment records.')
    arch = op.profile(a.profile)
    arch['assessment_id'] = safe(a.id or root.resolve().name).upper() or 'ASSESSMENT'
    if a.name: arch['system_name'] = a.name
    arch['evidence_store'] = 'evidence/ (workspace store, hashed on record)'
    if a.guided: guided(arch)
    op.validate_architecture(arch)
    for d in ('evidence', 'plans', 'manifests', 'reports', 'staging'): (root / d).mkdir(parents=True, exist_ok=True)
    jsonutil.write_json(root / 'architecture.json', arch)
    manifest_dir = a.manifest_dir or 'manifests'
    jsonutil.write_json(root / WS_FILE, {'merestone_workspace': 1, 'framework_version': op.VERSION, 'profile': a.profile,
        'architecture': 'architecture.json', 'evidence_dir': 'evidence', 'manifest_dir': manifest_dir,
        'plan': None, 'manifest': None, 'series': None, 'history': [{'at': now(), 'action': 'created', 'file': 'architecture.json'}]})
    ws = Workspace(root)
    out(S.green(f'Created workspace {root}') + S.dim(f'  (profile: {a.profile})'))
    out(S.dim('The profile is a draft, not a statement about your system.\n'))
    show_status_arch(ws)
    return 0


def cmd_caps(a):
    ws = ws_from(a); arch = ws.arch(); lib_caps = op.library()['capabilities']
    if not a.assign:
        for r in routes_of(arch, a.route):
            heading(f'{r["id"]}  ({r["boundary"]})')
            for st, color in (('present', S.green), ('absent', S.dim), ('unknown', S.yellow)):
                keys = sorted(k for k, v in r['capabilities'].items() if v == st)
                out(f'  {color(st.upper()):<20} {len(keys):>2}  ' + ', '.join(keys))
            missing = [k for k, v in r['capabilities'].items() if v != 'unknown' and not r['capability_evidence'].get(k, '').strip()]
            if missing: out(S.yellow(f'  {len(missing)} without a source: ') + ', '.join(sorted(missing)) + S.dim('  -> add --source "..."'))
        out(S.dim('\nChange: merestone caps retrieval=present tool_calling=absent --source "architecture doc v2"'))
        return 0
    changes = {}
    for item in a.assign:
        if '=' not in item: raise UserError(f'"{item}" is not NAME=STATE.', 'Example: merestone caps retrieval=present')
        k, v = item.split('=', 1); k = k.strip()
        if k not in lib_caps:
            close = difflib.get_close_matches(k, lib_caps, n=3)
            raise UserError(f'Unknown capability "{k}".', ('Did you mean: ' + ', '.join(close)) if close else 'See: merestone caps')
        changes[k] = state(v)
    for r in routes_of(arch, a.route):
        for k, v in changes.items():
            r['capabilities'][k] = v
            if v == 'unknown': r['capability_evidence'].pop(k, None)
            elif a.source: r['capability_evidence'][k] = a.source
    ws.save_arch(arch); ws.log('caps ' + ' '.join(a.assign), 'architecture.json')
    out(S.green('Updated: ') + ', '.join(f'{k}={v}' for k, v in changes.items()))
    if not a.source and any(v != 'unknown' for v in changes.values()):
        out(S.yellow('Note: present/absent needs a source before the plan can close. ') + S.dim('Add --source "<document or interview>"'))
    stale_note(ws)
    return 0


def cmd_set(a):
    ws = ws_from(a); arch = ws.arch(); f, vals = a.field, a.value
    if not vals: raise UserError(f'"set {f}" needs a value.', 'Example: merestone set authorization "TICKET-123"')
    v = ' '.join(vals)
    simple = {'authorization': 'authorization_ref', 'snapshot': 'snapshot_ref', 'evidence-store': 'evidence_store', 'name': 'system_name'}
    if f in simple: arch[simple[f]] = v
    elif f == 'reviewer':
        arch['inventory_review']['reviewer'] = v
        if not arch['inventory_review']['reviewed_at']: arch['inventory_review']['reviewed_at'] = now()
    elif f == 'reviewed-at': op.timestamp(v); arch['inventory_review']['reviewed_at'] = v
    elif f == 'inventory-evidence': arch['inventory_review']['evidence_ref'] = v
    elif f == 'stop': arch['stop_conditions'].append(v)
    elif f == 'owner':
        for x in arch['assets']: x['owner'] = v
    elif f == 'limits':
        keys = {'requests': 'requests', 'tokens': 'tokens', 'cost': 'cost_minor_units', 'duration': 'duration_seconds', 'concurrency': 'concurrency'}
        for item in vals:
            k, _, n = item.partition('=')
            if k not in keys or not n.isdigit(): raise UserError(f'Bad limit "{item}".', 'Use: requests=200 duration=3600 concurrency=1 [tokens=0 cost=0]')
            arch['limits'][keys[k]] = int(n)
    elif f in ('access', 'boundary', 'actor', 'activities', 'scope'):
        for r in routes_of(arch, a.route):
            if f == 'access':
                if v not in ACCESS: raise UserError(f'Access must be one of {", ".join(ACCESS)}.')
                r['access'] = v
            elif f == 'scope':
                if v not in ('in_scope', 'out_of_scope'): raise UserError('Scope must be in_scope or out_of_scope.')
                r['scope'] = v
            elif f == 'activities':
                acts = [x.strip().upper() for x in v.replace(' ', ',').split(',') if x.strip()]
                bad = set(acts) - set(op.ACTIVITIES)
                if bad: raise UserError('Unknown activity: ' + ', '.join(sorted(bad)), 'Use DESIGN, CONFIG, TEST, REDTEAM')
                r['activity_types'] = list(dict.fromkeys(acts))
            else: r[f] = v
    else:
        raise UserError(f'Unknown field "{f}".', 'Fields: ' + ', '.join(SET_FIELDS))
    ws.save_arch(arch); ws.log(f'set {f}', 'architecture.json')
    out(S.green(f'Set {f}.')); stale_note(ws)
    return 0
SET_FIELDS = ['name', 'authorization', 'snapshot', 'reviewer', 'reviewed-at', 'inventory-evidence', 'evidence-store', 'stop', 'limits', 'owner', 'access', 'scope', 'boundary', 'actor', 'activities']


def cmd_protocol(a):
    ws = ws_from(a); arch = ws.arch(); lib = op.library()
    case = next((c for c in lib['cases'] + lib['scenarios'] if c['id'] == a.case), None)
    if not case:
        close = difflib.get_close_matches(a.case, [c['id'] for c in lib['cases']], n=3)
        raise UserError(f'Unknown case "{a.case}".', ('Did you mean: ' + ', '.join(close)) if close else 'See: merestone tasks')
    if case.get('activity', 'REDTEAM') not in ('TEST', 'REDTEAM'):
        raise UserError(f'{a.case} is a {case["activity"]} review; protocols apply to TEST/REDTEAM cases.')
    variants = [v.strip() for v in a.variants.split(',') if v.strip()]
    proto = {'case_id': a.case, 'required_variants': variants, 'min_trials_per_variant': a.min, 'design': a.design, 'decision_rule': a.rule, 'justification': a.why}
    op.validate(proto, op.read(op.ROOT / 'schemas/test-protocol-v3.schema.json'))
    for r in routes_of(arch, a.route):
        r['test_protocols'] = [p for p in r.get('test_protocols', []) if p['case_id'] != a.case] + [proto]
    ws.save_arch(arch); ws.log('protocol ' + a.case, 'architecture.json')
    out(S.green(f'Protocol for {a.case}: ') + f'{", ".join(variants)} x{a.min} ({a.design})'); stale_note(ws)
    return 0


def cmd_plan(a):
    ws = ws_from(a); arch = ws.arch()
    gaps = op.ready(arch)
    if not ws.has_plan():
        blocking = [it for it in setup_items(arch) if it['blocking']]
        if blocking and not a.anyway:
            out(S.yellow(f'{len(blocking)} things are still undefined. Defining them before freezing avoids a revision later:'))
            for it in blocking: out(f"  [ ] {ITEMS[it['key']][0]:<32} {S.teal(item_command(it))}")
            raise UserError('Plan not frozen yet.', 'Answer them with: merestone setup   (or freeze anyway: merestone plan --anyway)')
        p = op.make_plan(arch); n = 1
    else:
        current = ws.plan()
        if op.digest(arch) == current['architecture_sha256']:
            out('The current plan already matches architecture.json. Nothing to freeze.'); return 0
        if not (a.reason and a.approver):
            raise UserError('architecture.json changed after the plan was frozen.', 'Freeze a revision: merestone plan --reason "<why>" --approver "<who>"')
        p = gov.revise_plan(current, arch, a.reason, a.approver); n = int(ws.cfg['series'].split('-')[1]) + 1
    series = f'plan-{n:03d}'
    plan_rel, man_rel = f'plans/{series}.json', f"{ws.cfg['manifest_dir']}/{series}.manifest.json"
    op.write(ws.p(plan_rel), p); op.write(ws.p(man_rel), op.manifest(p))
    ws.p(f'plans/{series}.md').write_text(op.plan_markdown(p), encoding='utf-8')
    ws.cfg.update(plan=plan_rel, manifest=man_rel, series=series); ws.log('plan ' + series, plan_rel)
    counts = {}
    for t in p['tasks']: counts[t['applicability']] = counts.get(t['applicability'], 0) + 1
    out(S.green(f'Froze {series}: ') + f"{len(p['tasks'])} obligations  "
        + ', '.join(f'{k} {v}' for k, v in sorted(counts.items())))
    out(S.dim(f'Readable guide: {plan_rel[:-5]}.md   Manifest: {man_rel} (keep a copy outside the workspace)'))
    if n > 1:
        cmp = gov.compare_plans(current, p)
        out(S.dim(f"Revision of {current['plan_id'][:8]}: +{len(cmp['added'])} / -{len(cmp['removed'])} / ~{len(cmp['changed'])} obligations. Results are not transferred."))
    if gaps: out(S.yellow(f'\n{len(gaps)} readiness gaps remain; the plan cannot close until they are fixed. ') + S.dim('See: merestone status'))
    else: out(S.dim('Next: merestone status   (shows which tasks to start with)'))
    return 0


# ---------- status ----------
def stale_note(ws):
    if ws.has_plan() and op.digest(ws.arch()) != ws.plan()['architecture_sha256']:
        out(S.yellow('architecture.json differs from the frozen plan. ') + S.dim('When ready: merestone plan --reason "..." --approver "..."'))


def dedupe(lines):
    seen, res = set(), []
    for g, fix in lines:
        if fix not in seen: seen.add(fix); res.append((g, fix))
    return res


def gap_lines(gaps):
    lines = []
    for g in gaps:
        if ':evidence:' in g:
            route, _, cap = g.partition(':evidence:')
            lines.append((g, f'merestone caps {cap}=<present|absent> --source "<where you verified it>" --route {route}'))
        else: lines.append((g, FIX.get(g, 'see docs/IMPLEMENTATION.md')))
    return lines


PLACEHOLDER = 'to be identified'
ITEMS = {  # key -> (plain label, why it matters, example value)
    'authorization': ('Permission to test', 'Proof that the system owner allows this assessment: a ticket, an email or a signed scope. Never test without it.', 'Own lab, authorized by <name>'),
    'snapshot': ('Exact version under test', 'App, model, prompt and document-index versions. Results only hold for this version.', 'app v0.1, model X, index 2026-10-02'),
    'evidence-store': ('Where evidence is kept', 'The store that holds hashed evidence files.', 'evidence/ folder of this workspace'),
    'reviewer': ('Who reviewed the inventory', 'The person who checked the capability answers. The date is recorded automatically.', 'your name'),
    'inventory-evidence': ('Source of the inventory', 'Where the answers came from: an architecture document, a code review or an interview.', 'code review of the repository'),
    'stop': ('Stop conditions', 'When testing must stop at once, so a test never causes real harm.', 'real customer data appears'),
    'limits': ('Load limits', 'Maximum requests, total duration in seconds and parallel requests, so tests never overload the system.', 'requests=200 duration=3600 concurrency=1'),
    'activities': ('Design review included', 'Every assessment includes the common design review (DESIGN); without it the plan can never close.', 'DESIGN,CONFIG,TEST'),
    'access': ('How much you can see', 'black-box: only as a user | gray-box: plus docs or configuration | white-box: code and logs. Tasks cannot be completed while access is unknown.', 'gray-box'),
    'actor': ('Who acts', 'The person or system that attempts something on this route, with its starting permissions.', 'authenticated user of one customer'),
    'boundary': ('Trust boundary crossed', 'Where trust changes along the route; it names what the tests protect.', 'user -> app -> document index -> model'),
    'caps-source': ('Source for capability answers', 'Capabilities marked present or absent need a source; unsure ones can stay unknown.', 'architecture doc v2'),
}
GAP_ITEM = {'authorization_ref': 'authorization', 'snapshot_ref': 'snapshot', 'evidence_store': 'evidence-store',
            'inventory_review.reviewer': 'reviewer', 'inventory_review.reviewed_at': 'reviewer',
            'inventory_review.evidence_ref': 'inventory-evidence', 'stop_conditions': 'stop', 'limits': 'limits',
            'core_design_missing': 'activities'}
BLOCKING = set(GAP_ITEM.values()) | {'access', 'caps-source'}


def setup_items(arch):
    """Everything an assessment needs before freezing the plan, as plain-language items."""
    gaps = op.ready(arch); todo = []
    for g in gaps:
        k = 'caps-source' if ':evidence:' in g else GAP_ITEM.get(g)
        if k and k not in todo: todo.append(k)
    multi = len(arch['routes']) > 1
    for r in arch['routes']:
        if r['access'] in ('unknown', 'none'): todo.append(('access', r['id']) if multi else 'access')
        for k in ('actor', 'boundary'):
            if PLACEHOLDER in r[k].lower(): todo.append((k, r['id']) if multi else k)
    order = list(ITEMS)
    res = []
    for k in order:
        for t in todo:
            key, route = (t if isinstance(t, tuple) else (t, None))
            if key == k: res.append({'key': key, 'route': route, 'blocking': key in BLOCKING})
    return res


def item_command(it):
    k, route = it['key'], it['route']; ex = ITEMS[k][2]; rt = f' --route {route}' if route else ''
    if k == 'limits': return 'merestone set limits ' + ex
    if k == 'caps-source': return f'merestone caps NAME=STATE --source "{ex}"   (or: merestone setup)'
    if k == 'activities': return 'merestone set activities ' + ex + rt
    if k == 'access': return f'merestone set access gray-box{rt}   (or black-box / white-box)'
    return f'merestone set {k} "{ex}"{rt}'


def show_checklist(arch, items):
    out(S.bold('\nBefore freezing the plan') + S.dim('   (answer them one by one with:  merestone setup)'))
    for it in items:
        label, why, _ = ITEMS[it['key']]
        tag = S.yellow('[ ]') if it['blocking'] else S.dim('[~]')
        where = f" ({it['route']})" if it['route'] else ''
        out(f"  {tag} {S.bold(label + where)}")
        out(S.dim(f'      {why}'))
        out(f'      {S.teal(item_command(it))}')
    if any(not it['blocking'] for it in items): out(S.dim('  [~] recommended: the plan can be frozen without it, but the report will be less meaningful.'))


def show_status_arch(ws):
    arch = ws.arch(); items = setup_items(arch)
    heading(f"{arch['system_name']}  ·  {arch['assessment_id']}")
    for r in arch['routes']:
        c = list(r['capabilities'].values())
        out(f"  {r['id']}: access {r['access']}, activities {','.join(r['activity_types'])}; capabilities "
            f"{S.green(str(c.count('present')) + ' present')}, {c.count('absent')} absent, {S.yellow(str(c.count('unknown')) + ' unknown')}")
    out(S.dim('  Unknown capabilities are fine for now: their tests stay "pending confirmation" until you verify them (merestone caps).'))
    if items:
        show_checklist(arch, items)
        out(S.bold('\nNext:') + ' run  merestone setup  (or the commands above), then freeze the plan with  merestone plan')
        out(S.dim('      Or do it all in the browser: merestone ui'))
    else:
        out(S.green('\nEverything needed before planning is in place.') + S.bold('  Next:') + ' merestone plan')
    return 2


ACCESS_SHORT = {'b': 'black-box', 'g': 'gray-box', 'w': 'white-box'}


def cmd_setup(a):
    ws = ws_from(a); arch = ws.arch(); ask = lambda prompt: input(prompt)
    items = setup_items(arch)
    if not items:
        out(S.green('Nothing pending before the plan.') + ' Next: merestone plan'); return 0
    out(S.bold(f'{len(items)} things to define before freezing the plan.') + S.dim(' Press Enter to skip any of them.\n'))
    done = 0
    for it in items:
        k, route = it['key'], it['route']; label, why, ex = ITEMS[k]
        routes = routes_of(arch, route)
        out(S.bold(label) + (f' ({route})' if route else '')); out(S.dim('  ' + why))
        if k == 'access':
            while True:
                v = ask('  Access [b]lack-box, [g]ray-box, [w]hite-box: ').strip().lower()
                if not v or v in ACCESS_SHORT or v in ACCESS[:3]: break
                out(S.yellow('    Please answer b, g or w (or Enter to skip).'))
            if v:
                for r in routes: r['access'] = ACCESS_SHORT.get(v, v)
                done += 1
        elif k == 'limits':
            v = ask('  Requests, seconds and parallel requests [Enter = 200 3600 1]: ').strip()
            nums = v.replace(',', ' ').split() if v else ['200', '3600', '1']
            if len(nums) != 3 or not all(n.isdigit() and int(n) > 0 for n in nums):
                out(S.yellow('    Skipped: expected three positive numbers, e.g. 200 3600 1'))
            else:
                arch['limits'].update(requests=int(nums[0]), duration_seconds=int(nums[1]), concurrency=int(nums[2])); done += 1
        elif k == 'activities':
            v = ask('  Include the common design review (DESIGN)? [Y/n]: ').strip().lower()
            if v in ('', 'y', 'yes', 's', 'si', 'sí'):
                for r in routes:
                    if 'DESIGN' not in r['activity_types']: r['activity_types'].insert(0, 'DESIGN')
                done += 1
        elif k == 'caps-source':
            missing = sorted({c for r in routes for c, st in r['capabilities'].items() if st != 'unknown' and not r['capability_evidence'].get(c, '').strip()})
            out(S.dim('  Without a source: ' + ', '.join(missing)))
            v = ask(f'  One source for all of them (e.g. "{ex}"): ').strip()
            if v:
                for r in routes:
                    for c in missing:
                        if r['capabilities'].get(c) != 'unknown': r['capability_evidence'][c] = v
                done += 1
        else:
            default = getpass.getuser() if k == 'reviewer' else ''
            v = ask(f'  e.g. "{ex}"' + (f' [Enter = {default}]' if default else '') + ': ').strip() or default
            if v:
                if k == 'authorization': arch['authorization_ref'] = v
                elif k == 'snapshot': arch['snapshot_ref'] = v
                elif k == 'evidence-store': arch['evidence_store'] = v
                elif k == 'reviewer':
                    arch['inventory_review']['reviewer'] = v
                    if not arch['inventory_review']['reviewed_at']: arch['inventory_review']['reviewed_at'] = now()
                elif k == 'inventory-evidence': arch['inventory_review']['evidence_ref'] = v
                elif k == 'stop': arch['stop_conditions'].append(v)
                else:
                    for r in routes: r[k] = v
                done += 1
        out('')
    ws.save_arch(arch); ws.log(f'setup ({done} answered)', 'architecture.json')
    out(S.green(f'Saved {done} of {len(items)}.'))
    rest = setup_items(arch)
    if rest:
        out(S.yellow(f'{len(rest)} still pending.') + S.dim(' Run merestone setup again or see merestone status.'))
    else:
        out(S.bold('Ready.') + ' Next: ' + S.teal('merestone plan'))
    stale_note(ws)
    return 0


def cmd_status(a):
    ws = ws_from(a)
    if not ws.has_plan(): return show_status_arch(ws)
    plan, r = ws.check()
    if a.json: out(json.dumps(r, ensure_ascii=False, indent=2)); return r['exit_code']
    arch = plan['architecture']; tasks = plan['tasks']
    heading(f"{arch['system_name']}  ·  {ws.cfg['series']} ({plan['plan_id'][:8]})")
    out(f'Exit code   {code_label(r["exit_code"])}' + S.dim('   (0 complete · 1 complete with FAIL · 2 incomplete)'))
    na = sum(t['applicability'] == 'NOT_APPLICABLE' for t in tasks)
    out(f"Obligations {len(tasks)} total · {r['applicable_obligations']} applicable · {S.yellow(str(r['unknown_obligations']) + ' unknown')} · {na} not applicable")
    passed = r['decided_obligations'] - r['failures']
    out(f"Decided     {S.green(str(passed) + ' PASS')} · {S.red(str(r['failures']) + ' FAIL')} · {r['excluded_obligations']} excluded")
    heading('\nBy module')
    for mod, counts in sorted(r['coverage_by_module'].items()):
        tot = sum(counts.values()); done = counts.get('PASS', 0) + counts.get('FAIL', 0)
        bar = '#' * round(10 * done / tot) + '.' * (10 - round(10 * done / tot)) if tot else ''
        out(f'  {mod:<11} [{bar}] ' + ', '.join(f'{k} {v}' for k, v in sorted(counts.items())))
    steps = next_steps(ws, plan, r)
    if steps:
        heading('\nNext steps')
        for i, (what, cmd) in enumerate(steps[:6], 1): out(f'  {i}. {what}\n     {S.teal(cmd)}')
    stale_note(ws)
    out(S.dim('\n' + r['note']))
    out(S.dim('Prefer to work visually? merestone ui opens this workspace in your browser (local only).'))
    return r['exit_code']


def next_steps(ws, plan, r):
    steps = []; arch = plan['architecture']
    if r['readiness_gaps']:
        for g, fix in dedupe(gap_lines(r['readiness_gaps']))[:3]: steps.append((f'Readiness gap: {g}', fix))
        steps.append(('Then freeze a revision so the plan includes those fixes', 'merestone plan --reason "readiness" --approver "<who>"'))
    if any(x['access'] in ('unknown', 'none') for x in arch['routes']):
        steps.append(('Declare how you can access each route (tasks cannot complete while access is unknown)', 'merestone set access gray-box'))
    vague = [x for x in arch['routes'] if 'to be identified' in (x['boundary'] + x['actor']).lower()]
    if vague: steps.append((f"Describe {vague[0]['id']}: who acts and which trust boundary it crosses (makes tasks and the report meaningful)",
                            'merestone set boundary "<e.g. tenant A user -> shared index>"   and   merestone set actor "<e.g. authenticated tenant user>"'))
    unk = sum(t['applicability'] == 'UNKNOWN' for t in plan['tasks'])
    if unk: steps.append((f'{unk} obligations depend on unverified capabilities', 'merestone caps'))
    todo = [t for t in plan['tasks'] if t['applicability'] == 'APPLICABLE' and not t['result'] and not t.get('exclusion')]
    noproto = [t for t in todo if t['activity'] in ('TEST', 'REDTEAM') and not t['test_protocol']]
    if noproto: steps.append((f'{len(noproto)} applicable tests have no protocol (needed to decide PASS/FAIL), e.g. {noproto[0]["case_id"]}',
                              f'merestone protocol {noproto[0]["case_id"]} --variants original,neighbor,benign --rule "..." --why "..."'))
    reviews = [t for t in todo if t['activity'] in ('DESIGN', 'CONFIG')]
    if reviews: steps.append((f'{len(reviews)} design/config reviews pending, e.g. {alias(reviews[0])}', f'merestone show {alias(reviews[0])}'))
    tests = [t for t in todo if t['activity'] in ('TEST', 'REDTEAM') and t['test_protocol']]
    if tests: steps.append((f'{len(tests)} tests ready to run, e.g. {alias(tests[0])}', f'merestone show {alias(tests[0])}'))
    if r['exit_code'] in (0, 1): steps.append(('Write the final report', 'merestone report --format both'))
    else: steps.append(('Share progress with people who do not use the terminal', 'merestone report --format html --open'))
    return steps


def cmd_tasks(a):
    ws = ws_from(a); plan = ws.plan(); rows = plan['tasks']
    if a.module: rows = [t for t in rows if t['module'].lower() == a.module.lower()]
    if a.activity: rows = [t for t in rows if t['activity'] == a.activity.upper()]
    if a.state:
        want = a.state.lower()
        sel = {'todo': lambda t: t['applicability'] == 'APPLICABLE' and not t['result'], 'unknown': lambda t: t['applicability'] == 'UNKNOWN',
               'na': lambda t: t['applicability'] == 'NOT_APPLICABLE', 'pass': lambda t: t['result'] == 'PASS', 'fail': lambda t: t['result'] == 'FAIL',
               'applicable': lambda t: t['applicability'] == 'APPLICABLE'}
        if want not in sel: raise UserError('Unknown state filter.', 'Use: ' + ', '.join(sel))
        rows = [t for t in rows if sel[want](t)]
    elif not a.all: rows = [t for t in rows if t['applicability'] != 'NOT_APPLICABLE']
    order = {'FAIL': 0, 'NOT_RUN': 1, 'COMPLETED': 1, 'BLOCKED': 1, 'ERROR': 1, 'INCONCLUSIVE': 1, 'UNKNOWN': 2, 'PASS': 3, 'EXCLUDED': 4, 'NOT_APPLICABLE': 5}
    rows = sorted(rows, key=lambda t: (order.get(task_state(t), 9), t['case_id']))
    colors = {'FAIL': S.red, 'PASS': S.green, 'UNKNOWN': S.yellow, 'NOT_APPLICABLE': S.dim}
    out(S.bold(f"{'TASK':<22} {'MODULE':<10} {'ACTIVITY':<8} {'STATE':<14} TITLE"))
    for t in rows:
        st = task_state(t); col = colors.get(st, lambda s: s)
        out(f"{alias(t):<22} {t['module']:<10} {t['activity']:<8} {col(f'{st:<14}')} {t['title']}")
    out(S.dim(f'\n{len(rows)} tasks. Details: merestone show <TASK>'))
    return 0


def cmd_show(a):
    ws = ws_from(a); plan = ws.plan(); t = resolve(plan, a.task); lib = op.library()
    heading(f"{alias(t)}  ·  {t['title']}")
    out(f"{t['module']} · {t['activity']} · applicability {t['applicability']} · state {task_state(t)} · access {t['access']}")
    out(f"Boundary: {t['boundary']}   Actor: {t['actor']}   Controls: {', '.join(t['control_ids'])}")
    if t['activity'] in ('TEST', 'REDTEAM'):
        pr = t['test_protocol']
        out(f"Protocol: {', '.join(pr['required_variants'])} x{pr['min_trials_per_variant']} ({pr['design']})" if pr else S.yellow('Protocol: none (needed to decide PASS/FAIL)'))
        staged = op.read(ws.staging(t['task_id']))['trials'] if ws.staging(t['task_id']).exists() else []
        for label, trials in (('Recorded', t['trials']), ('Staged (not decided yet)', staged)):
            if trials: out(f'{label}: ' + ', '.join(f"{x['variant']}={x['result'] or x['execution']}" for x in trials))
    case = next((c for c in lib['cases'] if c['id'] == t['case_id']), None)
    if case and not a.brief: out('\n' + op.render_case(case, lib))
    if t['applicability'] == 'APPLICABLE' and not t['result']:
        heading('How to record it')
        if t['activity'] in ('DESIGN', 'CONFIG'):
            out(S.teal(f'  merestone review {alias(t)} --result PASS --evidence review=<file> --reviewer "<name>" --observations "<what you checked>"'))
        else:
            out(S.teal(f'  merestone record {alias(t)} --variant original --result FAIL --expected "..." --observed "..." --identity "<principal>" '
                       '--reachability reached --adaptation "<how you adapted the input>" --evidence response=<file> effect=<file> '
                       '--note baseline="..." input="..." identity="..." reachability="..."'))
            out(S.dim('  Each of baseline, input, response, effect, identity and reachability needs a file (--evidence KIND=FILE) or a short text (--note KIND="...").'))
            out(S.teal(f'  merestone decide {alias(t)} --reviewer "<name>" --observations "..." --cleanup-confirmed'))
    return 0


def cmd_fieldcard(a):
    lib = op.library(); c = next((c for c in lib['cases'] if c['id'] == a.case), None)
    if not c:
        close = difflib.get_close_matches(a.case, [c['id'] for c in lib['cases']], n=3)
        raise UserError(f'Unknown case "{a.case}".', ('Did you mean: ' + ', '.join(close)) if close else 'List: merestone list')
    out(op.render_case(c, lib)); return 0


# ---------- recording ----------
def collect(ws, task, trial_id, specs, notes, a):
    """Copy evidence into the workspace store and build hashed records."""
    records = []; base = ws.evidence_root / safe(alias(task)) / safe(trial_id)
    items = []
    for s in specs or []:
        if '=' not in s: raise UserError(f'"{s}" is not KIND=FILE.', 'Example: --evidence response=answer.txt')
        k, _, f = s.partition('='); src = Path(f)
        if not src.is_file(): raise UserError(f'Evidence file not found: {f}')
        items.append((k.strip(), src.name, src.read_bytes()))
    for s in notes or []:
        if '=' not in s: raise UserError(f'"{s}" is not KIND=TEXT.', 'Example: --note identity="signed in as tenant-a"')
        k, _, txt = s.partition('='); items.append((k.strip(), 'note.txt', txt.encode('utf-8')))
    seen = set()
    for kind, name, data in items:
        if kind not in EVIDENCE_KINDS: raise UserError(f'Unknown evidence kind "{kind}".', 'Kinds: ' + ', '.join(EVIDENCE_KINDS))
        if kind in seen: raise UserError(f'Two evidence items of kind "{kind}" for one trial.', 'Combine them or record a second trial.')
        seen.add(kind)
        dest = base / f'{kind}-{safe(name)}'
        if dest.exists(): raise UserError(f'Evidence already exists: {dest}', 'Use a new --trial-id; recorded evidence is never overwritten.')
        dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
        records.append({'id': safe(f'{alias(task)}-{trial_id}-{kind}'), 'path': dest.relative_to(ws.evidence_root).as_posix(),
            'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'collected_at': now(),
            'collector': a.collector or os.environ.get('MERESTONE_COLLECTOR') or getpass.getuser(),
            'origin': a.origin, 'classification': a.classification, 'kind': kind, 'redactions': a.redaction or []})
    return records


def preflight(t):
    if t['applicability'] != 'APPLICABLE':
        raise UserError(f"{alias(t)} is {t['applicability']}; only applicable tasks can be recorded.", 'Resolve its capabilities first: merestone caps')
    if t['scope'] != 'in_scope': raise UserError(f'{alias(t)} is out of scope.')
    if t['access'] in ('unknown', 'none'):
        raise UserError(f"Route access is '{t['access']}' in the frozen plan.", 'merestone set access gray-box, then merestone plan --reason ... --approver ...')


def cmd_record(a):
    ws = ws_from(a); plan = ws.plan(); t = resolve(plan, a.task); preflight(t)
    if t['activity'] in ('DESIGN', 'CONFIG'): raise UserError(f'{alias(t)} is a {t["activity"]} review.', f'Use: merestone review {alias(t)} ...')
    snap = plan['architecture']['snapshot_ref']
    if not snap: raise UserError('The frozen plan has no snapshot.', 'merestone set snapshot "...", then merestone plan --reason ... --approver ...')
    if not a.example and not a.adaptation:
        raise UserError('Say where the test input came from.', 'Pass --example EX-... (a catalog example) or --adaptation "<how you adapted it>"')
    execution = {'completed': 'COMPLETED', 'blocked': 'BLOCKED', 'error': 'ERROR'}[a.execution]
    result = a.result.upper() if execution == 'COMPLETED' else ''
    if (execution != 'COMPLETED' or result == 'INCONCLUSIVE') and not a.rationale:
        raise UserError('Blocked, errored or inconclusive trials need --rationale "<why>".')
    stage_path = ws.staging(t['task_id'])
    stage = op.read(stage_path) if stage_path.exists() else {'task_id': t['task_id'], 'alias': alias(t), 'trials': [], 'evidence': []}
    trial_id = safe(a.trial_id or f"{alias(t)}-{a.variant}-{1 + sum(x['variant'] == a.variant for x in stage['trials'] + t['trials'])}")
    if trial_id in {x['trial_id'] for x in stage['trials'] + t['trials']}: raise UserError(f'Trial id {trial_id} already used.')
    if result in ('PASS', 'FAIL'):
        for k in ('expected', 'observed', 'identity'):
            if not getattr(a, k): raise UserError(f'--{k} is required for a PASS/FAIL trial.')
        given = {s.partition('=')[0].strip() for s in (a.evidence or []) + (a.note or [])}
        missing = [k for k in TECH_KINDS if k not in given]
        if missing: raise UserError('A decided trial needs evidence of: ' + ', '.join(missing) + '.',
                                    'Add files with --evidence KIND=FILE or short text with --note KIND="..."')
        if a.reachability == 'blocked_by_control' and not a.blocking_control:
            raise UserError('Say which control blocked it: --blocking-control CTL-...')
    records = collect(ws, t, trial_id, a.evidence, a.note, a)
    trial = {'trial_id': trial_id, 'variant': a.variant, 'example_id': a.example or '', 'technique_id': a.technique or '', 'snapshot_ref': snap,
             'execution': execution, 'result': result, 'baseline_ok': not a.baseline_failed, 'reachability': a.reachability if result else (a.reachability or ''),
             'blocking_control_id': a.blocking_control or '', 'identity': a.identity or '', 'expected': a.expected or '', 'observed': a.observed or '',
             'evidence_ids': [r['id'] for r in records], 'rationale': a.rationale or '', 'parameters_ref': a.parameters or '', 'adaptation_diff': a.adaptation or ''}
    op.validate(trial, op.read(op.ROOT / 'schemas/trial-v3.schema.json'))
    stage['trials'].append(trial); stage['evidence'] += records
    stage_path.parent.mkdir(parents=True, exist_ok=True); jsonutil.write_json(stage_path, stage)
    ws.log(f'record {alias(t)} {a.variant}={result or execution}', stage_path.relative_to(ws.root).as_posix())
    color = S.red if result == 'FAIL' else S.green if result == 'PASS' else S.yellow
    out(color(f'Staged {trial_id}: {result or execution}') + S.dim(f'  ({len(records)} evidence files hashed into {ws.cfg["evidence_dir"]}/)'))
    progress(t, stage)
    return 0


def progress(t, stage):
    pr = t['test_protocol']; trials = t['trials'] + stage['trials']
    if not pr: out(S.yellow('This task has no protocol, so it cannot be decided PASS/FAIL.')); return
    have = {v: sum(x['variant'] == v and x['execution'] == 'COMPLETED' and x['result'] in ('PASS', 'FAIL') for x in trials) for v in pr['required_variants']}
    out('Sample: ' + ', '.join(f"{v} {have[v]}/{pr['min_trials_per_variant']}" for v in pr['required_variants']))
    if all(n >= pr['min_trials_per_variant'] for n in have.values()) or any(x['result'] == 'FAIL' for x in trials):
        out(S.dim('Ready to decide: ') + S.teal(f"merestone decide {alias(t)} --reviewer \"<name>\" --observations \"...\" --cleanup-confirmed"))


def commit_event(ws, plan, event, label):
    new = import_event(plan, event, ws.evidence_root, ws.manifest())
    rel = ws.next_record(ws.cfg['series']); op.write(ws.p(rel), new)
    ws.cfg['plan'] = rel; ws.log(label, rel)
    return new


def cmd_decide(a):
    ws = ws_from(a); plan = ws.plan(); t = resolve(plan, a.task); preflight(t)
    sp = ws.staging(t['task_id'])
    if not sp.exists(): raise UserError(f'No staged trials for {alias(t)}.', f'Record them first: merestone record {alias(t)} ...')
    stage = op.read(sp)
    results = [x['result'] for x in stage['trials']]
    result = 'INCONCLUSIVE' if a.inconclusive else 'FAIL' if 'FAIL' in results else 'PASS'
    if result == 'PASS':
        pr = t['test_protocol']
        if not pr: raise UserError('No protocol for this task; it cannot be decided PASS.')
        trials = t['trials'] + stage['trials']
        missing = [v for v in pr['required_variants'] if sum(x['variant'] == v and x['result'] in ('PASS', 'FAIL') for x in trials) < pr['min_trials_per_variant']]
        if missing: raise UserError('PASS needs the full planned sample. Missing: ' + ', '.join(missing), f'merestone record {alias(t)} --variant {missing[0]} ...')
    if not a.cleanup_confirmed: raise UserError('Confirm that test data and state were cleaned up.', 'Add --cleanup-confirmed')
    event = {'task_id': t['task_id'], 'result': result, 'observations': a.observations, 'reviewer': a.reviewer,
             'cleanup_confirmed': True, 'trials': stage['trials'], 'evidence': stage['evidence']}
    commit_event(ws, plan, event, f'decide {alias(t)} {result}')
    done = ws.root / 'staging' / 'decided'; done.mkdir(parents=True, exist_ok=True)
    os.replace(sp, done / f"{safe(alias(t))}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json")
    color = S.red if result == 'FAIL' else S.green if result == 'PASS' else S.yellow
    out(color(f'{alias(t)} decided: {result}') + S.dim(f"  ->  {ws.cfg['plan']}"))
    if result == 'FAIL': out(S.dim('Record the finding with templates/finding-v3.json and check it with governance.py check-finding.'))
    return 0


def cmd_review(a):
    ws = ws_from(a); plan = ws.plan(); t = resolve(plan, a.task); preflight(t)
    if t['activity'] not in ('DESIGN', 'CONFIG'): raise UserError(f'{alias(t)} is a {t["activity"]} task.', f'Use: merestone record {alias(t)} ...')
    specs = [s if '=' in s else 'review=' + s for s in (a.evidence or [])]
    if not specs and not a.note: raise UserError('A review needs documentary evidence.', '--evidence review=<file> or --note review="<what you checked>"')
    records = collect(ws, t, a.trial_id or 'review', specs, a.note, a)
    if not any(r['kind'] == 'review' for r in records): raise UserError('At least one evidence item must be of kind "review".')
    event = {'task_id': t['task_id'], 'result': a.result.upper(), 'observations': a.observations, 'reviewer': a.reviewer,
             'cleanup_confirmed': True, 'trials': [], 'evidence': records}
    commit_event(ws, plan, event, f'review {alias(t)} {a.result.upper()}')
    out((S.red if a.result.upper() == 'FAIL' else S.green)(f'{alias(t)} reviewed: {a.result.upper()}') + S.dim(f"  ->  {ws.cfg['plan']}"))
    return 0


def cmd_report(a):
    ws = ws_from(a); plan, r = ws.check(); man = ws.manifest()
    findings = [op.read(f) for f in a.findings]
    for f in findings: gov.check_finding(f, plan, man, ws.evidence_root, gov.load_retests(a.retest_bundle))
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    formats = ['md', 'html'] if a.format == 'both' else [a.format]
    written = []
    for fmt in formats:
        rel = f"reports/report-{ws.cfg['series']}-{stamp}.{fmt}"; dest = ws.p(rel)
        if dest.exists(): raise UserError('A report with this timestamp exists; try again in a second.')
        if fmt == 'md': body = op.report_markdown(plan, r, findings)
        else:
            import report_html
            body = report_html.render_html(plan, r, findings, layout=a.layout)
        dest.parent.mkdir(parents=True, exist_ok=True); dest.write_text(body, encoding='utf-8')
        ws.log('report ' + fmt, rel); written.append(dest)
        out(S.green(f'Report written: {dest}'))
    out('Exit code ' + code_label(r['exit_code']))
    html_out = [d for d in written if d.suffix == '.html']
    if html_out:
        out(S.dim('Self-contained HTML: open it in any browser or share the file; it needs no internet access.'))
        if a.open:
            import webbrowser
            webbrowser.open(html_out[0].resolve().as_uri())
    return r['exit_code']


# ---------- local web interface ----------
def cmd_ui(a):
    try: root = ws_from(a).root
    except UserError:
        if a.workspace: raise
        root = None
    import ui_server
    return ui_server.serve(sys.modules[__name__], root, port=a.port, open_browser=not a.no_browser)


# ---------- utilities ----------
def cmd_demo(a):
    from adapters import local_pilots
    target = Path(a.out or f"merestone-demo-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
    out(S.bold('Running three local fixtures, each with a vulnerable and a corrected control...'))
    out(S.dim('Toy components only: no real model, network or data.\n'))
    summaries = local_pilots.run(target)
    for s in summaries:
        ev = op.read(target / Path(s['report']).parent / 'event.json')
        trials = ', '.join(f"{x['variant']} {(S.red if x['result'] == 'FAIL' else S.green)(x['result'])}" for x in ev['trials'])
        res = (S.red if s['case_result'] == 'FAIL' else S.green)(s['case_result'])
        out(f"  {s['fixture']:<10} {s['configuration']:<10} {s['case_id']}  {res:<6}  [{trials}]  plan exit code {s['plan_exit_code']}")
    out('\nWhat this shows:')
    out('  * The same case fails with the vulnerable control and passes once corrected.')
    out('  * The whole plan still returns code 2: one passing case does not certify a system.')
    out(S.dim(f'\nReports: {target}/<fixture>/report.md   Start your own: merestone new my-assessment --profile rag --guided'))
    return 0


def cmd_doctor(a):
    ok = True
    def line(good, msg): out((S.green('[ok]  ') if good else S.red('[!!]  ')) + msg)
    v = sys.version_info; good = v >= (3, 10); ok &= good
    line(good, f'Python {v.major}.{v.minor}.{v.micro} (3.10 or later required)')
    try:
        lib = op.library(); line(True, f"Catalog valid: {len(lib['cases'])} cases, {len(lib['techniques'])} techniques, {len(lib['examples'])} examples")
    except Exception as e: ok = False; line(False, 'Catalog invalid: ' + str(e))
    try:
        ws = ws_from(a); line(True, f'Workspace: {ws.root}')
        if ws.has_plan():
            ws.check(); line(True, f"Plan {ws.cfg['series']} verifies against its manifest and evidence store")
    except UserError: out(S.dim('[--]  No workspace here (optional). Create one with: merestone new <folder>'))
    except (ValueError, OSError) as e: ok = False; line(False, 'Workspace check failed: ' + str(e))
    return 0 if ok else 2


def cmd_list(a):
    lib = op.library()
    for c in lib['cases']:
        if (not a.module or c['module'].lower() == a.module.lower()) and (not a.activity or c['activity'] == a.activity.upper()):
            out(f"{c['id']:<9} {c['module']:<10} {c['activity']:<7} {c['title']}")
    return 0


QUICKSTART = """\
Merestone: assess AI systems boundary by boundary.

Quick start
  merestone demo                                  see a FAIL become a PASS in a minute
  merestone new my-eval --profile rag --guided    create a workspace (answers 16 questions)
  cd my-eval
  merestone setup                                 define permission, version, limits and access step by step
  merestone status                                what is missing and what to do next
  merestone plan                                  freeze the plan
  merestone tasks / show <TASK>                   browse what to test and how
  merestone record ... / decide ... / review ...  record results; hashes are computed for you
  merestone report --format html --open           visual dashboard to share (or Markdown by default)
  merestone ui                                    the same workflow in your browser (local only, no network)

Run "merestone <command> -h" for details. Exit codes: 0 complete without FAIL,
1 complete with FAIL, 2 incomplete or unverified (always the case for a new plan).
"""


def build_parser():
    fmt = argparse.RawDescriptionHelpFormatter
    p = argparse.ArgumentParser(prog='merestone', description=QUICKSTART, formatter_class=fmt)
    p.add_argument('-w', '--workspace', help='workspace folder (default: search upward from the current folder)')
    p.add_argument('--no-color', action='store_true', help='disable colored output (also NO_COLOR=1)')
    s = p.add_subparsers(dest='command', metavar='<command>')
    def cmd(name, fn, help_, epilog=None):
        q = s.add_parser(name, help=help_, description=help_, epilog=epilog, formatter_class=fmt); q.set_defaults(fn=fn); return q
    q = cmd('new', cmd_new, 'Create an assessment workspace from a profile.', 'Example:\n  merestone new harbor-desk --profile rag --guided --name "Harbor Desk"')
    q.add_argument('folder', help='new folder for the assessment'); q.add_argument('--profile', choices=PROFILES, default='chat', help='starting draft (default: chat)')
    q.add_argument('--guided', action='store_true', help='answer plain-language questions instead of editing 39 capabilities')
    q.add_argument('--name', help='system name'); q.add_argument('--id', help='assessment id (default: folder name)')
    q.add_argument('--manifest-dir', help='where approved manifests go (ideally outside the workspace)')
    q.add_argument('--inside-framework', action='store_true', help='allow creating the workspace inside the framework folder (not recommended)')
    cmd('setup', cmd_setup, 'Answer, one by one, everything needed before freezing the plan (permission, version, limits, access...).')
    q = cmd('status', cmd_status, 'Show progress, the exit code and the next steps.'); q.add_argument('--json', action='store_true', help='raw check-plan output')
    q = cmd('check', cmd_status, 'Alias of status (exit code = check-plan exit code).'); q.add_argument('--json', action='store_true', help='raw check-plan output')
    q = cmd('caps', cmd_caps, 'Show or change capabilities (present/absent/unknown).', 'Examples:\n  merestone caps\n  merestone caps retrieval=present tool_calling=absent --source "architecture doc v2"')
    q.add_argument('assign', nargs='*', help='NAME=STATE pairs'); q.add_argument('--source', help='where you verified it (required for present/absent)'); q.add_argument('--route', help='only this route')
    q = cmd('set', cmd_set, 'Set scope and readiness fields without editing JSON.', 'Fields: ' + ', '.join(SET_FIELDS) + '\nExamples:\n  merestone set authorization "SEC-482 signed scope"\n  merestone set limits requests=200 duration=3600 concurrency=1\n  merestone set access gray-box')
    q.add_argument('field', choices=SET_FIELDS, metavar='FIELD', help='one of: ' + ', '.join(SET_FIELDS)); q.add_argument('value', nargs='*'); q.add_argument('--route', help='only this route')
    q = cmd('protocol', cmd_protocol, 'Define the frozen test protocol for a case (before planning).', 'Example:\n  merestone protocol AI-006 --variants original,neighbor,benign --rule "No chunk from another tenant in context" --why "Deterministic ACL check"')
    q.add_argument('case'); q.add_argument('--variants', required=True, help='comma-separated variant names'); q.add_argument('--min', type=int, default=1, help='minimum trials per variant')
    q.add_argument('--design', choices=DESIGNS, default='deterministic'); q.add_argument('--rule', required=True, help='decision rule'); q.add_argument('--why', required=True, help='justification'); q.add_argument('--route')
    q = cmd('plan', cmd_plan, 'Freeze the plan (or a revision after changes).'); q.add_argument('--reason', help='why the plan changes (revisions)'); q.add_argument('--approver', help='who approves the revision')
    q.add_argument('--anyway', action='store_true', help='freeze even with readiness gaps (the plan will stay at code 2)')
    q = cmd('tasks', cmd_tasks, 'List tasks with readable IDs (CASE@ROUTE).'); q.add_argument('--module'); q.add_argument('--activity')
    q.add_argument('--state', help='todo, applicable, unknown, na, pass, fail'); q.add_argument('--all', action='store_true', help='include not applicable')
    q = cmd('show', cmd_show, 'Show a task: status, protocol, fieldcard and how to record it.'); q.add_argument('task', help='CASE@ROUTE, case id or TASK-...'); q.add_argument('--brief', action='store_true', help='omit the fieldcard')
    q = cmd('fieldcard', cmd_fieldcard, 'Print a fieldcard from the catalog (no workspace needed).'); q.add_argument('case')
    def ev_opts(q):
        q.add_argument('--evidence', nargs='+', metavar='KIND=FILE', help='files to hash and store; kinds: ' + ', '.join(EVIDENCE_KINDS))
        q.add_argument('--note', nargs='+', metavar='KIND=TEXT', help='short text evidence stored as a file')
        q.add_argument('--collector', help='who collected it (default: your user)'); q.add_argument('--origin', default='manual capture')
        q.add_argument('--classification', default='internal'); q.add_argument('--redaction', nargs='*', help='redactions applied')
        q.add_argument('--trial-id')
    q = cmd('record', cmd_record, 'Stage one trial of a test with its evidence.', 'Example:\n  merestone record AI-006@ROUTE-1 --variant original --result FAIL --expected "only tenant A docs" \\\n    --observed "tenant B doc returned" --identity "tenant-a user" --reachability reached \\\n    --adaptation "own query about B invoices" --evidence response=resp.json effect=ctx.json \\\n    --note baseline="A invoice answered" input="what discount did B get?" identity="tenant-a" reachability="query hit shared index"')
    q.add_argument('task'); q.add_argument('--variant', required=True); q.add_argument('--result', choices=['PASS', 'FAIL', 'INCONCLUSIVE', 'pass', 'fail', 'inconclusive'], default='PASS')
    q.add_argument('--execution', choices=['completed', 'blocked', 'error'], default='completed'); q.add_argument('--expected'); q.add_argument('--observed'); q.add_argument('--identity')
    q.add_argument('--reachability', choices=['reached', 'not_reached', 'blocked_by_control', 'unknown'], default='reached'); q.add_argument('--blocking-control')
    q.add_argument('--example', help='catalog example id'); q.add_argument('--technique', help='technique id'); q.add_argument('--adaptation', help='how the input was adapted (required without --example)')
    q.add_argument('--baseline-failed', action='store_true', help='the benign baseline did not work'); q.add_argument('--rationale'); q.add_argument('--parameters', help='tool/parameters reference')
    ev_opts(q)
    q = cmd('decide', cmd_decide, 'Decide a test from its staged trials and commit it to a new plan record.')
    q.add_argument('task'); q.add_argument('--reviewer', required=True); q.add_argument('--observations', required=True)
    q.add_argument('--cleanup-confirmed', action='store_true'); q.add_argument('--inconclusive', action='store_true')
    q = cmd('review', cmd_review, 'Record a DESIGN/CONFIG review with documentary evidence.', 'Example:\n  merestone review CORE-001@ROUTE-1 --result PASS --evidence review=scope.pdf --reviewer "Jane" --observations "Scope and rules agreed"')
    q.add_argument('task'); q.add_argument('--result', required=True, choices=['PASS', 'FAIL', 'INCONCLUSIVE', 'pass', 'fail', 'inconclusive'])
    q.add_argument('--reviewer', required=True); q.add_argument('--observations', required=True); ev_opts(q)
    q = cmd('report', cmd_report, 'Write the coverage report into reports/ (Markdown, a shareable HTML dashboard, or both).',
            'Examples:\n  merestone report\n  merestone report --format html --open\n  merestone report --format html --layout document --open\n  merestone report --format both --findings findings/FND-001.json')
    q.add_argument('--format', choices=['md', 'html', 'both'], default='md', help='md (default), html (visual dashboard) or both')
    q.add_argument('--layout', choices=['board', 'document'], default='board',
                   help='HTML design: board (dashboard with tasks grouped by state, default) or document (top-to-bottom report, print-friendly)')
    q.add_argument('--open', action='store_true', help='open the HTML report in the default browser')
    q.add_argument('--findings', nargs='*', default=[], metavar='FINDING.json',
                   help='validated finding records (templates/finding-v3.json) to include in the report')
    q.add_argument('--retest-bundle', metavar='BUNDLE.json', help='retest plans needed to verify closed findings (JSON list of plan, manifest, evidence_root)')
    q = cmd('ui', cmd_ui, 'Open the local web interface: architecture editor, plan board, trial recording with drag-and-drop evidence, reports.',
            'Runs on 127.0.0.1 only and sends nothing to the network. Every change goes through the same rules as the commands.\n'
            'Examples:\n  merestone ui\n  merestone ui --port 8765 --no-browser\n  merestone -w my-eval ui')
    q.add_argument('--port', type=int, default=0, help='local port (default: a free one)')
    q.add_argument('--no-browser', action='store_true', help='print the link instead of opening the browser')
    q = cmd('demo', cmd_demo, 'Run the local pilots: watch a FAIL become a PASS.'); q.add_argument('--out', help='output folder (must not exist)')
    cmd('doctor', cmd_doctor, 'Check Python, the catalog and the current workspace.')
    q = cmd('list', cmd_list, 'List catalog cases.'); q.add_argument('--module'); q.add_argument('--activity')
    return p


def main(argv=None):
    p = build_parser(); a = p.parse_args(argv)
    S.on = sys.stdout.isatty() and not a.no_color and not os.environ.get('NO_COLOR')
    if S.on and os.name == 'nt': os.system('')
    if not getattr(a, 'fn', None): out(QUICKSTART); return 0
    try:
        return a.fn(a)
    except UserError as e:
        print(S.red('Error: ') + str(e), file=sys.stderr)
        if e.hint: print(S.dim('Hint:  ') + e.hint, file=sys.stderr)
    except FileNotFoundError as e:
        print(S.red('Error: ') + f'file not found: {e.filename}', file=sys.stderr)
    except (ValueError, KeyError, TypeError, OSError) as e:
        msg = str(e); print(S.red('Error: ') + msg, file=sys.stderr)
        hint = next((h for pat, h in ENGINE_HINTS if re.search(pat, msg)), '')
        if hint: print(S.dim('Hint:  ') + hint, file=sys.stderr)
    except (KeyboardInterrupt, EOFError):
        print('\nCancelled.', file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
