from __future__ import annotations
import csv,json,re,sys,unicodedata
from pathlib import Path
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[4]
SKILL=ROOT/'.agent'/'skills'/'simesapo-sales-skills-dist'
sys.path.insert(0,str(SKILL/'shared'))
import sheets_io

SHEET='https://docs.google.com/spreadsheets/d/1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ/edit?usp=sharing'
START,END=2365,2664
HEADERS=['company_name','url','address','phone','maps_url','contact_url','message','sent_at','status','error_reason','screenshot_path','provider_used','提案区分','', '区分','検出ワード']
FILES=[
 ROOT/'local_data/simesapo/runs/20260803_phase1_auto/auto_final_verified_50.csv',
 ROOT/'local_data/simesapo/runs/20260803_phase1_pet/pet_final_verified_50.csv',
 ROOT/'local_data/simesapo/runs/20260803_phase1_fitness/fitness_final_verified_50.csv',
 ROOT/'local_data/simesapo/runs/20260804_phase1_education/education_final_verified_50.csv',
 ROOT/'local_data/simesapo/runs/20260804_phase1_bridal_photo/bridal_final_verified_50.csv',
 ROOT/'local_data/simesapo/runs/20260804_phase1_funeral/funeral_final_verified_50.csv',
]
def norm(v):return re.sub(r'\s+','',unicodedata.normalize('NFKC',v or '').lower())
def company_key(v):return re.sub(r'株式会社|有限会社|合同会社|一般社団法人|一般財団法人|[・･.,，．_/\'"()（）\[\]［］:：-]','',norm(v))
def domain_key(v):return re.sub(r'^www\.','',(urlparse(v).hostname or '').lower())
expected=[]
for path in FILES:
    rows=list(csv.DictReader(path.open(encoding='utf-8-sig',newline='')))
    if len(rows)!=50:raise SystemExit(f'{path.name}_count={len(rows)}')
    expected.extend([[r.get(h,'') if h else '' for h in HEADERS] for r in rows])
book=sheets_io.get_client().open_by_url(SHEET);ws=book.worksheet('シート1')
actual=ws.get(f'A{START}:P{END}')
actual=[r+['']*(16-len(r)) for r in actual]
required={'company_name':0,'url':1,'contact_url':5,'区分':14,'検出ワード':15}
missing={k:sum(not r[i].strip() for r in actual) for k,i in required.items()}
names=[company_key(r[0]) for r in actual];domains=[domain_key(r[1]) for r in actual]
dup_names=len(names)-len(set(names));dup_domains=len(domains)-len(set(domains))
exact=sum(a[:16]==e for a,e in zip(actual,expected))
outside_names=set();outside_domains=set()
for tab in book.worksheets():
    vals=tab.get_all_values()
    for rowno,row in enumerate(vals[1:],2):
        if tab.title=='シート1' and START<=rowno<=END:continue
        if row and row[0].strip():outside_names.add(company_key(row[0]))
        if len(row)>1 and row[1].strip():outside_domains.add(domain_key(row[1]))
outside_conflicts=sum(n in outside_names or d in outside_domains for n,d in zip(names,domains))
result={'range':f'A{START}:P{END}','rows':len(actual),'expected_rows':len(expected),'exact_rows':exact,'missing_required':missing,'duplicate_company':dup_names,'duplicate_domain':dup_domains,'outside_conflicts':outside_conflicts}
print(json.dumps(result,ensure_ascii=False))
if len(actual)!=300 or exact!=300 or any(missing.values()) or dup_names or dup_domains or outside_conflicts:raise SystemExit('final_300_audit_failed')
