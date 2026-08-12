import json, sys
from pathlib import Path
ROOT=Path(r"C:\Users\hangy\.gemini\antigravity")
DIST=ROOT/".agent"/"skills"/"simesapo-sales-skills-dist"
sys.path[:0]=[str(DIST/".codex_pydeps"),str(DIST/"shared")]
from sheets_io import get_client
sh=get_client(str(DIST/"shared"/"gcp_service_account.json")).open_by_key("1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ")
out={}
for tab in ["シート2","除外リスト","収集進捗管理"]:
    ws=sh.worksheet(tab)
    vals=ws.get_all_values()
    out[tab]={"rows":len(vals),"cols":ws.col_count,"header":vals[0] if vals else [],"tail":vals[-3:] if vals else []}
print(json.dumps(out,ensure_ascii=False,indent=2))
