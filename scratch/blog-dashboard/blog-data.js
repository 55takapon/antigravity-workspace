const CATEGORIES = [
  {id:'all',label:'すべて',icon:'📋',color:'#94a3b8'},
  {id:'A',label:'GBP・MEO対策',icon:'📍',color:'#22c55e'},
  {id:'B',label:'SEO・AI検索',icon:'🔍',color:'#3b82f6'},
  {id:'C',label:'SNS集客',icon:'📱',color:'#f472b6'},
  {id:'D',label:'ホームページ活用',icon:'🖥️',color:'#f59e0b'},
  {id:'E',label:'集客戦略・マーケ思考',icon:'🧠',color:'#a78bfa'},
  {id:'F',label:'成功事例',icon:'🏆',color:'#ef4444'},
];

const ARTICLES = [
  // ── A: GBP運用・MEO対策 ──
  {id:'A-01',cat:'A',title:'Googleビジネスプロフィールの始め方｜最初にやるべき5つの設定',kw:'Googleビジネスプロフィール 始め方 設定',type:'PREP',status:'done',file:'A-01_gbp-setup-guide.md',pillar:false,desc:'GBP登録後の初期設定5項目（ビジネス名・住所・電話番号・営業時間・説明文）を手順付きで解説。'},
  {id:'A-02',cat:'A',title:'MEO対策とは？SEOとの違いを地域で選ばれる店舗の視点で解説',kw:'MEO対策 とは SEOとの違い',type:'PREP',status:'done',file:'A-02_meo-vs-seo.md',pillar:false,desc:'MEOとSEOの違いを店舗オーナー向けにわかりやすく解説。フィルター書き換え型の冒頭テクニック適用。'},
  {id:'A-03',cat:'A',title:'Googleマップ上位表示の共通点5つ｜今日からできるMEO改善',kw:'Googleマップ 上位表示',type:'PREP',status:'done',file:'A-03_googlemap-top-display.md',pillar:false,desc:'上位表示される店舗の共通点を5つに整理し、すぐ実践できるMEO改善策を提示。'},
  {id:'A-04',cat:'A',title:'Googleマップの口コミ返信で差がつく｜返信テンプレート付き',kw:'口コミ 返信 書き方 テンプレート',type:'PAS',status:'done',file:'A-04_review-reply-template.md',pillar:false,desc:'口コミ返信の3ステップ基本型＋シーン別テンプレート（良い/改善/星のみ）＋NG例。'},
  {id:'A-05',cat:'A',title:'Googleビジネスプロフィールの投稿機能｜集客につながる使い方',kw:'GBP 投稿 使い方 集客',type:'PREP',status:'done',file:'A-05_gbp-post-guide.md',pillar:false,desc:'投稿の種類3つ（最新情報/特典/イベント）＋反応が取れる5つのコツ＋投稿手順。'},
  {id:'A-06',cat:'A',title:'MEO対策の費用相場と自分でやる方法｜業者に頼む前に読む記事',kw:'MEO対策 費用 相場 自分で',type:'PAS',status:'done',file:'A-06_meo-cost-guide.md',pillar:false,desc:'費用体系3パターン（月額固定/成果報酬/コンサル）＋自分でやれること＋悪質業者の見分け方。'},
  {id:'A-07',cat:'A',title:'Googleマップに写真を載せるコツ｜閲覧数が増える撮り方5選',kw:'Googleマップ 写真 載せ方',type:'PREP',status:'done',file:'A-07_googlemap-photo-tips.md',pillar:false,desc:'載せるべき5カテゴリ（外観/内装/商品/スタッフ/アクセス）＋スマホ撮影5テクニック。'},
  {id:'A-08',cat:'A',title:'Googleビジネスプロフィール完全攻略ガイド',kw:'Googleビジネスプロフィール 攻略',type:'PREP',status:'done',file:'A-08_gbp-complete-guide.md',pillar:true,desc:'【ピラー記事】A-01〜A-07全記事への内部リンクを集約したGBP運用の全体像ガイド。'},

  // ── B: SEO・AI検索対策 ──
  {id:'B-01',cat:'B',title:'店舗ホームページのSEO対策｜最初にやるべき3つのこと',kw:'店舗 ホームページ SEO対策',type:'PREP',status:'done',file:'B-01_store-seo-basics.md',pillar:false,desc:'誰に何をどこで書く＋タイトルタグ見直し＋ブログで入口を増やす。'},
  {id:'B-02',cat:'B',title:'検索順位を上げるブログの書き方｜店舗オーナー向けSEOライティング',kw:'ブログ 書き方 SEO 検索順位',type:'PREP',status:'done',file:'B-02_seo-writing-guide.md',pillar:false,desc:'5ステップ（KW選定→タイトル→結論から→見出し→CTA）で検索に強いブログを書く方法。'},
  {id:'B-03',cat:'B',title:'ローカルSEOとは？地域のお客さんに見つけてもらう方法',kw:'ローカルSEO とは 地域集客',type:'PREP',status:'done',file:'B-03_local-seo-guide.md',pillar:false,desc:'マップパック＋通常検索の両面戦略。関連性・距離・知名度の3要素と対策5選。'},
  {id:'B-04',cat:'B',title:'AI検索時代の店舗集客｜ChatGPTに紹介されるお店の条件',kw:'AI検索 店舗 集客 ChatGPT',type:'PAS',status:'done',file:'B-04_ai-search-store.md',pillar:false,desc:'AIに紹介される5条件（口コミ/FAQ/結論先出し/マップ情報/専門性）＋今すぐできる3対策。'},
  {id:'B-05',cat:'B',title:'SEO対策を自分でやるための完全チェックリスト',kw:'SEO対策 自分で チェックリスト',type:'PREP',status:'done',file:'B-05_seo-checklist.md',pillar:false,desc:'基本設定→マップ連携→ブログ運用→外部対策→効果確認の5段階チェックリスト。'},
  {id:'B-06',cat:'B',title:'検索順位が下がったときに確認すべき5つのチェックポイント',kw:'検索順位 下がった 原因',type:'PAS',status:'done',file:'B-06_ranking-drop-checklist.md',pillar:false,desc:'アルゴリズム更新/技術トラブル/内容変更/競合台頭/マップ問題の5チェック。'},
  {id:'B-07',cat:'B',title:'店舗のためのSEO入門｜検索から集客する全体像を解説',kw:'店舗 SEO 入門 検索対策',type:'PREP',status:'done',file:'B-07_seo-complete-guide.md',pillar:true,desc:'【ピラー記事】B-01〜B-06全記事リンク集約。HP設定→ブログ→ローカルSEO→AI検索の4ステップ。'},

  // ── C: SNS集客 ──
  {id:'C-01',cat:'C',title:'店舗のInstagram集客｜フォロワーよりも大切な3つのこと',kw:'店舗 Instagram 集客',type:'PAS',status:'done',file:'C-01_instagram-store-guide.md',pillar:false,desc:'プロフィール整備＋役立つ情報発信＋ストーリーズで人柄を見せる。'},
  {id:'C-02',cat:'C',title:'LINE公式アカウントで店舗集客｜友だちを来店につなげる方法',kw:'LINE公式アカウント 店舗 集客',type:'PREP',status:'done',file:'C-02_line-official-guide.md',pillar:false,desc:'LINE公式の役割＝リピート促進。友だち獲得→配信コツ3つ→自動応答＆リッチメニュー。'},
  {id:'C-03',cat:'C',title:'店舗のリール活用術｜15秒動画で新規のお客さんに届ける方法',kw:'Instagram リール 店舗 活用',type:'PREP',status:'done',file:'C-03_instagram-reels-guide.md',pillar:false,desc:'リールがフォロワー外に届く仕組み＋ネタ5選＋スマホ撮影4ステップ。'},
  {id:'C-04',cat:'C',title:'SNSとホームページの連携術｜店舗集客の導線設計ガイド',kw:'SNS ホームページ 連携 店舗',type:'PREP',status:'done',file:'C-04_sns-hp-integration.md',pillar:false,desc:'Instagram→HP→LINE→マップの導線5ポイント＋やりがちなミス3つ。'},
  {id:'C-05',cat:'C',title:'口コミを自然に増やす方法｜お客さんに喜んで書いてもらうコツ',kw:'口コミ 増やす 方法',type:'PAS',status:'done',file:'C-05_get-more-reviews.md',pillar:false,desc:'QRコード/サンキューカード/LINE翌日お願い/ベストタイミング/書き方ヒントの5方法。'},
  {id:'C-06',cat:'C',title:'SNS投稿のネタ切れを解消する｜店舗向け投稿アイデア30選',kw:'SNS 投稿 ネタ 店舗',type:'PREP',status:'done',file:'C-06_sns-content-ideas.md',pillar:false,desc:'6カテゴリ×5アイデア＝30個。裏側/役立つ情報/お客さんの声/人柄/季節/マップ投稿。'},
  {id:'C-07',cat:'C',title:'SNS×店舗集客の最強導線設計｜Instagram・LINE完全ガイド',kw:'SNS 店舗集客 導線設計',type:'PREP',status:'done',file:'C-07_sns-store-complete-guide.md',pillar:true,desc:'【ピラー記事】C-01〜C-06全記事リンク集約。発見→つながる→来店→口コミの4ステップ。'},

  // ── D: ホームページ活用（未着手） ──
  {id:'D-01',cat:'D',title:'集客できるホームページの条件｜作っただけでは意味がない理由',kw:'ホームページ 集客 条件',type:'PAS',status:'done',file:'D-01_hp-collection-conditions.md',pillar:false,desc:'HPを作って放置している店舗オーナー向け。集客するHPに必要な5つの条件。'},
  {id:'D-02',cat:'D',title:'店舗ホームページに必要なページ構成｜最低限の5ページとは',kw:'ホームページ ページ構成 店舗',type:'PREP',status:'done',file:'D-02_hp-page-structure.md',pillar:false,desc:'トップ/サービス/アクセス/ブログ/問い合わせの5ページ設計と各ページの役割。'},
  {id:'D-03',cat:'D',title:'問い合わせが増えるフォームの作り方｜店舗オーナー向け設計ガイド',kw:'問い合わせフォーム 作り方 店舗',type:'PREP',status:'done',file:'D-03_contact-form-design.md',pillar:false,desc:'入力3〜5項目に絞る・ボタン文言・安心感の挿入・LINE窓口追加。フォーム離脱を防ぐ5つのコツ。'},
  {id:'D-04',cat:'D',title:'ホームページのアクセス解析入門｜Googleアナリティクスの見方',kw:'ホームページ アクセス解析 初心者',type:'PREP',status:'done',file:'D-04_analytics-beginner-guide.md',pillar:false,desc:'GA4の基本3指標（ユーザー数/流入元/人気ページ）＋Search Consoleとの使い分けを解説。'},
  {id:'D-05',cat:'D',title:'集客できるホームページ完全ガイド｜作り方から改善まで',kw:'ホームページ 集客 ガイド',type:'PREP',status:'done',file:'D-05_hp-complete-guide.md',pillar:true,desc:'【ピラー記事】D-01〜D-04全記事リンク集約。HP活用の全体像。'},

  // ── E: 集客戦略・マーケ思考 ──
  {id:'E-01',cat:'E',title:'小さな店舗の集客はどこから始めるべき？優先順位の決め方',kw:'店舗 集客 何から始める',type:'PAS',status:'done',file:'E-01_store-marketing-priority.md',pillar:false,desc:'マップ→HP→ブログ→SNSの正しい優先順位と業種別の調整方法。'},
  {id:'E-02',cat:'E',title:'広告費をかけずに集客する5つの方法｜小さなお店の無料集客戦略',kw:'広告費 かけない 集客 方法',type:'PREP',status:'done',file:'E-02_free-marketing-methods.md',pillar:false,desc:'GBP/ブログ/口コミ/LINE/紹介の5つの無料集客チャネルと段階的組み合わせ方。'},
  {id:'E-03',cat:'E',title:'リピーターを増やす仕組みの作り方｜新規集客より大切なこと',kw:'リピーター 増やす 仕組み',type:'PAS',status:'done',file:'E-03_repeat-customer-system.md',pillar:false,desc:'来店翌日御礼フォロー＋定期配信＋顧客カルテの3つのリピート仕組み。'},
  {id:'E-04',cat:'E',title:'店舗集客を「仕組み化」する方法｜忙しいオーナーのための自動化ガイド',kw:'店舗 集客 仕組み化 自動化',type:'PREP',status:'done',file:'E-04_marketing-automation-guide.md',pillar:false,desc:'予約オンライン化/ステップ配信/口コミ依頼自動化/まとめコンテンツ作りの4施策。'},
  {id:'E-05',cat:'E',title:'小さな店舗の集客プロデュース入門｜戦略・仕組み・継続の全体像',kw:'店舗 集客 戦略 入門',type:'PREP',status:'done',file:'E-05_store-marketing-complete-guide.md',pillar:true,desc:'【ピラー記事】E-01〜E-04全記事リンク集約。集客戦略の全体像とロードマップ。'},

  // ── F: 成功事例 ──
  {id:'F-01',cat:'F',title:'閉業表示のマップが2ヶ月で復活｜関西・士業事務所のMEO対策事例',kw:'GBP 集客改善 事例 士業',type:'AIDA',status:'done',file:'F-01_case-study-legal-office-meo.md',pillar:false,desc:'閉業表示修正→設定最適化→定期投稿。2ヶ月でルート検索2.3倍・サイト閲覧3.5倍。'},
  {id:'F-02',cat:'F',title:'検索表示ゼロから43回へ｜託児所のGBP対策4ヶ月で閲覧2.8倍の事例',kw:'GBP 集客改善 事例 保育 託児所',type:'AIDA',status:'done',file:'F-02_case-study-nursery-gbp.md',pillar:false,desc:'放置状態のGBPを情報充実・写真追加・週1投稿で改善。4ヶ月で閲覧2.8倍・検索表示0→43回。'},
  {id:'F-03',cat:'F',title:'低評価口コミ対策で予約が埋まった｜関西・歯科クリニックのMEO対策事例',kw:'GBP 集客改善 事例 歯科 クリニック',type:'AIDA',status:'done',file:'F-03_case-study-dental-meo.md',pillar:false,desc:'低評価口コミ返信＋口コミ積み上げ＋地域KW対策。3ヶ月・前年同月比で電話発信1.4倍・検索表示1.4倍。'},
  {id:'F-04',cat:'F',title:'MEO対策の成功事例まとめ｜実績データで見る集客改善の共通点',kw:'MEO対策 成功事例 実績',type:'PREP',status:'done',file:'F-04_meo-case-study-summary.md',pillar:true,desc:'【ピラー記事】F-01〜F-03全事例リンク集約。3事例の共通成功パターンと応用方法。'},
];
