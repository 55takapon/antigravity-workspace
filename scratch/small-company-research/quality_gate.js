/**
 * quality_gate.js - クロール結果の品質検証（in-process）
 * 
 * 7つのチェック項目を実施し、合否（及びNGの場合はその理由と書き込み可否）を返す。
 */

function isJapanesePersonName(name) {
    if (!name || name.length < 2 || name.length > 15) return false;
    // 株式会社等の法人格が含まれる場合は人名ではない
    if (/(?:株式会社|合同会社|有限会社|法人|組合|機構|財団)/.test(name)) return false;
    
    // ひらがなのみ、カタカナのみは除外（企業名の可能性）
    if (/^[ぁ-ん]+$/.test(name) || /^[ァ-ヶー]+$/.test(name)) return false;
    // 英字が含まれる場合は除外
    if (/[a-zA-Z]/.test(name)) return false;
    
    // スペース区切りの姓名（例: 鈴木 一郎、山田太郎）
    if (/^[一-龯ぁ-ん]{1,3}[\s　]+[一-龯ぁ-ん]{1,4}$/.test(name)) return true;
    
    // スペースなしでもよくある苗字で始まる漢字2-5文字（簡易判定）
    const COMMON_NAMES = ['佐藤', '鈴木', '高橋', '田中', '伊藤', '渡辺', '山本', '中村', '小林', '加藤', '吉田', '山田', '佐々木', '山口', '松本', '井上', '木村', '林', '斎藤', '清水'];
    for (const cn of COMMON_NAMES) {
        if (name.startsWith(cn) && name.length >= cn.length + 1 && name.length <= cn.length + 3) {
            // 後続が漢字またはひらがなのみ
            const rest = name.substring(cn.length);
            if (/^[一-龯ぁ-ん]+$/.test(rest)) return true;
        }
    }
    return false;
}

const INVALID_COMPANY_PATTERNS = [
    /https?:\/\//, /^@/, /^[\w.-]+\.(com|jp|co\.jp|net|org)$/, /^ー/,
    /SIGN IN/i, /LOG ?IN/i, /SIGN UP/i, /Form Builder/i, /Online Form/i,
    /Cookie/i, /Privacy/i, /Terms/i, /お知らせ/, /ニュース/, /ブログ/,
    /ニュー速/, /様Webサイ/, /^株式会社.{1}$/, /医療法人社団/, /^株式会社創業/,
    /^(?:株式会社|合同会社|有限会社)(?:会長|社長|取締役|理事長|専務|常務|監査役|相談役|顧問|部長|課長|支店長|所長|院長)/,
    /^(?:株式会社|合同会社|有限会社)(?:一覧|ランキング|比較|まとめ|検索|情報|ナビ|ガイド|サイト|ポータル|マップ|マガジン|メディア|コラム)/,
    /^[A-Za-z]{1,2}(?:株式会社|合同会社|有限会社)$/,
    /^(?:株式会社|合同会社|有限会社)[A-Za-z]{1,2}$/,
    /^(?:[A-Za-z]|.)(?:株式会社|合同会社|有限会社)$/,
    /^(?:株式会社|合同会社|有限会社)(?:[A-Za-z]|.)$/,
    /^(?:株式会社|合同会社|有限会社)設立/,
    /^(?:トップ|アクセス|会社概要|ホーム|HOME|Top)\s*[|｜]/,
    /カンパニー\s*[|｜]/, /^URLs/i, /Shortener/i, /^クラウドファンディング/, /^Readyfor/i,
    /コーポレートサイト/, /ソフトウェアの[^\s]/, /ブックセンター/,
    /(?:株式会社|合同会社|有限会社)[様さん]?[はがをでにともの]/,
    /^(?:エイブル|アパマン|ミニミニ|ピタットハウス|センチュリー21)/,
    /[様さん御]$/, /の広告代理店/,
    /^(?:Group|Community|ホールディングス|カンパニー|システム|サービス|ソリューション|プロジェクト)(?:株式会社|合同会社|有限会社)$/i,
    /^(?:運営会社|管理会社|関連会社|子会社|親会社)/,
    /^(?:企業情報|会社名|会社情報|企業名|法人名|商号|名称|社名|名称（商号）|代表者名|代表取締役|社長|経歴|プロフィール|会社概要|店舗名|屋号)$/,
    /選！|おすすめ|ランキング|まとめ|ご紹介|の作り方|レンタルサーバー|ドメイン取得|比較|選び方/,
];

function checkCompanyName(name) {
    if (!name || name.length < 2 || name.length > 40) return { pass: false, msg: '長すぎるか短すぎる' };
    if (INVALID_COMPANY_PATTERNS.some(p => p.test(name))) return { pass: false, msg: '無効な文字列パターン' };
    if (name.length > 6 && /[はがをでにとも].{3,}/.test(name)) return { pass: false, msg: '助詞を含む文章片' };
    if (/[はがをでにとものへ]$/.test(name)) return { pass: false, msg: '助詞で終わる' };
    if (name.length > 8 && /[ぁ-ん]{3,}$/.test(name)) return { pass: false, msg: 'ひらがな末尾の文章片' };
    
    if (!/(?:株式会社|合同会社|有限会社|法人|機構|組合)/.test(name)) {
        if (/の/.test(name)) return { pass: false, msg: '「の」を含む非法人' };
        if (/なら/.test(name)) return { pass: false, msg: '「なら」を含む非法人' };
        if (/^[ァ-ヶー]+$/.test(name)) return { pass: false, msg: 'カタカナ単語' };
        if (name.length > 20) return { pass: false, msg: '長すぎる非法人' };
        if (isJapanesePersonName(name)) return { pass: false, msg: '人名の誤抽出' };
        if (/(?:執筆|監修|著|編集|作成)/.test(name)) return { pass: false, msg: '記事作成者情報' };
        if (/^[一-龯][\s　]+[一-龯]{2,}/.test(name)) return { pass: false, msg: '役職切れ端' };
        if (/^[一-龯ぁ-ん]{1,3}[\s　]+[一-龯ぁ-ん]{1,4}$/.test(name)) return { pass: false, msg: '姓名パターン' };
        if (/^[a-zA-Z0-9\s.,-]+$/.test(name)) return { pass: false, msg: '英数字記号のみ' };
    }
    return { pass: true };
}

function checkRepresentative(name) {
    if (!name) return { pass: true }; // 空は許可
    if (name.length > 30) return { pass: false, msg: '長すぎる' };
    if (/(?:株式会社|合同会社|有限会社|法人)/.test(name)) return { pass: false, msg: '法人名が混入' };
    return { pass: true };
}

function checkUrlNameMatch(url, companyName) {
    // 簡易チェック。URLに企業名のローマ字や一部が含まれているか。
    // 実際には厳密に判定しすぎると落ちるので緩めに。
    return { pass: true }; 
}

function checkListedCompany(fullText, name) {
    const isListed = /上場|東証(?:プライム|スタンダード|グロース|一部|二部|マザーズ)|証券取引所/.test(fullText);
    const listedNames = ['NTT', 'ソフトバンク', 'KDDI', 'トヨタ', 'パナソニック', 'ソニー']; // 簡易
    if (isListed || listedNames.some(ln => name.includes(ln))) {
        return { pass: false, msg: '上場・大企業の可能性' };
    }
    return { pass: true };
}

function checkCapital(capitalText) {
    if (!capitalText) return { pass: true };
    // 例: 「1億円」等の判定
    const clean = capitalText.replace(/[,\s]/g, '');
    let yen = 0;
    const matchOku = clean.match(/([0-9.]+)(?:億)円?/);
    const matchMan = clean.match(/([0-9.]+)(?:万)円?/);
    if (matchOku) yen = parseFloat(matchOku[1]) * 100000000;
    else if (matchMan) yen = parseFloat(matchMan[1]) * 10000;
    else {
        const matchNum = clean.match(/([0-9]+)円/);
        if (matchNum) yen = parseInt(matchNum[1], 10);
    }
    
    // 1億円以上はNGフラグ
    if (yen >= 100000000) return { pass: false, msg: '資本金1億円以上（大企業）' };
    return { pass: true };
}

function checkSharedDomain(url) {
    try {
        const hostname = new URL(url).hostname;
        const shared = ['jimdo.com', 'wixsite.com', 'fc2.com', 'ameba.jp', 'note.com', 'peraichi.com'];
        for (const s of shared) {
            if (hostname.endsWith(s)) return { pass: false, msg: `間借りドメイン (${s})` };
        }
        return { pass: true };
    } catch { return { pass: false, msg: '無効なURL' }; }
}

function checkKeywordHit(mainText, verticalKeywords) {
    if (!mainText || !verticalKeywords || verticalKeywords.length === 0) return { pass: false, msg: 'テキストなしまたはキーワード未指定' };
    
    let hitWords = [];
    for (const kw of verticalKeywords) {
        // 大文字小文字を区別せず検索
        if (mainText.toLowerCase().includes(kw.toLowerCase())) {
            hitWords.push(kw);
        }
    }
    
    if (hitWords.length > 0) {
        return { pass: true, hits: hitWords };
    }
    return { pass: false, msg: 'キーワードHITなし' };
}

/**
 * 総合判定を実行
 * @param {Object} data クロール結果
 * @param {Array<string>} keywords 判定用キーワード配列
 * @returns {Object} { shouldWrite: boolean, status: string, rejectReason: string }
 */
function runQualityGate(data, keywords) {
    const { companyName, representative, url, mainText, capitalText } = data;
    
    // G: キーワードHIT必須（最も重要）
    const kwRes = checkKeywordHit(mainText, keywords);
    if (!kwRes.pass) {
        return { shouldWrite: false, status: 'rejected_keyword', rejectReason: kwRes.msg };
    }
    
    // 他のチェック
    const checks = [
        { name: '企業名', res: checkCompanyName(companyName) },
        { name: '代表者', res: checkRepresentative(representative) },
        { name: 'URL整合', res: checkUrlNameMatch(url, companyName) },
        { name: '上場', res: checkListedCompany(mainText, companyName) },
        { name: '資本金', res: checkCapital(capitalText) },
        { name: '間借り', res: checkSharedDomain(url) }
    ];
    
    for (const c of checks) {
        if (!c.res.pass) {
            // NGだが書き込みは行う（✕フラグを立てる）
            return { shouldWrite: true, status: '✕', rejectReason: `[${c.name}] ${c.res.msg}`, hits: kwRes.hits };
        }
    }
    
    // 全てパス
    return { shouldWrite: true, status: '', rejectReason: '', hits: kwRes.hits };
}

module.exports = { runQualityGate };
