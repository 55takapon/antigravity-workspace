/**
 * check_ng_forms.js - 問い合わせフォームの営業NG文言チェック
 *
 * 【設計思想 v1.5.5】
 *   正規表現の組み合わせ列挙はきりがない。
 *   「セールス」「売り込み」「勧誘」「営業目的」はフォームページに
 *   出現した時点でほぼ100%お断り文脈 → キーワード存在だけで即NG。
 *   「営業」は「営業時間」「営業日」等の無害用途があるため、
 *   それらを除去した後にまだ残っていればNG判定。
 *   v1.5.5: 誤検知パターンを大幅追加（安心訴求・職種名・部署名・大手ブロック）
 *
 * 使い方:
 *   node check_ng_forms.js                # 全件チェック
 *   node check_ng_forms.js --dry-run      # テスト（書き込みなし）
 *   node check_ng_forms.js --start 100    # 行100から開始
 *   node check_ng_forms.js --max 20       # 最大20件チェック
 *   node check_ng_forms.js --sheet Webマーケティング_名古屋
 */

const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

const { getGoogleSheetsClient } = require('./sheets_writer');

const SPREADSHEET_ID = '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk';
let SHEET_NAME = 'Webマーケティング';

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// 営業NG判定ロジック（v1.5.5: 誤検知大幅削減）
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

/**
 * 大手企業・メディア・ポータルサイト等の除外リスト
 * （スプレッドシートへの登録自体を弾く）
 */
const BLOCKED_COMPANY_NAMES = [
    'オリコン株式会社', 'オリコン',
    '日経BOOKプラス', '日本経済新聞', '日経',
    'リクルート', 'リクルートホールディングス',
    'マイナビ', 'パーソル', 'エン・ジャパン',
    'Indeed', 'Wantedly',
    'ランサーズ', 'クラウドワークス',
    'Yahoo', 'Google', 'Amazon', 'Meta', 'LINE',
    '電通', '博報堂', 'ADK',
];

/**
 * 除外パターン（=NG判定しない安全な文脈）
 *
 * 【分類】
 * A: 自社が営業しない宣言（安心訴求）
 * B: 職種・部署・採用情報の見出し
 * C: 自社サービスや実績の説明文
 * D: 業界コンテンツ（ブログ記事・コラム等）
 * E: 法的表明・プライバシーポリシー文脈
 */
const EXCLUDE_PATTERNS = [
    // A: 自社から営業しない宣言（安心訴求）
    /(?:当社|弊社|私共|当店|当院|私達|こちら)からの?(?:無理な|しつこい|強引な)?(?:営業|勧誘|セールス|お電話|電話|ご連絡)/,
    /(?:無理な|しつこい|強引な)(?:営業|勧誘|セールス)/,
    /(?:営業|勧誘|セールス).*?(?:一切ありません|いたしません|行いません|しません|致しません|いたしかねます)/,
    /営業電話すること(?:は|が)ありません/,
    /無料相談後.*?営業(?:電話|メール)/,
    /お気軽に.*?(?:無理な)?営業.*?(?:おこない|致し|いたし)/,

    // B: 職種・部署・採用情報（「営業」が役職名・業種名として使われている）
    /(?:印刷|WEB|Web|IT|デジタル)媒体.*?営業/,
    /営業[・・]?(?:制作|マーケ|企画|デザイン|システム|開発|事務)/,
    /(?:マーケティング|営業|制作|開発)部(?:門|長|員)?[\s　]*[\／/｜|]?[\s　]*(?:営業|マーケ|制作|企画|統括)/,
    /(?:営業|セールス)[\s　]*(?:職|部|部門|企画|担当|マネージャー|リーダー|担当者)/,
    /(?:インサイド|フィールド|テレ|法人|個人|プロダクト|オリオン|IA|B2B|BtoB)[セールス|営業]/,
    /(?:営業|セールス)(?:力|活動|経験|職種|採用|募集)/,
    /(?:たくさん|様々)の職種/,
    /(?:営業|販売)(?:・|／|\/)(?:マーケティング|制作|開発|企画|事務|管理)/,

    // C: 自社サービス・実績の説明（「営業」をサービス対象として言及）
    /(?:営業|セールス)(?:支援|代行|強化|自動化|効率化|仕組化|DX|ツール|SaaS|プラットフォーム)(?:の|を|に|で|が|は|として|する|した|します)/,
    /(?:営業|セールス)を?(?:自動化|支援|強化|効率化|仕組化)/,
    /(?:営業|販売)(?:リスト|資料|資産|情報|データ|管理)/,
    /(?:24時間|365日)働く.*?営業(?:マン|パーソン)?/,
    /Webサイト.*?営業(?:マン|パーソン)?として/,
    /弊社(?:の|が)?(?:営業|セールス)(?:より|スタッフ|担当)(?:ご案内|ご提供|ご連絡|対応)/,
    /弊社営業より(?:提供|ご案内|ご連絡)/,
    /ランクインして(?:いる|る)企業.*?弊社営業/,

    // D: コンテンツ・ブログ記事文脈（「営業」が一般名詞として登場）
    /営業(?:と兼任|経験|成績|マン|パーソン|担当者).*?(?:方|人|ため|から)/,
    /(?:営業|マーケ)(?:と兼任|も兼任|兼務)/,
    /心当たりがある(?:の)?(?:ではないでしょうか|方)/,
    /(?:コンサルティング|カウンセリング|アドバイザー)営業/,
    /営業(?:領域|活動|行為)に対する/,
    /(?:対面|オフライン)営業/,
    /新規開拓営業/,
    /(?:生命保険|保険代理店).*?営業(?:経験|活動)/,
    /資産運用.*?営業/,
    /(?:被リンク|SEO|Web集客).*?(?:営業|代行)/,
    /(?:Cookie|クッキー).*?(?:営業|宣伝)/,
    /事業(?:の)?承継.*?(?:営業|譲渡)/,
    /年末年始営業(?:のお知らせ|について)/,
    /(?:戸建て|企業案件).*?営業/,
    /営業(?:マン)?にする方法/,
    /リフォーム業界.*?営業(?:マン)?/,
    /今すぐリホームページして営業/,
    /(?:問い合わせ|コンタクト)フォーム(?:営業|経由の営業)/,

    // E: 法的・プライバシーポリシー文脈
    /勧誘方針(?:（|）|　|\s)/,
    /金融商品取引法.*?勧誘/,
    /(?:媒介|勧誘).*?契約締結/,
    /事業(?:の)?承継.*?個人(?:データ|情報)/,
    // F: 問い合わせ種別（プルダウン）
    /(?:競業|パートナー|アライアンス|協業).*?(?:営業のご連絡|お問い合わせ)/,
    /(?:お問い合わせ種別|ご用件).*?(?:営業|ご提案)/,
];

const NG_PATTERNS = [
    // 即NG: 売り込み系
    /売り込み/,
    /売込み/,

    // 即NG: フォームページでのお断り文言
    /(?:営業|セールス|協業|提案)[^。！？\n]{0,40}(?:お断り|ご遠慮|お控え|禁止|固く|対応できかね|返信(?:いたし)?かね|不要|迷惑|専用フォーム|こちらのフォーム|下記フォーム|こちらより)/,
    /(?:弊社|当社|貴社|当サイト)への(?:営業|セールス|勧誘)(?!.*?歓迎)/, // 「歓迎します」は除外
    /営業の(?:ご連絡|お問い合わせ|ご案内|ご提案)/,
    /営業の方(?:\s|$|。)/,
    /セールス目的(?:の|で|は)/,
    /営業(?:メール|電話)(?:は)?(?:ご遠慮|お断り|お控え|受け付けておりません|していません|対応しておりません)/,
    /営業目的(?:の|で|は|に)(?:お問い合わせ|ご連絡|メール|問い合わせ)/,
    /フリーランス.*?営業には返信/,
    /(?:いたずら|迷惑).*?営業/,
];

// コマンドライン引数
const args = process.argv.slice(2);
const isDryRun = args.includes('--dry-run');
let startRow = 2;
let maxCheck = Infinity;

for (let i = 0; i < args.length; i++) {
    if (args[i] === '--start' && args[i + 1]) startRow = parseInt(args[i + 1], 10);
    if (args[i] === '--max' && args[i + 1]) maxCheck = parseInt(args[i + 1], 10);
    if (args[i] === '--sheet' && args[i + 1]) { SHEET_NAME = args[i + 1]; i++; }
}

/**
 * テキストからキーワードを含む一文を綺麗に抽出する
 */
function extractSentence(text, keyword) {
    const lines = text.split(/\r?\n/);
    for (let line of lines) {
        if (line.includes(keyword)) {
            // 句点・感嘆符等で分割（記号は残す）
            const sentences = line.split(/(?<=[。！？])/);
            for (let s of sentences) {
                if (s.includes(keyword)) {
                    s = s.trim();
                    // 「送信する ※営業お断り」のようなケースで「※」以降を抽出
                    if (s.includes('※') && s.indexOf(keyword) > s.indexOf('※')) {
                        s = s.substring(s.indexOf('※'));
                    }
                    return s;
                }
            }
            return line.trim();
        }
    }
    // フォールバック
    const idx = text.indexOf(keyword);
    return text.substring(Math.max(0, idx - 40), Math.min(text.length, idx + 40)).trim();
}

function extractCleanSentence(s, pattern) {
    const match = s.match(pattern);
    if (!match) return s;
    
    let startIdx = match.index;
    let endIdx = match.index + match[0].length;
    
    // 左側境界：空白、タブ、改行、スラッシュ、パイプなど
    let leftBoundary = 0;
    for (let i = startIdx - 1; i >= 0; i--) {
        if (/[ 　\t\n\/／|｜]/.test(s[i])) {
            leftBoundary = i + 1;
            break;
        }
        // 注意書きの記号はそのまま含める
        if (s[i] === '※' || s[i] === '▼' || s[i] === '■' || s[i] === '・' || s[i] === '【') {
            leftBoundary = i; 
            break;
        }
    }
    
    // 右側境界：句点は含め、空白等が出たらそこで切る
    let rightBoundary = s.length;
    for (let i = endIdx; i < s.length; i++) {
        if (/[。！？]/.test(s[i])) {
            rightBoundary = i + 1;
            break;
        }
        if (/[ 　\t\n\/／|｜]/.test(s[i])) {
            rightBoundary = i;
            break;
        }
    }
    
    let clean = s.substring(leftBoundary, rightBoundary).trim();
    if (clean.length < 5) return s.trim(); // 切り取りすぎて意味不明になるのを防ぐ保険
    return clean;
}

/**
 * ページテキストからNG文言を検出する
 * @returns {{ hasNG: boolean, context: string } | null}
 */
function detectNG(bodyText) {
    const lines = bodyText.split(/\r?\n/);
    for (const line of lines) {
        // 句点・感嘆符等で分割して文単位でチェック
        const sentences = line.split(/(?<=[。！？])/);
        for (let s of sentences) {
            s = s.trim();
            if (!s) continue;

            // ① 除外パターン（当社からの営業はありません等）ならスキップ
            if (EXCLUDE_PATTERNS.some(p => p.test(s))) continue;

            // ② NGパターンのどれかに合致したらアウト
            for (const p of NG_PATTERNS) {
                if (p.test(s)) {
                    return { context: extractCleanSentence(s, p) };
                }
            }
        }
    }
    return null;
}

async function checkFormPage(page, url) {
    try {
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 15000 });
        await page.waitForTimeout(2000);

        const bodyText = await page.evaluate(() => {
            return document.body ? document.body.innerText : '';
        });

        const hit = detectNG(bodyText);
        if (hit) {
            return {
                hasNG: true,
                message: hit.context,
                allHits: [hit.context],
            };
        }

        return { hasNG: false, message: null, allHits: [] };
    } catch (err) {
        return { hasNG: false, message: null, allHits: [], error: err.message.substring(0, 100) };
    }
}

async function main() {
    console.log('========================================');
    console.log('  営業NG文言チェッカー v1.5.5');
    console.log(`  モード: ${isDryRun ? 'ドライラン（テスト）' : '本番'}`);
    console.log(`  シート: ${SHEET_NAME}`);
    console.log(`  開始行: ${startRow}, 最大件数: ${maxCheck === Infinity ? '全件' : maxCheck}`);
    console.log('  判定方式: 文脈ベースの複合パターン抽出（誤検知大幅削減版）');
    console.log('========================================\n');

    const sheetsClient = await getGoogleSheetsClient();
    const response = await sheetsClient.spreadsheets.values.get({
        spreadsheetId: SPREADSHEET_ID,
        range: SHEET_NAME,
    });

    const allRows = response.data.values || [];
    const header = allRows[0];
    const dataRows = allRows.slice(1);
    console.log(`全${dataRows.length}件のデータを取得\n`);

    const formUrlCol = header.indexOf('問い合わせフォームURL');
    const reasonCol = header.indexOf('送信不可理由');
    const nameCol = header.indexOf('企業名');

    if (formUrlCol < 0) {
        console.error('「問い合わせフォームURL」列が見つかりません');
        process.exit(1);
    }
    console.log(`列マッピング: 企業名=${nameCol}, フォームURL=${formUrlCol}, 送信不可理由=${reasonCol}\n`);

    const targets = [];
    let blockedCount = 0;
    for (let i = 0; i < dataRows.length; i++) {
        const rowIdx = i + 2;
        if (rowIdx < startRow) continue;
        const row = dataRows[i];
        const formUrl = (row[formUrlCol] || '').trim();
        const name = (row[nameCol] || '').trim();
        const existingReason = (row[reasonCol] || '').trim();
        if (!formUrl || formUrl === '-' || formUrl === 'なし') continue;

        // 大手企業・メディアブロック
        const isBlocked = BLOCKED_COMPANY_NAMES.some(b => name.includes(b));
        if (isBlocked) {
            console.log(`[ブロック] 行${rowIdx}: ${name} → 大手・メディア除外`);
            blockedCount++;
            // もし素通り（送信可能）と登録されていればクリア
            if (!isDryRun && existingReason) {
                await sheetsClient.spreadsheets.values.update({
                    spreadsheetId: SPREADSHEET_ID,
                    range: `${SHEET_NAME}!H${rowIdx}:I${rowIdx}`,
                    valueInputOption: 'RAW',
                    requestBody: { values: [['', '']] },
                });
            }
            continue;
        }

        targets.push({ rowIdx, name, formUrl, existingReason });
        if (targets.length >= maxCheck) break;
    }

    console.log(`チェック対象: ${targets.length}件（フォームURLあり）\n`);
    if (targets.length === 0) { console.log('チェック対象がありません。'); return; }

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        locale: 'ja-JP',
        userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    });

    let ngCount = 0, checkedCount = 0, errorCount = 0;
    const ngResults = [];

    for (let idx = 0; idx < targets.length; idx++) {
        const t = targets[idx];
        checkedCount++;
        process.stdout.write(`[${checkedCount}/${targets.length}] ${t.name} ... `);

        const page = await context.newPage();
        const result = await checkFormPage(page, t.formUrl);
        await page.close();

        if (result.error) {
            console.log(`⚠️ エラー: ${result.error.substring(0, 60)}`);
            errorCount++;
        } else if (result.hasNG) {
            ngCount++;
            console.log(`🚫 NG検出: "${result.message.substring(0, 80)}"`);
            ngResults.push({ rowIdx: t.rowIdx, name: t.name, formUrl: t.formUrl, message: result.message });

            if (!isDryRun) {
                const ngNote = `【営業NG】${result.message.substring(0, 200)}`;
                await sheetsClient.spreadsheets.values.update({
                    spreadsheetId: SPREADSHEET_ID,
                    range: `${SHEET_NAME}!H${t.rowIdx}:I${t.rowIdx}`,
                    valueInputOption: 'RAW',
                    requestBody: { values: [['✕', ngNote]] },
                });
                console.log(`  → H${t.rowIdx}:I${t.rowIdx} に記入完了`);
            }
        } else {
            console.log('✅ OK');
            if (!isDryRun && t.existingReason && t.existingReason.startsWith('【営業NG】')) {
                await sheetsClient.spreadsheets.values.update({
                    spreadsheetId: SPREADSHEET_ID,
                    range: `${SHEET_NAME}!H${t.rowIdx}:I${t.rowIdx}`,
                    valueInputOption: 'RAW',
                    requestBody: { values: [['', '']] },
                });
                console.log(`  → H${t.rowIdx}:I${t.rowIdx} の既存誤検知フラグ（営業NG）をクリア（リスト復帰）`);
            } else if (!isDryRun && t.existingReason) {
                console.log(`  → H${t.rowIdx}:I${t.rowIdx} は別理由（${t.existingReason.substring(0, 10)}...）のため維持`);
            }
        }

        if (idx < targets.length - 1) {
            await new Promise(r => setTimeout(r, 2000 + Math.random() * 3000));
        }
    }

    await context.close();
    await browser.close();

    console.log('\n========================================');
    console.log('  チェック完了');
    console.log('========================================');
    console.log(`  チェック件数: ${checkedCount}件`);
    console.log(`  NG検出: ${ngCount}件`);
    console.log(`  エラー: ${errorCount}件`);
    console.log(`  正常: ${checkedCount - ngCount - errorCount}件`);

    if (ngResults.length > 0) {
        console.log('\n[NG一覧]');
        for (const r of ngResults) {
            console.log(`  行${r.rowIdx}: ${r.name}`);
            console.log(`    URL: ${r.formUrl}`);
            console.log(`    文言: ${r.message.substring(0, 120)}`);
        }
    }
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
