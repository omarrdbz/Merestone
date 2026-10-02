"""Read-only HTML dashboard for a Merestone plan.

Produces one self-contained file (no network, no external fonts or scripts) that
can be shared with people who do not use the terminal. It only presents what
check-plan already computed; it never changes or re-decides anything.
"""
from __future__ import annotations
import html, re
from collections import Counter
from datetime import datetime, timezone
import operational as op

E = lambda s: html.escape(str(s), quote=True)

STATE_ORDER = ['FAIL', 'TODO', 'UNKNOWN', 'PASS', 'EXCLUDED', 'NOT_APPLICABLE']
STATE_META = {
    'FAIL': ('Failed', 'A control did not hold: a demonstrated violation.'),
    'TODO': ('To do', 'Applicable and not decided yet (not run, blocked, errored or inconclusive).'),
    'UNKNOWN': ('Unknown', 'Depends on a capability nobody has verified yet. Never counts as PASS.'),
    'PASS': ('Passed', 'The control held across the full planned sample.'),
    'EXCLUDED': ('Excluded', 'Accepted outside execution with reason, approver and expiry.'),
    'NOT_APPLICABLE': ('Not applicable', 'A required capability is absent, with evidence.'),
}
CODE_META = {
    0: ('Complete, no FAIL', 'Every selected obligation is resolved and the evidence verifies. Coverage of the frozen scope, not a certificate.'),
    1: ('Complete, with FAIL', 'Nothing is pending and failures were demonstrated. Findings and remediation come next.'),
    2: ('Incomplete or unverified', 'Something is pending, unknown or unverifiable. A new plan always starts here: it is the to-do list.'),
}
GAP_LABEL = {'authorization_ref': 'Permission to test', 'snapshot_ref': 'Exact version under test', 'evidence_store': 'Evidence store',
             'inventory_review.reviewer': 'Inventory reviewer', 'inventory_review.reviewed_at': 'Inventory review date',
             'inventory_review.evidence_ref': 'Source of the inventory', 'stop_conditions': 'Stop conditions', 'limits': 'Load limits',
             'core_design_missing': 'Design review (DESIGN) on at least one route'}


def bucket(t):
    if t.get('exclusion'): return 'EXCLUDED'
    if t['result'] in ('PASS', 'FAIL'): return t['result']
    if t['applicability'] == 'NOT_APPLICABLE': return 'NOT_APPLICABLE'
    if t['applicability'] == 'UNKNOWN': return 'UNKNOWN'
    return 'TODO'


def alias(t): return f"{t['case_id']}@{t['route_id']}"


# ---------- tiny Markdown renderer for fieldcards (subset produced by render_case) ----------
def _inline(s):
    s = E(s)
    s = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', s)          # links are relative to the repo: keep the text
    s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
    s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
    return s


def md(text):
    out, para, lst, code = [], [], None, None
    def flush():
        nonlocal para, lst
        if para: out.append('<p>' + _inline(' '.join(para)) + '</p>'); para = []
        if lst: out.append(f'<{lst[0]}>' + ''.join(f'<li>{_inline(x)}</li>' for x in lst[1]) + f'</{lst[0]}>'); lst = None
    for line in text.splitlines():
        if code is not None:
            if line.strip().startswith('```'): out.append('<pre>' + E('\n'.join(code)) + '</pre>'); code = None
            else: code.append(line)
            continue
        if line.strip().startswith('```'): flush(); code = []; continue
        m = re.match(r'^(#{1,4})\s+(.*)', line)
        if m: flush(); lvl = min(len(m.group(1)) + 2, 6); out.append(f'<h{lvl}>{_inline(m.group(2))}</h{lvl}>'); continue
        m = re.match(r'^\s*[-*]\s+(.*)', line)
        if m:
            if para: flush()
            if not lst or lst[0] != 'ul': flush(); lst = ['ul', []]
            lst[1].append(m.group(1)); continue
        m = re.match(r'^\s*\d+\.\s+(.*)', line)
        if m:
            if para: flush()
            if not lst or lst[0] != 'ol': flush(); lst = ['ol', []]
            lst[1].append(m.group(1)); continue
        if not line.strip(): flush(); continue
        if lst: flush()
        para.append(line.strip())
    flush()
    return '\n'.join(out)


# ---------- Mojo (pixel mascot) as inline SVG ----------
MOJO = ["......MM......", "....MMNMM.....", "...KKKKKKKK...", "..KLLLLLLSSK..", ".KLLLLLLSSSSK.", ".KLLSSSSSSSDK.",
        ".KLWWSSSSWWDK.", ".KLWKSSSSWKDK.", ".KLSSSSSSSSDK.", ".KLCSSKKSSCDK.", ".KLSSSSSSSSDK.", "KKOOOOOOOOOOKK",
        "KKPPPPPPPPPPKK", ".KLSSSSSSSSDK.", ".KLSSSSSSSSDK.", ".KDDDDDDDDDDK.", "..KSSK..KSSK..", "..KKKK..KKKK.."]
PAL = {'K': '#18221F', 'S': '#9AA59F', 'L': '#C6CFC9', 'D': '#6E7A74', 'M': '#6DAA5F', 'N': '#3F7340', 'O': '#E0A64E',
       'P': '#A8701C', 'W': '#FFFFFF', 'C': '#E99A8B', 'G': '#4FBF7A', 'R': '#E2564B', 'Q': '#E0A64E'}
BADGE = {0: ["......G", ".....GG", "G...GG.", "GG.GG..", ".GGG...", "..G...."],
         1: [".RR.", ".RR.", ".RR.", ".RR.", "....", ".RR."],
         2: [".QQQQ.", "QQ..QQ", "...QQ.", "..QQ..", "......", "..QQ.."]}


def mojo_svg(code, px=6):
    g = [list('.' * 22) for _ in range(25)]
    for i, row in enumerate(MOJO):
        for j, ch in enumerate(row): g[i + 7][j + 1] = ch
    if code == 0:   # happy closed eyes
        for c in (4, 5, 10, 11): g[13][c] = 'S'; g[14][c] = 'K'
    if code == 1:   # alarmed: red band
        for c in range(3, 13): g[18][c] = 'R'
    for i, row in enumerate(BADGE[code]):
        for j, ch in enumerate(row):
            if ch != '.': g[i][15 + j] = ch
    rects = ''.join(f'<rect x="{x}" y="{y}" width="1.02" height="1.02" fill="{PAL[ch]}"/>'
                    for y, row in enumerate(g) for x, ch in enumerate(row) if ch in PAL)
    return f'<svg class="mojo" viewBox="0 0 22 25" width="{22 * px}" height="{25 * px}" shape-rendering="crispEdges" aria-hidden="true">{rects}</svg>'


MARK = ('<svg class="mark" viewBox="0 -14 100 140" width="26" height="36" aria-hidden="true"><polygon points="50,6 6,36 16,106 50,106" fill="var(--teal)"/>'
        '<polygon points="50,6 94,36 84,106 50,106" fill="var(--sand)"/><polygon points="50,6 94,36 84,106 16,106 6,36" fill="none" stroke="var(--ink)" '
        'stroke-width="7" stroke-linejoin="round"/><line x1="50" y1="-12" x2="50" y2="124" stroke="var(--ochre)" stroke-width="4.5" stroke-dasharray="8 7"/></svg>')

CSS = """
:root{--bg:#EEF1EE;--card:#FFFFFF;--ink:#18221F;--muted:#56635E;--line:#CBD3CD;--teal:#0F6A62;--sand:#F1E3C8;--ochre:#A8701C;
--pass:#2D7A4B;--pass-s:#D8EDDF;--fail:#B03F37;--fail-s:#F5DCD9;--unk:#A8701C;--unk-s:#F1E3C8;--todo:#3F5C56;--todo-s:#DDE8E5;--na:#9AA59F;--na-s:#E8ECE9;--ex:#6F6A86;--ex-s:#E6E4EE;
--night:#0E1513;--night-ink:#E4ECE8;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#111917;--card:#18221F;--ink:#E4ECE8;--muted:#9BABA5;--line:#2C3A36;--teal:#5CC2B3;--sand:#3A2D18;--ochre:#D9A050;
--pass:#6CC48D;--pass-s:#1A3324;--fail:#E77B72;--fail-s:#3D1F1C;--unk:#D9A050;--unk-s:#3A2D18;--todo:#9FC9C1;--todo-s:#1E2D2A;--na:#7E8C86;--na-s:#1C2522;--ex:#ADA7C9;--ex-s:#25233A;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 "Segoe UI",system-ui,-apple-system,Roboto,sans-serif}
code,pre,.mono{font-family:ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace}
.wrap{max-width:1240px;margin:0 auto;padding:0 20px}
header.top{background:var(--night);color:var(--night-ink);padding:22px 0 26px}
header.top .brand{display:flex;align-items:center;gap:10px;font-weight:700;font-size:20px;letter-spacing:-.02em}
header.top .brand .mark polygon:nth-child(2){fill:#18221F}header.top .brand .mark polygon:nth-child(3){stroke:#E4ECE8}
.hero{display:grid;grid-template-columns:auto 1fr auto;gap:28px;align-items:center;margin-top:18px}
.code{width:120px;height:120px;border-radius:50%;display:grid;place-items:center;font:700 72px/1 system-ui;color:#fff}
.c0{background:#2D7A4B}.c1{background:#B03F37}.c2{background:#A8701C}
.hero h1{margin:0;font-size:34px;letter-spacing:-.02em;line-height:1.1}.hero p{margin:6px 0 0;color:#B9C6C1;max-width:70ch}
.meta{display:flex;flex-wrap:wrap;gap:6px 18px;margin-top:12px;font-size:13px;color:#9BABA5}.meta b{color:#E4ECE8;font-weight:600}
.kpis{display:grid;grid-template-columns:repeat(7,1fr);gap:10px;margin:22px 0 8px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}.kpi b{display:block;font-size:26px;line-height:1.1}.kpi span{font-size:12px;color:var(--muted)}
h2{font-size:20px;margin:30px 0 12px;letter-spacing:-.01em}
.panel{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.gaps{display:flex;flex-wrap:wrap;gap:8px}.gap{background:var(--unk-s);color:var(--unk);border-radius:8px;padding:4px 10px;font-size:13px;font-weight:600}
.mods{display:grid;gap:8px}.mod{display:grid;grid-template-columns:110px 1fr 240px;gap:12px;align-items:center;font-size:13px}
.bar{display:flex;height:16px;border-radius:5px;overflow:hidden;background:var(--na-s)}.bar i{display:block;height:100%}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12px;color:var(--muted);margin-top:10px}.legend i{display:inline-block;width:10px;height:10px;border-radius:2px;margin-right:5px;vertical-align:-1px}
.s-FAIL{background:var(--fail)}.s-TODO{background:var(--todo)}.s-UNKNOWN{background:var(--unk)}.s-PASS{background:var(--pass)}.s-EXCLUDED{background:var(--ex)}.s-NOT_APPLICABLE{background:var(--na)}
.tools{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:12px}
.tools input,.tools select{font:inherit;padding:7px 10px;border:1px solid var(--line);border-radius:8px;background:var(--card);color:var(--ink)}
.board{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px;align-items:start}
.col{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px;min-width:0}
.col>h3{margin:2px 4px 2px;font-size:15px;display:flex;justify-content:space-between;align-items:center}.col>h3 small{font-weight:600;border-radius:999px;padding:1px 9px;color:#fff}
.col>p{margin:0 4px 10px;font-size:12px;color:var(--muted)}
.extra{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:12px}
details.task{border:1px solid var(--line);border-left:4px solid var(--c);border-radius:9px;margin:0 0 8px;background:var(--bg)}
details.task>summary{list-style:none;cursor:pointer;padding:8px 10px;display:grid;gap:2px}details.task>summary::-webkit-details-marker{display:none}
details.task>summary .id{font:600 12px ui-monospace,Consolas,monospace;color:var(--c)}details.task>summary .tt{font-weight:600;font-size:14px;line-height:1.3}
details.task>summary .tg{font-size:11px;color:var(--muted)}
details.task[open]>summary{background:var(--card);outline:2px solid var(--c);border-radius:8px}
details.task .body{position:fixed;top:0;right:0;bottom:0;width:min(760px,100vw);overflow:auto;z-index:20;background:var(--card);border-left:4px solid var(--c);box-shadow:-18px 0 50px rgba(0,0,0,.28);padding:18px 26px 40px;font-size:14px}
.body .dh{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;position:sticky;top:-18px;background:var(--card);padding:12px 0 10px;margin-top:-12px;border-bottom:1px solid var(--line)}
.body .dh h3{margin:0;font-size:20px;line-height:1.2}.body .dh .id{font:600 13px ui-monospace,Consolas,monospace;color:var(--c)}
.x{font:inherit;font-size:13px;padding:6px 12px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--ink);cursor:pointer;white-space:nowrap}
#scrim{position:fixed;inset:0;background:rgba(10,16,14,.45);z-index:19}
.body h3,.body h4,.body h5{margin:14px 0 4px;font-size:14px}.body pre{white-space:pre-wrap;background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:8px;font-size:12px}
.body ul,.body ol{padding-left:20px;margin:4px 0}.facts{display:grid;grid-template-columns:max-content 1fr;gap:3px 12px;font-size:13px;margin:8px 0}
.facts dt{color:var(--muted)}.facts dd{margin:0}
div.tw{overflow-x:auto}table.ev{width:100%;min-width:520px;border-collapse:collapse;font-size:12px;margin:6px 0}table.ev td,table.ev th{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}
.chip{display:inline-block;font:600 11px ui-monospace,Consolas,monospace;padding:1px 7px;border-radius:5px}
.cP{background:var(--pass-s);color:var(--pass)}.cF{background:var(--fail-s);color:var(--fail)}.cO{background:var(--na-s);color:var(--muted)}
.finding{border-left:4px solid var(--fail);margin-bottom:10px}
footer{margin:36px 0 40px;font-size:12.5px;color:var(--muted)}
.empty{font-size:12.5px;color:var(--muted);padding:6px 4px}
@media (max-width:980px){.board{grid-template-columns:repeat(2,minmax(0,1fr))}.kpis{grid-template-columns:repeat(4,1fr)}.hero{grid-template-columns:auto 1fr}.hero .mojo{display:none}}
@media (max-width:620px){.board,.extra{grid-template-columns:1fr}.kpis{grid-template-columns:repeat(2,1fr)}.mod{grid-template-columns:80px 1fr}.mod .n{display:none}}
@media print{body{background:#fff}header.top{background:#fff;color:#000}.tools,#scrim,.x{display:none}details.task{break-inside:avoid}details.task .body{position:static;width:auto;box-shadow:none;border:0;padding:6px 10px}}
"""

JS = """
(function(){var q=document.getElementById('q'),m=document.getElementById('m'),sc=document.getElementById('scrim');
function f(){var t=(q.value||'').toLowerCase(),mm=m.value;document.querySelectorAll('details.task').forEach(function(d){
var ok=(!t||d.dataset.s.indexOf(t)>=0)&&(!mm||d.dataset.m===mm);d.hidden=!ok;});
document.querySelectorAll('.col').forEach(function(c){var n=c.querySelectorAll('details.task:not([hidden])').length;var b=c.querySelector('h3 small');if(b)b.textContent=n;});}
function closeAll(){document.querySelectorAll('details.task[open]').forEach(function(d){d.open=false});}
document.querySelectorAll('details.task').forEach(function(d){d.addEventListener('toggle',function(){
if(d.open){document.querySelectorAll('details.task[open]').forEach(function(o){if(o!==d)o.open=false});sc.hidden=false;var b=d.querySelector('.body');if(b)b.scrollTop=0;}
else if(!document.querySelector('details.task[open]')){sc.hidden=true;}});});
document.querySelectorAll('[data-close]').forEach(function(b){b.addEventListener('click',closeAll)});
sc.addEventListener('click',closeAll);document.addEventListener('keydown',function(e){if(e.key==='Escape')closeAll();});
q.addEventListener('input',f);m.addEventListener('change',f);})();
"""


COLORS = {'FAIL': 'var(--fail)', 'TODO': 'var(--todo)', 'UNKNOWN': 'var(--unk)', 'PASS': 'var(--pass)', 'EXCLUDED': 'var(--ex)', 'NOT_APPLICABLE': 'var(--na)'}


def state_label(t):
    b = bucket(t)
    return (t['result'] or t['execution']) if b == 'TODO' else STATE_META[b][0]


def anchor(t): return 't-' + re.sub(r'[^A-Za-z0-9]+', '-', alias(t))


def task_details(t, case, ev_index):
    """Facts, trials, hashed evidence and fieldcard of one task (shared by both layouts)."""
    b = bucket(t); state = state_label(t)
    facts = [('State', state), ('Applicability', t['applicability']), ('Activity', t['activity']), ('Module', t['module']),
             ('Asset / route', f"{t['asset_id']} / {t['route_id']}"), ('Boundary', t['boundary']), ('Actor', t['actor']),
             ('Access / scope', f"{t['access']} / {t['scope']}"), ('Controls', ', '.join(t['control_ids']) or '-')]
    pr = t.get('test_protocol')
    if t['activity'] in ('TEST', 'REDTEAM'):
        facts.append(('Protocol', f"{', '.join(pr['required_variants'])} x{pr['min_trials_per_variant']} ({pr['design']}): {pr['decision_rule']}" if pr else 'none defined (required to decide PASS/FAIL)'))
    if t['reviewer']: facts.append(('Reviewer', t['reviewer']))
    if t['observations'].strip(): facts.append(('Observations', t['observations'].strip()))
    if t['rationale'].strip(): facts.append(('Rationale', t['rationale'].strip()))
    if t.get('exclusion'):
        ex = t['exclusion']; facts.append(('Exclusion', f"{ex.get('reason', '')} (approved by {ex.get('approver', '')}, expires {ex.get('expires_at', '')}; residual risk: {ex.get('residual_risk', '')})"))
    body = '<dl class="facts">' + ''.join(f'<dt>{E(k)}</dt><dd>{E(v)}</dd>' for k, v in facts) + '</dl>'
    if t['trials']:
        rows = ''.join(f"<tr><td class=mono>{E(x['trial_id'])}</td><td>{E(x['variant'])}</td><td><span class='chip {'cP' if x['result'] == 'PASS' else 'cF' if x['result'] == 'FAIL' else 'cO'}'>{E(x['result'] or x['execution'])}</span></td>"
                       f"<td>{E(x['expected'])}</td><td>{E(x['observed'])}</td><td>{E(x['reachability'])}</td></tr>" for x in t['trials'])
        body += '<h4>Trials</h4><div class="tw"><table class="ev"><tr><th>Trial</th><th>Variant</th><th>Result</th><th>Expected</th><th>Observed</th><th>Reachability</th></tr>' + rows + '</table></div>'
    if t['evidence_ids']:
        rows = ''.join(f"<tr title='{E(e)}'><td>{E(ev_index[e]['kind'])}</td><td class=mono title='{E(ev_index[e]['sha256'])}'>{E(ev_index[e]['sha256'][:16])}…</td><td class=mono>{E(ev_index[e]['path'])}</td><td>{E(ev_index[e]['collected_at'])}</td><td>{E(ev_index[e]['collector'])}</td></tr>"
                       for e in t['evidence_ids'] if e in ev_index)
        body += '<h4>Evidence (verified by hash)</h4><div class="tw"><table class="ev"><tr><th>Kind</th><th>SHA-256</th><th>File</th><th>Collected</th><th>By</th></tr>' + rows + '</table></div>'
    if case and b != 'NOT_APPLICABLE':
        body += '<h4>Fieldcard</h4>' + md(op.render_case(case))
    return body


def task_card(t, case, ev_index):
    b = bucket(t); state = state_label(t); colors = COLORS
    search = ' '.join([alias(t), t['title'], t['module'], t['activity'], t['boundary']]).lower()
    body = (f'<div class="dh"><div><div class="id">{E(alias(t))}</div><h3>{E(t["title"])}</h3></div>'
            '<button type="button" class="x" data-close>Close (Esc)</button></div>') + task_details(t, case, ev_index)
    return (f'<details class="task" style="--c:{colors[b]}" data-m="{E(t["module"])}" data-s="{E(search)}"><summary>'
            f'<span class="id">{E(alias(t))}</span><span class="tt">{E(t["title"])}</span>'
            f'<span class="tg">{E(t["module"])} · {E(t["activity"])} · {E(state)}</span></summary><div class="body">{body}</div></details>')


def render_board(plan, result, findings=(), generated_at=None):
    lib = op.library(); cases = {c['id']: c for c in lib['cases']}
    arch = plan['architecture']; tasks = plan['tasks']; code = result['exit_code']
    ev_index = {e['id']: e for e in plan['evidence']}
    groups = {k: [] for k in STATE_ORDER}
    for t in sorted(tasks, key=lambda t: (t['module'], t['case_id'], t['route_id'])): groups[bucket(t)].append(t)
    n = {k: len(v) for k, v in groups.items()}
    gen = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    # coverage by module
    mods = {}
    for t in tasks: mods.setdefault(t['module'], Counter())[bucket(t)] += 1
    mod_rows = ''
    for m in sorted(mods):
        c = mods[m]; tot = sum(c.values())
        segs = ''.join(f'<i class="s-{k}" style="width:{100 * c[k] / tot:.2f}%" title="{STATE_META[k][0]}: {c[k]}"></i>' for k in STATE_ORDER if c[k])
        summary = ' · '.join(f'{c[k]} {STATE_META[k][0].lower()}' for k in STATE_ORDER if c[k])
        mod_rows += f'<div class="mod"><b>{E(m)}</b><div class="bar" role="img" aria-label="{E(m)}: {E(summary)}">{segs}</div><span class="n">{E(summary)}</span></div>'
    legend = ''.join(f'<span><i class="s-{k}"></i>{STATE_META[k][0]}</span>' for k in STATE_ORDER)

    def column(k):
        label, why = STATE_META[k]
        cards = ''.join(task_card(t, cases.get(t['case_id']), ev_index) for t in groups[k]) or '<div class="empty">Nothing here.</div>'
        return f'<section class="col"><h3>{label} <small class="s-{k}">{n[k]}</small></h3><p>{E(why)}</p>{cards}</section>'

    gaps = result['readiness_gaps']
    gaps_html = ('<div class="gaps">' + ''.join(f'<span class="gap">{E(GAP_LABEL.get(g, g.replace(":evidence:", ": source missing for ")))}</span>' for g in gaps) + '</div>') if gaps else '<p>No readiness gaps.</p>'
    find_html = ''
    for f in findings:
        find_html += (f'<div class="panel finding"><b>{E(f["id"])} — {E(f["title"])}</b><dl class="facts"><dt>Status</dt><dd>{E(f["state"])}</dd>'
                      f'<dt>Priority (I×F)</dt><dd>{E(f["impact"])}×{E(f["feasibility"])} = {E(f["impact"] * f["feasibility"])}; confidence {E(f["confidence"])}</dd>'
                      f'<dt>Root cause</dt><dd>{E(f["root_cause"])}</dd><dt>Proven impact</dt><dd>{E(f["proven_impact"])}</dd>'
                      f'<dt>Correction</dt><dd>{E(f["remediation"])}</dd><dt>Owner / due</dt><dd>{E(f["owner"])} / {E(f["due_at"])}</dd></dl></div>')
    decided_pass = result['decided_obligations'] - result['failures']
    kpis = [(len(tasks), 'obligations'), (result['applicable_obligations'], 'applicable'), (result['unknown_obligations'], 'unknown'),
            (n['NOT_APPLICABLE'], 'not applicable'), (decided_pass, 'passed'), (result['failures'], 'failed'), (result['excluded_obligations'], 'excluded')]
    title, why = CODE_META[code]
    options = ''.join(f'<option value="{E(m)}">{E(m)}</option>' for m in sorted(mods))
    integrity = 'Integrity verified against the approved manifest and the evidence store.' if result['integrity_verified'] else 'Integrity NOT verified (no external manifest or evidence store was supplied).'
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:">
<title>Merestone report · {E(arch['system_name'])}</title><style>{CSS}</style></head><body>
<header class="top"><div class="wrap">
<div class="brand">{MARK}merestone <span style="font-weight:400;color:#9BABA5;font-size:14px">· read-only assessment report</span></div>
<div class="hero"><div class="code c{code}" aria-label="exit code {code}">{code}</div>
<div><h1>{E(title)}</h1><p>{E(why)}</p>
<div class="meta"><span>System <b>{E(arch['system_name'])}</b></span><span>Assessment <b>{E(arch['assessment_id'])}</b></span>
<span>Plan <b class="mono">{E(plan['plan_id'][:8])}</b></span><span>Version under test <b>{E(arch['snapshot_ref'] or '—')}</b></span>
<span>Authorization <b>{E(arch['authorization_ref'] or '—')}</b></span><span>Generated <b>{E(gen)}</b></span></div></div>
{mojo_svg(code)}</div></div></header>
<main class="wrap">
<div class="kpis">{''.join(f'<div class="kpi"><b>{v}</b><span>{E(l)}</span></div>' for v, l in kpis)}</div>
<h2>Readiness</h2><div class="panel">{gaps_html}<p style="margin:10px 0 0;font-size:13px;color:var(--muted)">{E(integrity)}</p></div>
<h2>Coverage by module</h2><div class="panel"><div class="mods">{mod_rows}</div><div class="legend">{legend}</div></div>
{('<h2>Findings</h2>' + find_html) if findings else ''}
<h2>Tasks</h2>
<div class="tools"><input id="q" type="search" placeholder="Search tasks (ID, title, boundary)" aria-label="Search tasks">
<select id="m" aria-label="Module"><option value="">All modules</option>{options}</select><span style="font-size:12.5px;color:var(--muted)">Select a task to see its details, evidence and fieldcard.</span></div>
<div class="board">{''.join(column(k) for k in STATE_ORDER[:4])}</div>
<div class="extra">{column('EXCLUDED')}{column('NOT_APPLICABLE')}</div>
<footer><p>{E(result['note'])}</p><p>Generated by Merestone {E(op.VERSION)} from the frozen plan record. This page is a view: it does not change or re-decide any result. Catalog <span class="mono">{E(plan['catalog_sha256'][:12])}</span> · architecture <span class="mono">{E(plan['architecture_sha256'][:12])}</span> · obligations <span class="mono">{E(plan['obligations_sha256'][:12])}</span>.</p></footer>
<div id="scrim" hidden></div></main><script>{JS}</script></body></html>
"""


# ---------- alternative layout: "document" (read top to bottom, print-friendly) ----------
DOC_CSS = """
:root{--bg:#F6F4EE;--card:#FFFFFF;--ink:#18221F;--muted:#5A6661;--line:#D8DCD5;--teal:#0F6A62;--sand:#F1E3C8;--ochre:#A8701C;
--pass:#2D7A4B;--pass-s:#D8EDDF;--fail:#B03F37;--fail-s:#F5DCD9;--unk:#A8701C;--unk-s:#F3E6CC;--todo:#3F5C56;--todo-s:#DDE8E5;--na:#B4BCB7;--na-s:#ECEFEC;--ex:#6F6A86;--ex-s:#E6E4EE;color-scheme:light}
@media (prefers-color-scheme:dark){:root{--bg:#141B19;--card:#1B2422;--ink:#E4ECE8;--muted:#9BABA5;--line:#2C3A36;--teal:#5CC2B3;--sand:#3A2D18;--ochre:#D9A050;
--pass:#6CC48D;--pass-s:#1A3324;--fail:#E77B72;--fail-s:#3D1F1C;--unk:#D9A050;--unk-s:#3A2D18;--todo:#9FC9C1;--todo-s:#1E2D2A;--na:#55635E;--na-s:#1C2522;--ex:#ADA7C9;--ex-s:#25233A;color-scheme:dark}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15.5px/1.6 "Segoe UI",system-ui,-apple-system,Roboto,sans-serif}
code,pre,.mono{font-family:ui-monospace,"Cascadia Mono",Consolas,Menlo,monospace}
.page{max-width:980px;margin:0 auto;padding:36px 22px 60px}
.serif,h1,h2{font-family:"Iowan Old Style","Palatino Linotype",Georgia,serif;font-weight:700;letter-spacing:-.01em}
.brand{display:flex;align-items:center;gap:10px;font-weight:700;font-size:15px;color:var(--muted);border-bottom:2px solid var(--ink);padding-bottom:10px}
.brand .mark polygon:nth-child(2){fill:var(--sand)}
h1{font-size:40px;line-height:1.08;margin:26px 0 6px}.sub{color:var(--muted);margin:0 0 22px}
h2{font-size:24px;margin:44px 0 14px;display:flex;gap:12px;align-items:baseline;border-top:1px solid var(--line);padding-top:18px}
h2 .num{font:600 13px ui-monospace,Consolas,monospace;color:var(--ochre);letter-spacing:.12em}
.verdict{display:grid;grid-template-columns:auto 1fr auto;gap:24px;align-items:center;background:var(--card);border:1px solid var(--line);border-left:10px solid var(--vc);border-radius:6px;padding:20px 24px}
.verdict .n{font:700 64px/1 "Iowan Old Style",Georgia,serif;color:var(--vc)}.verdict h3{margin:0;font-size:22px}.verdict p{margin:4px 0 0;color:var(--muted)}
.metaT{width:100%;border-collapse:collapse;margin-top:16px;font-size:14px}.metaT td{padding:6px 0;border-bottom:1px solid var(--line);vertical-align:top}.metaT td:first-child{color:var(--muted);width:210px}
.nums{display:flex;flex-wrap:wrap;gap:0;margin-top:18px;border:1px solid var(--line);border-radius:6px;background:var(--card)}
.nums div{flex:1 1 110px;padding:12px 14px;border-left:1px solid var(--line)}.nums div:first-child{border-left:0}.nums b{display:block;font:700 28px/1.1 "Iowan Old Style",Georgia,serif}.nums span{font-size:12px;color:var(--muted)}
.field{background:var(--card);border:1px solid var(--line);border-radius:6px;padding:16px 18px}
.frow{display:grid;grid-template-columns:120px 1fr 150px;gap:14px;align-items:center;padding:6px 0;border-bottom:1px dashed var(--line)}.frow:last-child{border-bottom:0}
.frow b{font-size:13px}.frow .cnt{font-size:12px;color:var(--muted);text-align:right}
.stones{display:flex;flex-wrap:wrap;gap:4px}.stones a{display:block;line-height:0;border-radius:3px}.stones a:focus-visible{outline:2px solid var(--teal);outline-offset:2px}
.stones svg{width:20px;height:21px;transition:transform .12s}.stones a:hover svg{transform:translateY(-3px) scale(1.15)}
.legend{display:flex;flex-wrap:wrap;gap:14px;font-size:12.5px;color:var(--muted);margin-top:12px}.legend svg{width:13px;height:14px;vertical-align:-2px;margin-right:4px}
.f-FAIL{fill:var(--fail)}.f-TODO{fill:var(--todo)}.f-UNKNOWN{fill:var(--unk)}.f-PASS{fill:var(--pass)}.f-EXCLUDED{fill:var(--ex)}.f-NOT_APPLICABLE{fill:var(--na)}
.att{background:var(--card);border:1px solid var(--line);border-left:6px solid var(--fail);border-radius:6px;padding:14px 20px;margin-bottom:14px}
.att h3{margin:0 0 2px;font-size:18px}.att .id{font:600 12.5px ui-monospace,Consolas,monospace;color:var(--fail)}
.list{margin:6px 0 0;padding-left:20px}.list a{color:var(--ink)}
.pill{display:inline-block;font:600 11px ui-monospace,Consolas,monospace;padding:2px 8px;border-radius:5px;white-space:nowrap}
.p-FAIL{background:var(--fail-s);color:var(--fail)}.p-TODO{background:var(--todo-s);color:var(--todo)}.p-UNKNOWN{background:var(--unk-s);color:var(--unk)}.p-PASS{background:var(--pass-s);color:var(--pass)}.p-EXCLUDED{background:var(--ex-s);color:var(--ex)}.p-NOT_APPLICABLE{background:var(--na-s);color:var(--muted)}
h3.mod{font-size:15px;margin:22px 0 6px;display:flex;justify-content:space-between}h3.mod small{font-weight:400;color:var(--muted)}
details.row{border-bottom:1px solid var(--line);background:var(--card)}details.row:first-of-type{border-top:1px solid var(--line)}
details.row>summary{list-style:none;cursor:pointer;display:grid;grid-template-columns:150px 1fr 80px 110px;gap:12px;padding:8px 12px;align-items:center;font-size:14px}
details.row>summary::-webkit-details-marker{display:none}details.row>summary:hover{background:var(--bg)}
details.row>summary .id{font:600 12px ui-monospace,Consolas,monospace}details.row>summary .act{font-size:12px;color:var(--muted)}
details.row[open]>summary{background:var(--bg);font-weight:600}details.row:target>summary{outline:2px solid var(--teal)}
.rbody{padding:6px 18px 16px;font-size:14px;border-top:1px dashed var(--line)}
.rbody h3,.rbody h4,.rbody h5{margin:14px 0 4px;font-size:14px}.rbody pre{white-space:pre-wrap;background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:8px;font-size:12px}
.rbody ul,.rbody ol{padding-left:20px;margin:4px 0}.facts{display:grid;grid-template-columns:max-content 1fr;gap:3px 14px;font-size:13.5px;margin:8px 0}.facts dt{color:var(--muted)}.facts dd{margin:0}
div.tw{overflow-x:auto}table.ev{width:100%;min-width:520px;border-collapse:collapse;font-size:12.5px;margin:6px 0}table.ev td,table.ev th{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}
.chip{display:inline-block;font:600 11px ui-monospace,Consolas,monospace;padding:1px 7px;border-radius:5px}.cP{background:var(--pass-s);color:var(--pass)}.cF{background:var(--fail-s);color:var(--fail)}.cO{background:var(--na-s);color:var(--muted)}
.gaps span{display:inline-block;background:var(--unk-s);color:var(--unk);border-radius:6px;padding:3px 10px;font-size:13px;font-weight:600;margin:0 6px 6px 0}
footer{margin-top:48px;padding-top:14px;border-top:2px solid var(--ink);font-size:12.5px;color:var(--muted)}
@media (max-width:640px){h1{font-size:30px}.verdict{grid-template-columns:auto 1fr}.verdict .mojo{display:none}.frow{grid-template-columns:1fr}.frow .cnt{text-align:left}
details.row>summary{grid-template-columns:1fr auto}details.row>summary .tt{grid-column:1/-1;order:3}details.row>summary .act{display:none}.metaT td:first-child{width:120px}}
@media print{body{background:#fff}.page{padding:0}details.row>summary:hover{background:none}.stones svg{transition:none}}
"""

DOC_JS = """
(function(){function openHash(){var h=location.hash.slice(1);if(!h)return;var d=document.getElementById(h);if(d&&d.tagName==='DETAILS'){d.open=true;}}
window.addEventListener('hashchange',openHash);openHash();
var was=[];window.addEventListener('beforeprint',function(){was=[];document.querySelectorAll('details').forEach(function(d){was.push(d.open);d.open=true;});});
window.addEventListener('afterprint',function(){document.querySelectorAll('details').forEach(function(d,i){d.open=was[i];});});})();
"""

STONE = '<svg viewBox="-30 -32 60 64" aria-hidden="true"><polygon class="f-{k}" points="0,-30 28,-10 18,30 -18,30 -28,-10"/></svg>'


def render_document(plan, result, findings=(), generated_at=None):
    lib = op.library(); cases = {c['id']: c for c in lib['cases']}
    arch = plan['architecture']; tasks = sorted(plan['tasks'], key=lambda t: (t['module'], t['case_id'], t['route_id']))
    code = result['exit_code']; ev_index = {e['id']: e for e in plan['evidence']}
    gen = generated_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    by = Counter(bucket(t) for t in tasks); mods = {}
    for t in tasks: mods.setdefault(t['module'], []).append(t)
    title, why = CODE_META[code]; vcol = {0: 'var(--pass)', 1: 'var(--fail)', 2: 'var(--ochre)'}[code]

    field = ''
    for m, ts in mods.items():
        c = Counter(bucket(t) for t in ts)
        stones = ''.join(f'<a href="#{anchor(t)}" title="{E(alias(t))} · {E(t["title"])} · {E(state_label(t))}">{STONE.format(k=bucket(t))}</a>' for t in sorted(ts, key=lambda t: STATE_ORDER.index(bucket(t))))
        field += f'<div class="frow"><b>{E(m)}</b><div class="stones">{stones}</div><span class="cnt">{E(" · ".join(f"{c[k]} {STATE_META[k][0].lower()}" for k in STATE_ORDER if c[k]))}</span></div>'
    legend = ''.join(f'<span>{STONE.format(k=k)}{STATE_META[k][0]} ({by[k]})</span>' for k in STATE_ORDER)

    fails = [t for t in tasks if bucket(t) == 'FAIL']
    att = ''.join(f'<div class="att"><div class="id">{E(alias(t))} · {E(t["module"])} · {E(t["activity"])}</div><h3>{E(t["title"])}</h3>'
                  f'<div class="rbody" style="border:0;padding:0">{task_details(t, cases.get(t["case_id"]), ev_index)}</div></div>' for t in fails)
    if not fails: att = '<p>No failed tasks.</p>'
    gaps = result['readiness_gaps']
    gaps_html = ('<p><b>Readiness gaps.</b> The plan cannot close until these are defined:</p><div class="gaps">' + ''.join(f'<span>{E(GAP_LABEL.get(g, g.replace(":evidence:", ": source missing for ")))}</span>' for g in gaps) + '</div>') if gaps else ''
    todo = [t for t in tasks if bucket(t) == 'TODO']
    todo_html = (f'<p><b>{len(todo)} applicable tasks are not decided yet.</b></p><ul class="list">' + ''.join(f'<li><a href="#{anchor(t)}">{E(alias(t))}</a> {E(t["title"])}</li>' for t in todo[:10]) + (f'<li>… and {len(todo) - 10} more below.</li>' if len(todo) > 10 else '') + '</ul>') if todo else ''
    unk = by['UNKNOWN']
    unk_html = f'<p><b>{unk} tasks depend on capabilities nobody has verified.</b> They stay in the plan and never count as passed until someone confirms them.</p>' if unk else ''

    sections = ''
    for m, ts in mods.items():
        rows = ''.join(f'<details class="row" id="{anchor(t)}"><summary><span class="id" style="color:{COLORS[bucket(t)]}">{E(alias(t))}</span><span class="tt">{E(t["title"])}</span>'
                       f'<span class="act">{E(t["activity"])}</span><span><span class="pill p-{bucket(t)}">{E(state_label(t))}</span></span></summary>'
                       f'<div class="rbody">{task_details(t, cases.get(t["case_id"]), ev_index)}</div></details>' for t in ts)
        c = Counter(bucket(t) for t in ts)
        sections += f'<h3 class="mod">{E(m)} <small>{len(ts)} obligations · {c["PASS"]} passed · {c["FAIL"]} failed</small></h3>{rows}'

    find_html = ''
    for f in findings:
        find_html += (f'<div class="att"><div class="id">{E(f["id"])} · {E(f["state"])}</div><h3>{E(f["title"])}</h3><dl class="facts">'
                      f'<dt>Priority (I×F)</dt><dd>{E(f["impact"])}×{E(f["feasibility"])} = {E(f["impact"] * f["feasibility"])}; confidence {E(f["confidence"])}</dd>'
                      f'<dt>Root cause</dt><dd>{E(f["root_cause"])}</dd><dt>Proven impact</dt><dd>{E(f["proven_impact"])}</dd>'
                      f'<dt>Correction</dt><dd>{E(f["remediation"])}</dd><dt>Owner / due</dt><dd>{E(f["owner"])} / {E(f["due_at"])}</dd></dl></div>')
    integrity = 'Verified against the approved manifest and the evidence store' if result['integrity_verified'] else 'NOT verified (no external manifest or evidence store supplied)'
    passed = result['decided_obligations'] - result['failures']
    nums = [(len(tasks), 'obligations'), (result['applicable_obligations'], 'applicable'), (passed, 'passed'), (result['failures'], 'failed'),
            (by['TODO'], 'to do'), (result['unknown_obligations'], 'unknown'), (by['NOT_APPLICABLE'], 'not applicable')]
    sec = 3 if findings else 2
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:">
<title>Merestone report · {E(arch['system_name'])}</title><style>{DOC_CSS}</style></head><body><div class="page">
<div class="brand">{MARK}merestone <span style="font-weight:400">· assessment report</span></div>
<h1>{E(arch['system_name'])}</h1><p class="sub">Assessment {E(arch['assessment_id'])} · plan <span class="mono">{E(plan['plan_id'][:8])}</span> · generated {E(gen)}</p>
<div class="verdict" style="--vc:{vcol}"><div class="n">{code}</div><div><h3>{E(title)}</h3><p>{E(why)}</p></div>{mojo_svg(code, 4)}</div>
<div class="nums">{''.join(f'<div><b>{v}</b><span>{E(l)}</span></div>' for v, l in nums)}</div>
<table class="metaT"><tr><td>Version under test</td><td>{E(arch['snapshot_ref'] or '—')}</td></tr><tr><td>Authorization</td><td>{E(arch['authorization_ref'] or '—')}</td></tr>
<tr><td>Inventory reviewed by</td><td>{E(arch['inventory_review']['reviewer'] or '—')} {E(arch['inventory_review']['reviewed_at'])}</td></tr><tr><td>Integrity</td><td>{E(integrity)}</td></tr></table>
<h2><span class="num">01</span>At a glance</h2>
<div class="field">{field}<div class="legend">{legend}</div></div>
<p style="font-size:13px;color:var(--muted)">Each stone is one obligation: a case at a boundary. Select a stone to jump to its details.</p>
<h2><span class="num">02</span>What needs attention</h2>{att}{gaps_html}{todo_html}{unk_html}
{(f'<h2><span class="num">03</span>Findings</h2>' + find_html) if findings else ''}
<h2><span class="num">0{sec + 1}</span>All obligations, by module</h2>{sections}
<footer><p>{E(result['note'])}</p><p>Generated by Merestone {E(op.VERSION)} from the frozen plan record. This document is a view: it does not change or re-decide any result. Catalog <span class="mono">{E(plan['catalog_sha256'][:12])}</span> · architecture <span class="mono">{E(plan['architecture_sha256'][:12])}</span> · obligations <span class="mono">{E(plan['obligations_sha256'][:12])}</span>.</p></footer>
</div><script>{DOC_JS}</script></body></html>
"""


LAYOUTS = {'board': render_board, 'document': render_document}


def render_html(plan, result, findings=(), generated_at=None, layout='board'):
    if layout not in LAYOUTS: raise ValueError('Unknown report layout: ' + layout)
    return LAYOUTS[layout](plan, result, findings, generated_at)
