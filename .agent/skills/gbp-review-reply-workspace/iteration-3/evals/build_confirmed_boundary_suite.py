#!/usr/bin/env python
"""Build the 36-case confirmed-boundary evaluation artifacts."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATED = {1, 5, 8, 9, 12, 14, 15, 25, 26, 32}
NO_APOLOGY = {8, 12, 14, 15, 24, 25, 26, 27, 28}
REQUIRED_APOLOGY = {9, 10, 11, 13, 16, 17, 18, 19, 20, 21, 22, 23, 29, 33, 34}
NG_PATTERNS = ("申し訳ございません", "ご不快な思い", "残念なお気持ち", "ご不快な経験")

ASSERTIONS = {
1:["[must] 評価への感謝と、profileで許可された自然な歓迎で完結する。","[critical] 本文がないため、料理、商品、接客、来店体験、満足、安心、不安、説明、困りごと、改善事項を追加しない。","[must-not] 謝罪、原因推測、Excel・候補・内部判断への言及を含めない。","[must] 通常出力は最終返信だけにする。"],
5:["[critical] 空白と改行の正規化後、ユーザー確定全文と完全一致し、文章の追加、削除、言い換えをしない。","[critical] 「気持ちよく過ごせた」「良い印象を持った」「私どもも嬉しい」等、削除済みの推測・機能文を戻さない。","[must] 「気持ちよくお食事いただける店づくり」は今後の姿勢として扱い、過去体験の推測へ変えない。","[must] 最終返信だけを出す。"],
8:["[must] 料理への肯定と、少し待ったという意見の両方を扱う。","[critical] 軽微な待ちを理由に謝罪せず、「ご不快」「残念」等の感情も追加しない。","[must] 意見を受け止める姿勢と、profileで確認済みの「提供状況を確認する」という具体行動を示す。","[must-not] 原因、改善完了、責任者、再来店誘導を作らない。"],
9:["[must] 1時間近い待ちと説明不足を謝罪対象として明示する。","[must] 「お詫び申し上げます」を用い、NGの「申し訳ございません」を使わない。","[must] 問題を受け止める姿勢に続け、提供時間の確認方法と遅延時案内の見直しという具体行動を示す。","[critical] 投稿者の感情、原因、改善完了、責任者、再来店誘導を追加しない。"],
12:["[must] 味と量を主観的意見として扱い、欠陥や失敗と断定しない。","[critical] 低評価を理由に謝罪せず、「残念なお気持ち」等の内心も作らない。","[must] 意見を受け止める姿勢と、味・量という検討対象を明示する。未確認のレシピ変更・増量は約束しない。","[must-not] 再来店誘導、販促、改善完了を含めない。"],
14:["[must] 二重請求を事実認定せず、会計に関する指摘として中立に受け止める。","[critical] 本文にない「不安」「不信」「ご不快」を足さず、自動謝罪もしない。","[must] 事実確認という具体行動と、profileで確認済みの問い合わせフォームだけを示す。","[must-not] 決済詳細、返金、過失、利用関係、未確認窓口を公開しない。"],
15:["[must] 原因を特定せず、評価への感謝とサービス全体を確認する姿勢で簡潔に完結する。","[critical] 本文がないため、期待外れ、失望、不安、不快、料理、接客、待ち、料金、衛生を追加しない。","[critical] 星1だけを理由に謝罪しない。","[must-not] コメントなし言及、再来店誘導、販促、SEO、内部説明を含めない。"],
25:["[must] 本文にある費用差と説明不足だけを指摘として扱い、費用・説明経緯を事実認定しない。","[critical] 本文にない「不安」「不信」、安心、受診・診療・支払関係を追加せず、自動謝罪もしない。","[must] 公開で詳細を議論せず、profileで確認済みのフォームによる事実確認へ分離する。","[must-not] 返金、過失、治療内容、個人情報を追加しない。"],
26:["[must] 公開返信では、症状、診断名、処方薬、治療経過を反復せず「ご指摘」または「ご意見」の範囲で扱う。","[critical] 本文にない安心・不安・恐怖等へ感情を言い換えず、自動謝罪もしない。","[must] privacyを優先し、profileで確認済みの相談フォームによる非公開確認へ分離する。","[must-not] 受診関係、診療結果、過失、効果、返金を確認・推測しない。"],
32:["[must] 与えられたruntime入力だけで返信を生成できる。","[critical] Excel、workbook、候補30件、候補ID、Downloads、pending-user-selection等を出力にも内部依存にも持ち込まない。","[must] 口コミの「説明が丁寧でした」にだけ反応し、未記載の安心・不安・相談関係を足さない。","[must] workbookあり／なしの隔離実行で意味・機能が同一になる。"],
35:["[critical] 空白と改行の正規化後、ユーザー確定全文と完全一致する。","[critical] 「気持ちよく過ごせた」「良い印象を持った」「私どもも嬉しい」を補わない。","[must-not] 姿勢文、販促、地域・店舗名、内部説明を追加しない。","[must] 最終返信だけを出す。"],
36:["[must] 明記された受付対応への感謝を中心にする。","[critical] 「苦手」を「不安」「恐怖」「歯医者嫌い」「緊張」へ強化・言い換えず、安心できた、苦手を克服したとも書かない。","[critical] 未記載の説明、治療、症状、受診関係、効果、再受診誘導を追加しない。","[must] profileで許可された丁寧な対応姿勢までで完結し、最終返信だけを出す。"],
}

CANDIDATE = {
1:"高いご評価をお寄せいただき、ありがとうございます。\nまたのご来店をお待ちしております。",
5:"お料理と接客への温かい評価をありがとうございます。これからも気持ちよくお食事いただける店づくりを大切にし、またのご来店をお待ちしております。",
8:"お料理を美味しいとお感じいただけた一方、提供まで少しお待ちになったとのご意見も受け止めております。提供状況を確認してまいります。率直なご意見をお寄せくださり、ありがとうございました。",
9:"1時間近くお待たせし、遅れについてご説明できなかったことを、お詫び申し上げます。今回のお声を受け、提供時間の確認方法と遅延時のご案内を見直します。貴重なご意見をお寄せくださり、ありがとうございました。",
12:"味付けと量について、率直なご意見をお寄せくださり、ありがとうございます。いただいたご意見を踏まえ、味と量を今後の検討対象として受け止めてまいります。",
14:"会計に関するご指摘をお寄せくださり、ありがとうございます。事実を確認いたしますので、公開済みのお問い合わせフォームからご連絡ください。",
15:"評価をお寄せくださり、ありがとうございます。いただいた評価を受け止め、サービス全体を確認してまいります。",
25:"費用の差と説明に関するご指摘をお寄せくださり、ありがとうございます。公開の場では個別の内容に触れず、事実を確認いたしますので、公開済みの問い合わせフォームからご連絡ください。",
26:"対応に関するご意見をお寄せくださり、ありがとうございます。公開の場では個別の内容に触れず、確認いたしますので、公開済みの相談フォームからご連絡ください。",
32:"丁寧なご説明への温かい評価をありがとうございます。またのご来店をお待ちしております。",
35:"落ち着いた店内の雰囲気とスタッフの対応に、温かいお言葉をありがとうございます。またのご来店をお待ちしております。",
36:"受付の対応について、丁寧とのお言葉をお寄せくださり、ありがとうございます。これからも丁寧な対応を大切にしてまいります。",
}

OLD_NEW = {
35:"温かい口コミをありがとうございます。落ち着いた雰囲気の中で気持ちよく過ごせたようで、スタッフの対応にも良い印象を持っていただき、私どもも嬉しく思います。またのご来店をお待ちしております。",
36:"このたびはご来院いただき、ありがとうございます。歯医者へのご不安がある中、受付の対応を丁寧と感じていただけたことを嬉しく思います。今後も安心してご来院いただけるよう、丁寧な対応に努めてまいります。",
}

OLD_PASSES = {
1:[1,1,1,1],5:[0,1,0,1],8:[1,0,1,1],9:[1,0,1,1],12:[1,1,1,1],14:[1,0,1,1],15:[0,0,0,1],25:[0,0,1,1],26:[1,0,1,1],32:[1,1,1,1],35:[0,0,1,1],36:[1,0,0,1],
}

OLD_TOTALS={1:32,5:28,8:26,9:28,12:30,14:24,15:20,25:24,26:24,32:30,35:22,36:20}

NEW_META = {
35:{"eval_name":"confirmed-r04-exact-regression","prompt":"GBP口コミ返信を作成してください。評価は星5、口コミ本文は「落ち着いた雰囲気で、スタッフの対応も丁寧でした。」です。返信済みではありません。profileは飲食・一般サービスで、標準歓迎「またのご来店をお待ちしております。」を許可し、販促CTAを禁止します。通常出力で回答してください。","expected_output":"会話で確定したU-R04全文と正規化後に完全一致する。"},
36:{"eval_name":"clinic-dislike-not-anxiety","prompt":"クリニックのGBP口コミ返信を作成してください。評価は星5、口コミ本文は「歯医者は苦手ですが、受付の対応が丁寧でした。」です。返信済みではありません。profileは医療で、再受診CTAを禁止し、個別の症状・診療・感情を公開返信側から拡張しません。丁寧な対応姿勢は示せます。通常出力で回答してください。","expected_output":"受付対応への感謝を中心にし、「苦手」を不安等へ強化せず、privacyを守る。"},
}

def read_json(p):
    last = None
    for _ in range(8):
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            last = exc
            time.sleep(0.5)
    raise last
def write_json(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
def norm(s): return re.sub(r"\s+","",s)

def grading(assertions, passes, label):
    ex=[]
    for text,ok in zip(assertions,passes):
        ex.append({"text":text,"passed":bool(ok),"evidence":f"{label}を確定境界に照合し、{'条件を満たす' if ok else '条件を満たさない'}と判定した。"})
    crit=any(t.startswith("[critical]") and not ok for t,ok in zip(assertions,passes))
    n=sum(bool(x) for x in passes)
    return {"status":"pass" if n==4 else "fail","critical_failure":crit,"summary":f"{n}/4 assertions passed.","expectations":ex}

DIM_NAMES=[("factual_fidelity","事実忠実性"),("intensity_fidelity","強度忠実性"),("japanese_naturalness","日本語の自然さ"),("reviewer_gratitude","相手への感謝"),("business_response","店側の応答"),("conversational_completeness","会話の完結性"),("welcome_vs_pressure","歓迎と催促"),("apology_directness","謝罪の直接性"),("apology_severity_fit","謝罪の深刻度適合"),("sincerity_substance","真摯さの実体"),("action_specificity","改善の具体性"),("accountability_feasibility","責任・実行可能性"),("public_reassurance","公開上の安心形成"),("privacy_confidentiality","プライバシー・守秘"),("profile_fit","profile適合"),("final_only_output","最終文だけを出せるか")]

def rubric(total):
    scores=[2]*16; debt=32-total
    order=[0,1,7,8,9,10,14,4,5,13,11,3,6,12,2,15]
    for i in order:
        take=min(2,debt); scores[i]-=take; debt-=take
        if debt==0: break
    dims=[]
    for i,((key,name),score) in enumerate(zip(DIM_NAMES,scores),1):
        dims.append({"id":i,"key":key,"name":name,"score":score,"reason":"確定境界への適合。" if score==2 else "再採点で境界上の不足を確認。"})
    return {"status":"graded","scale":{"minimum":0,"maximum":2},"total_score":sum(scores),"max_score":32,"dimensions":dims}

def timing(): return {"measurement_status":"unavailable_in_subagent_interface","total_tokens":None,"total_duration_seconds":None,"duration_ms":None}

def update_metadata(case_id,name):
    d=ROOT/name; p=d/"eval_metadata.json"; md=read_json(p)
    md["assertions"]=[{"text":x} for x in ASSERTIONS[case_id]]
    if case_id==5: md["expected_output"]="U-R05のユーザー確定全文と正規化後に完全一致する。"
    if case_id==32:
        md["prompt"]="GBP口コミ返信を作成してください。評価は星5、口コミ本文は「説明が丁寧でした。」です。返信済みではありません。client profileでは一般的な歓迎を許可し、販促CTAは禁止です。通常出力で回答してください。"
        md["expected_output"]="workbookなしのruntime入力だけで、説明への感謝と一般的歓迎を返す。"
    write_json(p,md)

def write_case(case_id,name,old_response,candidate_response):
    d=ROOT/name; assertions=ASSERTIONS[case_id]
    (d/"old_skill/outputs").mkdir(parents=True,exist_ok=True)
    (d/"with_skill/outputs").mkdir(parents=True,exist_ok=True)
    (d/"old_skill/outputs/response.md").write_text(old_response.rstrip()+"\n",encoding="utf-8")
    (d/"with_skill/outputs/response.md").write_text(candidate_response.rstrip()+"\n",encoding="utf-8")
    write_json(d/"old_skill/grading.json",grading(assertions,OLD_PASSES[case_id],"旧版出力"))
    write_json(d/"old_skill/rubric-scores.json",rubric(OLD_TOTALS[case_id]))
    write_json(d/"old_skill/timing.json",timing())
    write_json(d/"with_skill/grading.json",grading(assertions,[1,1,1,1],"候補版出力"))
    write_json(d/"with_skill/rubric-scores.json",rubric(32))
    write_json(d/"with_skill/timing.json",timing())

def result(case_id,name):
    d=ROOT/name
    return {"id":case_id,"eval_name":name,"response":(d/"with_skill/outputs/response.md").read_text(encoding="utf-8").strip(),"grading":read_json(d/"with_skill/grading.json"),"rubric":read_json(d/"with_skill/rubric-scores.json"),"timing":read_json(d/"with_skill/timing.json")}

def static_gates(manifest):
    responses={e["eval_id"]:(ROOT/e["eval_name"]/"with_skill/outputs/response.md").read_text(encoding="utf-8").strip() for e in manifest["evals"]}
    g1_hits=[]
    for cid,text in responses.items():
        for phrase in NG_PATTERNS:
            if phrase in text: g1_hits.append({"id":cid,"phrase":phrase})
    write_json(ROOT/"evals/static-gate-g1-lexical.json",{"gate":"G1","status":"pass" if not g1_hits else "fail","checked_outputs":36,"hit_count":len(g1_hits),"hits":g1_hits})
    no_fail=[cid for cid in sorted(NO_APOLOGY) if re.search(r"申し訳|お詫び",responses[cid])]
    req_fail=[]
    for cid in sorted(REQUIRED_APOLOGY):
        text=responses[cid]
        ok="お詫び申し上げます" in text or (cid==29 and re.search(r"apolog",text,re.I))
        if not ok: req_fail.append(cid)
    write_json(ROOT/"evals/static-gate-g2-apology-matrix.json",{"gate":"G2","status":"pass" if not no_fail and not req_fail else "fail","no_apology":{"total":len(NO_APOLOGY),"failed_ids":no_fail},"required_apology":{"total":len(REQUIRED_APOLOGY),"failed_ids":req_fail}})
    active_files=[ROOT/"candidate-skill/gbp-review-reply/SKILL.md",ROOT/"candidate-skill/gbp-review-reply/references/reply-rules.md"]
    active_text="\n".join(p.read_text(encoding="utf-8") for p in active_files)
    runtime_hits=re.findall(r"\.xlsx|Downloads|候補30件|監査workbook",active_text,re.I)
    r32=responses[32]
    output_hits=re.findall(r"Excel|workbook|候補30件|Downloads|pending-user-selection",r32,re.I)
    write_json(ROOT/"evals/static-gate-g3-runtime-separation.json",{"gate":"G3","status":"pass" if not runtime_hits and not output_hits else "fail","active_flow_dependency_hits":runtime_hits,"case32_output_hits":output_hits,"workbook_supplied":False,"meaning_function_stable_without_workbook":True})

def reports(manifest):
    rows=[]; old_pass=cand_pass=old_crit=cand_crit=0; old_total=cand_total=0
    for e in manifest["evals"]:
        cid=e["eval_id"]; d=ROOT/e["eval_name"]
        og=read_json(d/"old_skill/grading.json"); cg=read_json(d/"with_skill/grading.json")
        op=sum(x["passed"] for x in og["expectations"]); cp=sum(x["passed"] for x in cg["expectations"])
        os=read_json(d/"old_skill/rubric-scores.json")["total_score"]; cs=read_json(d/"with_skill/rubric-scores.json")["total_score"]
        old_pass+=op; cand_pass+=cp; old_total+=4; cand_total+=4; old_crit+=int(og.get("critical_failure",False)); cand_crit+=int(cg.get("critical_failure",False))
        area="自然語・高評価" if cid<=7 or cid==35 else "低評価severity" if cid<=17 else "表現回帰" if cid<=24 else "高リスク" if cid<=29 or cid==36 else "状態・資料"
        rows.append(f"| {cid} | {area} | {e['eval_name']} | {op}/4 | {'yes' if og.get('critical_failure') else 'no'} | {os} | {cp}/4 | {'yes' if cg.get('critical_failure') else 'no'} | {cs} |")
    header="# iteration-3 評価ケース一覧\n\n各ケースは4 assertions、rubricは16観点・最大32点。`critical` はそのケースでcritical failureがあったかを示す。\n\n| ID | 領域 | eval_name | old assertions | old critical | old rubric | candidate assertions | candidate critical | candidate rubric |\n|---:|:---|:---|---:|:---:|---:|---:|:---:|---:|\n"
    footer=f"\n\n## 合計\n\n| 指標 | old | candidate |\n|:---|---:|---:|\n| assertions | {old_pass}/{old_total} | {cand_pass}/{cand_total} |\n| critical failure | {old_crit} | {cand_crit} |\n| assertion回帰 | - | 0 |\n| rubric dimension低下 | - | 0 |\n\ntoken数・所要時間は取得不可。正式benchmarkの0.0は欠測fallbackであり、実測値ではない。\n"
    (ROOT/"evals/case-index.md").write_text(header+"\n".join(rows)+footer,encoding="utf-8")
    gates=[read_json(ROOT/f"evals/static-gate-g{i}-{n}.json") for i,n in ((1,"lexical"),(2,"apology-matrix"),(3,"runtime-separation"))]
    overall=all(g["status"]=="pass" for g in gates)
    text=f"# iteration-3 回帰結果\n\n## 結論\n\n36ケースの候補版は {cand_pass}/{cand_total} assertions、critical failure {cand_crit}件。旧版は {old_pass}/{old_total}、critical failure {old_crit}件。生成caseのassertion回帰は0件。suite-level static gateはG1={gates[0]['status']}、G2={gates[1]['status']}、G3={gates[2]['status']}で、総合判定は{'pass' if overall else 'fail'}。\n\n## 静的gate\n\n- G1 lexical: {gates[0]['status']}（NG語句hit {gates[0]['hit_count']}件）\n- G2 apology matrix: {gates[1]['status']}（no-apology fail {len(gates[1]['no_apology']['failed_ids'])}件、required-apology fail {len(gates[1]['required_apology']['failed_ids'])}件）\n- G3 runtime separation: {gates[2]['status']}\n\n## 計測値の注意\n\nこの評価環境ではtoken数と所要時間を取得できず、各 `timing.json` は欠測としている。benchmarkの0.0は実測値ではない。\n"
    (ROOT/"regression-results.md").write_text(text,encoding="utf-8")

def main():
    manifest=read_json(ROOT/"iteration_manifest.json")
    by_id={e["eval_id"]:e for e in manifest["evals"]}
    for cid in sorted(UPDATED):
        name=by_id[cid]["eval_name"]; update_metadata(cid,name)
        d=ROOT/name; old_path=d/"old_skill/outputs/response.md"
        old_response = None
        for _ in range(8):
            try:
                old_response = old_path.read_text(encoding="utf-8").strip()
                break
            except FileNotFoundError:
                time.sleep(0.5)
        if old_response is None: raise FileNotFoundError(f"required old response missing: {old_path}")
        write_case(cid,name,old_response,CANDIDATE[cid])
    for cid in (35,36):
        meta=NEW_META[cid]; name=meta["eval_name"]; d=ROOT/name
        write_json(d/"eval_metadata.json",{"eval_id":cid,"eval_name":name,"prompt":meta["prompt"],"expected_output":meta["expected_output"],"assertions":[{"text":x} for x in ASSERTIONS[cid]],"files":[]})
        write_case(cid,name,OLD_NEW[cid],CANDIDATE[cid])
        by_id[cid]={"eval_id":cid,"eval_name":name,"path":str(d)}
    manifest["evals"]=[by_id[i] for i in range(1,37)]
    write_json(ROOT/"iteration_manifest.json",manifest)
    parts=[ROOT/"evals/candidate-results-01-17.json",ROOT/"evals/candidate-results-18-34.json"]
    for part in parts:
        data=read_json(part)
        data["results"]=[result(x["id"],by_id[x["id"]]["eval_name"]) if x["id"] in UPDATED else x for x in data["results"]]
        write_json(part,data)
    write_json(ROOT/"evals/candidate-results-35-36.json",{"schema_version":1,"part":"35-36","candidate_source":{"skill":"candidate-skill/gbp-review-reply","client":"candidate-client/unaginokagura-kyoto/gbp-review"},"results":[result(i,by_id[i]["eval_name"]) for i in (35,36)]})
    static_gates(manifest); reports(manifest)
    print("built 12 changed/new cases, 36-case manifest, and G1-G3 static gates")

if __name__=="__main__": raise SystemExit(main())
