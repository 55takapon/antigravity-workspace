import csv,json,sys
from pathlib import Path
ROOT=Path(r'C:\Users\hangy\.gemini\antigravity');DIST=ROOT/'.agent/skills/simesapo-sales-skills-dist';RUN=Path(__file__).parent
sys.path[:0]=[str(DIST/'.codex_pydeps'),str(DIST/'shared')]
from sheets_io import get_client
names={'株式会社 第一通信社','株式会社 双葉通信社','株式会社 メディアデプト','コモンズ株式会社','株式会社 春光社'}
def pad(r,n=16):return r+['']*(n-len(r))
sh=get_client(str(DIST/'shared/gcp_service_account.json')).open_by_key('1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ');ws=sh.worksheet('シート2');ex=sh.worksheet('除外リスト');pw=sh.worksheet('収集進捗管理')
sv=[pad(r) for r in ws.get('A1:P',value_render_option='FORMULA')];ev=[pad(r) for r in ex.get('A1:P',value_render_option='FORMULA')]
found=[(i,r) for i,r in enumerate(sv[1:],2) if r[0] in names and 'JAAA' in r[14]]
if len(found)!=5:raise SystemExit('STOP expected 5 found '+str(len(found)))
with (RUN/'sheet2_before_withdraw.data').open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(sv)
with (RUN/'exclusion_before_withdraw.data').open('w',encoding='utf-8-sig',newline='') as f:csv.writer(f).writerows(ev)
ers=[]
for _,r in found:
 x=['']*16;x[0]=r[0];x[1]=r[1];x[5]=r[5];x[8]='skip監査除外';x[9]='ユーザー判断：JAAA追加5社は提案対象として不採用';x[12]='JAAA再判定';x[14]='除外｜JAAA再判定';x[15]=f'【除外根拠】ユーザー判断により提案対象外｜【補足】規模・系列・協業確度を総合して5社すべて不採用｜【根拠URL】{r[1]}｜【監査日】2026-08-12';ers.append(x)
ex.append_rows(ers,value_input_option='RAW',table_range=f'A{len(ev)+1}:P')
for i,_ in sorted(found,reverse=True):ws.delete_rows(i)
pw.update(range_name='A87:F87',values=[['4','NEXT-A-JAAA-001','日本広告業協会（JAAA）会員社一覧','公式公開136件／既存104／新規除外32','追加5社を再判定し全件不採用','5社を除外リストへ移動済み']],value_input_option='RAW')
pw.update(range_name='A89:F89',values=[['進捗','再計算完了','純増864社','8.64%','有効基準9,105社','残り9,136社']],value_input_option='RAW')
sv2=[pad(r) for r in ws.get('A1:P',value_render_option='FORMULA')];ev2=[pad(r) for r in ex.get('A1:P',value_render_option='FORMULA')];first=next(i for i,r in enumerate(sv2[1:],2) if r[14].startswith('除外'))
rep={'removed':5,'exclusions_added':5,'sheet2_before':len(sv),'sheet2_after':len(sv2),'exclusion_before':len(ev),'exclusion_after':len(ev2),'send_count':sum(r[14].startswith('送付対象') for r in sv2[1:]),'first_exclusion_row':first,'contiguous':all(r[14].startswith('除外') for r in sv2[first-1:]),'remaining_jaaa_send':[r[0] for r in sv2 if 'JAAA' in r[14] and r[14].startswith('送付対象')],'progress':pw.get('A87:F87')+pw.get('A89:F89')}
if not(len(sv2)==len(sv)-5 and len(ev2)==len(ev)+5 and rep['send_count']==864 and rep['contiguous'] and not rep['remaining_jaaa_send']):raise SystemExit('STOP '+json.dumps(rep,ensure_ascii=False))
(RUN/'withdraw_verification.json').write_text(json.dumps(rep,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(rep,ensure_ascii=False,indent=2))
