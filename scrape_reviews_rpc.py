import requests
import json
import re

def main():
    # Google Maps RPC endpoint for reviews
    # pb parameter contains the place ID (FID) in a specific protobuf-like format
    # FID: 0x3554e19574fcf3ef:0x8fd62496a7888795
    # hex 3554e19574fcf3ef -> dec 3842940608518976495
    # hex 8fd62496a7888795 -> dec 10364654388152526741
    
    # pb payload structure: !1m2!1y{ID1}!2y{ID2}!2m2!1i{START}!2i{COUNT}!3e1
    pb_payload = "!1m2!1y3842940608518976495!2y10364654388152526741!2m2!1i0!2i60!3e1"
    url = f"https://www.google.com/maps/rpc/listreviews?authuser=0&hl=ja&gl=jp&pb={pb_payload}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Referer": "https://www.google.com/maps/"
    }
    
    print(f"Fetching reviews via RPC...")
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            # Google RPC response usually starts with )]}'
            content = response.text
            if content.startswith(")]}'"):
                content = content[4:].strip()
            
            # This is a nested list structure, not pure JSON
            # We can try to extract names and comments using regex or list parsing
            print("RPC call success. Parsing content...")
            
            # Simple regex to find blocks that look like reviews [name, text, rating, date]
            # Google's internal format is very complex, so we'll look for strings
            
            reviews = []
            # 各クチコミは特定のパターンの後に続くことが多い
            # 簡略化のため、JSONとしてパースを試みる（一部不正な形式を含む可能性あり）
            try:
                data = json.loads(content)
                # data[2] にクチコミリストが入っていることが多い
                review_list = data[2]
                for r in review_list:
                    try:
                        name = r[0][1]
                        text = r[3]
                        rating = r[4]
                        date = r[1]
                        
                        if text and text.strip():
                            reviews.append({
                                "name": name,
                                "text": text,
                                "rating": f"{rating} stars",
                                "date": date
                            })
                    except: continue
            except:
                # 正規表現によるフォールバック抽出
                names = re.findall(r'\"([^\"]+)\",null,\[null,null,null,null,\[\"https:\/\/lh3\.googleusercontent\.com', content)
                comments = re.findall(r'\[\"([^\"]+)\",\"ja\",null,null,null,null,null,null,null,null,null,0\]', content)
                # 注意: RPCレスポンスのパースは非常に不安定なため、あくまで試行
                print(f"Regex found {len(names)} names and {len(comments)} comments.")

            if not reviews:
                # 最終手段: contentをそのまま保存して確認
                with open("rpc_debug.txt", "w", encoding="utf-8") as f:
                    f.write(content)
            
            with open("google_rpc_reviews.json", "w", encoding="utf-8") as f:
                json.dump(reviews, f, ensure_ascii=False, indent=2)
            
            print(f"Done. Found {len(reviews)} reviews.")
        else:
            print(f"RPC call failed with status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
