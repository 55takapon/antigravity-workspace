import csv
from pathlib import Path
p=Path(__file__).parent
rows=list(csv.DictReader((p/"jlaa_final_audit_33.csv").open(encoding="utf-8-sig")))
for r in rows:
    if r["company_name"]=="株式会社アクティブイエロー":
        r.update(classification="送付対象",contact_check="real_form_confirmed_manual",contact_url="https://docs.google.com/forms/d/e/1FAIpQLSftAbJCUhElC_0XOb6pp4yosD25ebiqyEtlV2SQvfm3_lIR1Q/viewform?usp=sf_link",audit_reason="広告・出版・地域情報発信／公式サイトからGoogleフォームへの導線を確認")
    if r["company_name"]=="株式会社ライズウィル":
        r["classification"]="除外"; r["audit_reason"]+="／001正規除外照合で非採用"
out=p/"final_audit_confirmed_33.csv"
with out.open("w",encoding="utf-8-sig",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
print(out)
