"""
Googleマップ レビュー口コミ分析スクリプト
=========================================
抽出済みレビューJSONを入力し、プロマーケター視点で多面的に分析する。
外部NLPライブラリ不要（日本語キーワード辞書ベース）。

使用方法:
  python analyze_reviews.py reviews.json [--output report.md]

入力JSONフォーマット:
  { "reviews": [{"name": "...", "rating": 5, "date": "1年前", "text": "...", "owner_reply": "...", "has_owner_reply": true}] }

  または既存フォーマット:
  { "bomnal_chicken": [{"name": "...", "rating": "5 stars", "date": "1年前", "text": "..."}] }
"""

import json
import re
import sys
import os
import datetime
from collections import Counter, defaultdict
from argparse import ArgumentParser

# ============================================================
# 日本語分析用辞書定義
# ============================================================

# センチメント辞書
POSITIVE_WORDS = [
    "美味しい", "おいしい", "うまい", "旨い", "ンマ", "最高", "絶品", "大好き",
    "素敵", "素晴らしい", "嬉しい", "楽しい", "幸せ", "感動",
    "丁寧", "親切", "気さく", "笑顔", "優しい", "温かい", "あたたかい",
    "綺麗", "キレイ", "きれい", "清潔", "オシャレ", "おしゃれ",
    "コスパ", "お手頃", "リーズナブル", "安い",
    "おすすめ", "オススメ", "お勧め", "おススメ",
    "リピート", "リピ", "また行", "また買", "また来", "また利用",
    "満足", "大満足", "間違いない", "ハズレなし",
    "柔らかい", "ジューシー", "新鮮", "本格的", "本場",
    "落ち着く", "居心地", "アットホーム", "癒し",
    "星5", "⭐5", "文句なし",
]

NEGATIVE_WORDS = [
    "まずい", "不味い", "微妙", "残念", "がっかり", "期待外れ",
    "高い", "高すぎ", "割高",
    "遅い", "時間がかかる", "待ち時間",
    "冷たい", "態度が悪い", "不愛想", "対応が悪い",
    "汚い", "不衛生", "臭い",
    "少ない", "量が少ない", "物足りない",
    "うるさい", "騒がしい",
]

# トピック分類キーワード
TOPIC_KEYWORDS = {
    "味・品質": [
        "美味しい", "おいしい", "うまい", "旨い", "味", "辛い", "甘い", "酸味",
        "柔らか", "ジューシー", "サクサク", "パリパリ", "揚げたて", "作りたて",
        "出来たて", "本格", "本場", "クセになる", "癖になる",
    ],
    "接客・人柄": [
        "接客", "店員", "マスター", "オーナー", "店主", "スタッフ",
        "丁寧", "親切", "気さく", "笑顔", "感じが良い", "感じのいい",
        "温かい", "あたたかい", "対応", "人柄", "愛想",
    ],
    "価格・コスパ": [
        "コスパ", "値段", "価格", "安い", "リーズナブル", "お手頃",
        "高い", "割高", "お得", "サービス", "スタンプ",
    ],
    "雰囲気・清潔さ": [
        "雰囲気", "内装", "店内", "清潔", "キレイ", "綺麗", "きれい",
        "落ち着く", "居心地", "アットホーム", "オシャレ", "おしゃれ",
        "レトロ", "癒し",
    ],
    "立地・アクセス": [
        "駅", "徒歩", "近く", "アクセス", "場所", "立地",
        "駐車場", "分程",
    ],
    "待ち時間・オペレーション": [
        "待ち時間", "待ち", "予約", "テイクアウト", "持ち帰り",
        "注文してから", "LINE", "ライン", "Uber", "出前",
    ],
}

# 顧客像キーワード
CUSTOMER_KEYWORDS = {
    "家族連れ": ["家族", "子供", "子ども", "息子", "娘", "ファミリー", "お子様"],
    "一人客": ["一人", "ひとり", "1人"],
    "カップル・友人": ["友達", "友人", "彼女", "彼氏", "デート", "カップル"],
    "リピーター": ["リピート", "リピ", "何度も", "いつも", "定期的", "通って"],
}

# USP検出パターン
USP_PATTERNS = [
    r"一番[^\s、。！]{0,10}(美味|おいし|うまい)",
    r"ダントツ",
    r"(今まで|これまで).*一番",
    r"他[^\s]*と比べ",
    r"ここが一番",
    r"どこより",
    r"最高[にで]",
    r"こんな.*食べたことない",
    r"間違いない",
]

# リピート意向パターン
REPEAT_PATTERNS = [
    r"また[^\s]*行[きくい]", r"また[^\s]*買[いう]", r"また[^\s]*来[るたい]",
    r"また[^\s]*利用", r"リピート", r"リピ確定", r"リピ[しする]",
    r"何度も", r"通[いう]たい",
]

# 推奨意向パターン
RECOMMEND_PATTERNS = [
    r"おすすめ", r"オススメ", r"お勧め", r"おススメ",
    r"一度[^\s]*行[くき]べき", r"行って[みほ]",
    r"皆[さ様].*是非",
]


# ============================================================
# レビューデータ正規化
# ============================================================

def normalize_reviews(data: dict | list) -> list[dict]:
    """さまざまなJSONフォーマットを統一形式に変換"""
    reviews = []
    
    if isinstance(data, list):
        # リスト形式: [{"name": ..., "rating": ...}, ...]
        raw_list = data
    elif isinstance(data, dict):
        if "reviews" in data:
            raw_list = data["reviews"]
        else:
            # 店舗名キーの辞書: {"store_name": [...]}
            raw_list = []
            for key, val in data.items():
                if isinstance(val, list):
                    raw_list.extend(val)
    else:
        return []
    
    for item in raw_list:
        rating = item.get("rating")
        if isinstance(rating, str):
            m = re.search(r'(\d)', rating)
            rating = int(m.group(1)) if m else None
        
        has_reply = item.get("has_owner_reply", False)
        owner_reply = item.get("owner_reply")
        text = item.get("text", "")
        
        # テキスト内の「オーナーからの返信:」を分離
        if "オーナーからの返信" in text and not owner_reply:
            parts = re.split(r'オーナーからの返信[:：]', text, maxsplit=1)
            text = parts[0].strip()
            owner_reply = parts[1].strip() if len(parts) > 1 else None
            has_reply = owner_reply is not None
        
        reviews.append({
            "name": item.get("name", "不明"),
            "rating": rating,
            "date": item.get("date", "不明"),
            "text": text,
            "has_owner_reply": has_reply,
            "owner_reply": owner_reply,
        })
    
    return reviews


def parse_relative_date(date_str: str) -> str:
    """相対日付を大まかな時期区分に変換"""
    if re.search(r'[12]?\d\s*か月前', date_str):
        m = re.search(r'(\d+)', date_str)
        months = int(m.group(1)) if m else 0
        if months <= 3:
            return "直近(〜3ヶ月)"
        elif months <= 6:
            return "半年以内"
        else:
            return "半年〜1年"
    elif "年前" in date_str:
        m = re.search(r'(\d+)', date_str)
        years = int(m.group(1)) if m else 1
        if years == 1:
            return "1年前"
        elif years <= 2:
            return "2年前"
        else:
            return f"{years}年以上前"
    elif "週間前" in date_str or "日前" in date_str:
        return "直近(〜3ヶ月)"
    else:
        return "不明"


# ============================================================
# 分析エンジン
# ============================================================

def analyze_rating_summary(reviews: list[dict]) -> dict:
    """セクション1: 評価サマリー"""
    ratings = [r["rating"] for r in reviews if r["rating"] is not None]
    if not ratings:
        return {"error": "評価データなし"}
    
    distribution = Counter(ratings)
    sorted_ratings = sorted(ratings)
    n = len(sorted_ratings)
    median = sorted_ratings[n // 2] if n % 2 == 1 else (sorted_ratings[n//2 - 1] + sorted_ratings[n//2]) / 2
    
    # 時期別
    period_ratings = defaultdict(list)
    for r in reviews:
        if r["rating"] is not None:
            period = parse_relative_date(r["date"])
            period_ratings[period].append(r["rating"])
    
    period_summary = {}
    for period, vals in period_ratings.items():
        period_summary[period] = {
            "件数": len(vals),
            "平均": round(sum(vals) / len(vals), 2),
        }
    
    return {
        "総レビュー数": len(reviews),
        "評価あり件数": len(ratings),
        "平均評価": round(sum(ratings) / len(ratings), 2),
        "中央値": median,
        "星分布": {f"★{i}": distribution.get(i, 0) for i in range(5, 0, -1)},
        "星分布率": {f"★{i}": f"{distribution.get(i, 0) / len(ratings) * 100:.1f}%" for i in range(5, 0, -1)},
        "時期別傾向": period_summary,
    }


def analyze_text(reviews: list[dict]) -> dict:
    """セクション2: テキスト分析"""
    texts = [r["text"] for r in reviews if r["text"]]
    all_text = " ".join(texts)
    
    # --- センチメント分析 ---
    sentiment_results = {"ポジティブ": 0, "ネガティブ": 0, "ニュートラル": 0}
    review_sentiments = []
    
    for r in reviews:
        text = r["text"]
        if not text:
            continue
        pos_count = sum(1 for w in POSITIVE_WORDS if w in text)
        neg_count = sum(1 for w in NEGATIVE_WORDS if w in text)
        
        if pos_count > neg_count:
            sentiment = "ポジティブ"
        elif neg_count > pos_count:
            sentiment = "ネガティブ"
        else:
            # 星評価で補完
            if r["rating"] and r["rating"] >= 4:
                sentiment = "ポジティブ"
            elif r["rating"] and r["rating"] <= 2:
                sentiment = "ネガティブ"
            else:
                sentiment = "ニュートラル"
        
        sentiment_results[sentiment] += 1
        review_sentiments.append({
            "name": r["name"],
            "rating": r["rating"],
            "sentiment": sentiment,
            "pos_hits": pos_count,
            "neg_hits": neg_count,
        })
    
    # --- 頻出キーワード ---
    # 日本語のキーワードカウント（辞書ベース）
    all_keywords = POSITIVE_WORDS + NEGATIVE_WORDS
    for topic_words in TOPIC_KEYWORDS.values():
        all_keywords.extend(topic_words)
    all_keywords = list(set(all_keywords))
    
    keyword_counts = Counter()
    for word in all_keywords:
        count = sum(1 for text in texts if word in text)
        if count > 0:
            keyword_counts[word] = count
    
    # --- トピック分類 ---
    topic_counts = {}
    topic_reviews = defaultdict(list)
    
    for topic, keywords in TOPIC_KEYWORDS.items():
        count = 0
        for r in reviews:
            if any(kw in r["text"] for kw in keywords):
                count += 1
                topic_reviews[topic].append(r["name"])
        topic_counts[topic] = count
    
    # --- 顧客像 ---
    customer_segments = {}
    for segment, keywords in CUSTOMER_KEYWORDS.items():
        matched = []
        for r in reviews:
            if any(kw in r["text"] for kw in keywords):
                matched.append(r["name"])
        if matched:
            customer_segments[segment] = {
                "検出数": len(matched),
                "投稿者": matched[:5],  # 上位5名まで
            }
    
    total_with_text = len(texts)
    
    return {
        "センチメント": {
            "分布": sentiment_results,
            "ポジティブ率": f"{sentiment_results['ポジティブ'] / max(total_with_text, 1) * 100:.1f}%",
        },
        "頻出キーワードTOP20": dict(keyword_counts.most_common(20)),
        "トピック別言及数": topic_counts,
        "トピック別言及率": {k: f"{v / max(total_with_text, 1) * 100:.1f}%" for k, v in topic_counts.items()},
        "顧客像の手がかり": customer_segments,
        "レビュー平均文字数": round(sum(len(t) for t in texts) / max(len(texts), 1), 1),
    }


def analyze_strengths_weaknesses(reviews: list[dict]) -> dict:
    """セクション3: 強み・弱み分析"""
    
    # --- USP抽出 ---
    usp_reviews = []
    for r in reviews:
        for pattern in USP_PATTERNS:
            if re.search(pattern, r["text"]):
                usp_reviews.append({
                    "投稿者": r["name"],
                    "評価": r["rating"],
                    "該当文": r["text"][:100],
                })
                break
    
    # --- 改善点（低評価 or ネガティブキーワード）---
    improvement_reviews = []
    for r in reviews:
        neg_words_found = [w for w in NEGATIVE_WORDS if w in r["text"]]
        if neg_words_found or (r["rating"] and r["rating"] <= 3):
            improvement_reviews.append({
                "投稿者": r["name"],
                "評価": r["rating"],
                "指摘内容": r["text"][:150],
                "検出ネガワード": neg_words_found,
            })
    
    # --- リピート意向 ---
    repeat_count = 0
    repeat_reviews = []
    for r in reviews:
        for pattern in REPEAT_PATTERNS:
            if re.search(pattern, r["text"]):
                repeat_count += 1
                repeat_reviews.append(r["name"])
                break
    
    # --- 推奨意向 ---
    recommend_count = 0
    recommend_reviews = []
    for r in reviews:
        for pattern in RECOMMEND_PATTERNS:
            if re.search(pattern, r["text"]):
                recommend_count += 1
                recommend_reviews.append(r["name"])
                break
    
    total = len(reviews)
    
    return {
        "USP（独自の強み）": {
            "検出数": len(usp_reviews),
            "該当レビュー": usp_reviews[:10],
        },
        "改善点・弱み": {
            "検出数": len(improvement_reviews),
            "該当レビュー": improvement_reviews[:10],
        },
        "リピート意向": {
            "件数": repeat_count,
            "率": f"{repeat_count / max(total, 1) * 100:.1f}%",
            "投稿者": repeat_reviews[:10],
        },
        "推奨意向": {
            "件数": recommend_count,
            "率": f"{recommend_count / max(total, 1) * 100:.1f}%",
            "投稿者": recommend_reviews[:10],
        },
    }


def analyze_owner_replies(reviews: list[dict]) -> dict:
    """セクション4: オーナー返信分析"""
    total = len(reviews)
    replied = [r for r in reviews if r["has_owner_reply"]]
    not_replied = [r for r in reviews if not r["has_owner_reply"]]
    
    # 返信のテンプレ度（返信テキスト間の類似度を簡易チェック）
    reply_texts = [r["owner_reply"] for r in replied if r.get("owner_reply")]
    template_score = None
    if len(reply_texts) >= 2:
        # 共通フレーズの検出
        common_phrases = [
            "ご来店ありがとう",
            "今後とも",
            "よろしくお願い",
            "またのご来店",
            "心よりお待ちして",
            "精進して",
        ]
        phrase_counts = {phrase: sum(1 for t in reply_texts if phrase in t) for phrase in common_phrases}
        common_ratio = sum(1 for c in phrase_counts.values() if c / len(reply_texts) > 0.5) / len(common_phrases)
        template_score = f"{common_ratio * 100:.0f}%"
    
    # 低評価で未返信のレビュー（要対応）
    needs_attention = []
    for r in not_replied:
        if r["rating"] and r["rating"] <= 3:
            needs_attention.append({
                "投稿者": r["name"],
                "評価": r["rating"],
                "内容": r["text"][:100],
            })
    
    return {
        "返信率": f"{len(replied) / max(total, 1) * 100:.1f}% ({len(replied)}/{total})",
        "テンプレート利用度": template_score or "判定不能（返信数不足）",
        "頻出返信フレーズ": {p: c for p, c in phrase_counts.items() if c > 0} if reply_texts else {},
        "要対応レビュー（低評価＋未返信）": needs_attention,
    }


def generate_action_plan(rating_summary: dict, text_analysis: dict, sw_analysis: dict, reply_analysis: dict) -> dict:
    """セクション5: アクションプラン生成"""
    
    # 強み3つの抽出
    strengths = []
    top_keywords = list(text_analysis.get("頻出キーワードTOP20", {}).keys())[:5]
    
    # トピック別で最も言及が多いものを強みとする
    topics = text_analysis.get("トピック別言及数", {})
    sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)
    
    if sorted_topics:
        strengths.append(f"「{sorted_topics[0][0]}」が最も多く言及され、お客様の満足度の核")
    if len(sorted_topics) > 1:
        strengths.append(f"「{sorted_topics[1][0]}」も高い評価を獲得")
    
    usp_count = sw_analysis.get("USP（独自の強み）", {}).get("検出数", 0)
    if usp_count > 0:
        strengths.append(f"{usp_count}件のレビューで「他と比べて一番」等の最上級評価")
    
    repeat_rate = sw_analysis.get("リピート意向", {}).get("率", "0%")
    strengths.append(f"リピート意向率 {repeat_rate}")
    
    # 課題3つ
    challenges = []
    improvement = sw_analysis.get("改善点・弱み", {})
    if improvement.get("検出数", 0) > 0:
        neg_items = improvement.get("該当レビュー", [])
        neg_words_all = []
        for item in neg_items:
            neg_words_all.extend(item.get("検出ネガワード", []))
        top_neg = Counter(neg_words_all).most_common(3)
        for word, count in top_neg:
            challenges.append(f"「{word}」に関する指摘 ({count}件)")
    
    needs_att = reply_analysis.get("要対応レビュー（低評価＋未返信）", [])
    if needs_att:
        challenges.append(f"低評価＋未返信レビュー {len(needs_att)}件が要対応")
    
    if not challenges:
        challenges.append("明確な課題は少ない（良好な状態）")
    
    # 即アクション3つ
    actions = []
    if needs_att:
        actions.append(f"★優先: 未返信の低評価レビュー{len(needs_att)}件に返信")
    
    avg = rating_summary.get("平均評価", 0)
    if avg >= 4.5:
        actions.append("高評価を活かしたSNS投稿（口コミ引用画像の作成）")
    
    recommend_count = sw_analysis.get("推奨意向", {}).get("件数", 0)
    if recommend_count > 0:
        actions.append(f"「おすすめ」表現をした{recommend_count}件のレビューをGBPの引用に活用")
    
    actions.append("定期的なレビュー返信による顧客エンゲージメント強化")
    
    # SNS素材候補
    sns_quotes = []
    for r in sw_analysis.get("USP（独自の強み）", {}).get("該当レビュー", []):
        if r.get("評価", 0) and r["評価"] >= 4:
            sns_quotes.append({
                "投稿者": r["投稿者"],
                "引用文": r["該当文"],
            })
    
    # 返信テンプレ案
    reply_templates = {
        "高評価（★4-5）向け": "この度はご来店いただきありがとうございます。{キーワード}をお楽しみいただけたようで大変嬉しく思います。またのお越しを心よりお待ちしております。",
        "低評価（★1-3）向け": "この度はご来店いただきありがとうございます。{ご指摘内容}について、貴重なご意見として真摯に受け止め、改善に努めてまいります。お気づきの点がございましたら、いつでもお申し付けください。",
    }
    
    return {
        "エグゼクティブサマリー": {
            "強み": strengths[:3],
            "課題": challenges[:3],
            "即アクション": actions[:3],
        },
        "MEO改善ヒント": {
            "GBP最適化キーワード": top_keywords,
            "説明": "これらのキーワードはレビューで頻出しており、GBPの説明文やカテゴリに含めることで検索流入の向上が見込めます",
        },
        "返信テンプレート案": reply_templates,
        "SNS活用素材（引用候補）": sns_quotes[:5],
    }


# ============================================================
# Markdownレポート生成
# ============================================================

def generate_markdown_report(
    rating: dict, text_anal: dict, sw: dict, reply: dict, action: dict, meta: dict = None
) -> str:
    """分析結果をMarkdownレポートとして出力"""
    
    lines = []
    now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M")
    
    lines.append(f"# 📊 Googleマップ レビュー分析レポート")
    lines.append(f"")
    if meta:
        lines.append(f"- **対象URL**: {meta.get('source_url', '不明')}")
    lines.append(f"- **分析日時**: {now}")
    lines.append(f"- **総レビュー数**: {rating.get('総レビュー数', '不明')}")
    lines.append(f"")
    
    # エグゼクティブサマリー
    exec_summary = action.get("エグゼクティブサマリー", {})
    lines.append("---")
    lines.append("")
    lines.append("## 🎯 エグゼクティブサマリー")
    lines.append("")
    lines.append("### 💪 強み")
    for s in exec_summary.get("強み", []):
        lines.append(f"- {s}")
    lines.append("")
    lines.append("### ⚠️ 課題")
    for c in exec_summary.get("課題", []):
        lines.append(f"- {c}")
    lines.append("")
    lines.append("### 🚀 即アクション")
    for a in exec_summary.get("即アクション", []):
        lines.append(f"1. {a}")
    lines.append("")
    
    # セクション1: 評価サマリー
    lines.append("---")
    lines.append("")
    lines.append("## 1️⃣ 評価サマリー")
    lines.append("")
    lines.append(f"| 指標 | 値 |")
    lines.append(f"|------|------|")
    lines.append(f"| 平均評価 | **{rating.get('平均評価', '-')}** / 5.0 |")
    lines.append(f"| 中央値 | {rating.get('中央値', '-')} |")
    lines.append(f"| 評価あり件数 | {rating.get('評価あり件数', '-')} |")
    lines.append("")
    
    # 星分布
    lines.append("### 星分布")
    lines.append("")
    lines.append("| 星 | 件数 | 割合 |")
    lines.append("|---:|-----:|-----:|")
    dist = rating.get("星分布", {})
    dist_pct = rating.get("星分布率", {})
    for star in ["★5", "★4", "★3", "★2", "★1"]:
        count = dist.get(star, 0)
        pct = dist_pct.get(star, "0%")
        bar = "█" * count
        lines.append(f"| {star} | {count} | {pct} {bar} |")
    lines.append("")
    
    # 時期別
    period = rating.get("時期別傾向", {})
    if period:
        lines.append("### 時期別傾向")
        lines.append("")
        lines.append("| 時期 | 件数 | 平均評価 |")
        lines.append("|------|-----:|--------:|")
        for p, vals in sorted(period.items()):
            lines.append(f"| {p} | {vals['件数']} | {vals['平均']} |")
        lines.append("")
    
    # セクション2: テキスト分析
    lines.append("---")
    lines.append("")
    lines.append("## 2️⃣ テキスト分析")
    lines.append("")
    
    sentiment = text_anal.get("センチメント", {})
    s_dist = sentiment.get("分布", {})
    lines.append("### センチメント分布")
    lines.append("")
    lines.append(f"| 判定 | 件数 |")
    lines.append(f"|------|-----:|")
    for k in ["ポジティブ", "ニュートラル", "ネガティブ"]:
        emoji = {"ポジティブ": "😊", "ニュートラル": "😐", "ネガティブ": "😟"}.get(k, "")
        lines.append(f"| {emoji} {k} | {s_dist.get(k, 0)} |")
    lines.append(f"")
    lines.append(f"ポジティブ率: **{sentiment.get('ポジティブ率', '-')}**")
    lines.append("")
    
    # 頻出キーワード
    keywords = text_anal.get("頻出キーワードTOP20", {})
    if keywords:
        lines.append("### 頻出キーワード TOP20")
        lines.append("")
        lines.append("| キーワード | 出現レビュー数 |")
        lines.append("|-----------|-------------:|")
        for word, count in keywords.items():
            lines.append(f"| {word} | {count} |")
        lines.append("")
    
    # トピック分類
    topics = text_anal.get("トピック別言及数", {})
    topic_pcts = text_anal.get("トピック別言及率", {})
    if topics:
        lines.append("### トピック別言及")
        lines.append("")
        lines.append("| トピック | 件数 | 割合 |")
        lines.append("|---------|-----:|-----:|")
        for topic in sorted(topics, key=topics.get, reverse=True):
            lines.append(f"| {topic} | {topics[topic]} | {topic_pcts.get(topic, '-')} |")
        lines.append("")
    
    # 顧客像
    segments = text_anal.get("顧客像の手がかり", {})
    if segments:
        lines.append("### 顧客像の手がかり")
        lines.append("")
        for seg, info in segments.items():
            lines.append(f"- **{seg}**: {info['検出数']}件")
        lines.append("")
    
    lines.append(f"レビュー平均文字数: {text_anal.get('レビュー平均文字数', '-')} 文字")
    lines.append("")
    
    # セクション3: 強み・弱み
    lines.append("---")
    lines.append("")
    lines.append("## 3️⃣ 強み・弱み分析")
    lines.append("")
    
    usp = sw.get("USP（独自の強み）", {})
    lines.append(f"### USP（独自の強み）: {usp.get('検出数', 0)}件検出")
    lines.append("")
    for item in usp.get("該当レビュー", [])[:5]:
        lines.append(f"> 「{item['該当文']}」 — {item['投稿者']}（★{item.get('評価', '?')}）")
        lines.append("")
    
    improvement = sw.get("改善点・弱み", {})
    lines.append(f"### 改善点: {improvement.get('検出数', 0)}件検出")
    lines.append("")
    for item in improvement.get("該当レビュー", [])[:5]:
        neg_words = ", ".join(item.get("検出ネガワード", []))
        lines.append(f"- ★{item.get('評価', '?')} {item['投稿者']}: {item['指摘内容'][:80]}...")
        if neg_words:
            lines.append(f"  - 指摘キーワード: {neg_words}")
    lines.append("")
    
    repeat = sw.get("リピート意向", {})
    recommend = sw.get("推奨意向", {})
    lines.append(f"### ロイヤルティ指標")
    lines.append("")
    lines.append(f"| 指標 | 件数 | 率 |")
    lines.append(f"|------|-----:|---:|")
    lines.append(f"| リピート意向 | {repeat.get('件数', 0)} | {repeat.get('率', '-')} |")
    lines.append(f"| 推奨意向 | {recommend.get('件数', 0)} | {recommend.get('率', '-')} |")
    lines.append("")
    
    # セクション4: オーナー返信
    lines.append("---")
    lines.append("")
    lines.append("## 4️⃣ オーナー返信分析")
    lines.append("")
    lines.append(f"- **返信率**: {reply.get('返信率', '-')}")
    lines.append(f"- **テンプレート利用度**: {reply.get('テンプレート利用度', '-')}")
    lines.append("")
    
    freq_phrases = reply.get("頻出返信フレーズ", {})
    if freq_phrases:
        lines.append("### 返信で多用されるフレーズ")
        lines.append("")
        for phrase, count in sorted(freq_phrases.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"- 「{phrase}」({count}回)")
        lines.append("")
    
    needs_att = reply.get("要対応レビュー（低評価＋未返信）", [])
    if needs_att:
        lines.append("### 🚨 要対応レビュー（低評価＋未返信）")
        lines.append("")
        for item in needs_att:
            lines.append(f"- ★{item['評価']} {item['投稿者']}: {item['内容']}")
        lines.append("")
    
    # セクション5: アクションプラン
    lines.append("---")
    lines.append("")
    lines.append("## 5️⃣ アクションプラン")
    lines.append("")
    
    meo = action.get("MEO改善ヒント", {})
    lines.append("### MEO改善キーワード")
    lines.append("")
    meo_kw = meo.get("GBP最適化キーワード", [])
    if meo_kw:
        lines.append(f"GBPの説明文に活用すべきキーワード: **{', '.join(meo_kw)}**")
        lines.append("")
    
    templates = action.get("返信テンプレート案", {})
    if templates:
        lines.append("### 返信テンプレート案")
        lines.append("")
        for label, tmpl in templates.items():
            lines.append(f"**{label}:**")
            lines.append(f"```")
            lines.append(tmpl)
            lines.append(f"```")
            lines.append("")
    
    sns = action.get("SNS活用素材（引用候補）", [])
    if sns:
        lines.append("### SNS活用素材（引用候補）")
        lines.append("")
        for item in sns:
            lines.append(f"> 「{item['引用文']}」 — {item['投稿者']}")
            lines.append("")
    
    lines.append("---")
    lines.append(f"*レポート生成: {now}*")
    
    return "\n".join(lines)


# ============================================================
# メイン
# ============================================================

def main():
    parser = ArgumentParser(description="Googleマップ レビュー口コミ分析ツール")
    parser.add_argument("input", help="レビューJSONファイルパス")
    parser.add_argument("--output", "-o", default=None, help="出力ファイルパス")
    parser.add_argument("--json-output", "-j", default=None, help="JSON出力ファイルパス")
    args = parser.parse_args()
    
    # 入力読み込み
    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    meta = data.get("meta", {}) if isinstance(data, dict) else {}
    
    # 正規化
    reviews = normalize_reviews(data)
    print(f"[INFO] {len(reviews)} 件のレビューを読み込み")
    
    if not reviews:
        print("[ERROR] レビューが見つかりません")
        sys.exit(1)
    
    # 5セクション分析実行
    print("[INFO] セクション1: 評価サマリー...")
    rating_summary = analyze_rating_summary(reviews)
    
    print("[INFO] セクション2: テキスト分析...")
    text_analysis = analyze_text(reviews)
    
    print("[INFO] セクション3: 強み・弱み分析...")
    sw_analysis = analyze_strengths_weaknesses(reviews)
    
    print("[INFO] セクション4: オーナー返信分析...")
    reply_analysis = analyze_owner_replies(reviews)
    
    print("[INFO] セクション5: アクションプラン...")
    action_plan = generate_action_plan(rating_summary, text_analysis, sw_analysis, reply_analysis)
    
    # Markdownレポート生成
    report = generate_markdown_report(
        rating_summary, text_analysis, sw_analysis, reply_analysis, action_plan, meta
    )
    
    # 出力
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    md_output = args.output or f"review_analysis_{timestamp}.md"
    with open(md_output, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"[OUTPUT] Markdownレポート: {md_output}")
    
    json_output = args.json_output or f"review_analysis_{timestamp}.json"
    all_results = {
        "meta": meta,
        "rating_summary": rating_summary,
        "text_analysis": text_analysis,
        "strengths_weaknesses": sw_analysis,
        "owner_reply_analysis": reply_analysis,
        "action_plan": action_plan,
    }
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"[OUTPUT] JSONデータ: {json_output}")
    
    # サマリーを標準出力に表示
    print("\n" + "=" * 60)
    print("📊 分析サマリー")
    print("=" * 60)
    print(f"  総レビュー数: {rating_summary.get('総レビュー数', '-')}")
    print(f"  平均評価: {rating_summary.get('平均評価', '-')} / 5.0")
    exec_s = action_plan.get("エグゼクティブサマリー", {})
    print(f"  強み: {', '.join(exec_s.get('強み', [])[:2])}")
    print(f"  課題: {', '.join(exec_s.get('課題', [])[:2])}")
    print("=" * 60)
    
    return md_output


if __name__ == "__main__":
    main()
