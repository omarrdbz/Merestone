import base64, hashlib, json, re, sys, tempfile, threading, unittest, urllib.error, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import merestone as ms
import ui_server
from test_cli import CAPS, notes, ready_ws, run

ROOT = Path(__file__).resolve().parents[1]


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k): return None


class UiServerTests(unittest.TestCase):
    """The local web interface: local-only safeguards and the same rules as the CLI."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = Path(self.tmp.name)

    def tearDown(self):
        if getattr(self, 'srv', None): self.srv.shutdown(); self.srv.server_close()
        self.tmp.cleanup()

    def start(self, root=None, start_dir=None):
        self.srv, self.app = ui_server.make_server(ms, root, 0, start_dir or self.d)
        ms.S.on = False
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = f'http://127.0.0.1:{self.app.port}'
        self.cookie = f'merestone_{self.app.port}={self.app.token}'

    def req(self, path, body=None, headers=None, cookie=True, xhdr=True, origin=True):
        h = dict(headers or {})
        if cookie: h.setdefault('Cookie', self.cookie)
        if xhdr: h.setdefault('X-Merestone', '1')
        data = None
        if body is not None:
            data = json.dumps(body).encode(); h.setdefault('Content-Type', 'application/json')
            if origin: h.setdefault('Origin', self.base)
        try:
            with urllib.request.urlopen(urllib.request.Request(self.base + path, data=data, headers=h)) as r:
                raw = r.read(); return r.status, r.headers, raw
        except urllib.error.HTTPError as e:
            return e.code, e.headers, e.read()

    def api(self, path, body=None, **kw):
        code, _, raw = self.req('/api/' + path, body, **kw)
        return code, json.loads(raw or b'{}')

    def evidence(self, kinds, data=b'evidence', bad_hash=False):
        return [{'kind': k, 'name': f'{k}.txt', 'sha256': '0' * 64 if bad_hash else hashlib.sha256(data + k.encode()).hexdigest(),
                 'data': base64.b64encode(data + k.encode()).decode()} for k in kinds]

    # ---------- safeguards ----------
    def test_page_requires_the_session_key_and_sets_a_strict_cookie(self):
        ws = ready_ws(self.d); self.start(ws)
        code, _, raw = self.req('/', cookie=False, xhdr=False)
        self.assertEqual(code, 403); self.assertIn(b'link printed', raw)
        self.assertEqual(self.req('/?key=wrong', cookie=False, xhdr=False)[0], 403)
        opener = urllib.request.build_opener(NoRedirect)
        with self.assertRaises(urllib.error.HTTPError) as cm:
            opener.open(self.base + '/?key=' + self.app.token)
        self.assertEqual(cm.exception.code, 303)
        cookie = cm.exception.headers['Set-Cookie']
        for part in ('HttpOnly', 'SameSite=Strict', self.app.token): self.assertIn(part, cookie)
        code, headers, raw = self.req('/', xhdr=False)
        self.assertEqual(code, 200); page = raw.decode()
        csp = headers['Content-Security-Policy']
        nonce = re.search(r"'nonce-([^']+)'", csp).group(1)
        self.assertIn(f'<script nonce="{nonce}">', page); self.assertNotIn('__NONCE__', page)
        for d in ("default-src 'none'", "connect-src 'self'", "frame-ancestors 'none'", "base-uri 'none'"): self.assertIn(d, csp)
        self.assertNotIn('unsafe-inline', csp.split('script-src')[1].split(';')[0])
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')

    def test_app_page_loads_nothing_from_the_network(self):
        page = (ROOT / 'ui' / 'app.html').read_text(encoding='utf-8')
        self.assertFalse(re.search(r'(src|href)\s*=\s*["\']?(https?:)?//', page), 'no external resources')
        self.assertNotIn('fetch("http', page); self.assertNotIn("fetch('http", page)
        self.assertNotIn('innerHTML=e.', page)

    def test_api_rejects_cross_site_and_foreign_hosts(self):
        ws = ready_ws(self.d); self.start(ws)
        self.assertEqual(self.api('state', cookie=False)[0], 403)
        self.assertEqual(self.api('state', xhdr=False)[0], 404)          # no custom header: not an API call
        self.assertEqual(self.api('set', {'field': 'name', 'value': 'x'}, origin=False)[0], 403)
        self.assertEqual(self.api('set', {'field': 'name', 'value': 'x'}, headers={'Origin': 'http://evil.example'})[0], 403)
        self.assertEqual(self.api('state', headers={'Host': f'evil.example:{self.app.port}'})[0], 421)   # DNS rebinding
        self.assertEqual(self.req('/api/state', headers={'Host': f'evil.example:{self.app.port}'})[0], 421)
        code, _, _ = self.req('/api/set', body=None, headers={'Content-Type': 'text/plain'})
        self.assertIn(code, (403, 404, 405))
        self.assertEqual(ms.Workspace(ws).arch()['system_name'], 'Fixture system')

    def test_server_binds_to_loopback_only(self):
        ws = ready_ws(self.d); self.start(ws)
        self.assertEqual(self.srv.server_address[0], '127.0.0.1')

    # ---------- same rules as the CLI ----------
    def test_full_flow_through_the_interface(self):
        ws = ready_ws(self.d, present=('retrieval', 'llm_generation', 'multi_tenant'), activities='DESIGN,TEST', protocols=[('AI-006', 'original,benign')])
        self.start(ws)
        code, st = self.api('state'); self.assertEqual(code, 200)
        self.assertFalse(st['workspace']['has_plan']); self.assertFalse([i for i in st['setup_items'] if i['blocking']])
        self.assertEqual(self.api('plan', {})[0], 200)
        _, st = self.api('state'); self.assertEqual(st['check']['exit_code'], 2)
        task = next(t for t in st['plan']['tasks'] if t['case_id'] == 'AI-006')
        self.assertEqual((task['alias'], task['bucket']), ('AI-006@ROUTE-1', 'TODO'))
        trial = {'task': 'AI-006@ROUTE-1', 'variant': 'original', 'result': 'FAIL', 'expected': 'A only', 'observed': 'B leaked',
                 'identity': 'tenant-a', 'adaptation': 'own query'}
        # a hash that does not match the bytes is refused and nothing is stored
        code, err = self.api('record', dict(trial, evidence=self.evidence(ms.TECH_KINDS, bad_hash=True)))
        self.assertEqual(code, 400); self.assertIn('different hash', err['error'])
        self.assertFalse((ws / 'evidence').exists() and any((ws / 'evidence').rglob('*.txt')))
        # same rule as the CLI: a decided trial needs all six technical kinds
        code, err = self.api('record', dict(trial, evidence=self.evidence(['response'])))
        self.assertEqual(code, 400); self.assertIn('needs evidence of', err['error'])
        code, out = self.api('record', dict(trial, evidence=self.evidence(['response', 'effect']), notes=[{'kind': k, 'text': 'n ' + k} for k in ('baseline', 'input', 'identity', 'reachability')]))
        self.assertEqual(code, 200, out); self.assertIn('6 evidence files hashed', out['output'])
        self.assertFalse((ws / 'staging' / 'uploads').exists(), 'temporary uploads are removed')
        _, st = self.api('state')
        staged = next(t for t in st['plan']['tasks'] if t['case_id'] == 'AI-006')['staged']
        resp = next(e for e in staged['evidence'] if e['kind'] == 'response')
        self.assertEqual(resp['sha256'], hashlib.sha256(b'evidenceresponse').hexdigest())
        self.assertEqual((ws / 'evidence' / resp['path']).read_bytes(), b'evidenceresponse')
        code, err = self.api('decide', {'task': 'AI-006@ROUTE-1', 'reviewer': 'R', 'observations': 'leak', 'cleanup_confirmed': False})
        self.assertEqual(code, 400); self.assertIn('cleaned up', err['error'])
        self.assertEqual(self.api('decide', {'task': 'AI-006@ROUTE-1', 'reviewer': 'R', 'observations': 'leak <script>', 'cleanup_confirmed': True})[0], 200)
        code, out = self.api('review', {'task': 'CORE-001@ROUTE-1', 'result': 'PASS', 'reviewer': 'R', 'observations': 'ok', 'notes': [{'kind': 'review', 'text': 'scope agreed'}]})
        self.assertEqual(code, 200, out)
        _, st = self.api('state')
        by = {t['case_id']: t for t in st['plan']['tasks']}
        self.assertEqual((by['AI-006']['result'], by['CORE-001']['result']), ('FAIL', 'PASS'))
        self.assertEqual(st['integrity_error'], ''); self.assertTrue(st['check']['integrity_verified'])
        self.assertEqual(run('-w', ws, 'status')[0], 2)          # the CLI reads the very same records
        # reports: written into reports/ and served only by exact name
        code, out = self.api('report', {'format': 'both', 'layout': 'document'})
        self.assertEqual(code, 200); self.assertEqual(sorted(Path(f).suffix for f in out['files']), ['.html', '.md'])
        html_name = next(f for f in out['files'] if f.endswith('.html'))
        code, headers, raw = self.req('/reports/' + html_name, xhdr=False)
        self.assertEqual(code, 200); self.assertIn(b'&lt;script&gt;', raw); self.assertNotIn(b'leak <script>', raw)
        self.assertIn("default-src 'none'", headers['Content-Security-Policy'])
        self.assertIn('attachment', self.req('/reports/' + html_name + '?download=1', xhdr=False)[1]['Content-Disposition'])
        for bad in ('../merestone.json', '..%2fmerestone.json', 'report-x/../../merestone.json', 'merestone.json'):
            self.assertEqual(self.req('/reports/' + bad, xhdr=False)[0], 404, bad)
        self.assertEqual(self.req('/reports/' + html_name, cookie=False, xhdr=False)[0], 403)

    def test_architecture_edits_and_freeze_rules(self):
        self.assertEqual(run('new', self.d / 'w', '--profile', 'rag')[0], 0); ws = self.d / 'w'
        self.start(ws)
        _, st = self.api('state')
        keys = {i['key'] for i in st['setup_items']}
        self.assertTrue({'authorization', 'snapshot', 'limits', 'access'} <= keys)
        code, err = self.api('plan', {})                                  # same guard as "merestone plan"
        self.assertEqual(code, 400); self.assertIn('Plan not frozen yet', err['error'])
        self.assertEqual(self.api('set', {'field': 'authorization', 'value': 'SEC-1'})[0], 200)
        self.assertEqual(self.api('set', {'field': 'limits', 'value': ['requests=10', 'duration=60', 'concurrency=1']})[0], 200)
        self.assertEqual(self.api('set', {'field': 'stop', 'value': 'real data'})[0], 200)
        self.assertEqual(self.api('set', {'field': 'boundary', 'value': 'app -> index -> model', 'route': 'ROUTE-1'})[0], 200)
        code, err = self.api('set', {'field': 'access', 'value': 'everything'})
        self.assertEqual(code, 400); self.assertIn('Access must be one of', err['error'])
        self.assertEqual(self.api('caps', {'assign': {'retrieval': 'present', 'tool_calling': 'absent'}, 'source': 'doc v2', 'route': 'ROUTE-1'})[0], 200)
        code, err = self.api('caps', {'assign': {'retreival': 'present'}})
        self.assertEqual(code, 400); self.assertIn('Did you mean: retrieval', err['error'] + err['hint'])
        self.assertEqual(self.api('stop-remove', {'index': 0})[0], 200)
        self.assertEqual(self.api('protocol', {'case': 'AI-006', 'variants': 'original,benign', 'min': 1, 'design': 'deterministic', 'rule': 'r', 'why': 'w'})[0], 200)
        a = ms.Workspace(ws).arch(); r = a['routes'][0]
        self.assertEqual((a['authorization_ref'], a['limits']['requests'], a['stop_conditions'], r['boundary']), ('SEC-1', 10, [], 'app -> index -> model'))
        self.assertEqual((r['capabilities']['retrieval'], r['capability_evidence']['retrieval']), ('present', 'doc v2'))
        self.assertEqual(r['test_protocols'][0]['case_id'], 'AI-006')
        self.assertEqual(self.api('plan', {'anyway': True})[0], 200)
        self.assertEqual(self.api('set', {'field': 'snapshot', 'value': 'v2'})[0], 200)
        _, st = self.api('state'); self.assertTrue(st['plan']['stale'])
        code, err = self.api('plan', {})
        self.assertEqual(code, 400); self.assertIn('changed after the plan was frozen', err['error'])
        self.assertEqual(self.api('plan', {'reason': 'snapshot set', 'approver': 'R'})[0], 200)
        _, st = self.api('state'); self.assertEqual((st['workspace']['series'], st['plan']['stale']), ('plan-002', False))

    def test_start_screen_creates_and_opens_workspaces(self):
        self.start(None, start_dir=self.d)
        _, st = self.api('state'); self.assertIsNone(st['workspace'])
        code, out = self.api('new', {'folder': 'harbor', 'profile': 'chat', 'name': 'Harbor Desk'})
        self.assertEqual(code, 200, out); self.assertTrue((self.d / 'harbor' / 'merestone.json').is_file())
        _, st = self.api('state'); self.assertEqual(st['arch']['system_name'], 'Harbor Desk')
        self.assertEqual(self.api('open', {'folder': str(self.d)})[0], 400)
        self.assertEqual(self.api('open', {'folder': 'harbor'})[0], 200)

    def test_static_data_and_fieldcards(self):
        ws = ready_ws(self.d); self.start(ws)
        _, s = self.api('static')
        self.assertEqual({c['key'] for c in s['capabilities']}, set(CAPS))
        self.assertNotIn('Other', {c['group'] for c in s['capabilities']}, 'every capability has a plain-language label')
        self.assertEqual(set(s['tech_kinds']), set(ms.TECH_KINDS)); self.assertTrue(set(s['kinds']) >= set(ms.EVIDENCE_KINDS))
        for g in s['guide']: self.assertTrue(set(g['caps']) <= set(CAPS))
        code, fc = self.api('fieldcard?case=AI-006'); self.assertEqual(code, 200); self.assertIn('RAG retrieval ACL', fc['html'])
        self.assertEqual(self.api('fieldcard?case=NOPE')[0], 404)

    def test_rev_changes_when_the_terminal_writes(self):
        ws = ready_ws(self.d); self.start(ws)
        _, a = self.api('rev')
        import time; time.sleep(0.02)
        self.assertEqual(run('-w', ws, 'set', 'name', 'Renamed from the terminal')[0], 0)
        _, b = self.api('rev'); self.assertNotEqual(a['rev'], b['rev'])

    def test_cli_exposes_the_ui_command(self):
        p = ms.build_parser(); help_text = p.format_help()
        self.assertIn('ui', help_text); self.assertIn('merestone ui', ms.QUICKSTART)
        sub = p._subparsers._group_actions[0].choices['ui'].format_help()
        for opt in ('--port', '--no-browser', '127.0.0.1'): self.assertIn(opt, sub)


if __name__ == '__main__':
    unittest.main()
