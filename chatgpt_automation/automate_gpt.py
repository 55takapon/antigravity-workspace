import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        # ブラウザを起動 (headless=False で画面を表示)
        # ユーザーが操作を見たり、ログイン操作を行うために必要です
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        context = await browser.new_context()
        page = await context.new_page()

        print("--- ChatGPT自動化スクリプト ---")
        print("1. ChatGPTのログイン画面へ移動します...")
        await page.goto("https://chatgpt.com/auth/login")

        # ユーザー操作待機
        print("\n" + "="*50)
        print("【一時停止中】")
        print("これより先は手動で操作をお願いします。")
        print("Googleアカウント等でログインを行い、チャット画面の準備ができたら、")
        print("このターミナルに戻り Enter キーを押して続きを実行してください。")
        print("="*50 + "\n")
        input() # ユーザーの入力待機

        print("2. GPTストアへ移動して「ワークコンパスAI」を検索します...")
        
        try:
            # GPTストアへ直接移動
            await page.goto("https://chatgpt.com/gpts")
            
            # 検索ボックス待機 (英語/日本語どちらのUIにも対応できるよう試みます)
            # input[type='search'] は比較的汎用的です
            search_selector = "input[type='search']"
            try:
                await page.wait_for_selector(search_selector, timeout=10000)
            except:
                print("検索ボックスが見つかりませんでした。画面の構造が変わっている可能性があります。")
                return

            # 入力
            await page.fill(search_selector, "ワークコンパスAI")
            await page.press(search_selector, "Enter")
            
            print("   検索中...")
            await page.wait_for_timeout(3000) # 結果表示待ち
            
            # 「ワークコンパスAI」というテキストを持つ要素をクリック
            # 完全に一致するか、部分一致か。まずは部分一致で探します。
            # 複数の候補が出る可能性があるため、最初に見つかったものをクリックします。
            # タイトルとして表示されている可能性が高い要素を狙います。
            
            # Locatorの作成
            target = page.locator("div").filter(has_text="ワークコンパスAI").first
            
            # 明示的にクリックできるか確認してからクリック
            if await target.count() > 0:
                print("   ターゲットが見つかりました。クリックします...")
                # 少し強引ですが、座標クリックではなく要素クリックを試みます
                # 実際には検索結果のカード全体がクリック可能であることが多いです
                await target.click()
            else:
                print("「ワークコンパスAI」が見つかりませんでした。")
                print("手動で選択してください。選択後、Enterを押してください。")
                input()
            
            print("3. チャット画面への遷移を待機しています...")
            # URLが /g/ を含むものに変わるか、テキストエリアが表示されるのを待つ
            try:
                await page.wait_for_selector("#prompt-textarea", timeout=10000)
            except:
                print("チャット入力欄が見つかりませんでした。")
                print("手動で「チャットを開始」ボタンなどを押してください。")
                print("準備ができたら Enter を押してください。")
                input()

            textarea_selector = "#prompt-textarea"
            
            print(f"4. メッセージ「SNS運用始めたい」を入力します...")
            await page.fill(textarea_selector, "SNS運用始めたい")
            
            print("   入力完了。送信しますか？ (Enterで送信)")
            input()
            
            await page.press(textarea_selector, "Enter")
            print("   送信しました！")
            
            # 送信後の様子を見るために少し待機
            await asyncio.sleep(10)

        except Exception as e:
            print(f"\nエラーが発生しました: {e}")
            print("自動操作を中断します。ブラウザはそのまま開いています。")

        finally:
            print("\nスクリプトを終了します。ブラウザを閉じます。")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
