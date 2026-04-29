/**
 * crawler.js - 企業HPクローラー
 *
 * 各企業のWebサイトにアクセスし、以下を抽出:
 *   - 企業名（titleタグ・OGP・会社概要ページから厳密に抽出）
 *   - 従業員数（会社概要ページ等から正規表現で抽出）
 *   - 代表者名（フルネーム必須、取得不能時は「ご担当者」）
 *   - 設定キーワードの含有チェック
 *   - 問い合わせフォームURLの検出
 */

const { randomDelay } = require('./searcher');

// ═══════════════════════════════════════════
//  正規表現パターン定義
// ═══════════════════════════════════════════

// 全角数字→半角変換
function normalizeDigits(text) {
    return text.replace(/[０-９]/g, c => String.fromCharCode(c.charCodeAt(0) - 0xFEE0));
}

// 従業員数を抽出する正規表現パターン (カンマ区切り対応)
// ★ テーブル構造では <th>従業員</th><td>20名</td> が innerText で「従業員\n20名」になるため
//    改行（\n）をセパレータとして許容するパターンを追加
const EMPLOYEE_PATTERNS = [
    // テーブル型: ラベル\n値（改行区切り）
    /従業員[数]?\n[約]?([\d,]+)[名人]/,
    /社員[数]?\n[約]?([\d,]+)[名人]/,
    /スタッフ[数]?\n([\d,]+)[名人]/,
    // 通常型: ラベル：値（同一行）
    /従業員[数]?[：:\s]*[約]?([\d,]+)[名人]/,
    /社員[数]?[：:\s]*[約]?([\d,]+)[名人]/,
    /スタッフ[数]?[：:\s]*[約]?([\d,]+)[名人]/,
    /メンバー[：:\s]*[約]?([\d,]+)[名人]/,
    /([\d,]+)[名人]\s*[（(].*?[正社員|パート|アルバイト]/,
    /人[員数]?[：:\s]*[約]?([\d,]+)/,
    /([\d,]+)\s*(?:名|人)\s*(?:在籍|所属)/,
    /正社員[：:\s]*([\d,]+)[名人]/,
    /従業[員]?[：:\s]*約?([\d,]+)/,
    /社員[：:\s]*([\d,]+)[名人]?\s*[（(]/,
];

// 資本金を抽出する正規表現パターン
// ★ テーブル型: <th>資本金</th><td>900万円</td> → innerTextで「資本金\n900万円」
const CAPITAL_PATTERNS = [
    // テーブル型（改行区切り）
    /資本金\n([\d,]+\s*(?:万円|億円|円|万|億))/,
    // 通常型（同一行）
    /資本金[：:\s]*([\d,.]+[万億]?円?[^<{\n]*)/,
    /([\d,.]+[万億]円)\s*（.*?資本準備金/,
];

// 代表者名を抽出する正規表現パターン（フルネーム＝姓+名でスペース付きを優先）
const REPRESENTATIVE_PATTERNS = [
    // スペース付きフルネーム優先（最も信頼性が高い）
    /代表取締役[社長]*[：:\s\u3000]+([一-龯ぁ-んァ-ヶ]{1,5}[\s\u3000][一-龯ぁ-んァ-ヶ]{1,6})/,
    /代表者[名]?[：:\s\u3000]+([一-龯ぁ-んァ-ヶ]{1,5}[\s\u3000][一-龯ぁ-んァ-ヶ]{1,6})/,
    /CEO[：:\s\u3000]+([一-龯ぁ-んァ-ヶ]{1,5}[\s\u3000][一-龯ぁ-んァ-ヶ]{1,6})/,
    /代表[：:\s\u3000]+([一-龯ぁ-んァ-ヶ]{1,5}[\s\u3000][一-龯ぁ-んァ-ヶ]{1,6})/,
    // v1.2.0 追加: 「社長」ラベルパターン
    /社長[：:\s\u3000]+([一-龯]{1,5}[\s\u3000][一-龯]{1,6})/,
    // v1.2.0 追加: 「代表取締役　姓名」（コロンなし直結）
    /代表\s*取締\s*役[\s\u3000]*[社長]*[\s\u3000]*([一-龯]{1,5}[\s\u3000][一-龯]{1,6})/,
    // スペースなしだが3文字以上のフルネーム
    /代表取締役[社長]*[：:\s\u3000]+([一-龯ぁ-んァ-ヶ]{3,5})(?![\u4e00-\u9faf\u3041-\u3093\u30a1-\u30f6])/,
    /代表者[名]?[：:\s\u3000]+([一-龯ぁ-んァ-ヶ]{3,5})(?![\u4e00-\u9faf\u3041-\u3093\u30a1-\u30f6])/,
    /CEO[：:\s\u3000]+([一-龯ぁ-んァ-ヶ]{3,5})(?![\u4e00-\u9faf\u3041-\u3093\u30a1-\u30f6])/,
    /代表[：:\s\u3000]+([一-龯ぁ-んァ-ヶ]{3,5})(?![\u4e00-\u9faf\u3041-\u3093\u30a1-\u30f6])/,
    // v1.2.0 追加
    /社長[：:\s\u3000]+([一-龯]{3,5})(?![\u4e00-\u9faf\u3041-\u3093\u30a1-\u30f6])/,
];

// 会社概要ページへのリンクパターン
const COMPANY_PAGE_PATTERNS = [
    /company/i, /about/i, /corporate/i,
    /会社概要/, /会社案内/, /会社情報/,
    /企業情報/, /企業概要/,
    /プロフィール/, /profile/i,
];

// お問い合わせフォームへのリンクパターン
const CONTACT_PAGE_PATTERNS = [
    /contact/i, /inquiry/i, /form/i,
    /お問い?合わせ/, /お問合せ/, /お問い合せ/,
    /ご相談/, /ご依頼/, /見積/,
    /資料請求/, /entry/i, /無料相談/,
];

// ═══════════════════════════════════════════
//  まとめ記事判定
// ═══════════════════════════════════════════

const ARTICLE_URL_PATTERNS = [
    /\/column\//i, /\/blog\//i, /\/news\//i,
    /\/article\//i, /\/media\//i, /\/post\//i,
    /\/posts\//i, /\/archives\//i, /\/entry\//i,
    /\/topics\//i, /\/guide\//i, /\/ranking\//i,
    /\/comparison\//i, /\/recommend\//i,
    /\/\d{4}\/\d{2}\//,
];

const ARTICLE_TITLE_PATTERNS = [
    /\d+選/, /おすすめ/, /比較/, /ランキング/,
    /まとめ/, /一覧/, /紹介/, /選び方/,
    /【/, /】/,
];

function isArticlePage(url, title = '') {
    try {
        const u = new URL(url);
        const pathIsArticle = ARTICLE_URL_PATTERNS.some(p => p.test(u.pathname));
        const titleIsArticle = ARTICLE_TITLE_PATTERNS.some(p => p.test(title));
        return pathIsArticle || titleIsArticle;
    } catch {
        return false;
    }
}

// ═══════════════════════════════════════════
//  記事リンク収集時の除外ドメイン（徹底）
// ═══════════════════════════════════════════

const ARTICLE_LINK_EXCLUDE_DOMAINS = [
    // SNS
    'google', 'twitter', 'facebook', 'instagram', 'youtube',
    'tiktok', 'linkedin', 'pinterest', 'amazon', 'rakuten',
    'wikipedia', 'yahoo', 'hubspot', 'salesforce', 'marketo',
    'getpocket', 'feedly', 'slack', 'notion', 'medium',
    'apple.com', 'play.google', 'line.me', 'note.com',
    'ameblo', 'hatenablog', 'livedoor', 'qiita', 'zenn',
    'baseconnect', 'aumo.jp',
    // メッセージ・通知サービス
    'lmes.jp', 's.lmes.jp',
    // フォームサービス
    'hsforms.com', 'typeform.com', 'formrun.com',
    // 写真素材
    'pixta.jp', 'shutterstock', 'adobestock',
    // レジ・POS
    'smaregi.jp', 'airpay',
    // レンタル・アフィリエイト
    'rentracks.jp', 'a8.net', 'valuecommerce',
    // 比較サイト・メディア（自社ではない）
    'dime.jp', 'ferret-plus', 'liskul.com',
    // 幹事系サービス（同一グループ）
    '-kanji.com', 'web-kanji',
    // その他ツール系
    'chatwork.com', 'zendesk.com', 'intercom.com',
    // 求人（追加）
    'job-gear.net', 'job-list.net', 'helloworkplus.com',
    'kyujinbu.com', 'career-on.jp',
    // 法人情報DB
    'houjin.jp', 'houjin-lookup.info',
    // ナビ・地図
    'navitime.co.jp',
    // クラウドファンディング
    'camp-fire.jp',
    // パチンコ
    'p-world.co.jp',
    // ニュース・大手メディア
    'mainichi.jp', 'nikkei.com', 'chunichi.co.jp', 'asahi.com',
    'yomiuri.co.jp', 'sankei.com', 'nhk.or.jp', 'prtimes.jp',
    // 行政
    'mhlw.go.jp', 'soumu.go.jp',
    // 金融情報
    'smbcnikko.co.jp',
    // その他
    'bestcalendar.jp', 'dreamnews.jp',
    // ★ 事例記事に登場しやすい大手・有名サービス
    // EC・ショッピング
    'base.ec', 'makeshop', 'futureshop', 'shopify',
    // 求人・転職大手
    'rikunabi', 'mynavi', 'doda.jp', 'en-japan', 'wantedly',
    'type.jp', 'bizreach', 'green-japan',
    // クラウド・SaaS
    'microsoft.com', 'office.com', 'cybozu',
    'moneyforward', 'freee.co.jp', 'kintone',
    // 大手メーカー・企業（事例として登場する）
    'toyota.co.jp', 'honda.co.jp', 'sony.com', 'fujitsu.com',
    'ntt.com', 'ntt-west.co.jp', 'ntt-east.co.jp', 'docomo.ne.jp',
    'softbank.co.jp', 'panasonic.com', 'sharp.co.jp',
    'hitachi.co.jp', 'toshiba.co.jp', 'mitsubishi.co.jp',
    'dentsu.co.jp', 'hakuhodo.co.jp',
    // フリマ・掲示板系
    'jmty.jp', 'mercari.com', 'jimoty.jp',
    // スポーツ関連
    'npb.or.jp', 'jleague.jp',
    // 比較・レビューサイト
    'boxil.jp', 'itreview.jp', 'imitsu.jp', 'cocolobo.jp',
    // 無料ホームページサービス
    'jimdo.com', 'wix.com', 'fc2.com', 'seesaa.net',
];

// 記事本文領域セレクタ
const CONTENT_SELECTORS = [
    'article', '.entry-content', '.post-content', '.article-body',
    '.content-area', '.main-content', '[role="main"]', 'main',
    '.single-content', '.blog-content', '.post-body',
    '.the-content', '.article-content', '#content',
];

// 記事内で除外するDOM領域セレクタ
const CONTENT_EXCLUDE_SELECTORS = [
    'nav', 'header', 'footer', 'aside',
    '.sidebar', '.widget', '.widget-area',
    '.ad', '.advertisement', '.banner', '.sponsor',
    '.related-posts', '.recommend', '.popular', '.ranking-widget',
    '.breadcrumb', '.pagination', '.comment', '.comments',
    '.author-box', '.share', '.social', '.sns',
    '.cta', '.cv-area', '.contact-banner',
];

// 1記事あたりの最大抽出企業数
const MAX_LINKS_PER_ARTICLE = 20;

// ═══════════════════════════════════════════
//  企業名バリデーション
// ═══════════════════════════════════════════

/**
 * 企業名として妥当かどうかを判定
 * @param {string} name
 * @returns {boolean}
 */
function isValidCompanyName(name) {
    if (!name || name.length < 2 || name.length > 40) return false;

    // 明らかに企業名でないパターン
    const INVALID_PATTERNS = [
        /https?:\/\//,                // URL（社名のどこにあってもNG）
        /^@/,                          // SNSハンドル
        /^[\w.-]+\.(com|jp|co\.jp|net|org)$/, // ドメイン名
        /^ー/,                         // v1.2.0: 先頭が長音符（切れた企業名）
        /SIGN IN/i, /LOG ?IN/i, /SIGN UP/i,
        /Form Builder/i, /Online Form/i,
        /Cookie/i, /Privacy/i, /Terms/i,
        /お知らせ/, /ニュース/, /ブログ/,
        /とのパートナー/, /のお知ら/,
        /当社が/, /薬会社が/, /弊社は/,
        /は様々な/, /を運営/, /サービスを/,
        /なら【/, /導入の依頼/, /相談・比較/,
        /するなら/, /獲得するなら/,
        /企業名[^\u3000\s]/, // 「企業名」が先頭についているが後にスペースがない
        /認知・来店/, /両軸で/,
        /ログインはこちら/,
        /formerly/i,
        /ブックマーク/, /Bookmark/i,
        /hatena/i, /はてな/,
        // v1.1.0 追加: 文章片・フレーズの除外
        /様を/, /を掲載/, /を紹介/, /をご紹介/,
        /との連携/, /との提携/, /とのパー/,
        /により$/, /について/, /における/,
        /しました$/, /します$/, /しています$/, /されました$/,
        /できる$/, /できます$/,
        /求人会社/, /求人$/, /採用$/, /転職$/,
        /会社が[^名]/, /会社は[^こ]/, /会社を[^設]/,
        /^求人/, /^採用/, /^転職/,
        /ランキング/, /おすすめ/, /選$/, /[0-9０-９]+選/,
        /一覧$/, /まとめ$/, /比較$/,
        /口コミ/, /評判/, /レビュー/,
        // v1.1.1 追加: 実データから検出した追加パターン
        /Copyright/i,
        /なので$/, /ため$/, /ですが$/, /けど$/, /から$/, /まで$/,
        /では$/, /には$/,
        /さま\d/, /様\d/,
        /使い方/, /ガイド$/, /の会社情報/, /の企業情報/,
        /採用サイト/, /人材派遣/, /派遣サービス/,
        /プレスリリース/, /ニュースリリース/,
        /の公式/, /公式ホーム/,
        /^Google/, /^Amazon/, /^Microsoft/,
        /\.\.\.$/, /\.\.\./, /…$/,
        // v2.0.0 追加: 住所・会社概要テキスト混入防止
        /所在地/, /代表取締役/, /設立年月日/, /創立\d/,
        /事業内容/, /本社所在/, /業務案内/, /業務内容/,
        /愛知県|東京都|大阪府|名古屋市|横浜市|福岡市|千代田区|渋谷区|港区|新宿区/,
        /導入事例/, /公式サイト|電子版/,
        // v2.1.0 追加: 「株式会社様」等整式後に敢語を含むもの
        /(?:株式会社|合同会社|有限会社)[様さん]$/,
        // v2.1.0 追加: ニュース・まとめサイト系
        /速報$/, /まとめ$/, /ニュース$/, /情報サイト/,
        /2ch/, /5ch/, /掘り下げ/, /アンテナ/,
        // ★ v2.2.0 追加: 誤抽出パターン絶対再発防止
        // 「移動株式会社」「提供株式会社」等: 先頭が動詞・名詞で法人格がその後
        /^(?:移動|提供|利用|導入|運営|設立|採用|転職|求人|比較|一覧|まとめ|活用|管理|販売|制作|開発|運用|構築|実施|実行|対応|支援|参加|登録|申込|掲載|紹介|予約)(?:株式会社|合同会社|有限会社)/,
        // 「株式会社様」: 末尾が敬称で終わる（cleanCompanyNameで処理済みのはずが漏れた場合）
        /^株式会社[様さん御]$/,
        /^(?:株式会社|合同会社|有限会社)$/, // 法人格だけの場合
        // 大学・学術機関・公共機関
        /大学|学校法人|独立行政法人|国立研究開発法人|社会福祉法人|宗教法人/,
        // 広告代理店大手
        /^(?:博報堂|電通|ADK|オグルヴィ|マッキャン|dentsu)/,
        // 野球団・スポーツ球団
        /(?:野球団|フットボールクラブ|バスケットボール|サッカークラブ|Jリーグ|球団)/,
        // 出版・媒体社・調査会社大手
        /(?:出版$|新聞社$|放送局$|メディア社$|雑誌社$|ガイド社$)/,
        /^(?:オリコン|日経|東洋経済|ダイヤモンド|プレジデント|日刊|産経)/,
        // 就職・採用大手グループ
        /(?:マイナビ|リクルート|パーソル|テンプ|ランスタッド)/,
        // 不動産・住宅大手
        /^(?:エイブル|アパマン|ミニミニ|ピタットハウス|センチュリー21)/,
        // ★ v2.8.0 追加: 敬称付き企業名の完全排除
        // 末尾が「様」「さん」「御」など敬称で終わる（cleanCompanyName未適用の生データ対策）
        /[様さん御]$/,
        // ★ 名古屋シートのゴミ対応
        /の広告代理店/, // 例: 「名古屋の広告代理店」
        /^(?:Group|Community|ホールディングス|カンパニー|システム|サービス|ソリューション|プロジェクト)(?:株式会社|合同会社|有限会社)$/i, // 例: Group株式会社
        /^(?:運営会社|管理会社|関連会社|子会社|親会社)/, // 例: 運営会社栄公園振興株式会社
        // ★ 見出し・ラベルがそのまま抽出されるのを防止
        /^(?:企業情報|会社名|会社情報|企業名|法人名|商号|名称|社名|名称（商号）|代表者名|代表取締役|社長|経歴|プロフィール|会社概要|店舗名|屋号)$/,
    ];

    if (INVALID_PATTERNS.some(p => p.test(name))) return false;

    // 助詞チェック: しきい値を6に引き下げ（短い文章片も検出）
    if (name.length > 6 && /[はがをでにとも].{3,}/.test(name)) return false;

    // 末尾が助詞で終わる場合も無効（例: 「株式会社MGPは」「福田執筆の」）
    if (/[はがをでにとものへ]$/.test(name)) return false;

    // ひらがな3文字以上で終わる場合は文章片の可能性大（企業名はカタカナ/漢字/英字で終わる）
    if (name.length > 8 && /[ぁ-ん]{3,}$/.test(name)) return false;

    // ★ v2.3.0 & v2.4.0: ページタイトル混入パターン追加
    // ★ v2.6.0 ゴミテキスト対策追加
    if (/https/i.test(name)) return false;            // URLの混入
    if (/ニュー速/.test(name)) return false;           // まとめサイトの混入
    if (/様Webサイ/.test(name)) return false;          // 抽出失敗ゴミ
    if (/^株式会社.{1}$/.test(name)) return false;    // 「株式会社調」などの1文字ゴミ
    if (/医療法人社団/.test(name)) return false;       // クリニックそのもの
    if (/^株式会社創業/.test(name)) return false;      // 「株式会社創業2017年」等の抽出失敗ゴミ
    // ★ v2.9.0: 役職語が後続する誤抽出パターン（「株式会社会長」「株式会社社長」等）
    if (/^(?:株式会社|合同会社|有限会社)(?:会長|社長|取締役|理事長|専務|常務|監査役|相談役|顧問|部長|課長|支店長|所長|院長)/.test(name)) return false;
    // ★ v2.9.0: ポータルサイト・まとめサイト系の名前パターン
    if (/^(?:株式会社|合同会社|有限会社)(?:一覧|ランキング|比較|まとめ|検索|情報|ナビ|ガイド|サイト|ポータル|マップ|マガジン|メディア|コラム)/.test(name)) return false;
    // ★ v2.8.0: 英字1-2文字のみ+法人格（「C株式会社」「TH株式会社」等）を排除
    if (/^[A-Za-z]{1,2}(?:株式会社|合同会社|有限会社)$/.test(name)) return false;
    if (/^(?:株式会社|合同会社|有限会社)[A-Za-z]{1,2}$/.test(name)) return false;
    if (/^(?:[A-Za-z]|.)(?:株式会社|合同会社|有限会社)$/.test(name)) return false; // 「C株式会社」等の1文字ゴミ
    if (/^(?:株式会社|合同会社|有限会社)(?:[A-Za-z]|.)$/.test(name)) return false; // 「株式会社C」等の1文字ゴミ
    if (/^(?:株式会社|合同会社|有限会社)設立/.test(name)) return false; // 「株式会社設立」等

    // 「トップ |」「アクセス |」「会社概要」で始まるものはページタイトル
    if (/^(?:トップ|アクセス|会社概要|ホーム|HOME|Top)s*[|｜]/.test(name)) return false;
    // 「〇〇ソリューションカンパニー|株式会社」のような社内部署名パターン
    if (/カンパニーs*[|｜]/.test(name)) return false;
    // URLショートナー・Webサービス名
    if (/^URLs/i.test(name) || /Shortener/i.test(name)) return false;
    // クラウドファンディング・プラットフォーム系
    if (/^クラウドファンディング/.test(name) || /^Readyfor/i.test(name)) return false;
    // 「コーポレートサイト」そのものが企業名
    if (/コーポレートサイト/.test(name)) return false;
    // 「建築構造計算ソフトウェアの〇〇株式会社」のような冗長なページタイトル
    if (/ソフトウェアの[^s]/.test(name)) return false;
    // 「〇〇 - 〇〇本店」のような書店・施設名
    if (/ブックセンター/.test(name)) return false;

    // 法人格の直後に助詞が来る場合は文章片（例: 「株式会社との」「株式会社様を」）
    if (/(?:株式会社|合同会社|有限会社)[様さん]?[はがをでにともの]/.test(name)) return false;

    // === 法人格（株式会社など）が含まれない場合の厳格化 ===
    if (!/(?:株式会社|合同会社|有限会社|法人|機構|組合)/.test(name)) {
        if (/の/.test(name)) return false; // 例: 「名古屋のWeb制作」「福田執筆の」
        if (/なら/.test(name)) return false; // 例: 「Seo対策ならseoパートナーズ」
        if (/^[ァ-ヶー]+$/.test(name)) return false; // 例: 「インフルエンサー」などのカタカナ単語
        if (name.length > 20) return false; // 長すぎるものはキャッチコピーの可能性大
        // 人名がそのまま企業名として誤抽出されるのを防ぐ（例: 長林順之亮、石原新也）
        if (isJapanesePersonName(name)) return false;

        // ★ v2.9.1 追加: 文章片・人名ノイズの完全排除（絶対に抽出させない）
        if (/(?:執筆|監修|著|編集|作成)/.test(name)) return false; // 記事作成者情報
        if (/^[一-龯][\s　]+[一-龯]{2,}/.test(name)) return false; // 「長　伊藤」等の役職切れ端+人名
        if (/^[一-龯ぁ-ん]{1,3}[\s　]+[一-龯ぁ-ん]{1,4}$/.test(name)) return false; // 姓と名がスペースで区切られている人名パターン
        if (/^[a-zA-Z0-9\s.,-]+$/.test(name)) return false; // 英数字と記号だけの文字列
    }

    return true;
}

/**
 * 企業名をクリーニング
 */
function cleanCompanyName(raw) {
    if (!raw) return '';
    let name = raw.trim();

    // ★ v2.2.0: 先頭の不要語を除去（「移動（株式会社〇〇）」等への対策）
    // 「〇〇（株式会社△△）」のように括弧内に法人格がある場合、括弧内を本体として抽出
    const innerCorp = name.match(/[（(]([^）)]*(?:株式会社|合同会社|有限会社)[^）)]*)[）)]/);
    if (innerCorp) { name = innerCorp[1].trim(); }
    // パイプ・ダッシュ以降を除去
    name = name.replace(/\s*[|｜]\s*.+$/, '');
    name = name.replace(/\s*[-–—]\s*.{5,}$/, '');
    // 括弧を除去
    name = name.replace(/（.*?）$/, '');
    name = name.replace(/\(.*?\)$/, '');
    // ノイズワードを除去
    name = name.replace(/のホームページ$/, '');
    name = name.replace(/の公式サイト$/, '');
    name = name.replace(/公式サイト$/, '');
    name = name.replace(/ホームページ$/, '');
    name = name.replace(/オフィシャルサイト$/, '');
    name = name.replace(/様$/, '');
    name = name.replace(/さん$/, '');
    name = name.replace(/とのパー.*$/, '');
    name = name.replace(/ログイン.*$/, '');
    name = name.replace(/当社が$/, '');
    // 先頭の「企業名」除去
    name = name.replace(/^企業名\s*/, '');
    // 末尾の「株式会社」「合同会社」以降の余分なテキスト除去
    const corpMatch = name.match(/((?:株式会社|合同会社|有限会社)[^\s]{1,20}|[^\s]{1,20}(?:株式会社|合同会社|有限会社))/);
    if (corpMatch && name.length > corpMatch[0].length + 5) {
        // 「株式会社〇〇」部分だけを抽出
        name = corpMatch[0];
    }

    return name.trim();
}

/**
 * 上場企業判定キーワード
 */
const LISTED_KEYWORDS = [
    '東証プライム', '東証スタンダード', '東証グロース',
    '東証一部', '東証二部', 'JASDAQ', 'マザーズ',
    '上場企業', '証券コード', '株式上場', 'IPO',
    '東京証券取引所', '名古屋証券取引所', '札幌証券取引所', '福岡証券取引所',
];

/**
 * テキストから上場企業かどうかを判定する
 */
function isListedCorporation(text) {
    if (!text) return false;
    return LISTED_KEYWORDS.some(kw => text.includes(kw));
}

// ═══════════════════════════════════════════
//  代表者名バリデーション v1.2.1
//  設計思想: 「人名でないものを除外」ではなく「人名であるかを判定」
//
//  日本人の人名の特徴:
//    - 漢字のみで構成される（姓1-4文字 + 名1-4文字）
//    - 合計3〜8文字
//    - スペースで姓と名が区切られていることが多い
//    - カタカナ語（=外来語=職種・資格・サービス名）を含まない
//    - ひらがなのみの名前もごく稀にある（まこと、さくら等）
// ═══════════════════════════════════════════

/**
 * 文字列が日本人の人名パターンに合致するか判定する
 * @param {string} name - 検証する文字列
 * @returns {boolean} 人名として妥当ならtrue
 */
function isJapanesePersonName(name) {
    if (!name) return false;

    // === 絶対NGチェック（これがあった時点で人名ではない） ===
    // URL・英数字・記号を含む
    if (/[a-zA-Z0-9@#.\/:]/.test(name)) return false;
    // カタカナ2文字以上の連続を含む（＝外来語＝職種/資格/サービス名）
    if (/[ァ-ヶー]{2,}/.test(name)) return false;
    // 「士」「師」で終わる（資格名: 〇〇士、〇〇師）
    if (/[士師]$/.test(name)) return false;
    // 「長」「員」「役」「官」で終わる（役職名）
    if (/[長員役官]$/.test(name) && name.length > 2) return false;
    // 「者」で終わる（代表者、担当者）
    if (/者$/.test(name)) return false;
    // 助詞・接続詞を含む（人名に助詞は絶対に入らない）
    if (/から|より|まで|への|との|について|により|として|における|にて|皆様|様へ|です|ます/.test(name)) return false;

    // === 正のパターンマッチ ===
    // パターンA: 漢字姓(1-4) + スペース + 漢字名(1-4) = 最も信頼性高
    if (/^[一-龯]{1,4}[\s\u3000][一-龯]{1,4}$/.test(name)) return true;

    // パターンB: 漢字のみ3-8文字（スペースなしフルネーム）
    if (/^[一-龯]{3,8}$/.test(name)) return true;

    // パターンC: ひらがな姓名（まれだが実在）
    if (/^[ぁ-ん]{2,4}[\s\u3000][ぁ-ん]{2,4}$/.test(name)) return true;

    // パターンD: 漢字+ひらがな混合（例: さくら、まこと）
    if (/^[一-龯ぁ-ん]{3,8}$/.test(name) && /[一-龯]/.test(name)) return true;

    // パターンE: 漢字姓 + ひらがな名 or その逆
    if (/^[一-龯]{1,4}[\s\u3000][ぁ-ん]{1,4}$/.test(name)) return true;
    if (/^[ぁ-ん]{1,4}[\s\u3000][一-龯]{1,4}$/.test(name)) return true;

    // どれにも合致しない → 人名ではない
    return false;
}

function cleanRepresentativeName(raw) {
    if (!raw) return '';
    let name = raw.trim();
    // 記号・数字を除去
    name = name.replace(/[0-9０-９\-－()（）「」【】『』\[\]]/g, '').trim();
    // 株式会社等が含まれたら除外
    if (/株式会社|合同会社|有限会社|Co\.|Inc\./.test(name)) return '';

    // === 名前の後ろに付くゴミを除去（実データに基づく） ===
    // 肩書き・役職（名前の後ろに付くパターン）
    name = name.replace(/取締役.*$/, '').trim();
    name = name.replace(/執行役員.*$/, '').trim();
    name = name.replace(/社長.*$/, '').trim();
    name = name.replace(/会長.*$/, '').trim();
    name = name.replace(/理事.*$/, '').trim();
    name = name.replace(/監査役.*$/, '').trim();
    name = name.replace(/常務.*$/, '').trim();
    name = name.replace(/専務.*$/, '').trim();
    // 文章・ラベル（名前の後ろに続く本文）
    name = name.replace(/から.*$/, '').trim();
    name = name.replace(/より.*$/, '').trim();
    name = name.replace(/連絡先.*$/, '').trim(); // 「空閑涼太連絡先」対策
    name = name.replace(/本社移転.*$/, '').trim(); // 「松浦法子本社移転」対策
    name = name.replace(/事業内容.*$/, '').trim();
    name = name.replace(/設立.*$/, '').trim();
    name = name.replace(/資本金.*$/, '').trim();
    name = name.replace(/所在地.*$/, '').trim();
    name = name.replace(/従業員.*$/, '').trim();
    name = name.replace(/についてf.*$/, '').trim();
    // 敬称
    name = name.replace(/氏$/, '').trim();
    name = name.replace(/さん$/, '').trim();
    name = name.replace(/様$/, '').trim();
    // 括弧以降
    name = name.replace(/\s*（.*$/, '').trim();
    name = name.replace(/\s*\(.*$/, '').trim();
    
    // 代表取締役社長などの「社長」が消えた後に残る「長　佐藤丈亮」対策
    name = name.replace(/^長[\s　]+/, '').trim();

    // ★ 「名前＋一般名詞」連結ノイズの除去
    // 例: 「中山陽平中小企業」→「中山陽平」、「田中太郎経営者」→「田中太郎」
    const NOUN_NOISE = [
        '中小企業', '大手企業', '中小企業者', '経営者', '事業者', '事業主',
        '経営', '情報', '支援', '業務', '採用', '転職',
        '企業様', '会社様', '担当者', '顧客', '法人',
    ];
    for (const noise of NOUN_NOISE) {
        if (name.endsWith(noise) && name.length > noise.length) {
            name = name.slice(0, name.length - noise.length).trim();
        }
    }

    // ★ 9文字以上で漢字のみの場合、先頭から人名部分を抽出
    // 例: 「中山陽平中小企業向け」が残った場合
    if (name.length >= 9 && /^[一-龯]{4,}$/.test(name)) {
        for (let len = 4; len >= 3; len--) {
            const candidate = name.substring(0, len);
            if (isJapanesePersonName(candidate)) { name = candidate; break; }
        }
    }

    // === 核心: 人名かどうかを正で判定 ===
    if (!isJapanesePersonName(name)) return '';

    return name;
}


// ═══════════════════════════════════════════
//  記事内リンク収集
// ═══════════════════════════════════════════

async function extractCompanyLinksFromArticle(page, articleUrl, keywords, region) {
    const companies = [];
    try {
        await page.goto(articleUrl, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await randomDelay(1500, 3000);

        const articleDomain = new URL(articleUrl).hostname;
        const excludeList = ARTICLE_LINK_EXCLUDE_DOMAINS;

        // 本文領域限定 + コンテキスト付きリンク抽出
        const links = await page.evaluate(({ artDomain, excludeKws, contentSels, excludeSels }) => {
            // Step1: 本文領域を特定
            let contentRoot = null;
            for (const sel of contentSels) {
                const el = document.querySelector(sel);
                if (el) { contentRoot = el; break; }
            }
            // 本文領域が見つからない場合はbodyから（ただしナビ等を除外）
            if (!contentRoot) contentRoot = document.body;

            // Step2: 除外領域のリンクを特定するためのSet
            const excludedLinks = new Set();
            for (const sel of excludeSels) {
                contentRoot.querySelectorAll(sel).forEach(el => {
                    el.querySelectorAll('a[href]').forEach(a => excludedLinks.add(a));
                });
            }
            // ページ全体のheader/footer/nav/asideからのリンクも除外
            document.querySelectorAll('body > header, body > footer, body > nav, body > aside, #header, #footer, #sidebar').forEach(el => {
                el.querySelectorAll('a[href]').forEach(a => excludedLinks.add(a));
            });

            // Step3: 本文領域内のリンクを取得（除外領域を除く）
            return Array.from(contentRoot.querySelectorAll('a[href]'))
                .filter(a => !excludedLinks.has(a))
                .map(a => {
                    // リンクの前後コンテキストを取得（親要素のテキスト）
                    const parent = a.closest('li, p, div, td, section');
                    const context = (parent?.textContent || '').trim().substring(0, 300);
                    return {
                        href: a.href,
                        text: (a.textContent || '').trim().substring(0, 200),
                        context: context,
                    };
                })
                .filter(l => {
                    try {
                        const u = new URL(l.href);
                        const host = u.hostname.toLowerCase();
                        if (host === artDomain) return false;
                        if (excludeKws.some(kw => host.includes(kw))) return false;
                        // .co.jp または .jp のみ
                        return host.endsWith('.co.jp') || host.endsWith('.jp');
                    } catch { return false; }
                });
        }, {
            artDomain: articleDomain,
            excludeKws: excludeList,
            contentSels: CONTENT_SELECTORS,
            excludeSels: CONTENT_EXCLUDE_SELECTORS,
        });

        // 重複排除してトップページURLに正規化（上限あり）
        const seen = new Set();
        for (const link of links) {
            if (companies.length >= MAX_LINKS_PER_ARTICLE) {
                console.log(`  [記事解析] 上限${MAX_LINKS_PER_ARTICLE}件に達したため打ち切り`);
                break;
            }
            try {
                const u = new URL(link.href);
                if (seen.has(u.hostname)) continue;
                seen.add(u.hostname);
                const rootUrl = `${u.protocol}//${u.hostname}/`;
                companies.push({
                    url: rootUrl,
                    title: '',
                    source: 'article_link',
                    snippet: '',
                });
            } catch { continue; }
        }

        console.log(`  [記事解析] ${articleUrl} から ${companies.length}件の企業リンクを抽出（本文領域限定）`);
    } catch (err) {
        console.log(`  [記事解析エラー] ${err.message.substring(0, 80)}`);
    }
    return companies;
}

// ═══════════════════════════════════════════
//  企業名抽出（解析データに基づく根本修正版）
// ═══════════════════════════════════════════

// 企業名候補から除外すべき文章片パターン
const CORP_NAME_NOISE_PATTERNS = [
    /様を/, /様の/, /様が/, /様は/,
    /との/, /とは/, /とも/,
    /により/, /について/, /における/,
    /しました/, /します/, /しています/, /されました/,
    /できる/, /できます/,
    /を掲載/, /を紹介/, /をご紹介/,
    /を設立/, /を運営/,
    /が提供/, /が運営/,
    /は様々/, /の一覧/, /のお知/,
];

/**
 * テキストから「株式会社〇〇」「〇〇株式会社」等の
 * 法人名部分だけを正規表現で切り出す共通関数
 */
function extractCorpName(text) {
    if (!text) return '';
    // パターン1: 「株式会社〇〇」（前置型）
    // ※マッチ長12に制限（20だと代表者名・住所まで巻き込む）
    // ※後続に「代表」「所在」「設立」等が続く場合はマッチを打ち切り
    // negative lookahead: 役職語（会長・社長・取締役等）や住所・事業内容ラベルが続く場合は除外
    const pre = text.match(/(株式会社|合同会社|有限会社)([A-Za-zＡ-Ｚａ-ｚ0-9０-９一-龯ァ-ヶー・＆&\-.]{1,12})(?![代表所在設立事業資本従業創立本社会社取社長会長理専常監])/);
    // パターン2: 「〇〇株式会社」（後置型）  ※直後がスペース/区切り/文末の場合のみ
    const post = text.match(/([一-龯ァ-ヶA-Za-zＡ-Ｚａ-ｚ0-9０-９ー・＆&\-.]{1,15})(株式会社|合同会社|有限会社)(?=[\s|｜／\/（(\n]|$)/);

    let candidates = [];
    if (pre) {
        let name = pre[1] + pre[2];
        // 前置型: 末尾の括弧以降を除去
        name = name.replace(/[（(].*$/, '').trim();
        // 助詞・動詞パターンが含まれていたら除外
        if (!CORP_NAME_NOISE_PATTERNS.some(p => p.test(name))) {
            if (name.length >= 5 && name.length <= 30) candidates.push(name);
        }
    }
    if (post) {
        let name = post[1] + post[2];
        // 後置型: 先頭に助詞「なら」「は」「が」「を」「で」があれば除去して再マッチ
        name = name.replace(/^.*(?:なら|では|には|ては|から|する|した|って)/g, '').trim();
        if (!name.match(/^(株式会社|合同会社|有限会社)/)) {
            const reMatch = name.match(/([一-龯ァ-ヶA-Za-zＡ-Ｚ0-9０-９ー・]{1,15})(株式会社|合同会社|有限会社)/);
            if (reMatch) name = reMatch[1] + reMatch[2];
        }
        if (!CORP_NAME_NOISE_PATTERNS.some(p => p.test(name))) {
            if (name.length >= 5 && name.length <= 30) candidates.push(name);
        }
    }

    // 候補が複数ある場合は短い方を優先（冗長なのを避ける）
    candidates.sort((a, b) => a.length - b.length);
    for (const c of candidates) {
        const cleaned = cleanCompanyName(c);
        if (cleaned && cleaned.length >= 3 && isValidCompanyName(cleaned)) return cleaned;
    }
    return '';
}

/**
 * 会社名ラベル（tableMatch）専用の抽出関数
 * フリガナ（英数字直後のカタカナ連続）を除去して企業名を取得
 * 例: "株式会社WEBGRAMウェブグラム" → "株式会社WEBGRAM"
 */
function extractCorpFromLabel(labelText) {
    if (!labelText) return '';
    // まず通常のextractCorpNameを試行
    let corp = extractCorpName(labelText);
    if (!corp) return '';
    // 英数字直後にカタカナが4文字以上続いていたらフリガナとして除去
    const defurigana = corp.replace(/([A-Za-zＡ-Ｚ0-9０-９])[ァ-ヶー]{4,}$/, '$1');
    if (defurigana.length >= 5 && isValidCompanyName(defurigana)) return defurigana;
    return corp;
}

/**
 * ページ情報を多段階で解析して企業名を取得
 * 優先順位:
 *   1. 会社概要ページのtitle → 「会社概要 | 株式会社〇〇」形式で最もクリーン
 *   2. 本文の会社名/商号ラベル
 *   3. OGP og:site_name から法人名切り出し
 *   4. メインページ title から法人名切り出し
 *   5. 本文全体からフォールバック
 */
async function extractCompanyName(page, fullText, aboutTitle) {
    try {
        // Step 1: 会社概要ページのtitle
        if (aboutTitle) {
            const corp = extractCorpName(aboutTitle);
            if (corp) return corp;
        }

        // Step 2: 本文の会社名/商号ラベル（フリガナ対応）
        const tableMatch = fullText.match(/(?:会社名|商号|法人名)[：:／\s\u3000]*([^\n]{3,40})/);
        if (tableMatch) {
            const corp = extractCorpFromLabel(tableMatch[1]);
            if (corp) return corp;
        }

        // Step 3: OGP og:site_name
        const ogSiteName = await page.evaluate(() => {
            const el = document.querySelector('meta[property="og:site_name"]');
            return el?.getAttribute('content') || '';
        });
        if (ogSiteName) {
            const corp = extractCorpName(ogSiteName);
            if (corp) return corp;
        }

        // Step 4: メインページ title
        const titleTag = await page.evaluate(() => document.title || '');
        if (titleTag) {
            const corp = extractCorpName(titleTag);
            if (corp) return corp;
        }

        // Step 5: 本文先頭5000文字からフォールバック
        const corp = extractCorpName(fullText.substring(0, 5000));
        if (corp) return corp;

    } catch { }

    return '';
}

// ═══════════════════════════════════════════
//  テーブル型データ専用パーサー（th/td構造対応）
// ═══════════════════════════════════════════

/**
 * ページ内の <table> 要素から th-td ペアを辞書形式で抽出する
 * 例: <tr><th>資本金</th><td>900万円</td></tr>
 *  → { '資本金': '900万円', '従業員': '20名', ... }
 *
 * innerText では th と td の間に改行が挟まれてしまうため
 * DOM を直接解析してキーと値を対応付ける。
 */
async function extractTableData(page) {
    try {
        return await page.evaluate(() => {
            const result = {};
            // th/td パターン（横並び）
            document.querySelectorAll('table tr').forEach(tr => {
                const th = tr.querySelector('th');
                const td = tr.querySelector('td');
                if (th && td) {
                    const key = (th.innerText || th.textContent || '').trim().replace(/\s+/g, '');
                    const val = (td.innerText || td.textContent || '').trim().replace(/\s+/g, ' ');
                    if (key && val) result[key] = val;
                }
            });
            // dl/dt/dd パターン
            document.querySelectorAll('dl').forEach(dl => {
                const dts = dl.querySelectorAll('dt');
                const dds = dl.querySelectorAll('dd');
                dts.forEach((dt, i) => {
                    if (dds[i]) {
                        const key = (dt.innerText || dt.textContent || '').trim().replace(/\s+/g, '');
                        const val = (dds[i].innerText || dds[i].textContent || '').trim().replace(/\s+/g, ' ');
                        if (key && val) result[key] = val;
                    }
                });
            });
            return result;
        });
    } catch {
        return {};
    }
}

/**
 * テーブルデータから従業員数を抽出する
 */
function parseEmployeeFromTable(tableData) {
    const KEYS = ['従業員数', '従業員', '社員数', '社員', 'スタッフ数', 'スタッフ', '人員', '役職員数', '職員数'];
    for (const key of KEYS) {
        if (tableData[key]) {
            const val = normalizeDigits(tableData[key]);
            const m = val.match(/([\d,]+)/);
            if (m) return { count: parseInt(m[1].replace(/,/g, ''), 10), raw: tableData[key] };
        }
    }
    return null;
}

/**
 * テーブルデータから資本金を抽出する
 */
function parseCapitalFromTable(tableData) {
    const KEYS = ['資本金', '資本金額', '払込資本金'];
    for (const key of KEYS) {
        if (tableData[key]) {
            const val = tableData[key].trim();
            const m = val.match(/^([\d,]+\s*(?:万円|億円|円|万|億))/);
            if (m) return m[1].trim();
            // 円なし純数字（6桁以上）
            const numOnly = val.match(/^([\d,]+)/);
            if (numOnly && numOnly[1].replace(/,/g, '').length >= 6) return numOnly[1] + '円';
        }
    }
    return null;
}

// ═══════════════════════════════════════════
//  メインクロール関数
// ═══════════════════════════════════════════

async function crawlCompanyWebsite(page, url, config) {
    const speed = config.speed || {};
    const hpKeywords = config.filters?.hp_check_keywords || [];
    const result = {
        url: url,
        companyName: '',
        employeeCount: null,
        employeeCountRaw: '',
        capitalRaw: '',
        representative: 'ご担当者',  // デフォルト
        contactFormUrl: '',
        companyPageUrl: '',
        keywordHits: [],
        keywordHitFlag: false,
        error: null,
    };

    try {
        // メインページにアクセス
        console.log(`  [クロール] ${url}`);
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await randomDelay(speed.page_wait_min || 2000, speed.page_wait_max || 5000);

        let fullText = await page.evaluate(() => document.body?.innerText || '');

        // リンク一覧を取得
        const links = await page.evaluate(() => {
            return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                href: a.href,
                text: (a.textContent || '').trim().substring(0, 100),
            }));
        });

        // 問い合わせフォームURLを検出
        for (const link of links) {
            if (CONTACT_PAGE_PATTERNS.some(p => p.test(link.href) || p.test(link.text))) {
                if (link.href && link.href.startsWith('http') && !link.href.match(/\.(pdf|doc|docx|zip)$/i)) {
                    result.contactFormUrl = link.href;
                    break;
                }
            }
        }

        // 会社概要ページURLを検出
        let companyPageUrl = '';
        for (const link of links) {
            if (COMPANY_PAGE_PATTERNS.some(p => p.test(link.href) || p.test(link.text))) {
                companyPageUrl = link.href;
                result.companyPageUrl = link.href;
                break;
            }
        }

        // 会社概要ページがあればクロールして情報追加
        let aboutTitle = '';
        if (companyPageUrl && companyPageUrl !== url) {
            try {
                console.log(`  [クロール] 会社概要: ${companyPageUrl}`);
                await page.goto(companyPageUrl, { waitUntil: 'domcontentloaded', timeout: 20000 });
                await randomDelay(speed.page_wait_min || 2000, speed.page_wait_max || 5000);
                aboutTitle = await page.evaluate(() => document.title || '');
                const companyText = await page.evaluate(() => document.body?.innerText || '');
                fullText += '\n' + companyText;

                // もしメインページでフォームが見つかっていなければ、会社概要ページでも探す
                if (!result.contactFormUrl) {
                    const aboutLinks = await page.evaluate(() => Array.from(document.querySelectorAll('a[href]')).map(a => ({ href: a.href, text: (a.textContent || '').trim().substring(0, 100) })));
                    for (const link of aboutLinks) {
                        if (CONTACT_PAGE_PATTERNS.some(p => p.test(link.href) || p.test(link.text))) {
                            if (link.href && link.href.startsWith('http') && !link.href.match(/\.(pdf|doc|docx|zip)$/i)) {
                                result.contactFormUrl = link.href;
                                console.log(`  [フォームURL再検出] ${result.contactFormUrl}`);
                                break;
                            }
                        }
                    }
                }
            } catch (err) {
                console.log(`  [クロール] 会社概要アクセス失敗: ${err.message.substring(0, 50)}`);
            }
        }

        // ── 企業名を抽出 ──
        try {
            // 会社概要ページにいる場合はそのまま、メインページの場合も戻らない
            result.companyName = await extractCompanyName(page, fullText, aboutTitle);
            if (result.companyName) {
                console.log(`  [企業名] ${result.companyName}`);
            } else {
                console.log(`  [企業名] 取得不可`);
            }
        } catch { }

        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        // ★ DOM テーブルパーサー優先（th/td・dl/dt/dd構造に対応）
        //    innerText ではラベルと値の間に改行が入るため
        //    正規表現マッチが失敗するケースをここで吸収する
        // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        const tableData = await extractTableData(page);

        // 従業員数: テーブルパーサー → 正規表現フォールバック
        const tableEmployee = parseEmployeeFromTable(tableData);
        if (tableEmployee) {
            result.employeeCount = tableEmployee.count;
            result.employeeCountRaw = tableEmployee.raw;
            console.log(`  [従業員数] ${result.employeeCount}名 [テーブル抽出] (${result.employeeCountRaw})`);
        } else {
            // フォールバック: 全角数字→半角変換済みテキストで正規表現マッチ
            const normalizedText = normalizeDigits(fullText);
            for (const pattern of EMPLOYEE_PATTERNS) {
                const match = normalizedText.match(pattern);
                if (match) {
                    result.employeeCount = parseInt(match[1].replace(/,/g, ''), 10);
                    const idx = normalizedText.indexOf(match[0]);
                    result.employeeCountRaw = normalizedText.substring(Math.max(0, idx - 10), idx + match[0].length + 10).trim();
                    console.log(`  [従業員数] ${result.employeeCount}名 [正規表現] (${result.employeeCountRaw})`);
                    break;
                }
            }
        }

        // 資本金: テーブルパーサー → 正規表現フォールバック
        const tableCapital = parseCapitalFromTable(tableData);
        if (tableCapital) {
            result.capitalRaw = tableCapital;
            console.log(`  [資本金] ${result.capitalRaw} [テーブル抽出]`);
        } else {
            // フォールバック: 正規表現マッチ
            for (const pattern of CAPITAL_PATTERNS) {
                const match = fullText.match(pattern);
                if (match) {
                    let raw = match[1].trim();
                    const cleaned = raw.match(/^([\d,]+\s*(?:万円|億円|円|万|億))/);
                    if (cleaned) {
                        result.capitalRaw = cleaned[1].trim();
                    } else {
                        const numOnly = raw.match(/^([\d,]+)/);
                        if (numOnly && numOnly[1].replace(/,/g, '').length >= 6) {
                            result.capitalRaw = numOnly[1] + '円';
                        }
                    }
                    if (result.capitalRaw) {
                        console.log(`  [資本金] ${result.capitalRaw} [正規表現]`);
                    }
                    break;
                }
            }
        }

        // 代表者名を抽出（フルネーム必須）
        for (const pattern of REPRESENTATIVE_PATTERNS) {
            const match = fullText.match(pattern);
            if (match) {
                const cleaned = cleanRepresentativeName(match[1]);
                if (cleaned) {
                    result.representative = cleaned;
                    console.log(`  [代表者] ${result.representative}`);
                    break;
                }
            }
        }
        if (result.representative === 'ご担当者') {
            console.log(`  [代表者] ご担当者（フルネーム未検出）`);
        }

        // HP内キーワードチェック
        for (const keyword of hpKeywords) {
            if (fullText.includes(keyword)) {
                result.keywordHits.push(keyword);
            }
        }
        result.keywordHitFlag = result.keywordHits.length > 0;
        if (result.keywordHits.length > 0) {
            console.log(`  [キーワードHIT] ${result.keywordHits.join(', ')}`);
        } else {
            console.log(`  [キーワードHIT] なし`);
        }

        // 上場企業チェック（v2.0.0: 有効化）
        result.isListed = isListedCorporation(fullText);
        if (result.isListed) {
            console.log(`  [上場企業] 検出`);
        }

        if (result.contactFormUrl) {
            console.log(`  [フォームURL] ${result.contactFormUrl}`);
        } else {
            console.log(`  [フォームURL] 未検出`);
        }

    } catch (err) {
        result.error = err.message.substring(0, 100);
        console.log(`  [クロールエラー] ${result.error}`);
    }

    return result;
}

function employeeFilter(count, max) {
    if (count === null) return true;
    return count <= max;
}

// ═══════════════════════════════════════════
//  NG業種除外ゲート (v2.0.0)
// ═══════════════════════════════════════════

const NG_INDUSTRY_KEYWORDS = [
    // 金融・保険
    '保険', '銀行', '証券', '信用金庫', '信託', 'アセットマネジメント', 'ファイナンス', 'キャピタル',
    // 不動産
    '不動産', '賃貸', '土地', '分譲', '仲介', 'マンション', 'プロパティ',
    // 製造・メーカー・重工
    '製造', '工業', '製作所', '化学', 'プラスチック', '鋼機', '電機', '重工', '造船', '精工',
    // 運輸・物流
    '鉄道', '空港', '航空', '運輸', '倉庫', '物流', '交通', '海運', '陸運', '通運',
    // エネルギー・インフラ（今回強化）
    '電力', 'ガス', '水道', '発電', '送電', '原燃', '原子力', 'エナジー', 'エネルギー', 'エネシス', 'パイプライン', '送配電', '石油', '燃料', '資源', '鉱業',
    // プラント・大規模開発
    'プラント', '都市開発', '地域開発',
    // メディア・放送
    'テレビ', 'ＴＶ', 'FM', 'ＦＭ', 'ラジオ', '放送', '新聞', '出版',
    // 飲食・食品・農畜産
    '食品', '味噌', 'しょうゆ', '醸造', 'ういろう', '製菓', '製パン', '水産', '農産', '畜産', '飼料', '肥料', 'ペットフード', '養鶏', '養豚',
    // 小売（非Web）
    '眼鏡', '腕時計', '楽器', '家具', 'ホームセンター', '百貨店', 'スーパーマーケット',
    // 医療・薬品関連
    '病院', 'クリニック', '医院', '薬局', '薬品', '製薬', 'ドラッグストア',
    // 建設
    '建設', '工務店', 'ハウスメーカー', 'ゼネコン', '土木', '建材',
    // 自動車
    '自動車', 'モーター', 'モータース',
    // 施設・レジャー
    'シネマ', '映画', '地下街', '展示場', 'ホテル', '旅館', 'リゾート', 'ゴルフ',
    // 旅行
    '旅行', 'ツアー', 'ツーリスト',
    // 葬儀
    '葬儀', '葬祭', 'セレモニー',
    // 公的・非営利・教育
    '大学', '専門学校', '財団', '組合', '商工会議所', '協議会', '機構', '公社', '事業団', '連合会', '生協', '生コン',
    // ★ v2.2.0 追加: 絶対再発防止
    // スポーツ・球団
    '野球団', '球団', 'フットボール', 'バスケットボール', 'サッカークラブ',
    // 出版・媒体
    'ガイド社', '出版', '新聞社', '放送局', '雑誌社',
    // 求人・人材大手グループ
    'マイナビ', 'リクルート', 'パーソル', 'テンプスタッフ',
    // 不動産仲介大手
    'エイブル', 'アパマン', 'ミニミニ', 'ピタットハウス',
    // 広告代理店大手
    '博報堂', '電通', 'ADK',
    // 製造（合金・精密部品等）
    '合金', '製作所', '製鋼', '板金', '鋳造', '鍛造', '射出成形',
    // 大学系VC・インキュベーター
    'プラットフォーム開発', '協創', 'ベンチャーキャピタル',
    
    // ★ v2.3.0 & v2.4.0 水平展開追加: 大手インフラ・グループ企業・漏れ業種
    // 計測・精密機器・防衛（東京計器等）
    '計器', '計測', '精密機器', '光学機器', '測定器', '測量', '航法', '船舶機器', '防衛装備', '防衛機器',
    // 電力・エネルギーグループ
    '東電', 'TEPCO', '関電', '九電', '東北電力', '中部電力', '関西電力', '九州電力',
    // モビリティ・次世代インフラ
    'モビリティ', 'Mobility', 'e-Mobility',
    // 鉄道・交通大手グループ
    'JR', 'メトロ', '京王', '小田急', '東急', '阪急', '近鉄', '名鉄', '西鉄', '東京地下鉄',
    // 通信大手グループ
    'KDDI', 'SoftBank', 'ソフトバンク',
    // 金融メガグループ
    'MUFG', 'SMBC', 'みずほ', '三井住友', '三菱UFJ', 'センチュリー株式会社',
    // 総合電機・ITゼネコン・精密機器グループ
    '東芝', '日立', 'パナソニック', 'Panasonic', 'ソニー', 'Sony', '三菱電機', '富士通', 'NEC', '日本電気', 'シャープ', 'キヤノン', 'Canon', 'リコー', 'RICOH', 'セイコー', 'エプソン', 'EPSON',
    // 自動車メーカーグループ
    'トヨタ', 'ホンダ', '日産', 'マツダ', 'スバル', 'ダイハツ', 'スズキ', 'デンソー', '自動車株式会社',
    // インフラ・電気工事
    '電設', 'タワーライン', 'データセンター',
    // 交通・輸送
    'バス株式会社', '運輸株式会社', '交通株式会社',
    // 食品・農業
    '青果', 'バイオパートナー', '農業',
    // 住宅・不動産系
    '住宅保証', '建築検査', 'レコードマネジメント', '文書管理',
    // 金融・リース・商社
    '双日', '伊藤忠', '丸紅', '住友商事',
    // 保険（東京海上等）
    '損保', '損害保険', '生命保険', '火災保険', 'あんしんコンサルティング',
    // 医療・ヘルスケア
    '総合メディカル', 'メディカル株式会社', '病院', '医療法人', 'GENOVA',
    // 調査・リサーチ
    '商工リサーチ', '日経リサーチ', 'リサーチ株式会社', '信用調査',
    // 書店・出版物販
    'ブックセンター', '書店', '本店',
    // エンタメ・施設
    'ドーム株式会社', 'スタジアム', '展示会', 'TSP太陽',
    // ガス・エネルギー大手
    '岩谷', 'ガス株式会社',
    // 工学・CAE・専門ソフト
    'CAEソリューション', 'MBD', '構造計算', 'Idaj',
    // 投資育成・VC
    '投資育成', '中小企業投資',
    // 環境系
    'エコ・プラン', '環境コンサル',
    
    // ★ v2.5.0〜v2.7.0 統合パッチ（サイレントエラー復旧）
    // ホールディングス・持株会社
    'ホールディングス', 'HD', 'グループ本社',
    // ISP・プロバイダ大手
    'ビッグローブ', 'BIGLOBE', 'So-net', 'Nifty', 'OCN', 'ぷらら', 'インターネットイニシアティブ', 'IIJ',
    // シンクタンク・研究機関
    '研究所', '総研', 'シンクタンク',
    // クリニック物理支援（開業時の不動産・建築・医療機器）
    '貿易', '医療機器', '歯科産業', '産業株式会社', '地所', 'プロパティマネジメント', '建築', '日建', '設計', '調剤薬局',
    // 医療・介護の「実務・システム・検査」系
    '臨床検査', '血液検査', '電子カルテ', 'レセコン', 'PHC', 'ウィーメックス', 'エスアールエル', 'SRL', '介護', '福祉', '訪問看護', 'デイサービス', '老人ホーム', '医療事業開発', 'ケアマックス', 'ドクターソリューション', '医療サポート', 'メディカルフロント', 'メディカルガレージ', 'オクスアイ',

    // ★ v2.8.0 ユーザー指摘による追加（大企業・コンビニ・信販）
    'ジャックス', 'ファミリーマート', 'セブンイレブン', 'ローソン', 'ミニストップ', 'コンビニエンス',
    'クレジットカード', 'カード株式会社', 'JACCS', '信販株式会社',
];

/**
 * NG業種判定: 企業名にNG業種キーワードが含まれているかチェック
 * ※サイトテキスト全体でのチェックは誤爆リスクがあるため企業名のみ
 * @param {string} companyName
 * @returns {{blocked: boolean, reason: string}}
 */
function isNGIndustry(companyName) {
    if (!companyName) return { blocked: false, reason: '' };
    for (const kw of NG_INDUSTRY_KEYWORDS) {
        if (companyName.includes(kw)) {
            return { blocked: true, reason: kw };
        }
    }
    return { blocked: false, reason: '' };
}

module.exports = {
    crawlCompanyWebsite,
    extractCompanyLinksFromArticle,
    isArticlePage,
    isValidCompanyName,
    isListedCorporation,
    isNGIndustry,
    isJapanesePersonName,
    cleanRepresentativeName,
    cleanCompanyName,
    employeeFilter,
    EMPLOYEE_PATTERNS,
    REPRESENTATIVE_PATTERNS,
    CONTACT_PAGE_PATTERNS,
    COMPANY_PAGE_PATTERNS,
    NG_INDUSTRY_KEYWORDS,
};
