import json,sys
from pathlib import Path
R=Path(r"C:\Users\hangy\.gemini\antigravity");D=R/".agent"/"skills"/"simesapo-sales-skills-dist";sys.path[:0]=[str(D/".codex_pydeps"),str(D/"shared")]
from sheets_io import get_client
sh=get_client(str(D/"shared"/"gcp_service_account.json")).open_by_key("1gX4I6gfqoadr8nAtIu8uf9uPFc-lHhq1ORaKEuvnkJQ")
targets={"ジェービーエフ","jbf","totsu-ag.com"}
out=[]
for ws in sh.worksheets():
  vals=ws.get_all_values()
  for i,r in enumerate(vals[1:],2):
    if r and any(t.lower() in ((r[0] if len(r)>0 else "")+" "+(r[1] if len(r)>1 else "")).lower() for t in targets): out.append({"tab":ws.title,"row":i,"values":r[:16]})
print(json.dumps(out,ensure_ascii=False,indent=2))
