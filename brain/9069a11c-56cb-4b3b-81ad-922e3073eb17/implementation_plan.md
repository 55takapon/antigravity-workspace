# Implementation Plan - Refine Himeji Review Extraction

「Refine(リファイン) 姫路」のGoogleクチコミ55件を、ボット検知を回避しながら正確に抽出します。

## Proposed Changes

### [Web Scraping Component]

#### [MODIFY] [scrape_reviews_mobile.py](file:///c:/Users/hangy/.gemini/antigravity/scratch/scrape_reviews_mobile.py)
以前の汎用的なスクリプトを「Refine(リファイン) 姫路」専用に最適化します。
- **ステルス性の強化**: `playwright-stealth` 相当のJS注入を強化し、指紋（fingerprint）を隠蔽します。
- **待機戦略の変更**: 固定の待機ではなく、人間が読んでいるようなランダムな待機とスクロール速度を導入します。
- **要素セレクタの更新**: モバイル版Google検索の最新の要素構造に合わせてセレクタを厳密に定義します。
- **データ保存**: 抽出結果を `refine_himeji_reviews.json` に保存します。

## Verification Plan

### Automated Tests
- スクリプト単体実行: `python c:/Users/hangy/.gemini/antigravity/scratch/scrape_reviews_mobile.py` を実行し、コンソールに出力される抽出件数を確認します。
- JSON検証: 生成された `refine_himeji_reviews.json` を読み込み、件数が55件（または全件）に達しているか、データ形式が正しいかを確認します。

### Manual Verification
- デバッグ用スクリーンショット: 実行中に `debug_capture_*.png` を保存し、正しくレビュー一覧が表示・スクロールされているかを目視で確認します。
