"""Offline verification of the catalog, generated views, walkthroughs and local links."""
import argparse,hashlib,json,re,sys
from pathlib import Path
from urllib.parse import unquote
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R));import operational as op
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
 lib=op.library();checks={};errors=[]
 def check(value,label):
  if not value:errors.append(label)
 # Case/control links are bidirectional; a source association cannot silently substitute a case.
 cids={c['id'] for c in lib['cases']}
 for ctl in lib['controls']:
  check(set(ctl['case_ids'])<={c['id'] for c in lib['cases'] if ctl['id'] in c['control_ids']},'Control inconsistent: '+ctl['id'])
 for c in lib['cases']:
  for ctl in c['control_ids']:check(c['id'] in next(x for x in lib['controls'] if x['id']==ctl)['case_ids'],'Case inconsistent: '+c['id'])
  path=R/'playbook/fieldcards'/(c['id']+'.md')
  check(path.exists() and path.read_text(encoding='utf-8')==op.render_case(c,lib),'Stale fieldcard: '+c['id'])
 check({p.stem for p in (R/'playbook/fieldcards').glob('*.md')}==cids,'Stale/deleted case still rendered')
 checks['cases']=len(cids);checks['controls']=len(lib['controls']);checks['techniques']=len(lib['techniques']);checks['examples']=len(lib['examples']);checks['scenarios']=len(lib['scenarios'])
 # Every technique family has a generated walkthrough; every example is reachable from a technique.
 fams={t['family'] for t in lib['techniques'] if t.get('family')}
 check({p.stem for p in (R/'playbook/walkthroughs').glob('*.md')}=={'README'}|fams,'Walkthrough family mismatch')
 checks['walkthroughs']=len(fams)
 tids={t['id'] for t in lib['techniques']}
 check(all(set(e['technique_ids'])<=tids for e in lib['examples']),'Example with unknown technique')
 # Local links in framework docs resolve.
 docs=[p for folder in [R/'playbook',R/'templates',R/'docs'] for p in folder.rglob('*.md')]+[R/'README.md']
 links=0
 for p in docs:
  content=p.read_text(encoding='utf-8');content=re.sub(r'```.*?```','',content,flags=re.S)
  for match in re.finditer(r'\]\(([^\n)]+)\)',content):
   target=match.group(1).strip().strip('<>')
   if re.match(r'^[a-zA-Z]+://',target) or target.startswith('#'):continue
   target=unquote(target.split('#',1)[0]);links+=1
   check((p.parent/target).exists(),'Broken link: '+str(p.relative_to(R))+' -> '+target)
 checks['local_links_verified']=links
 sr=op.read(R/'catalog/sources/references.json');check(sha(R/'catalog/sources'/sr['snapshot_path'])==sr['snapshot_sha256'],'Reference snapshot hash')
 mappings=op.read(R/'catalog/mappings/index.json')
 check(all(m['entity_id'] in cids and all(m.get(k) for k in ('rationale','version','url','consulted_on','reviewer')) for m in mappings),'Mapping metadata')
 checks['mappings']=len(mappings)
 return {'status':'PASS' if not errors else 'FAIL','checks':checks,'errors':errors,
   'scope':'Integrity of the catalog, generated views, walkthroughs, references and local links. No claim of system certification; no independent human review.'}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out');a=p.parse_args()
 try:
  r=verify()
  if a.out:op.write(a.out,r)
  print(json.dumps(r,ensure_ascii=False,indent=2));sys.exit(0 if r['status']=='PASS' else 1)
 except (OSError,ValueError,KeyError,TypeError) as e:print(str(e),file=sys.stderr);sys.exit(2)
