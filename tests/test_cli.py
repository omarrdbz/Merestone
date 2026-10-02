import contextlib, io, json, sys, tempfile, unittest
from pathlib import Path
from unittest import mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import operational as op
import merestone as ms

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
        for text in ('Permission to test', 'How much you can see', 'Who acts', 'Trust boundary crossed', 'merestone setup', 'merestone set access'):
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

    def test_fieldcard_and_doctor(self):
        code, out, _ = run('fieldcard', 'AI-002'); self.assertEqual(code, 0); self.assertIn('Indirect injection', out)
        self.assertEqual(run('doctor')[0], 0)

    def test_demo(self):
        code, out, err = run('demo', '--out', Path(self.d) / 'demo')
        self.assertEqual(code, 0, err); self.assertIn('FAIL', out); self.assertIn('PASS', out)
        self.assertTrue((Path(self.d) / 'demo/summary.json').exists())


if __name__ == '__main__':
    unittest.main()
