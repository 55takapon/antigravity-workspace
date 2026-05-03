// skills-data.js — スキル一覧データ
// generate-data.ps1 で自動再生成可能

const SKILLS_DATA = [
  // ── システム・ツール系 ────────────────────────────
  {
    id: "skill-management",
    name: "スキル管理",
    folder: "skill-management",
    category: "system",
    description: "スキルの作り方・保存場所・命名規則・更新ルールを定めたメタスキル。あらゆるタスク実行前に「現在のスキル一覧」を確認し、該当スキルがあればSKILL.mdを読んでから作業を開始すること。",
    command: "/skill-management",
    lastModified: "2026-05-03T05:41:01",
    tags: ["メタ", "管理", "ルール"]
  },
  {
    id: "chat-ng-learner",
    name: "チャットNG学習",
    folder: "chat-ng-learner",
    category: "system",
    description: "チャットでの指摘や品質エラー（NG）をリアルタイムで検知し、絶対にすり抜けや再発を起こさないための最上位ルールレジストリへ強制記録させるメタスキル。",
    command: null,
    lastModified: "2026-05-01T14:46:33",
    tags: ["品質管理", "NG防止", "メタ"]
  },
  {
    id: "anticrow",
    name: "AntiCrow連携",
    folder: "anticrow",
    category: "system",
    description: "AntiCrow拡張機能の機能を活用するためのスキル。チームモード、連続オートモード、IPC通信、進捗報告、ファイル送信などの使い方を理解する。",
    command: null,
    lastModified: "2026-05-02T09:31:17",
    tags: ["Discord", "自動化", "IPC"]
  },
  {
    id: "git-backup",
    name: "Gitバックアップ",
    folder: "git-backup",
    category: "system",
    description: "GitHubへのバックアップを実行するスキル。手動で「バックアップして」と言われたとき、または作業区切りのタイミングで使用する。sync-github.ps1スクリプトを呼び出してコミット＆プッシュを行う。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["Git", "バックアップ", "GitHub"]
  },
  {
    id: "company-search",
    name: "企業検索",
    folder: "company-search",
    category: "system",
    description: "Web検索で企業情報を自動収集し、Google Sheetsに書き込む営業リスト作成ツール。3段階フォールバック検索、企業HPクロール、重複/除外フィルタリング、品質チェック必須報告機能を搭載。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["企業リスト", "営業", "自動化"]
  },
  {
    id: "company-search-quality-check",
    name: "企業リスト品質チェック",
    folder: "company-search-quality-check",
    category: "system",
    description: "企業リスト（Google Sheets）の品質を、これまで発生した全是正事例をMECEに網羅した独立チェックスキル。company-searchスキルで収集したデータの書き込み後に必ず実行する。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["品質管理", "企業リスト", "チェック"]
  },
  {
    id: "form-automation",
    name: "フォーム自動入力",
    folder: "form-automation",
    category: "system",
    description: "PlaywrightでWebフォームに自動入力するスキル。Google Sheets連携で営業メール・問い合わせフォームへの一括送信を実現。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["Playwright", "自動化", "フォーム"]
  },
  {
    id: "contact-auto",
    name: "コンタクト自動化",
    folder: "contact-auto",
    category: "system",
    description: "企業への問い合わせ・営業コンタクトを自動化するスキル。フォーム自動入力との連携でアウトリーチ業務を効率化する。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["営業", "自動化", "アウトリーチ"]
  },
  {
    id: "ops-pdca",
    name: "運用PDCA",
    folder: "ops-pdca",
    category: "system",
    description: "contact-autoの日次運用PDCAサイクル。「送信→集計→分析→パッチ→検証→SKILL反映」の一気通貫フローを定義。daily-reportのCHECK-1/CHECK-2とcontact-autoの学習エンジンを橋渡しする。",
    command: "/ops-pdca",
    lastModified: "2026-05-01T14:45:19",
    tags: ["PDCA", "運用", "自動化"]
  },
  {
    id: "idea-inbox",
    name: "アイデア受信箱",
    folder: "idea-inbox",
    category: "system",
    description: "アイデア・思いつき・メモをクリエイティブ源泉として蓄積・整理するスキル。daily-reportとは完全分離。実施前提ではなく「忘れないための置き場」として運用する。デフォルトはサイレント保存モード。",
    command: null,
    lastModified: "2026-05-02T09:49:08",
    tags: ["メモ", "アイデア", "インボックス"]
  },

  // ── レポート・日次運用系 ──────────────────────────
  {
    id: "daily-report",
    name: "デイリーレポート",
    folder: "daily-report",
    category: "report",
    description: "日次作業報告レポートを作成するスキル。ファイル名はYYMMDDdaily-report.md、保存先はdaily-reports/。STEP 0〜7を順守すること。スキルを読まずに独自フォーマットで作成することは絶対禁止。",
    command: "/daily-report",
    lastModified: "2026-05-02T21:03:02",
    tags: ["日次", "報告", "レポート"]
  },
  {
    id: "daily-report-quality-check",
    name: "デイリーレポートQC",
    folder: "daily-report-quality-check",
    category: "report",
    description: "デイリーレポート完成後に実行する品質チェックスキル。全セッション網羅・INCIDENT漏れ・クライアント名正確性・重要度順序を検証する。",
    command: "/daily-report-quality-check",
    lastModified: "2026-05-01T22:22:52",
    tags: ["品質管理", "日次", "QC"]
  },

  // ── SNS・コンテンツ系 ─────────────────────────────
  {
    id: "sns",
    name: "SNS投稿",
    folder: "sns",
    category: "content",
    description: "Instagram/Threads/Facebook/Xの投稿生成・戦略スキル。プラットフォーム別の最適化、トピックリサーチ、AI実行プロンプトまで体系化。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["SNS", "Instagram", "投稿生成"]
  },
  {
    id: "content-strategy",
    name: "コンテンツ戦略",
    folder: "content-strategy",
    category: "content",
    description: "ジェットプロデュースのブログコンテンツを中長期で計画・運用するための戦略スキル。ピラー・クラスター構造管理、編集カレンダー、KPI設計（3Tier）、季節テーマ、PDCAフロー。",
    command: "/content-strategy",
    lastModified: "2026-05-03T05:18:34",
    tags: ["SEO", "コンテンツ計画", "KPI"]
  },
  {
    id: "blog-title-research",
    name: "ブログタイトルリサーチ",
    folder: "blog-title-research",
    category: "content",
    description: "ジェットプロデュースのコラムブログ用記事タイトルをリサーチ・設計するスキル。SEO/AI検索最適化・CTR向上・競合分析・KW調査の5ステップフロー。PREP/PAS/AIDA構成に対応したタイトル案を3パターン生成。",
    command: "/blog-title-research",
    lastModified: "2026-05-03T05:17:49",
    tags: ["SEO", "タイトル", "キーワード調査"]
  },
  {
    id: "blog-writing",
    name: "ブログ執筆",
    folder: "blog-writing",
    category: "content",
    description: "ジェットプロデュースのコラムブログ記事を執筆するスキル。店舗・クリニック・士業向けSEO/AI検索最適化記事を3,000〜5,000文字で生成。コンテンツブリーフ作成→PREP/PAS/AIDA構成選択→読者目線ライティング→WordPress/SWELL整形まで一貫対応。",
    command: "/blog-writing",
    lastModified: "2026-05-03T05:45:15",
    tags: ["ブログ", "SEO", "執筆"]
  },
  {
    id: "blog-writing-qa",
    name: "ブログ品質検査",
    folder: "blog-writing-qa",
    category: "content",
    description: "ジェットプロデュースのブログ記事を、ユーザーへの報告前に品質検査するスキル。SEOキーワード配置・構成フレームワーク適合・ライティング品質・法令コンプライアンス・ブランドボイス・冒頭キャッチー度を7軸で採点し、合否と改善指示を出力。",
    command: "/blog-writing-qa",
    lastModified: "2026-05-03T05:40:35",
    tags: ["ブログ", "品質管理", "QA"]
  },

  // ── Web制作系 ────────────────────────────────────
  {
    id: "website-production",
    name: "ホームページ制作",
    folder: "website-production",
    category: "web",
    description: "WordPressとSWELLテーマを使ったホームページ制作の完全フロー。企画→デザイン→構築→公開→SEOまでの全工程チェックリストと知見を集積。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["WordPress", "SWELL", "Web制作"]
  },
  {
    id: "coconala-listing",
    name: "ココナラ出品",
    folder: "coconala-listing",
    category: "web",
    description: "ococonaラ出品文の作成・改善スキル。出品画面スクショで確認した公式仕様・Proマーケター視点での構成設計・NGパターンを定義。",
    command: "/coconala-listing",
    lastModified: "2026-05-01T14:45:19",
    tags: ["ココナラ", "出品", "コピーライティング"]
  },
  {
    id: "great-presenter",
    name: "プレゼン・講話",
    folder: "great-presenter",
    category: "web",
    description: "プロフェッショナル・スピーチ＆プレゼンテーション総合スキル。講話の企画・台本作成・レジュメ設計・演出ポイント・添削を支援する。倫理法人会モーニングセミナー40分講話にも完全対応。",
    command: "/great-presenter",
    lastModified: "2026-05-02T06:41:53",
    tags: ["プレゼン", "スピーチ", "台本"]
  },

  // ── リサーチ系 ───────────────────────────────────
  {
    id: "small-company-research",
    name: "小規模企業リサーチ",
    folder: "small-company-research",
    category: "research",
    description: "小規模企業の提案候補リストを作成するリサーチスキル。ポータルサイト・検索結果・比較記事から候補企業を収集し、公式サイトから企業情報を抽出、キーワード判定・重複管理・品質チェックを経てGoogle Sheets/CSVに出力する。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["リサーチ", "企業リスト", "営業"]
  },
  {
    id: "gbp-partner-research",
    name: "GBPパートナーリサーチ",
    folder: "gbp-partner-research",
    category: "research",
    description: "GBP/MEO運用サービスの協業パートナー候補となる業種をリサーチし、優先順位付けとキーワード設計を行うコアスキル。1000社超の集客支援実績を持つプロマーケターの視点で業種評価・キーワード設計を行い、company-searchスキルと連携して企業リスト抽出まで一気通貫で実行する。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["GBP", "パートナー", "リサーチ"]
  },

  // ── GBP基盤系 ────────────────────────────────────
  {
    id: "gbp-meo-core",
    name: "GBPコア",
    folder: "gbp-meo-core",
    category: "gbp-core",
    description: "Googleビジネスプロフィール（GBP）のMEO対策・ローカルSEO運用を、200社以上の支援実績を持つプロマーケターの視点で体系化したコアスキル。戦略立案→実行→効果測定→改善のPDCAを業種横断で実装する。",
    command: null,
    lastModified: "2026-05-01T22:43:43",
    tags: ["GBP", "MEO", "ローカルSEO"]
  },
  {
    id: "gbp-diagnostic",
    name: "GBP診断レポート",
    folder: "gbp-diagnostic",
    category: "gbp-core",
    description: "GoogleマップURLを入力するだけで、見込み顧客のGBPを5軸×5段階で自動診断し、伸びしろTOP3・推定機会損失を含む営業用レポートを生成する。オーナーが「専門家に任せたい」と思える設計。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["GBP", "診断", "営業ツール"]
  },
  {
    id: "gbp-meo-post-core",
    name: "GBP長文投稿",
    folder: "gbp-meo-post-core",
    category: "gbp-core",
    description: "Googleビジネスプロフィール（GBP）運用において、検索アルゴリズム（NLP）の関連性評価を最大化するための「本文1000文字＋固定フッター150〜200文字」型プロフェッショナル投稿ライティングスキル。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["GBP", "投稿", "ライティング"]
  },
  {
    id: "gbp-monthly-report",
    name: "GBP月次レポート",
    folder: "gbp-monthly-report",
    category: "gbp-core",
    description: "クライアント向けGBP月次パフォーマンスレポートを自動生成するスキル。Google SheetsのCSVデータを読み込み、KPI計算・競合比較・推奨アクションを含むHTML/PDFレポートをNode.jsスクリプトで一括生成。gbp-diagnostic スキルのSection 0.2 で仕様定義済み。",
    command: "node generate_monthly_report.js",
    lastModified: "2026-05-02T06:24:24",
    tags: ["GBP", "月次レポート", "自動生成", "PDF"]
  },
  {
    id: "gbp-report-quality-check",
    name: "GBPレポートQC",
    folder: "gbp-report-quality-check",
    category: "gbp-core",
    description: "GBP月次レポートのHTML/PDF生成物が正しいかを機械的に検査・検証する。生成後の品質保証として必ず実行する。",
    command: "/gbp-report-quality-check",
    lastModified: "2026-05-02T06:24:24",
    tags: ["GBP", "品質管理", "QC"]
  },

  // ── GBP投稿業種別 ────────────────────────────────
  {
    id: "gbp-meo-post-dental-occlusion",
    name: "歯科投稿（噛み合わせ）",
    folder: "gbp-meo-post-dental-occlusion",
    category: "gbp-post",
    description: "ジェットプロデュースのクライアントワーク用。月を入力すると8つの季節テーマ案を提示し、選んだ4記事を確実な医療広告ガイドライン準拠（慎重表現ルール等）のもと、1000文字規模で一括生成するハイエンドプロンプト。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["歯科", "噛み合わせ", "GBP投稿"]
  },
  {
    id: "gbp-meo-post-dental-preventive",
    name: "歯科投稿（予防）",
    folder: "gbp-meo-post-dental-preventive",
    category: "gbp-post",
    description: "ジェットプロデュースのクライアントワーク用。月を入力すると8つの季節テーマ案を提示し、選ばれた4記事を「1000文字の本文＋オーナー報告用の目的文」のセットで一括生成するプロンプト。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["歯科", "予防歯科", "GBP投稿"]
  },
  {
    id: "gbp-meo-post-jetproduce",
    name: "JP自社GBP投稿",
    folder: "gbp-meo-post-jetproduce",
    category: "gbp-post",
    description: "ジェットプロデュース様自身のGBPにおける集客・相談獲得を目的とした長文投稿作成スキル。「寄り添い型のパートナー」トーンでMEOあるある（30テーマ）の課題を提示し、ホームページからの問い合わせへ誘導する。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["GBP投稿", "自社", "集客"]
  },

  // ── GBP業種別運用 ────────────────────────────────
  {
    id: "gbp-meo-beauty",
    name: "GBP美容室・エステ",
    folder: "gbp-meo-beauty",
    category: "gbp-industry",
    description: "美容室・エステサロン・ネイルサロンに特化したGBP MEO運用スキル。ホットペッパービューティーとの棲み分け・スタイル写真の撮影戦略・スタイリスト別口コミ獲得・予約導線設計・美容師法の広告規制まで体系化。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["美容室", "エステ", "MEO"]
  },
  {
    id: "gbp-meo-bodywork",
    name: "GBP施術院（整体）",
    folder: "gbp-meo-bodywork",
    category: "gbp-industry",
    description: "施術院（整体院・整骨院・鍼灸院）に特化したGBP MEO運用スキル。整体/整骨/鍼灸のカテゴリ使い分け・資格差に基づく広告規制・施術写真の撮影テクニック・症状別キーワード戦略・あはき法対応まで体系化。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["整体", "整骨院", "MEO"]
  },
  {
    id: "gbp-meo-education",
    name: "GBP学習塾",
    folder: "gbp-meo-education",
    category: "gbp-industry",
    description: "学習塾・予備校・スクールに特化したGBP MEO運用スキル。口コミ機能制限リスク回避・保護者/生徒の二層ターゲット戦略・合格実績の訴求方法・季節講習連動施策・カテゴリ設定の落とし穴まで体系化。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["学習塾", "教育", "MEO"]
  },
  {
    id: "gbp-meo-legal",
    name: "GBP士業",
    folder: "gbp-meo-legal",
    category: "gbp-industry",
    description: "士業（税理士・司法書士フォーカス）に特化したGBP MEO運用スキル。YMYL/E-E-A-T最重要の専門家ブランディング・守秘義務と口コミの両立・専門特化キーワード戦略・法改正連動の投稿施策・高権威Schema実装まで体系化。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["士業", "税理士", "MEO"]
  },
  {
    id: "gbp-meo-medical",
    name: "GBPクリニック",
    folder: "gbp-meo-medical",
    category: "gbp-industry",
    description: "クリニック（歯科フォーカス）に特化したGBP MEO運用スキル。医療広告ガイドライン遵守・YMYL/E-E-A-T対応・患者口コミ獲得・診療科目別カテゴリ設定・Schema実装まで、医療機関固有のノウハウを体系化。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["クリニック", "歯科", "MEO"]
  },
  {
    id: "gbp-meo-real-estate",
    name: "GBP不動産",
    folder: "gbp-meo-real-estate",
    category: "gbp-industry",
    description: "不動産会社（賃貸仲介・売買仲介・管理会社）に特化したGBP MEO運用スキル。物件検索行動への対応・エリア別キーワード戦略・来店予約導線・宅建業法の広告規制・ポータルサイトとの棲み分けまで体系化。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["不動産", "賃貸", "MEO"]
  },
  {
    id: "gbp-meo-restaurant",
    name: "GBP飲食店（居酒屋）",
    folder: "gbp-meo-restaurant",
    category: "gbp-industry",
    description: "飲食店（居酒屋フォーカス）に特化したGBP MEO運用スキル。メニュー戦略・予約連携・口コミ獲得・季節施策・GBP新機能活用まで、飲食業界固有のノウハウを体系化。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["飲食", "居酒屋", "MEO"]
  },
  {
    id: "gbp-meo-retail",
    name: "GBP小売・物販",
    folder: "gbp-meo-retail",
    category: "gbp-industry",
    description: "小売店・物販店舗（アパレル・雑貨・花屋・書店・食料品店等）に特化したGBP MEO運用スキル。商品写真戦略・EC連携・Googleショッピング連動・在庫情報活用・季節商戦連動施策まで体系化。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["小売", "物販", "MEO"]
  },
  {
    id: "gbp-meo-service",
    name: "GBP工務店・リフォーム",
    folder: "gbp-meo-service",
    category: "gbp-industry",
    description: "工務店・リフォーム会社・住宅関連サービスに特化したGBP MEO運用スキル。施工事例の効果的な見せ方・エリア戦略・建設業法の広告規制・見積り相談への導線設計・ビフォーアフターの活用方法まで体系化。",
    command: null,
    lastModified: "2026-05-01T14:45:19",
    tags: ["工務店", "リフォーム", "MEO"]
  },
];

// カテゴリ定義
const CATEGORIES = [
  { id: "all",          label: "すべて",         icon: "⚡", color: "#a78bfa" },
  { id: "system",       label: "システム・ツール", icon: "🛠️", color: "#60a5fa" },
  { id: "report",       label: "レポート・日次",  icon: "📋", color: "#34d399" },
  { id: "content",      label: "SNS・コンテンツ", icon: "📱", color: "#f472b6" },
  { id: "web",          label: "Web制作・その他", icon: "🌐", color: "#fb923c" },
  { id: "research",     label: "リサーチ",        icon: "🔍", color: "#fbbf24" },
  { id: "gbp-core",     label: "GBP基盤",         icon: "📊", color: "#4ade80" },
  { id: "gbp-post",     label: "GBP投稿業種別",   icon: "✍️", color: "#a78bfa" },
  { id: "gbp-industry", label: "GBP業種別運用",   icon: "🏪", color: "#38bdf8" },
];
