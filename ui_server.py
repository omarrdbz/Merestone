"""merestone ui: a local web interface over the same workspace records as the CLI.

The server binds to 127.0.0.1 only, uses the standard library only and never
contacts the network. Every change goes through the very same functions as the
CLI commands (cmd_caps, cmd_set, cmd_plan, cmd_record, cmd_decide, ...), so the
interface cannot relax a rule the terminal enforces; check-plan stays the source
of truth.

Local-only safeguards:
  * loopback bind; the Host header must name that loopback address (DNS rebinding);
  * a random session key, given once in the URL printed in the terminal and then
    kept in a SameSite=Strict, HttpOnly cookie;
  * every API call also needs a custom header (no simple cross-site requests) and
    a same-origin Origin header on writes;
  * a strict Content-Security-Policy with a per-response script nonce;
  * uploaded evidence is hashed in the browser and re-hashed here; a mismatch is
    rejected before anything is stored.
"""
from __future__ import annotations
import base64, contextlib, getpass, hashlib, hmac, io, json, os, re, secrets, shutil, sys, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import operational as op
import report_html as rh

HERE = Path(__file__).resolve().parent
APP_FILE = HERE / 'ui' / 'app.html'
MAX_BODY = 64 * 1024 * 1024          # JSON body, evidence included as base64
REPORT_NAME = re.compile(r'^report-[A-Za-z0-9._-]+\.(html|md)$')
ANSI = re.compile(r'\x1b\[[0-9;]*m')

# Plain-language description and group of every catalog capability.
CAP_INFO = {
    'llm_generation': ('Model', 'Generates text with a language model'),
    'model_inference': ('Model', 'Runs model inference (any model type)'),
    'predictive_model': ('Model', 'Uses a predictive or classic ML model'),
    'automated_judge': ('Model', 'A model judges, scores or grades outputs'),
    'guardrail': ('Model', 'A guardrail or filter checks inputs or outputs'),
    'external_provider': ('Model', 'Relies on an external model or API provider'),
    'streaming': ('Model', 'Streams responses as they are generated'),
    'retrieval': ('Data and memory', 'Searches documents or a knowledge base (RAG)'),
    'multi_tenant': ('Data and memory', 'Several customers, teams or tenants share it'),
    'persistent_memory': ('Data and memory', 'Remembers information between sessions'),
    'conversation_storage': ('Data and memory', 'Stores conversations'),
    'cache': ('Data and memory', 'Caches prompts, responses or embeddings'),
    'file_access': ('Data and memory', 'Reads or writes files'),
    'multimodal_input': ('Data and memory', 'Accepts images, audio or uploaded files'),
    'artifact_loading': ('Data and memory', 'Loads models or serialized artifacts'),
    'tool_calling': ('Tools and agents', 'Calls tools, functions or APIs by itself'),
    'effectful_operations': ('Tools and agents', 'Tools change things: send, write, pay, delete'),
    'human_approval': ('Tools and agents', 'A human approves some actions before they run'),
    'autonomous_loop': ('Tools and agents', 'Works autonomously in loops'),
    'delegation': ('Tools and agents', 'Delegates work to other agents'),
    'code_execution': ('Tools and agents', 'Executes generated code'),
    'text_to_sql': ('Tools and agents', 'Turns output into SQL queries'),
    'html_rendering': ('Tools and agents', 'Output is rendered as HTML in a browser'),
    'network_egress': ('Tools and agents', 'Fetches URLs or reaches the internet'),
    'scheduled_or_event_trigger': ('Tools and agents', 'Runs on a schedule or on external events'),
    'mcp_client': ('MCP', 'Connects to MCP servers as a client'),
    'mcp_host': ('MCP', 'Hosts MCP clients (an MCP host application)'),
    'mcp_server': ('MCP', 'Exposes its own MCP server'),
    'mcp_stdio': ('MCP', 'Uses MCP over stdio'),
    'mcp_http': ('MCP', 'Uses MCP over HTTP'),
    'oauth': ('MCP', 'Uses OAuth for authorization'),
    'oauth_proxy': ('MCP', 'Acts as an OAuth proxy for other services'),
    'api': ('Platform and pipeline', 'Exposes an API'),
    'deployment': ('Platform and pipeline', 'Has a deployment pipeline you can review'),
    'dependencies': ('Platform and pipeline', 'Depends on third-party packages or models'),
    'telemetry': ('Platform and pipeline', 'Produces logs, traces or telemetry'),
    'automated_scanner': ('Platform and pipeline', 'Uses automated security scanners'),
    'training': ('Platform and pipeline', 'You train models for it'),
    'fine_tuning': ('Platform and pipeline', 'You fine-tune models for it'),
}
KIND_INFO = {
    'baseline': 'The equivalent benign operation worked within the permission.',
    'input': 'The exact input or stimulus you sent.',
    'response': 'What the system answered.',
    'effect': 'The final effect: what changed, was retrieved, executed or sent.',
    'identity': 'Who acted: account, tenant, token or role used.',
    'reachability': 'Proof that the input reached the component under test.',
    'review': 'Documentary evidence of the review (minutes, document, screenshot).',
    'configuration': 'Relevant configuration extract.',
    'snapshot': 'Versions or state captured for this trial.',
    'metric': 'A measurement (rate, count, latency).',
}
TRUST_INFO = {   # what can change at a trust boundary (ms.TRUST_CHANGES), in plain language
    'permissions': ('Permissions', 'What is allowed changes: a filter or rule must hold here (e.g. only customer A documents).'),
    'identity': ('Identity', 'Who the request runs as changes: user session, service account, token or tenant.'),
    'authority': ('Authority', 'Who decides or executes changes: e.g. model output becomes a tool call or a write.'),
    'data_trust': ('Data trust', 'Content of lower trust enters: documents, web pages, tool output or user files.'),
}
ACTIVITY_INFO = {
    'DESIGN': 'Design review: requirements, architecture and responsibilities against documentation.',
    'CONFIG': 'Configuration review: settings, permissions and deployment, without attacking.',
    'TEST': 'Technical tests with a frozen protocol, variants and evidence.',
    'REDTEAM': 'Adversarial scenarios that chain several cases.',
}


class ApiError(Exception):
    def __init__(self, status, msg, hint=''):
        super().__init__(msg); self.status, self.hint = status, hint


class App:
    """State shared by request handlers: the open workspace and the session key."""

    def __init__(self, ms, root=None, start_dir=None):
        self.ms = ms
        self.root = Path(root).resolve() if root else None
        self.start_dir = Path(start_dir or os.getcwd()).resolve()
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.RLock()
        self.port = 0
        self._lib = None
        self._static = None

    # ---------- helpers ----------
    @property
    def lib(self):
        if self._lib is None: self._lib = op.library()
        return self._lib

    def ws(self):
        if not self.root: raise ApiError(409, 'No workspace is open.', 'Create or open one first.')
        return self.ms.Workspace(self.root)

    def run(self, fn, **kw):
        """Run a CLI command function in-process and capture what it prints."""
        a = SimpleNamespace(workspace=str(self.root), **kw)
        buf = io.StringIO()
        with self.lock, contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            code = fn(a)
        return {'ok': True, 'code': code, 'output': ANSI.sub('', buf.getvalue()).strip()}

    def rev(self):
        """Changes whenever the workspace changes on disk (also from the terminal)."""
        if not self.root: return 'none'
        parts = []
        for p in (self.root / self.ms.WS_FILE, self.root / 'architecture.json', self.root / 'staging', self.root / 'reports', self.root / 'plans'):
            try: st = p.stat(); parts.append(f'{p.name}:{st.st_mtime_ns}:{st.st_size}')
            except OSError: parts.append(p.name + ':-')
        for p in sorted((self.root / 'staging').glob('*.json')) if (self.root / 'staging').is_dir() else []:
            st = p.stat(); parts.append(f'{p.name}:{st.st_mtime_ns}')
        return hashlib.sha256('|'.join(parts).encode()).hexdigest()[:16]

    # ---------- read model ----------
    def static(self):
        if self._static is None:
            lib = self.lib
            per_cap = {k: [] for k in lib['capabilities']}
            for c in lib['cases']:
                for clause in c['applies_if']:
                    for k in clause:
                        if c['id'] not in per_cap[k]: per_cap[k].append(c['id'])
            caps = [{'key': k, 'group': CAP_INFO.get(k, ('Other', ''))[0], 'label': CAP_INFO.get(k, ('', k.replace('_', ' ')))[1],
                     'cases': per_cap[k]} for k in lib['capabilities']]
            cases = {c['id']: {'id': c['id'], 'title': c['title'], 'module': c['module'], 'activity': c['activity'], 'applies_if': c['applies_if'],
                               'variants': c.get('variants', []), 'example_ids': c.get('example_ids', []), 'technique_ids': c.get('technique_ids', []),
                               'control_ids': c.get('control_ids', []), 'objective': c.get('objective', '')}
                     for c in lib['cases']}
            for s in lib['scenarios']:
                cases[s['id']] = {'id': s['id'], 'title': s['title'], 'module': 'SCENARIOS', 'activity': 'REDTEAM', 'applies_if': s.get('applies_if', []),
                                  'variants': s.get('variants', []), 'example_ids': [], 'technique_ids': [], 'control_ids': [], 'objective': s.get('objective', '')}
            self._static = {
                'framework_version': op.VERSION, 'capabilities': caps, 'cases': cases,
                'guide': [{'q': q, 'caps': ks} for q, ks in self.ms.GUIDE],
                'items': {k: {'label': v[0], 'why': v[1], 'example': v[2]} for k, v in self.ms.ITEMS.items()},
                'gap_label': rh.GAP_LABEL, 'state_meta': rh.STATE_META, 'code_meta': {str(k): v for k, v in rh.CODE_META.items()},
                'kinds': KIND_INFO, 'tech_kinds': list(self.ms.TECH_KINDS), 'evidence_kinds': list(self.ms.EVIDENCE_KINDS),
                'activities': ACTIVITY_INFO, 'access': list(self.ms.ACCESS[:3]),
                'trust_changes': [{'key': k, 'label': TRUST_INFO[k][0], 'hint': TRUST_INFO[k][1]} for k in self.ms.TRUST_CHANGES], 'designs': list(self.ms.DESIGNS), 'profiles': list(self.ms.PROFILES),
                'mojo': {str(c): rh.mojo_svg(c, 5) for c in (0, 1, 2)}, 'mark': rh.MARK, 'user': getpass.getuser(),
            }
        return self._static

    # ---------- plan preview (the engine's own selection, nothing re-implemented) ----------
    def route_summary(self, arch, route_id):
        """Obligations one route would produce, by applicability and activity, with a few explained examples.

        Uses op.expected_tasks, the function that builds and verifies frozen plans, so the counts are
        exactly what freezing this architecture would produce for the route."""
        lib = self.lib; route = next(r for r in arch['routes'] if r['id'] == route_id)
        rules = {c['id']: c['applies_if'] for c in lib['cases'] + lib['scenarios']}
        specs = op.expected_tasks(dict(arch, routes=[route]), lib)
        res = {'total': len(specs), 'APPLICABLE': 0, 'UNKNOWN': 0, 'NOT_APPLICABLE': 0, 'activities': {}, 'modules': {}, 'examples': []}
        for s in specs:
            res[s['applicability']] += 1
            a = res['activities'].setdefault(s['activity'], {'APPLICABLE': 0, 'UNKNOWN': 0, 'NOT_APPLICABLE': 0}); a[s['applicability']] += 1
            m = res['modules'].setdefault(s['module'], {'APPLICABLE': 0, 'UNKNOWN': 0, 'NOT_APPLICABLE': 0}); m[s['applicability']] += 1
        res['activities'] = {k: res['activities'][k] for k in op.ACTIVITIES if k in res['activities']}
        caps = route['capabilities']
        def why(s):
            rule = rules[s['case_id']]
            if any(not clause for clause in rule): return {'core': True}
            if s['applicability'] == 'APPLICABLE':
                return {'present': next(cl for cl in rule if all(caps.get(k, 'unknown') == 'present' for k in cl))}
            if s['applicability'] == 'UNKNOWN':
                return {'unknown': sorted({k for cl in rule if all(caps.get(x, 'unknown') != 'absent' for x in cl) for k in cl if caps.get(k, 'unknown') == 'unknown'})}
            return {'absent': sorted({k for cl in rule for k in cl if caps.get(k, 'unknown') == 'absent'})}
        ex = lambda s: {'alias': self.ms.alias(s), 'case_id': s['case_id'], 'title': s['title'], 'activity': s['activity'], 'module': s['module'],
                        'applicability': s['applicability'], 'why': why(s)}
        picks = []
        for act in op.ACTIVITIES:                         # one applicable example per activity, preferring capability-driven ones
            cand = [s for s in specs if s['activity'] == act and s['applicability'] == 'APPLICABLE']
            cand.sort(key=lambda s: 'core' in why(s))
            if cand: picks.append(cand[0])
        picks += sorted((s for s in specs if s['applicability'] == 'UNKNOWN'), key=lambda s: (len(why(s)['unknown']), s['case_id']))[:2]
        picks += [s for s in specs if s['applicability'] == 'NOT_APPLICABLE'][:1]
        res['examples'] = [ex(s) for s in picks[:6]]
        return res

    def revision(self, ws, plan, arch):
        """What freezing a revision now would change, per route, compared with the frozen plan."""
        specs = op.expected_tasks(arch, self.lib)
        before = {t['task_id']: t for t in plan['tasks']}; after = {s['task_id']: s for s in specs}
        fields = ('case_revision', 'applicability', 'scope', 'access', 'control_ids', 'threat_ids', 'technique_ids', 'test_protocol', 'boundary')
        routes = {}
        def bump(rid, k): routes.setdefault(rid, {'added': 0, 'removed': 0, 'changed': 0, 'results': 0})[k] += 1
        for k in after.keys() - before.keys(): bump(after[k]['route_id'], 'added')
        for k in before.keys() - after.keys(): bump(before[k]['route_id'], 'removed')
        for k in before.keys() & after.keys():
            if any(before[k][f] != after[k][f] for f in fields): bump(after[k]['route_id'], 'changed')
        for t in plan['tasks']:
            if t['result']: bump(t['route_id'], 'results')
        total = {k: sum(r[k] for r in routes.values()) for k in ('added', 'removed', 'changed', 'results')}
        return dict(total, routes=routes, record=ws.cfg.get('plan'), series=ws.cfg.get('series'))

    def preview(self, route_id, activities):
        """Draft preview: the saved architecture with this route's activities replaced (nothing is written)."""
        with self.lock:
            arch = self.ws().arch()
            route = next((r for r in arch['routes'] if r['id'] == route_id), None)
            if not route: raise ApiError(404, f'Unknown route {route_id}.')
            acts = [a.strip().upper() for a in activities.split(',') if a.strip()]
            if not acts or set(acts) - set(op.ACTIVITIES): raise ApiError(400, 'Choose activities among DESIGN, CONFIG, TEST and REDTEAM.')
            route['activity_types'] = list(dict.fromkeys(acts))
            return {'route': route_id, 'activities': route['activity_types'], 'draft': self.route_summary(arch, route_id)}

    def state(self):
        ms = self.ms
        if not self.root:
            near = sorted(str(c.name) for c in self.start_dir.iterdir() if c.is_dir() and (c / ms.WS_FILE).is_file()) if self.start_dir.is_dir() else []
            framework = Path(__file__).resolve().parent
            default_folder = str(framework.parent / 'assessments' / 'my-assessment') if self.start_dir.is_relative_to(framework) else 'my-assessment'
            return {'workspace': None, 'start_dir': str(self.start_dir), 'default_folder': default_folder, 'nearby': near, 'rev': 'none'}
        with self.lock:
            ws = self.ws(); arch = ws.arch()
            items = []
            for it in ms.setup_items(arch):
                items.append(dict(it, command=ms.item_command(it)))
            try:
                preview = {r['id']: self.route_summary(arch, r['id']) for r in arch['routes']}
            except (KeyError, ValueError, StopIteration):
                preview = {}
            res = {'workspace': {'root': str(ws.root), 'name': ws.root.name, 'series': ws.cfg.get('series'), 'profile': ws.cfg.get('profile'),
                                 'history': ws.cfg.get('history', [])[-80:], 'has_plan': ws.has_plan(), 'evidence_dir': ws.cfg['evidence_dir']},
                   'arch': arch, 'readiness': op.ready(arch), 'setup_items': items, 'preview': preview, 'rev': self.rev(),
                   'reports': self.reports(ws)}
            if ws.has_plan():
                plan = ws.plan()
                try:
                    _, r = ws.check(plan); res['check'] = r; res['integrity_error'] = ''
                except (ValueError, OSError, KeyError) as e:
                    res['check'] = None; res['integrity_error'] = str(e)
                staged = {}
                sdir = ws.root / 'staging'
                if sdir.is_dir():
                    for f in sdir.glob('TASK-*.json'):
                        try: s = op.read(f); staged[s['task_id']] = {'trials': s['trials'], 'evidence': s['evidence']}
                        except (ValueError, OSError, KeyError): pass
                tasks = []
                for t in plan['tasks']:
                    tasks.append({k: t[k] for k in ('task_id', 'case_id', 'title', 'module', 'activity', 'route_id', 'boundary', 'actor', 'applicability',
                                                     'scope', 'access', 'test_protocol', 'execution', 'result', 'rationale', 'observations', 'reviewer',
                                                     'evidence_ids', 'trials', 'cleanup_confirmed', 'exclusion', 'control_ids', 'technique_ids', 'example_ids')}
                                 | {'alias': ms.alias(t), 'bucket': rh.bucket(t), 'state': ms.task_state(t), 'staged': staged.get(t['task_id'])})
                frozen = plan['architecture']
                res['plan'] = {'plan_id': plan['plan_id'], 'created_at': plan['created_at'], 'series': ws.cfg.get('series'),
                               'record': ws.cfg.get('plan'), 'stale': op.digest(arch) != plan['architecture_sha256'],
                               'snapshot_ref': frozen['snapshot_ref'], 'tasks': tasks,
                               'evidence': plan['evidence'], 'amendments': plan.get('amendments', []),
                               # the frozen description of each route: tasks are explained with what was frozen, not later edits
                               'routes': [{k: x.get(k, d) for k, d in (('id', ''), ('access', ''), ('scope', ''), ('activity_types', []), ('actor', ''), ('actor_permissions', ''),
                                                                      ('boundary', ''), ('trust_boundaries', []), ('capabilities', {}), ('capability_evidence', {}), ('test_protocols', []))}
                                          | {'check': ms.route_check(frozen, x)} for x in frozen['routes']]}
                try:
                    res['revision'] = self.revision(ws, plan, arch)
                except (KeyError, ValueError):
                    res['revision'] = None
            return res

    def reports(self, ws):
        d = ws.root / 'reports'
        if not d.is_dir(): return []
        rows = [{'name': p.name, 'bytes': p.stat().st_size, 'mtime': p.stat().st_mtime} for p in d.iterdir() if p.is_file() and REPORT_NAME.match(p.name)]
        return sorted(rows, key=lambda r: r['mtime'], reverse=True)[:30]

    def fieldcard(self, case_id):
        c = next((c for c in self.lib['cases'] if c['id'] == case_id), None)
        if not c: raise ApiError(404, f'Unknown case {case_id}.')
        return {'html': rh.md(op.render_case(c, self.lib))}

    # ---------- write model (every write goes through a CLI command) ----------
    def act(self, action, b):
        ms = self.ms
        s = lambda k, d='': (str(b.get(k)) if b.get(k) is not None else d).strip()
        if action == 'new':
            folder = s('folder')
            if not folder: raise ApiError(400, 'Choose a folder name for the workspace.')
            target = Path(folder) if Path(folder).is_absolute() else self.start_dir / folder
            out = self.run(ms.cmd_new, folder=str(target), profile=s('profile', 'chat'), id=s('id') or None, name=s('name') or None,
                           guided=False, manifest_dir=None, inside_framework=False)
            self.root = target.resolve(); return out
        if action == 'open':
            folder = s('folder'); target = (Path(folder) if Path(folder).is_absolute() else self.start_dir / folder).resolve()
            if not (target / ms.WS_FILE).is_file(): raise ApiError(400, f'"{folder}" is not a Merestone workspace.', 'Pick a folder that contains merestone.json.')
            self.root = target; return {'ok': True, 'output': f'Opened {target}'}
        self.ws()
        if action == 'caps':
            assign = [f'{k}={v}' for k, v in (b.get('assign') or {}).items()]
            if not assign: raise ApiError(400, 'Nothing to change.')
            return self.run(ms.cmd_caps, assign=assign, source=s('source') or None, route=s('route') or None)
        if action == 'set':
            value = b.get('value')
            value = [str(x) for x in value] if isinstance(value, list) else [str(value or '')]
            if not ' '.join(value).strip(): raise ApiError(400, 'Write a value first.')
            return self.run(ms.cmd_set, field=s('field'), value=value, route=s('route') or None)
        if action == 'stop-remove':
            with self.lock:
                ws = self.ws(); arch = ws.arch(); i = int(b.get('index', -1))
                if not 0 <= i < len(arch['stop_conditions']): raise ApiError(400, 'No such stop condition.')
                removed = arch['stop_conditions'].pop(i); ws.save_arch(arch); ws.log('ui: remove stop condition', 'architecture.json')
            return {'ok': True, 'output': f'Removed stop condition: {removed}'}
        if action == 'route':
            what = s('op')
            if what not in ('add', 'edit', 'remove'): raise ApiError(400, 'Unknown route action.')
            opt = lambda k: b.get(k) if b.get(k) is not None else None
            trust = b.get('trust')
            if trust is not None and not (isinstance(trust, list) and all(isinstance(x, dict) for x in trust)):
                raise ApiError(400, 'Trust boundaries must be a list of objects.')
            return self.run(ms.cmd_route, action=what, id=s('route'), actor=opt('actor'), permissions=opt('permissions'), path=opt('path'),
                            access=opt('access'), activities=opt('activities'), scope=opt('scope'), check=opt('check'), trust=trust,
                            no_trust=False, like=s('like') or None, copy_caps=bool(b.get('copy_caps')))
        if action == 'protocol':
            return self.run(ms.cmd_protocol, case=s('case'), variants=s('variants'), min=int(b.get('min') or 1), design=s('design', 'deterministic'),
                            rule=s('rule'), why=s('why'), route=s('route') or None)
        if action == 'plan':
            return self.run(ms.cmd_plan, reason=s('reason') or None, approver=s('approver') or None, anyway=bool(b.get('anyway')))
        if action in ('record', 'review'):
            return self.record(action, b)
        if action == 'decide':
            return self.run(ms.cmd_decide, task=s('task'), reviewer=s('reviewer'), observations=s('observations'),
                            cleanup_confirmed=bool(b.get('cleanup_confirmed')), inconclusive=bool(b.get('inconclusive')))
        if action == 'report':
            ws = self.ws(); before = {r['name'] for r in self.reports(ws)}
            fmt = s('format', 'html'); layout = s('layout', 'board')
            if fmt not in ('md', 'html', 'both') or layout not in ('board', 'document'): raise ApiError(400, 'Unknown report format or layout.')
            out = self.run(ms.cmd_report, format=fmt, layout=layout, open=False, findings=[], retest_bundle=None)
            out['files'] = [r['name'] for r in self.reports(ws) if r['name'] not in before]
            return out
        raise ApiError(404, f'Unknown action {action}.')

    def record(self, action, b):
        ms = self.ms
        s = lambda k, d='': (str(b.get(k)) if b.get(k) is not None else d).strip()
        ws = self.ws(); tmp = ws.root / 'staging' / 'uploads' / secrets.token_hex(8)
        specs, notes = [], []
        try:
            for item in b.get('evidence') or []:
                kind = str(item.get('kind', '')).strip()
                try: data = base64.b64decode(item.get('data', ''), validate=True)
                except (ValueError, TypeError): raise ApiError(400, f'Evidence "{kind}" could not be decoded.')
                digest = hashlib.sha256(data).hexdigest()
                if digest != str(item.get('sha256', '')).lower():
                    raise ApiError(400, f'Evidence "{kind}" arrived with a different hash than the one computed in your browser.',
                                   'Nothing was stored. Drop the file again.')
                name = ms.safe(Path(str(item.get('name') or 'file')).name) or 'file'
                dest = tmp / kind / name; dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(data)
                specs.append(f'{kind}={dest}')
            for item in b.get('notes') or []:
                text = str(item.get('text', '')).strip()
                if text: notes.append(f"{str(item.get('kind', '')).strip()}={text}")
            common = dict(evidence=specs or None, note=notes or None, collector=s('collector') or None, origin=s('origin', 'manual capture (merestone ui)'),
                          classification=s('classification', 'internal'), redaction=[x for x in (b.get('redaction') or []) if str(x).strip()] or None,
                          trial_id=s('trial_id') or None)
            if action == 'review':
                return self.run(ms.cmd_review, task=s('task'), result=s('result', 'PASS').upper(), reviewer=s('reviewer'), observations=s('observations'), **common)
            return self.run(ms.cmd_record, task=s('task'), variant=s('variant'), result=s('result', 'PASS').upper(), execution=s('execution', 'completed'),
                            expected=s('expected') or None, observed=s('observed') or None, identity=s('identity') or None,
                            reachability=s('reachability', 'reached'), blocking_control=s('blocking_control') or None,
                            example=s('example') or None, technique=s('technique') or None, adaptation=s('adaptation') or None,
                            baseline_failed=bool(b.get('baseline_failed')), rationale=s('rationale') or None, parameters=s('parameters') or None, **common)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
            with contextlib.suppress(OSError): (ws.root / 'staging' / 'uploads').rmdir()


def csp(nonce=None, report=False):
    script = "'unsafe-inline'" if report else f"'nonce-{nonce}'"
    return (f"default-src 'none'; script-src {script}; style-src 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; "
            "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


class Handler(BaseHTTPRequestHandler):
    app: App = None
    server_version = 'merestone-ui'
    sys_version = ''

    def log_message(self, fmt, *args):  # quiet: the terminal shows only what matters
        pass

    # ---------- plumbing ----------
    def send(self, status, body, ctype='application/json; charset=utf-8', headers=None):
        data = body if isinstance(body, bytes) else body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', ctype); self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store'); self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer'); self.send_header('X-Frame-Options', 'DENY')
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin'); self.send_header('Cross-Origin-Resource-Policy', 'same-origin')
        for k, v in (headers or {}).items(): self.send_header(k, v)
        self.end_headers()
        if self.command != 'HEAD': self.wfile.write(data)

    def json(self, status, obj): self.send(status, json.dumps(obj, ensure_ascii=False))

    def cookie_name(self): return f'merestone_{self.app.port}'

    def host_ok(self):
        return self.headers.get('Host', '') in (f'127.0.0.1:{self.app.port}', f'localhost:{self.app.port}')

    def session_ok(self):
        raw = self.headers.get('Cookie', '')
        for part in raw.split(';'):
            k, _, v = part.strip().partition('=')
            if k == self.cookie_name() and hmac.compare_digest(v, self.app.token): return True
        return False

    def origin_ok(self):
        o = self.headers.get('Origin')
        return o in (f'http://127.0.0.1:{self.app.port}', f'http://localhost:{self.app.port}')

    def page(self, status, title, text):
        html = (f'<!doctype html><meta charset="utf-8"><title>{rh.E(title)}</title><body style="font:16px system-ui;margin:40px;max-width:60ch;'
                f'background:#EEF1EE;color:#18221F"><h1 style="font-size:22px">{rh.E(title)}</h1><p>{rh.E(text)}</p></body>')
        self.send(status, html, 'text/html; charset=utf-8', {'Content-Security-Policy': csp('x')})

    # ---------- routes ----------
    def do_HEAD(self): self.do_GET()

    def do_GET(self):
        if not self.host_ok():
            if self.path.startswith('/api/'): return self.json(421, {'error': 'Wrong host.'})
            return self.page(421, 'Wrong host', 'Open Merestone through the 127.0.0.1 address printed in the terminal.')
        url = urlsplit(self.path); q = parse_qs(url.query)
        if url.path == '/':
            key = (q.get('key') or [''])[0]
            if key:
                if not hmac.compare_digest(key, self.app.token):
                    return self.page(403, 'This link has expired', 'Use the link printed by "merestone ui" in your terminal.')
                cookie = f'{self.cookie_name()}={self.app.token}; Path=/; HttpOnly; SameSite=Strict'
                self.send_response(303); self.send_header('Location', '/'); self.send_header('Set-Cookie', cookie)
                self.send_header('Cache-Control', 'no-store'); self.send_header('Content-Length', '0'); self.end_headers(); return
            if not self.session_ok():
                return self.page(403, 'Open the link from your terminal', 'For your safety this local page only opens through the link printed by "merestone ui" (it carries a one-time session key).')
            nonce = secrets.token_urlsafe(16)
            body = APP_FILE.read_text(encoding='utf-8').replace('__NONCE__', nonce)
            return self.send(200, body, 'text/html; charset=utf-8', {'Content-Security-Policy': csp(nonce)})
        if url.path == '/favicon.ico': return self.send(204, b'', 'image/x-icon')
        if not self.session_ok(): return self.json(403, {'error': 'Session key missing.', 'hint': 'Open the link printed in the terminal.'})
        if url.path.startswith('/reports/'):
            return self.report_file(url.path[len('/reports/'):], 'download' in q)
        if not url.path.startswith('/api/') or self.headers.get('X-Merestone') != '1':
            return self.json(404, {'error': 'Not found.'})
        try:
            if url.path == '/api/static': return self.json(200, self.app.static())
            if url.path == '/api/state': return self.json(200, self.app.state())
            if url.path == '/api/rev': return self.json(200, {'rev': self.app.rev()})
            if url.path == '/api/fieldcard': return self.json(200, self.app.fieldcard((q.get('case') or [''])[0]))
            if url.path == '/api/preview': return self.json(200, self.app.preview((q.get('route') or [''])[0], (q.get('activities') or [''])[0]))
            return self.json(404, {'error': 'Not found.'})
        except Exception as e:  # noqa: BLE001 - report every failure to the page
            return self.fail(e)

    def do_POST(self):
        if not self.host_ok(): return self.json(421, {'error': 'Wrong host.'})
        if not (self.session_ok() and self.origin_ok() and self.headers.get('X-Merestone') == '1'):
            return self.json(403, {'error': 'Request refused: it did not come from this Merestone page.'})
        url = urlsplit(self.path)
        if not url.path.startswith('/api/'): return self.json(404, {'error': 'Not found.'})
        n = int(self.headers.get('Content-Length') or 0)
        if n > MAX_BODY: return self.json(413, {'error': f'Upload too large (limit {MAX_BODY // (1024 * 1024)} MB per request).'})
        if not (self.headers.get('Content-Type') or '').startswith('application/json'): return self.json(415, {'error': 'JSON expected.'})
        try:
            body = json.loads(self.rfile.read(n) or b'{}')
            if not isinstance(body, dict): raise ApiError(400, 'JSON object expected.')
            return self.json(200, self.app.act(url.path[len('/api/'):], body))
        except Exception as e:  # noqa: BLE001
            return self.fail(e)

    def do_OPTIONS(self): self.json(403, {'error': 'Cross-origin requests are not allowed.'})
    do_PUT = do_DELETE = do_PATCH = do_OPTIONS

    def fail(self, e):
        ms = self.app.ms
        if isinstance(e, ApiError): return self.json(e.status, {'error': str(e), 'hint': e.hint})
        if isinstance(e, ms.UserError): return self.json(400, {'error': str(e), 'hint': e.hint})
        if isinstance(e, json.JSONDecodeError): return self.json(400, {'error': 'Malformed JSON.'})
        if isinstance(e, (ValueError, KeyError, TypeError, OSError)):
            msg = str(e); hint = next((h for pat, h in ms.ENGINE_HINTS if re.search(pat, msg)), '')
            return self.json(400, {'error': msg, 'hint': hint})
        return self.json(500, {'error': f'Unexpected error: {type(e).__name__}: {e}'})

    def report_file(self, name, download):
        if not REPORT_NAME.match(name) or not self.app.root: return self.json(404, {'error': 'Not found.'})
        base = (self.app.root / 'reports').resolve(); p = (base / name).resolve()
        if p.parent != base or not p.is_file(): return self.json(404, {'error': 'Not found.'})
        data = p.read_bytes()
        headers = {'Content-Security-Policy': csp(report=True)}
        if download: headers['Content-Disposition'] = f'attachment; filename="{name}"'
        ctype = 'text/html; charset=utf-8' if name.endswith('.html') else 'text/plain; charset=utf-8'
        return self.send(200, data, ctype, headers)


def make_server(ms, root=None, port=0, start_dir=None):
    app = App(ms, root, start_dir)
    handler = type('BoundHandler', (Handler,), {'app': app})
    srv = ThreadingHTTPServer(('127.0.0.1', port), handler)
    srv.daemon_threads = True
    app.port = srv.server_address[1]
    return srv, app


def serve(ms, root=None, port=0, open_browser=True, start_dir=None):
    ms.S.on = False
    srv, app = make_server(ms, root, port, start_dir)
    url = f'http://127.0.0.1:{app.port}/?key={app.token}'
    print('Merestone UI running on this computer only (nothing is sent to the network).')
    print(f'  Workspace: {app.root or "(none yet: create or open one in the page)"}')
    print(f'  Open:      {url}')
    print('  Keep this window open while you work; press Ctrl+C to stop.')
    sys.stdout.flush()
    if open_browser:
        import webbrowser
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        print('\nStopped.')
    finally:
        srv.server_close()
    return 0
