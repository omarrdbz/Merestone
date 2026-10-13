import contextlib, copy, io, json, sys, tempfile, unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import jsonutil
import operational as op
import merestone as ms

ROOT = Path(__file__).resolve().parents[1]

CAPS = op.library()['capabilities']


def run(*args):
    """Run the CLI in-process; return (exit_code, stdout, stderr)."""
    o, e = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(o), contextlib.redirect_stderr(e):
        code = ms.main([str(a) for a in args])
    return code, o.getvalue(), e.getvalue()


def ready_ws(base, present=(), activities='DESIGN', protocols=()):
    """A workspace with every readiness field set through the CLI only."""
    ws = Path(base) / 'ws'
    assert run('new', ws, '--profile', 'chat', '--name', 'Fixture system')[0] == 0
    w = ('-w', ws)
    for args in (('set', 'authorization', 'AUTH-1 signed scope'), ('set', 'snapshot', 'app 1.0 / model x / index 7'),
                 ('set', 'reviewer', 'Fixture Reviewer'), ('set', 'inventory-evidence', 'architecture doc v2'),
                 ('set', 'stop', 'real customer data appears'), ('set', 'limits', 'requests=100', 'duration=600', 'concurrency=1'),
                 ('set', 'access', 'white-box'), ('set', 'activities', activities)):
        code, _, err = run(*w, *args); assert code == 0, err
    assign = [f'{k}={"present" if k in present else "absent"}' for k in CAPS]
    code, _, err = run(*w, 'caps', *assign, '--source', 'fixture configuration'); assert code == 0, err
    for case, variants in protocols:
        code, _, err = run(*w, 'protocol', case, '--variants', variants, '--rule', 'fixture rule', '--why', 'fixture'); assert code == 0, err
    return ws


def notes(prefix='x'):
    return ['--note'] + [f'{k}={prefix} {k}' for k in ms.TECH_KINDS]


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.d = self.tmp.name
    def tearDown(self): self.tmp.cleanup()

    def test_quickstart_without_command(self):
        code, out, _ = run()
        self.assertEqual(code, 0); self.assertIn('Quick start', out)

    def test_guide_maps_to_real_capabilities(self):
        for _, keys in ms.GUIDE: self.assertTrue(set(keys) <= set(CAPS), keys)

    def test_guided_new_sets_states_and_sources(self):
        answers = iter(['y', 'y', 'n', 'n', 'n', 'n', '?', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'n', 'architecture doc v2', 'Harbor Desk'])
        with mock.patch('builtins.input', lambda _='': next(answers)):
            code, _, err = run('new', Path(self.d) / 'g', '--profile', 'rag', '--guided')
        self.assertEqual(code, 0, err)
        a = op.read(Path(self.d) / 'g' / 'architecture.json'); r = a['routes'][0]
        self.assertEqual(a['system_name'], 'Harbor Desk')
        self.assertEqual(r['capabilities']['retrieval'], 'present'); self.assertEqual(r['capability_evidence']['retrieval'], 'architecture doc v2')
        self.assertEqual(r['capabilities']['tool_calling'], 'absent')
        self.assertEqual(r['capabilities']['persistent_memory'], 'unknown'); self.assertNotIn('persistent_memory', r['capability_evidence'])

    def test_new_never_overwrites(self):
        p = Path(self.d) / 'busy'; p.mkdir(); (p / 'keep.txt').write_text('x')
        code, _, err = run('new', p)
        self.assertEqual(code, 2); self.assertIn('not empty', err); self.assertEqual((p / 'keep.txt').read_text(), 'x')

    def test_typo_gets_suggestion(self):
        ws = Path(self.d) / 'w'; run('new', ws)
        code, _, err = run('-w', ws, 'caps', 'retreival=present')
        self.assertEqual(code, 2); self.assertIn('Did you mean: retrieval', err)

    def test_status_before_plan_explains_fixes(self):
        ws = Path(self.d) / 'w'; run('new', ws)
        code, out, _ = run('-w', ws, 'status')
        self.assertEqual(code, 2); self.assertIn('merestone set authorization', out); self.assertIn('merestone plan', out)
        self.assertEqual(out.count('merestone set reviewer'), 1)
        code, out, err = run('-w', ws, 'plan')
        self.assertEqual(code, 2); self.assertIn('--anyway', err); self.assertFalse((ws / 'plans/plan-001.json').exists())
        self.assertEqual(run('-w', ws, 'plan', '--anyway')[0], 0)

    def test_documentary_assessment_reaches_code_0_with_cli_only(self):
        ws = ready_ws(self.d)
        self.assertEqual(run('-w', ws, 'plan')[0], 0)
        plan = ms.Workspace(ws).plan()
        todo = [ms.alias(t) for t in plan['tasks'] if t['applicability'] == 'APPLICABLE']
        self.assertTrue(todo and all(a.startswith(('CORE-', 'CFG-')) for a in todo))
        self.assertEqual(run('-w', ws, 'status')[0], 2)
        for a in todo:
            code, _, err = run('-w', ws, 'review', a, '--result', 'PASS', '--note', 'review=checked against scope', '--reviewer', 'Rev', '--observations', 'ok')
            self.assertEqual(code, 0, err)
        code, out, _ = run('-w', ws, 'status')
        self.assertEqual(code, 0, out); self.assertIn('complete, no FAIL', out)
        self.assertEqual(run('-w', ws, 'report')[0], 0)
        self.assertEqual(len(list((ws / 'reports').glob('report-*.md'))), 1)
        # every decision produced a new plan record; the frozen original is untouched
        self.assertEqual(op.read(ws / 'plans/plan-001.json')['tasks'], plan['tasks'])
        self.assertEqual(len(list((ws / 'plans').glob('plan-001.r*.json'))), len(todo))

    def test_technical_trials_hash_evidence_and_decide(self):
        ws = ready_ws(self.d, present=('retrieval', 'llm_generation', 'multi_tenant'), activities='DESIGN,TEST',
                      protocols=[('AI-006', 'original,benign')])
        run('-w', ws, 'plan'); w = ('-w', ws)
        common = ('--expected', 'only tenant A docs', '--identity', 'tenant-a', '--adaptation', 'own query')
        code, _, err = run(*w, 'record', 'AI-006@ROUTE-1', '--variant', 'original', '--result', 'PASS', '--observed', 'only A', *common, *notes())
        self.assertEqual(code, 0, err)
        code, _, err = run(*w, 'decide', 'AI-006', '--reviewer', 'R', '--observations', 'o', '--cleanup-confirmed')
        self.assertEqual(code, 2); self.assertIn('Missing: benign', err)
        code, _, err = run(*w, 'record', 'AI-006', '--variant', 'benign', '--result', 'PASS', '--observed', 'only A', *common, *notes('b'))
        self.assertEqual(code, 0, err)
        code, _, err = run(*w, 'decide', 'AI-006', '--reviewer', 'R', '--observations', 'o', '--cleanup-confirmed')
        self.assertEqual(code, 0, err)
        t = ms.resolve(ms.Workspace(ws).plan(), 'AI-006')
        self.assertEqual((t['result'], len(t['trials']), len(t['evidence_ids'])), ('PASS', 2, 12))
        code, out, _ = run(*w, 'status')
        self.assertEqual(code, 2); self.assertIn('1 PASS', out)

    def test_fail_is_decided_even_with_partial_sample(self):
        ws = ready_ws(self.d, present=('retrieval', 'llm_generation', 'multi_tenant'), activities='DESIGN,TEST',
                      protocols=[('AI-006', 'original,neighbor,benign')])
        run('-w', ws, 'plan')
        run('-w', ws, 'record', 'AI-006', '--variant', 'original', '--result', 'FAIL', '--expected', 'A only', '--observed', 'B leaked',
            '--identity', 'tenant-a', '--adaptation', 'own query', *notes())
        code, out, err = run('-w', ws, 'decide', 'AI-006', '--reviewer', 'R', '--observations', 'leak', '--cleanup-confirmed')
        self.assertEqual(code, 0, err); self.assertIn('FAIL', out)
        self.assertEqual(ms.resolve(ms.Workspace(ws).plan(), 'AI-006')['result'], 'FAIL')

    def test_record_lists_missing_evidence_kinds(self):
        ws = ready_ws(self.d, present=('retrieval', 'llm_generation', 'multi_tenant'), activities='DESIGN,TEST', protocols=[('AI-006', 'original')])
        run('-w', ws, 'plan')
        code, _, err = run('-w', ws, 'record', 'AI-006', '--variant', 'original', '--result', 'PASS', '--expected', 'e', '--observed', 'o',
                           '--identity', 'i', '--adaptation', 'a', '--note', 'response=r')
        self.assertEqual(code, 2)
        for k in ('baseline', 'input', 'effect', 'identity', 'reachability'): self.assertIn(k, err)

    def test_input_provenance_required(self):
        ws = ready_ws(self.d, present=('retrieval', 'llm_generation', 'multi_tenant'), activities='DESIGN,TEST', protocols=[('AI-006', 'original')])
        run('-w', ws, 'plan')
        code, _, err = run('-w', ws, 'record', 'AI-006', '--variant', 'original', '--result', 'PASS', '--expected', 'e', '--observed', 'o', '--identity', 'i', *notes())
        self.assertEqual(code, 2); self.assertIn('--adaptation', err)

    def test_tampered_evidence_is_detected(self):
        ws = ready_ws(self.d); run('-w', ws, 'plan')
        a = next(ms.alias(t) for t in ms.Workspace(ws).plan()['tasks'] if t['applicability'] == 'APPLICABLE')
        run('-w', ws, 'review', a, '--result', 'PASS', '--note', 'review=checked', '--reviewer', 'R', '--observations', 'ok')
        f = next((ws / 'evidence').rglob('review-*'))
        f.write_text('edited later')
        code, _, err = run('-w', ws, 'status')
        self.assertEqual(code, 2); self.assertIn('changed after it was recorded', err)

    def test_revision_requires_reason_and_keeps_history(self):
        ws = ready_ws(self.d); run('-w', ws, 'plan')
        run('-w', ws, 'caps', 'retrieval=present', '--source', 'new doc')
        code, _, err = run('-w', ws, 'plan')
        self.assertEqual(code, 2); self.assertIn('--reason', err)
        code, _, err = run('-w', ws, 'plan', '--reason', 'RAG added', '--approver', 'Owner')
        self.assertEqual(code, 0, err)
        w = ms.Workspace(ws); self.assertEqual(w.cfg['series'], 'plan-002')
        self.assertEqual(w.plan()['amendments'][0]['reason'], 'RAG added')
        self.assertTrue((ws / 'plans/plan-001.json').exists() and (ws / 'manifests/plan-001.manifest.json').exists())

    def test_unchanged_plan_is_not_refrozen(self):
        ws = ready_ws(self.d); run('-w', ws, 'plan')
        code, out, _ = run('-w', ws, 'plan')
        self.assertEqual(code, 0); self.assertIn('Nothing to freeze', out)

    def test_aliases_resolve_and_suggest(self):
        ws = ready_ws(self.d, present=('retrieval',), activities='DESIGN,TEST'); run('-w', ws, 'plan')
        plan = ms.Workspace(ws).plan()
        self.assertEqual(ms.resolve(plan, 'AI-006@ROUTE-1'), ms.resolve(plan, 'AI-006'))
        with self.assertRaises(ms.UserError) as cm: ms.resolve(plan, 'AI-0066')
        self.assertIn('Did you mean', cm.exception.hint)
        code, out, _ = run('-w', ws, 'tasks', '--module', 'RAG')
        self.assertEqual(code, 0); self.assertIn('AI-006@ROUTE-1', out)

    def test_unknown_access_blocks_with_hint(self):
        ws = ready_ws(self.d); run('-w', ws, 'set', 'access', 'unknown')
        code, _, err = run('-w', ws, 'plan')
        self.assertEqual(code, 2); self.assertIn('merestone setup', err)
        run('-w', ws, 'plan', '--anyway')
        a = next(ms.alias(t) for t in ms.Workspace(ws).plan()['tasks'] if t['applicability'] == 'APPLICABLE')
        code, _, err = run('-w', ws, 'review', a, '--result', 'PASS', '--note', 'review=x', '--reviewer', 'R', '--observations', 'o')
        self.assertEqual(code, 2); self.assertIn('set access', err)

    def test_checklist_explains_access_actor_boundary(self):
        ws = Path(self.d) / 'w'; run('new', ws, '--profile', 'rag')
        code, out, _ = run('-w', ws, 'status')
        for text in ('Permission to test', 'How much you can see', 'not the actor\'s permissions', 'Who starts the action', 'Path of the flow',
                     'not a trust boundary by default', 'merestone setup', 'merestone set access'):
            self.assertIn(text, out)

    def test_setup_wizard_answers_everything_then_plan_freezes(self):
        ws = Path(self.d) / 'w'; run('new', ws, '--profile', 'rag')
        def answer(prompt=''):
            if 'Access' in prompt: return 'g'
            if 'Requests' in prompt or 'Enter =' in prompt: return ''
            if 'DESIGN' in prompt: return 'y'
            if 'source' in prompt: return 'architecture doc v2'
            return 'fixture value'
        with mock.patch('builtins.input', answer):
            code, out, err = run('-w', ws, 'setup')
        self.assertEqual(code, 0, err); self.assertIn('Ready.', out)
        a = op.read(ws / 'architecture.json'); r = a['routes'][0]
        self.assertEqual(r['access'], 'gray-box'); self.assertEqual(a['limits']['requests'], 200)
        self.assertTrue(a['inventory_review']['reviewer'] and a['inventory_review']['reviewed_at'])
        self.assertEqual(ms.setup_items(a), []); self.assertEqual(op.ready(a), [])
        code, out, err = run('-w', ws, 'plan')
        self.assertEqual(code, 0, err); self.assertIn('Froze plan-001', out)

    def test_setup_skips_on_enter(self):
        ws = Path(self.d) / 'w'; run('new', ws, '--profile', 'chat')
        before = len(ms.setup_items(op.read(ws / 'architecture.json')))
        with mock.patch('builtins.input', lambda prompt='': 'n' if 'DESIGN' in prompt else ''):
            code, out, _ = run('-w', ws, 'setup')
        self.assertEqual(code, 0); self.assertIn('still pending', out)
        self.assertLess(len(ms.setup_items(op.read(ws / 'architecture.json'))), before)  # only defaults (reviewer, limits) applied

    def test_new_refuses_inside_framework(self):
        target = ms.op.ROOT / 'tmp-ws-should-not-exist'
        code, _, err = run('new', target)
        self.assertEqual(code, 2); self.assertIn('outside the framework', err); self.assertFalse(target.exists())

    def test_missing_workspace_points_to_child(self):
        base = Path(self.d); run('new', base / 'child-eval')
        cwd = Path.cwd()
        try:
            import os; os.chdir(base); code, _, err = run('status')
        finally: os.chdir(cwd)
        self.assertEqual(code, 2); self.assertIn('cd child-eval', err)

    def _mixed_ws(self):
        ws = ready_ws(self.d, present=('retrieval', 'llm_generation', 'multi_tenant'), activities='DESIGN,TEST', protocols=[('AI-006', 'original,benign')])
        run('-w', ws, 'plan')
        run('-w', ws, 'record', 'AI-006', '--variant', 'original', '--result', 'FAIL', '--expected', 'A only', '--observed', 'B leaked',
            '--identity', 'tenant-a', '--adaptation', 'own query', *notes())
        run('-w', ws, 'decide', 'AI-006', '--reviewer', 'R', '--observations', 'leak <script>alert(1)</script>', '--cleanup-confirmed')
        run('-w', ws, 'review', 'CORE-001', '--result', 'PASS', '--note', 'review=scope agreed', '--reviewer', 'R', '--observations', 'ok')
        return ws

    def test_html_report_is_complete_safe_and_offline(self):
        ws = self._mixed_ws()
        code, out, err = run('-w', ws, 'report', '--format', 'html')
        self.assertEqual(code, 2, err)
        page = next((ws / 'reports').glob('*.html')).read_text(encoding='utf-8')
        plan = ms.Workspace(ws).plan()
        for t in plan['tasks']: self.assertIn(ms.alias(t), page)
        self.assertIn('class="code c2"', page); self.assertIn("Content-Security-Policy", page)
        self.assertNotIn('<script>alert(1)</script>', page); self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', page)
        import re
        self.assertFalse(re.search(r'(src|href)=["\']?https?:', page), 'report must not load external resources')
        self.assertIn('Objective and risk', page)                     # fieldcards embedded
        failed = page.split('<h3>Failed')[1].split('</section>')[0]
        self.assertIn('AI-006@ROUTE-1', failed)
        passed = page.split('<h3>Passed')[1].split('</section>')[0]
        self.assertIn('CORE-001@ROUTE-1', passed)

    def test_html_document_layout(self):
        import re
        ws = self._mixed_ws()
        code, out, err = run('-w', ws, 'report', '--format', 'html', '--layout', 'document')
        self.assertEqual(code, 2, err)
        page = next((ws / 'reports').glob('*.html')).read_text(encoding='utf-8')
        plan = ms.Workspace(ws).plan()
        for t in plan['tasks']: self.assertIn(ms.alias(t), page)
        self.assertIn("Content-Security-Policy", page)
        self.assertNotIn('<script>alert(1)</script>', page); self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', page)
        self.assertFalse(re.search(r'(src|href)=["\']?https?:', page), 'report must not load external resources')
        anchors = set(re.findall(r'<details class="row" id="([^"]+)"', page))
        self.assertEqual(len(anchors), len(plan['tasks']))
        links = set(re.findall(r'href="#([^"]+)"', page))
        self.assertTrue(links and links <= anchors, 'every in-page link must target a task row')
        attention = page.split('What needs attention')[1].split('All obligations')[0]
        self.assertIn('AI-006@ROUTE-1', attention); self.assertIn('Objective and risk', attention)
        self.assertNotIn('CORE-001@ROUTE-1', attention)

    def test_report_both_formats(self):
        ws = self._mixed_ws()
        self.assertEqual(run('-w', ws, 'report', '--format', 'both')[0], 2)
        self.assertEqual({p.suffix for p in (ws / 'reports').iterdir()}, {'.md', '.html'})

    def test_markdown_subset_renderer(self):
        import report_html as rh
        h = rh.md('# Title\n\n- one `x`\n- two\n\n1. a\n2. b\n\n````text\n<b>raw</b>\n````\nSee [doc](../x.md).')
        for frag in ('<h3>Title</h3>', '<ul><li>one <code>x</code></li><li>two</li></ul>', '<ol><li>a</li><li>b</li></ol>', '<pre>&lt;b&gt;raw&lt;/b&gt;</pre>', 'See doc.'):
            self.assertIn(frag, h)

    def test_fieldcards_carry_no_provenance_boilerplate(self):
        lib = op.library()
        for c in lib['cases']:
            text = op.render_case(c, lib)
            for phrase in ('not a transcription', 'not literal payloads', 'Merestone-original'):
                self.assertNotIn(phrase, text, c['id'])

    def test_fieldcard_and_doctor(self):
        code, out, _ = run('fieldcard', 'AI-002'); self.assertEqual(code, 0); self.assertIn('Indirect injection', out)
        self.assertEqual(run('doctor')[0], 0)

    def test_demo(self):
        code, out, err = run('demo', '--out', Path(self.d) / 'demo')
        self.assertEqual(code, 0, err); self.assertIn('FAIL', out); self.assertIn('PASS', out)
        self.assertTrue((Path(self.d) / 'demo/summary.json').exists())


class RouteTests(unittest.TestCase):
    """Routes: the concrete flows being assessed (actor, permissions, path, trust boundaries, check)."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.ws = Path(self.tmp.name) / 'w'
        assert run('new', self.ws, '--profile', 'rag')[0] == 0
    def tearDown(self): self.tmp.cleanup()
    def r(self, *args): return run('-w', self.ws, *args)
    def arch(self): return op.read(self.ws / 'architecture.json')

    def test_edit_sets_every_field_in_one_write(self):
        code, out, err = self.r('route', 'edit', 'ROUTE-1', '--actor', 'Authenticated user of customer A', '--permissions', 'Read only customer A documents',
                                '--path', 'App → Document search → Model → Answer', '--check', 'Customer B documents are never retrieved',
                                '--trust', 'actor -> App: identity', '--trust', 'Document search -> Model: data trust | retrieved text is data')
        self.assertEqual(code, 0, err)
        a = self.arch(); r = a['routes'][0]
        self.assertEqual((r['actor'], r['actor_permissions'], r['boundary']),
                         ('Authenticated user of customer A', 'Read only customer A documents', 'App -> Document search -> Model -> Answer'))
        self.assertEqual(r['trust_boundaries'], [{'from': 'actor', 'to': 'App', 'changes': ['identity']},
                                                 {'from': 'Document search', 'to': 'Model', 'changes': ['data_trust'], 'note': 'retrieved text is data'}])
        self.assertEqual(ms.route_check(a, r), 'Customer B documents are never retrieved')
        history = op.read(self.ws / 'merestone.json')['history']
        self.assertEqual(sum(h['action'].startswith('route edit ROUTE-1') for h in history), 1)
        self.assertIn('Path         actor -> App -> Document search', self.r('route')[1])

    def test_invalid_edit_writes_nothing(self):
        before = (self.ws / 'architecture.json').read_bytes()
        for bad in (['--actor', 'X', '--path', 'App -> Model', '--trust', 'App -> Search: identity'],    # not a step of the path
                    ['--actor', 'X', '--trust', 'actor -> App: secrecy'],                                # unknown change
                    ['--actor', 'X', '--path', 'App -> -> Model'],                                       # unnamed component
                    ['--actor', ' ']):
            code, _, err = self.r('route', 'edit', 'ROUTE-1', *bad)
            self.assertEqual(code, 2, bad); self.assertTrue(err.strip(), bad)
            self.assertEqual((self.ws / 'architecture.json').read_bytes(), before, bad)

    def test_path_change_keeps_only_marks_that_are_still_steps(self):
        self.r('route', 'edit', 'ROUTE-1', '--path', 'App -> Search -> Model', '--trust', 'actor -> App: identity', '--trust', 'Search -> Model: data_trust')
        code, out, _ = self.r('set', 'boundary', 'App -> Index -> Model')
        self.assertEqual(code, 0); self.assertIn('Search -> Model', out)
        self.assertEqual(self.arch()['routes'][0]['trust_boundaries'], [{'from': 'actor', 'to': 'App', 'changes': ['identity']}])
        self.r('route', 'edit', 'ROUTE-1', '--no-trust')
        self.assertNotIn('trust_boundaries', self.arch()['routes'][0])

    def test_add_and_remove_routes_without_touching_plans(self):
        code, out, err = self.r('route', 'add', 'orders', '--path', 'App -> Model -> Orders API -> Order updated')
        self.assertEqual(code, 0, err)
        a = self.arch(); new = a['routes'][1]
        self.assertEqual((new['id'], new['access'], new['scope']), ('ORDERS', 'unknown', 'in_scope'))
        self.assertEqual(set(new['capabilities'].values()), {'unknown'}); self.assertEqual(new['capability_evidence'], {})
        self.assertEqual(new['activity_types'], a['routes'][0]['activity_types'])
        self.assertNotEqual(new['threat_ids'], a['routes'][0]['threat_ids'])
        self.assertEqual(self.r('route', 'add', 'ORDERS')[0], 2)                       # duplicate ID
        self.assertEqual(self.r('route', 'add', 'two words')[0], 2)                    # invalid ID
        self.r('caps', 'retrieval=present', '--source', 'doc', '--route', 'ROUTE-1')
        self.assertEqual(self.r('route', 'add', 'COPY', '--copy-caps')[0], 0)
        self.assertEqual(self.arch()['routes'][2]['capability_evidence'], {'retrieval': 'doc'})
        self.assertEqual(self.r('plan', '--anyway')[0], 0)
        plan_bytes = (self.ws / 'plans/plan-001.json').read_bytes()
        code, _, err = self.r('route', 'remove', 'ORDERS')                             # in the frozen plan
        self.assertEqual(code, 2); self.assertIn('--scope out_of_scope', err)
        self.r('route', 'add', 'LATER')
        code, out, err = self.r('route', 'remove', 'LATER')
        self.assertEqual(code, 0, err); self.assertIn('No plan or evidence was changed', out)
        self.assertEqual([r['id'] for r in self.arch()['routes']], ['ROUTE-1', 'ORDERS', 'COPY'])
        self.assertEqual((self.ws / 'plans/plan-001.json').read_bytes(), plan_bytes)
        self.assertEqual({t['id'] for t in self.arch()['threats']}, {t for r in self.arch()['routes'] for t in r['threat_ids']})

    def test_check_on_a_shared_threat_gets_its_own_threat(self):
        a = self.arch(); a['routes'].append(dict(copy.deepcopy(a['routes'][0]), id='ROUTE-2')); jsonutil.write_json(self.ws / 'architecture.json', a)
        self.assertEqual(self.r('set', 'check', 'Only own orders change', '--route', 'ROUTE-2')[0], 0)
        a = self.arch(); r1, r2 = a['routes']
        self.assertNotEqual(r1['threat_ids'], r2['threat_ids'])
        self.assertEqual((ms.route_check(a, r1), ms.route_check(a, r2)), ('', 'Only own orders change'))
        self.assertEqual(self.r('set', 'permissions', 'Change own orders', '--route', 'ROUTE-2')[0], 0)
        self.assertEqual(self.arch()['routes'][1]['actor_permissions'], 'Change own orders')

    def test_descriptive_fields_never_change_the_obligations(self):
        """Old architectures stay valid and new descriptive fields never add or remove tasks."""
        a = self.arch(); lib = op.library()
        before = op.digest(op.expected_tasks(a, lib))
        self.r('route', 'edit', 'ROUTE-1', '--permissions', 'Read own documents', '--trust', 'actor -> App: identity', '--path', 'App -> Model', '--check', 'B never leaks')
        after = self.arch(); r = after['routes'][0]
        self.assertTrue({'actor_permissions', 'trust_boundaries'} <= set(r))
        specs = op.expected_tasks(after, lib)
        self.assertEqual([s['task_id'] for s in specs], [s['task_id'] for s in op.expected_tasks(a, lib)])
        self.assertEqual(before, op.digest([dict(s, boundary=a['routes'][0]['boundary']) for s in specs]))
        bad = copy.deepcopy(after); bad['routes'][0]['trust_boundaries'][0]['changes'] = ['secrecy']
        with self.assertRaises(ValueError): op.validate_architecture(bad, lib)
        for p in sorted((ROOT / 'examples/pilots-final').glob('*/plan.json')):           # frozen records from before the change
            plan = op.read(p); op.check_plan(plan)


if __name__ == '__main__':
    unittest.main()
