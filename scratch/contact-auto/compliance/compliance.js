/**
 * compliance.js
 * ─────────────────────────────────────────────────────────────────────────────
 * コンプライアンスモジュール
 * - 営業NGキーワード検出（拡張版: 90+パターン）
 * - 用途限定フォーム検出
 * - ブラックリスト管理
 * - 送信レート制御
 * ─────────────────────────────────────────────────────────────────────────────
 */

const fs = require('fs');
const path = require('path');

// ── 営業NGキーワード（旧44パターン → 拡張90+パターン） ──
const SALES_NG_KEYWORDS = [
    // 直接的な禁止表現
    '営業お断り', '営業禁止', '営業目的', 'セールス禁止', 'セールスお断り',
    '営業・勧誘', '営業活動', '売り込み禁止', '売り込みお断り',
    '営業メール禁止', '営業電話禁止', '営業以外', '営業のお電話',
    '営業・セールス', '営業等のお電話', '営業に関するお問い合わせ',
    '営業目的のお問い合わせ', '営業のお問い合わせ', '営業関連',
    // 丁寧な拒否表現
    'お控えください', 'ご遠慮ください', 'お断りいたします',
    'お断りさせていただきます', 'お受けできません', '受け付けておりません',
    '受付できません', '対応いたしかねます', '対応できません',
    'お答えできません', 'おやめください', 'お断りしております',
    'ご遠慮いただ', 'お控えいただ',
    // メール系
    '営業メール', '営業メールはお控え', '営業メールは', 'セールスメール',
    '営業のメール', '営業目的のメール', '営業に関するメール',
    // 勧誘系
    '勧誘お断り', '勧誘禁止', '勧誘目的', '勧誘は', '勧誘等',
    'セールス目的', 'セールスに関する', 'セールスは', 'セールス等',
    '勧誘行為', 'セールス行為',
    // 売り込み系
    '商品・サービスの売り込み', '商品の売り込み', 'サービスの売り込み',
    '売り込みの一切', '売り込みを', '売込み', '売り込み行為',
    // 対策系
    '営業対策', '営業対策をしています', '悪質な営業', '営業対策を行って',
    '営業メール対策', 'スパム対策',
    // 業者系
    '取引のお誘い', '業者様', '同業者', '取引先開拓', '営業代行',
    '業者の方', '営業会社', '営業業者',
    // 目的限定
    'お取引を目的', '営業を目的', '勧誘を目的', 'セールスを目的',
    '商談目的', '提案目的', '売込み目的', '売り込みを目的',
    '営業活動を目的', '販売を目的',
    // 遠慮系
    '営業行為はご遠慮', 'セールス行為はご遠慮', '営業はご遠慮',
    '勧誘はご遠慮', 'セールスはご遠慮', '営業活動はご遠慮',
    '売り込みはご遠慮',
    // 強い拒否
    '絶対におやめ', '一切お断り', '固くお断り', '全てお断り',
    '絶対にお断り', '完全にお断り',
    // 複合表現
    '営業のお問い合わせはご遠慮', '営業目的でのご利用はお断り',
    '営業に関するお問合せはお断り', '営業に関する問い合わせはお断り',
    '営業電話お断り', '営業FAXお断り', '営業訪問お断り',
    // 追加パターン（実運用で発見）
    '営業のご連絡', '営業についてのお問い合わせ', '売込みメール',
    '商用メール', '広告・宣伝', '宣伝メール', '商用利用禁止',
    'DM禁止', '営業DM'
];

// ── 用途限定フォームキーワード ──
const FORM_PURPOSE_KEYWORDS = {
    recruitment: ['採用', '求人', '応募', 'エントリー', '新卒', '中途', 'キャリア', '採用情報', '採用フォーム', '応募フォーム'],
    support: ['サポート', 'ヘルプデスク', '技術サポート', '不具合報告', 'バグ報告', '修理依頼', '返品', '交換'],
    media: ['取材', 'メディア', 'プレス', '報道関係', '広報窓口'],
    existing_customer: ['既存顧客', '会員専用', 'ログイン', '契約者', '利用者']
};

// ── スプレッドシートのスキップキーワード ──
const SHEET_SKIP_KEYWORDS = [
    '営業NG', '営業ng', 'NG', '送信不可', 'スキップ', '除外', 'フォームなし',
    '閉鎖', '削除', 'リンク切れ', 'エラー', '対象外'
];

/**
 * 営業NGキーワードを検出
 * @param {string} text - ページのテキスト
 * @returns {string|null} 検出されたキーワード、なければnull
 */
function checkSalesNG(text) {
    for (const kw of SALES_NG_KEYWORDS) {
        if (text.includes(kw)) return kw;
    }
    return null;
}

/**
 * 用途限定フォームを検出
 * @param {string} text - ページのテキスト
 * @returns {{ isPurposeLimited: boolean, purpose: string, keyword: string }}
 */
function checkFormPurpose(text) {
    for (const [purpose, keywords] of Object.entries(FORM_PURPOSE_KEYWORDS)) {
        for (const kw of keywords) {
            if (text.includes(kw)) {
                // 「お問い合わせ」等の汎用ワードと一緒に含まれている場合はスキップしない
                // 「採用フォーム」「採用のみ受付」等の明示的な限定のみ検出
                const limitPatterns = [
                    `${kw}フォーム`, `${kw}のみ`, `${kw}専用`, `${kw}に関する`,
                    `${kw}についてのお問い合わせ`, `${kw}窓口`
                ];
                for (const pat of limitPatterns) {
                    if (text.includes(pat)) {
                        return { isPurposeLimited: true, purpose, keyword: pat };
                    }
                }
            }
        }
    }
    return { isPurposeLimited: false, purpose: '', keyword: '' };
}

/**
 * ブラックリスト管理
 */
class BlacklistManager {
    constructor(filePath) {
        this.filePath = filePath;
        this.blacklist = this._load();
    }

    _load() {
        try {
            if (fs.existsSync(this.filePath)) {
                return JSON.parse(fs.readFileSync(this.filePath, 'utf-8'));
            }
        } catch { }
        return { domains: [], urls: [] };
    }

    _save() {
        fs.writeFileSync(this.filePath, JSON.stringify(this.blacklist, null, 2), 'utf-8');
    }

    isBlocked(url) {
        try {
            const urlObj = new URL(url);
            const domain = urlObj.hostname.replace(/^www\./, '');
            return this.blacklist.domains.includes(domain) || this.blacklist.urls.includes(url);
        } catch {
            return false;
        }
    }

    addDomain(domain) {
        domain = domain.replace(/^www\./, '');
        if (!this.blacklist.domains.includes(domain)) {
            this.blacklist.domains.push(domain);
            this._save();
        }
    }

    addUrl(url) {
        if (!this.blacklist.urls.includes(url)) {
            this.blacklist.urls.push(url);
            this._save();
        }
    }
}

/**
 * 送信レート制御（ランダム遅延）
 */
function randomDelay(minMs = 5000, maxMs = 15000) {
    const delay = Math.floor(Math.random() * (maxMs - minMs + 1)) + minMs;
    return new Promise(resolve => setTimeout(resolve, delay));
}

/**
 * リトライ機構（指数バックオフ）
 */
async function withRetry(fn, maxRetries = 3, baseDelay = 2000) {
    let lastError;
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
            return await fn();
        } catch (e) {
            lastError = e;
            if (attempt < maxRetries) {
                const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
                console.log(`  🔄 リトライ ${attempt + 1}/${maxRetries} (${Math.round(delay / 1000)}秒後)...`);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
    throw lastError;
}

module.exports = {
    SALES_NG_KEYWORDS,
    SHEET_SKIP_KEYWORDS,
    checkSalesNG,
    checkFormPurpose,
    BlacklistManager,
    randomDelay,
    withRetry
};
