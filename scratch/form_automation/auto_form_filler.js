const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

const fs = require('fs');
const path = require('path');
const csvParser = require('csv-parser');
const { createObjectCsvWriter } = require('csv-writer');
const { google } = require('googleapis');

const salesNGKeywords = [
    '営業お断り', '営業禁止', '営業目的', 'セールス禁止', 'セールスお断り',
    '営業・勧誘', '営業活動', '売り込み禁止', '売り込みお断り',
    '営業メール禁止', '営業電話禁止', '営業以外', '営業のお電話',
    '営業・セールス', '営業等のお電話', '営業に関するお問い合わせ',
    '営業目的のお問い合わせ', '営業のお問い合わせ', '営業関連',
    'お控えください', 'ご遠慮ください', 'お断りいたします',
    'お断りさせていただきます', 'お受けできません', '受け付けておりません',
    '受付できません', '対応いたしかねます', '対応できません',
    'お答えできません', 'おやめください', 'お断りしております',
    'ご遠慮いただ', 'お控えいただ',
    '営業メール', '営業メールはお控え', '営業メールは', 'セールスメール',
    '営業のメール', '営業目的のメール', '営業に関するメール',
    '勧誘お断り', '勧誘禁止', '勧誘目的', '勧誘は', '勧誘等',
    'セールス目的', 'セールスに関する', 'セールスは', 'セールス等',
    '勧誘行為', 'セールス行為',
    '商品・サービスの売り込み', '商品の売り込み', 'サービスの売り込み',
    '売り込みの一切', '売り込みを', '売込み', '売り込み行為',
    '営業対策', '営業対策をしています', '悪質な営業', '営業対策を行って',
    '営業メール対策', 'スパム対策',
    '取引のお誘い', '業者様', '同業者', '取引先開拓', '営業代行',
    '業者の方', '営業会社', '営業業者',
    'お取引を目的', '営業を目的', '勧誘を目的', 'セールスを目的',
    '商談目的', '提案目的', '売込み目的', '売り込みを目的',
    '営業活動を目的', '販売を目的',
    '営業行為はご遠慮', 'セールス行為はご遠慮', '営業はご遠慮',
    '勧誘はご遠慮', 'セールスはご遠慮', '営業活動はご遠慮',
    '売り込みはご遠慮',
    '絶対におやめ', '一切お断り', '固くお断り', '全てお断り',
    '絶対にお断り', '完全にお断り',
    '営業のお問い合わせはご遠慮', '営業目的でのご利用はお断り',
    '営業に関するお問合せはお断り', '営業に関する問い合わせはお断り',
    '営業電話お断り', '営業FAXお断り', '営業訪問お断り'
];

async function main() {
    const args = process.argv.slice(2);
    const isSubmit = args.includes('--submit');
    const isDryRun = args.includes('--dry-run') || !isSubmit;
    const isAllFields = args.includes('--all-fields');
    
    let targetUrl = null;
    let listFile = null;
    let spreadsheetId = null;
    let sheetName = null;
    let profileFile = 'web-company_profile.json';  // default
    let mappingFile = 'web-company_mapping.json';  // default

    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--url' && args[i+1]) targetUrl = args[i+1];
        if (args[i] === '--list' && args[i+1]) listFile = args[i+1];
        if (args[i] === '--sheets' && args[i+1]) spreadsheetId = args[i+1];
        if (args[i] === '--sheet-name' && args[i+1]) sheetName = args[i+1];
        if (args[i] === '--profile' && args[i+1]) profileFile = args[i+1];
        if (args[i] === '--mapping' && args[i+1]) mappingFile = args[i+1];
    }

    if (!targetUrl && !listFile && !spreadsheetId) {
        console.error('Usage: node auto_form_filler.js [--url <URL> | --list <list.csv> | --sheets <ID> --sheet-name <NAME>] [--submit | --dry-run] [--all-fields] [--profile <file>] [--mapping <file>]');
        process.exit(1);
    }

    const profilePath = path.join(__dirname, profileFile);
    const mappingPath = path.join(__dirname, mappingFile);
    
    if (!fs.existsSync(profilePath) || !fs.existsSync(mappingPath)) {
        console.error(`Missing ${profileFile} or ${mappingFile}.`);
        process.exit(1);
    }

    const profile = JSON.parse(fs.readFileSync(profilePath, 'utf-8'));
    const mapping = JSON.parse(fs.readFileSync(mappingPath, 'utf-8'));

    // Create screenshots dir
    const screenshotsDir = path.join(__dirname, 'screenshots');
    if (!fs.existsSync(screenshotsDir)) fs.mkdirSync(screenshotsDir);

    const browser = await chromium.launch({ headless: false });
    const context = await browser.newContext();

    if (spreadsheetId) {
        // === Google Sheets API Mode ===
        if (!sheetName) { console.error('--sheet-name is required with --sheets'); process.exit(1); }
        console.log(`[Sheets] Reading from spreadsheet: ${spreadsheetId} / sheet: ${sheetName}`);
        const sheetsClient = await getGoogleSheetsClient();
        const { headers, rows } = await readSheet(sheetsClient, spreadsheetId, sheetName);

        // Find column indexes
        const colIdx = (name) => headers.indexOf(name);
        const urlCol     = colIdx('問い合わせフォームURL');
        const statusCol  = colIdx('送信○×');
        const reasonCol  = colIdx('送信不可理由');
        const dateCol    = colIdx('送信日');
        const companyCol = colIdx('企業名');
        const repCol     = colIdx('代表者名');
        const numCol     = colIdx('№');

        if (urlCol < 0) { console.error('Column "問い合わせフォームURL" not found in sheet.'); process.exit(1); }

        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            const statusVal = statusCol >= 0 ? row[statusCol] : '';
            const formUrl   = urlCol >= 0 ? row[urlCol] : '';

            // Skip already-processed rows or rows with no URL
            if (statusVal === '〇' || statusVal === '×' || !formUrl || !formUrl.startsWith('http')) {
                continue;
            }

            const companyName = companyCol >= 0 ? row[companyCol] : '';
            const repName     = repCol >= 0 ? row[repCol] : '';
            const rowNum      = numCol >= 0 ? row[numCol] : i + 2; // 1-indexed, +1 for header
            const sheetRowNum = i + 2; // actual sheet row (1=header, 2=first data)

            console.log(`\n--- [Sheets] Row ${sheetRowNum}: ${companyName} (${repName}) ---`);
            const page = await context.newPage();
            const result = await processForm(page, formUrl, profile, mapping, isDryRun, rowNum, { company: companyName, rep_name: repName }, isAllFields);
            await page.close();

            const today = new Date().toISOString().split('T')[0].replace(/-/g, '/');

            // Write result back to sheet immediately for this row
            if (!isDryRun) {
                await updateSheetRow(sheetsClient, spreadsheetId, sheetName, sheetRowNum, {
                    statusCol, reasonCol, dateCol,
                    status: result.status,
                    reason: result.reason || '',
                    date: today
                });
                console.log(`[Sheets] Updated row ${sheetRowNum}: ${result.status}`);
            } else {
                console.log(`[Sheets DryRun] Row ${sheetRowNum} would be: ${result.status} / ${result.reason}`);
            }
        }
        console.log('\n[Sheets] Batch process complete.');

    } else if (listFile) {
        console.log(`Starting batch process for list: ${listFile}`);
        const rows = await readCSV(listFile);
        for (let i = 0; i < rows.length; i++) {
            const row = rows[i];
            // Skip if already processed or missing URL
            if (row['送信○×'] === '〇' || row['送信○×'] === '×' || !row['問い合わせフォームURL']) {
                continue;
            }

            const companyName = row['企業名'] || '';
            const repName = row['代表者名'] || '';
            console.log(`\n--- Processing Row ${row['№'] || i+1}: ${companyName} (担当: ${repName}) ---`);
            const page = await context.newPage();
            const result = await processForm(page, row['問い合わせフォームURL'], profile, mapping, isDryRun, row['№'] || i+1, { company: companyName, rep_name: repName }, isAllFields);
            
            row['送信○×'] = result.status;
            row['送信不可理由'] = result.reason || '';
            row['送信日'] = new Date().toISOString().split('T')[0].replace(/-/g, '/');
            
            await page.close();
        }

        // Write updated CSV
        const outPath = listFile.replace('.csv', '_result.csv');
        await writeCSV(outPath, Object.keys(rows[0]), rows);
        console.log(`\nBatch process finished. Wrote results to ${outPath}`);

    } else if (targetUrl) {
        console.log(`Starting single URL process: ${targetUrl}`);
        const page = await context.newPage();
        // Single URL mode: use profile defaults (no CSV row data)
        const result = await processForm(page, targetUrl, profile, mapping, isDryRun, 'single', {}, isAllFields);
        console.log(`\nFinal Status: ${result.status}, Reason: ${result.reason}`);
        if (isDryRun) {
            console.log('Dry run mode. Browser will remain open. Press Ctrl+C to exit.');
            await new Promise(() => {}); // hang
        }
    }

    await browser.close();
}

/**
 * @param {object} rowData - Per-row overrides: { company, rep_name }
 */
async function processForm(page, url, profile, mapping, isDryRun, idString, rowData = {}, isAllFields = false) {
    // Build personalized profile for this row
    const personalizedProfile = Object.assign({}, profile);
    if (personalizedProfile.message) {
        personalizedProfile.message = personalizedProfile.message
            .replace(/\{\{company\}\}/g, rowData.company || '')
            .replace(/\{\{rep_name\}\}/g, rowData.rep_name || '');
    }
    // Also expose company name as a fillable field from the row
    if (rowData.company) personalizedProfile.company = rowData.company;
    // Split name into sei (last) and mei (first) if space-separated
    if (personalizedProfile.name) {
        const parts = personalizedProfile.name.trim().split(/\s+/);
        personalizedProfile.name_sei = parts[0] || '';
        personalizedProfile.name_mei = parts.slice(1).join(' ') || '';
    }
    // Split kana same way
    if (personalizedProfile.kana) {
        const parts = personalizedProfile.kana.trim().split(/\s+/);
        personalizedProfile.kana_sei = parts[0] || '';
        personalizedProfile.kana_mei = parts.slice(1).join(' ') || '';
    }
    // Split phone number by hyphen (e.g. 090-1234-5678 → [090, 1234, 5678])
    if (personalizedProfile.phone) {
        const parts = personalizedProfile.phone.split('-');
        personalizedProfile.phone_1 = parts[0] || '';
        personalizedProfile.phone_2 = parts[1] || '';
        personalizedProfile.phone_3 = parts[2] || '';
    }
    // Split zipcode by hyphen (e.g. 675-0042 → [675, 0042])
    if (personalizedProfile.address) {
        // Extract zipcode from address if present (〒NNN-NNNN format)
        const zipMatch = personalizedProfile.address.match(/(\d{3})[-ー](\d{4})/);
        if (zipMatch) {
            personalizedProfile.zipcode = zipMatch[1] + '-' + zipMatch[2];
            personalizedProfile.zipcode_1 = zipMatch[1];
            personalizedProfile.zipcode_2 = zipMatch[2];
            
            // Remove the zipcode portion from the address field for cleaner input
            personalizedProfile.address = personalizedProfile.address.replace(/〒?\s*\d{3}[-ー]\d{4}\s*/, '').trim();
        }
    }
    // Use personalized profile for filling
    profile = personalizedProfile;

    try {
        console.log(`Navigating to ${url}...`);
        await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await page.waitForTimeout(2000); // Wait for scripts to settle

        const pageText = await page.evaluate(() => document.body.textContent || '');
        let ngKeywordFound = null;
        for (const kw of salesNGKeywords) {
            if (pageText.includes(kw)) {
                ngKeywordFound = kw;
                break;
            }
        }

        if (ngKeywordFound) {
            console.log(`[Sales NG] Found keyword: ${ngKeywordFound}. Skipping submission.`);
            return { status: '×', reason: `営業お断り記載あり（${ngKeywordFound}）` };
        }

        console.log('Analyzing form fields...');
        const fieldsData = await page.evaluate(() => {
            const inputs = Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="image"]), textarea, select'));
            return inputs.map(el => {
                let labelText = '';
                if (el.labels && el.labels.length > 0) labelText = el.labels[0].innerText || el.labels[0].textContent;
                if (!labelText && el.getAttribute('aria-label')) labelText = el.getAttribute('aria-label');
                if (!labelText && el.id) {
                    const label = document.querySelector(`label[for="${el.id}"]`);
                    if (label) labelText = label.innerText || label.textContent;
                }
                if (!labelText && el.getAttribute('placeholder')) labelText = el.getAttribute('placeholder');
                
                let parentForReq = el.closest('td, th, div, p, li, label, dd');
                if (!labelText && parentForReq) {
                    labelText = (parentForReq.innerText || parentForReq.textContent || '').substring(0, 100);
                }

                let isRequired = false;
                if (el.required || el.getAttribute('aria-required') === 'true' || el.hasAttribute('required')) {
                    isRequired = true;
                }
                const classString = (el.className || '') + (el.labels && el.labels.length > 0 ? ' ' + el.labels[0].className : '');
                if (classString.toLowerCase().includes('required') || classString.toLowerCase().includes('hissu')) {
                    isRequired = true;
                }
                if (!isRequired) {
                    const widerParent = el.closest('tr, li, dl, .form-group, .row') || parentForReq;
                    if (widerParent) {
                        const textContent = widerParent.innerText || widerParent.textContent || '';
                        if (textContent.includes('必須') || textContent.toLowerCase().includes('required')) {
                            isRequired = true;
                        }
                    }
                }

                function getXPath(element) {
                    if (element.id !== '') return 'id("' + element.id + '")';
                    if (element === document.body) return element.tagName;
                    let ix = 0;
                    const siblings = element.parentNode ? element.parentNode.childNodes : [];
                    for (let i = 0; i < siblings.length; i++) {
                        const sibling = siblings[i];
                        if (sibling === element) return getXPath(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) ix++;
                    }
                    return '';
                }

                return {
                    id: el.id,
                    name: el.getAttribute('name') || '',
                    type: el.type || el.tagName.toLowerCase(),
                    tagName: el.tagName.toLowerCase(),
                    labelText: (labelText || '').trim().replace(/\s+/g, ' '),
                    xpath: getXPath(el),
                    isRequired: isRequired
                };
            });
        });

        // Sort mapping entries by the length of their keywords descending
        // so that specific keys like "last-name" match before generic "name"
        const mappingEntries = Object.entries(mapping).sort((a, b) => {
            const maxLenA = Math.max(...a[1].map(k => k.length));
            const maxLenB = Math.max(...b[1].map(k => k.length));
            return maxLenB - maxLenA;
        });

        for (const field of fieldsData) {
            let matchedKey = null;
            const textToMatch = `${field.labelText} ${field.name}`.toLowerCase();

            if (field.type === 'checkbox' || field.type === 'radio') {
                const autoCheckTriggers = [
                    '同意', '規約', '確認', '個人情報', 'プライバシー', '契約', '合意'
                ];
                if (autoCheckTriggers.some(kw => textToMatch.includes(kw))) {
                    console.log(`[Auto-Check] ${field.labelText || field.name || 'Checkbox'}`);
                    try {
                        const sel = field.name ? `[name="${field.name}"]` : `xpath=${field.xpath}`;
                        await page.locator(sel).first().check({ timeout: 2000 });
                    } catch (e) {}
                    continue;
                }
            }

            outerLoop:
            for (const [key, keywords] of mappingEntries) {
                for (const keyword of keywords) {
                    // Check exact phrase or substring match
                    if (textToMatch.includes(keyword.toLowerCase())) {
                        matchedKey = key;
                        break outerLoop;
                    }
                }
            }

            if (matchedKey && profile[matchedKey] !== undefined) {
                // If a generic 'name', 'kana', 'phone', or 'zipcode' was matched, try to be smarter by looking at the input name/id
                if (matchedKey === 'name') {
                    if (field.name.match(/sei|last|1/i) || field.id.match(/sei|last|1/i)) matchedKey = 'name_sei';
                    else if (field.name.match(/mei|first|2/i) || field.id.match(/mei|first|2/i)) matchedKey = 'name_mei';
                } else if (matchedKey === 'kana') {
                    if (field.name.match(/sei|last|1/i) || field.id.match(/sei|last|1/i)) matchedKey = 'kana_sei';
                    else if (field.name.match(/mei|first|2/i) || field.id.match(/mei|first|2/i)) matchedKey = 'kana_mei';
                } else if (matchedKey === 'phone') {
                    if (field.name.match(/1|first/i) || field.id.match(/1|first/i)) matchedKey = 'phone_1';
                    else if (field.name.match(/2|mid/i) || field.id.match(/2|mid/i)) matchedKey = 'phone_2';
                    else if (field.name.match(/3|last/i) || field.id.match(/3|last/i)) matchedKey = 'phone_3';
                } else if (matchedKey === 'zipcode') {
                    if (field.name.match(/1|first/i) || field.id.match(/1|first/i)) matchedKey = 'zipcode_1';
                    else if (field.name.match(/2|last/i) || field.id.match(/2|last/i)) matchedKey = 'zipcode_2';
                }

                // Always fill message field even if optional.
                // All other non-required fields are skipped unless --all-fields is specified.
                const alwaysFillKeys = ['message'];
                if (!isAllFields && !field.isRequired && !alwaysFillKeys.includes(matchedKey) && !textToMatch.includes('同意')) {
                    console.log(`[Skip] "${field.labelText || field.name}" mapped to ${matchedKey} but is NOT required. Use --all-fields to override.`);
                    continue; 
                }

                console.log(`[Fill] "${field.labelText || field.name}" -> ${matchedKey} = "${String(profile[matchedKey]).substring(0,30)}"`);
                try {
                    // Prefer name-attribute selector over XPath (more reliable for CF7 / no-id forms)
                    const sel = field.name ? `[name="${field.name}"]` : `xpath=${field.xpath}`;
                    const locator = page.locator(sel).first();

                    if (field.tagName === 'select') {
                        // First try exact match from profile
                        let selected = false;
                        if (profile[matchedKey]) {
                            try {
                                await locator.selectOption({ label: profile[matchedKey] }, { timeout: 1000 });
                                selected = true;
                            } catch(e) {}
                        }
                        // If it's an inquiry type and no match, fallback to preferred generic options
                        if (!selected) {
                            const optionsText = await locator.evaluate(el => Array.from(el.options).map(o => o.text));
                            let prefs;
                            if (matchedKey === 'preferred_contact') {
                                // Always choose メール first
                                prefs = ['メール', 'メールでの応答', 'e-mail', 'email', 'メールアドレス'];
                            } else if (matchedKey === 'preferred_time') {
                                prefs = ['いつでも', '不問', '午前', '午後', '10時', '12時'];
                            } else {
                                // For inquiry_type: prefer partnership/proposal, avoid 営業
                                prefs = ['協業', '業務提携', '業務提携・協業', 'アライアンス', 'パートナー', '提案', 'ビジネス', '外部パートナー', 'その他', 'その他のお問い合わせ'];
                            }
                            for (const pref of prefs) {
                                const match = optionsText.find(opt => opt.includes(pref));
                                if (match) {
                                    // Skip options that contain 営業 (sales)
                                    if (match.includes('営業') && matchedKey !== 'preferred_contact') break;
                                    await locator.selectOption({ label: match }, { timeout: 1000 });
                                    console.log(`  -> Auto-selected option: ${match}`);
                                    selected = true;
                                    break;
                                }
                            }
                        }
                    } else if (field.type === 'radio') {
                        // If it's a radio, we need to find the specific radio button in the group that matches our preference
                        const radioGroup = page.locator(`input[type="radio"][name="${field.name}"]`);
                        const count = await radioGroup.count();
                        let clicked = false;
                        
                        // First try to match profile value
                        if (profile[matchedKey]) {
                            for (let i = 0; i < count; i++) {
                                const r = radioGroup.nth(i);
                                const val = await r.getAttribute('value') || '';
                                const id = await r.getAttribute('id');
                                let labelText = val;
                                if (id) {
                                    const lbl = await page.locator(`label[for="${id}"]`).textContent().catch(()=>'');
                                    if (lbl) labelText += ' ' + lbl;
                                }
                                if (labelText.includes(profile[matchedKey])) {
                                    await r.check({ timeout: 1000 });
                                    clicked = true;
                                    break;
                                }
                            }
                        }
                        
                        // Fallback to preferred options
                        if (!clicked) {
                            let prefs;
                            if (matchedKey === 'preferred_contact') {
                                prefs = ['メール', 'e-mail', 'email', 'メールアドレス', 'メールでの返信'];
                            } else if (matchedKey === 'preferred_time') {
                                prefs = ['いつでも', '不問', '午前', '午後', '10時', '12時'];
                            } else {
                                prefs = ['協業', '業務提携', 'アライアンス', 'パートナー', '提案', 'ビジネス', '外部パートナー', 'その他', 'その他のお問い合わせ'];
                            }
                            for (const pref of prefs) {
                                for (let i = 0; i < count; i++) {
                                    const r = radioGroup.nth(i);
                                    const val = await r.getAttribute('value') || '';
                                    const id = await r.getAttribute('id');
                                    let labelText = val;
                                    const parentText = await r.evaluate(el => el.closest('label')?.textContent || '');
                                    if (id) {
                                        const lbl = await page.locator(`label[for="${id}"]`).textContent().catch(()=>'');
                                        if (lbl) labelText += ' ' + lbl;
                                    }
                                    labelText += ' ' + parentText;
                                    
                                    if (labelText.includes(pref)) {
                                        await r.check({ timeout: 1000 });
                                        console.log(`  -> Auto-checked radio for: ${pref}`);
                                        clicked = true;
                                        break;
                                    }
                                }
                                if (clicked) break;
                            }
                        }

                    } else if (field.type !== 'checkbox') {
                        await locator.fill(String(profile[matchedKey]), { timeout: 3000 });
                    }
                } catch (e) {
                    console.log(`  -> Failed to fill: ${e.message.substring(0, 80)}`);
                }
            } else {
                if (field.name && !['submit','button','image','hidden','reset'].includes(field.type)) {
                    console.log(`[Unmatched] type:${field.type} name:"${field.name}" label:"${field.labelText}"`);
                }
            }
        }

        if (isDryRun) {
            console.log('Dry run: Skipping submission.');
            return { status: '未', reason: 'Dry run test mode' };
        } else {
            console.log('Submitting form...');
            const submitBtn = page.locator(
                'input[type="submit"], button:has-text("送信"), button:has-text("確認"), button[type="submit"], input[value*="送信"], input[value*="確認"]'
            ).first();

            if (await submitBtn.isVisible({ timeout: 3000 })) {
                await submitBtn.click();

                // --- CF7 AJAX: wait for the response-output div to change ---
                let successConfirmed = false;
                try {
                    // Wait up to 10s for CF7's response to appear
                    await page.waitForFunction(() => {
                        const el = document.querySelector('.wpcf7-response-output');
                        return el && el.textContent.trim().length > 0 && el.offsetParent !== null;
                    }, { timeout: 10000 });
                    const responseText = await page.locator('.wpcf7-response-output').textContent({ timeout: 3000 });
                    console.log(`CF7 response: ${responseText}`);
                    if (responseText.includes('ありがとう') || responseText.includes('送信されました') || responseText.includes('sent') || responseText.includes('thank')) {
                        successConfirmed = true;
                    }
                } catch (e) {
                    console.log(`No CF7 response div found, assuming page-transition form.`);
                }

                // Fallback: check for a second submit button (2-step confirmation page)
                if (!successConfirmed) {
                    await page.waitForTimeout(3000);
                    const finalSubmit = page.locator('input[type="submit"], button:has-text("送信"), button[type="submit"], input[value*="送信"]').first();
                    if (await finalSubmit.isVisible({ timeout: 2000 }).catch(() => false)) {
                        console.log('Clicking final submit button on confirmation page...');
                        await finalSubmit.click();
                        await page.waitForTimeout(4000);
                    }
                }

                // Scroll to bottom to capture the response message, then screenshot
                await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
                await page.waitForTimeout(500);
                const screenPath = path.join(__dirname, 'screenshots', `success_row_${idString}.png`);
                await page.screenshot({ path: screenPath, fullPage: false });
                console.log(`Screenshot saved to ${screenPath}`);

                if (successConfirmed) {
                    return { status: '〇', reason: '' };
                } else {
                    // Check if page shows an error
                    const pageContent = await page.evaluate(() => document.body.textContent);
                    if (pageContent.includes('エラー') || pageContent.includes('問題があります') || pageContent.includes('error')) {
                        return { status: '×', reason: 'バリデーションエラー' };
                    }
                    return { status: '〇', reason: '' };
                }
            } else {
                console.log('Submit button not found.');
                return { status: '×', reason: '送信ボタンが見つかりません' };
            }
        }

    } catch (e) {
        console.log(`Error processing ${url}: ${e.message}`);
        return { status: '×', reason: 'エラー: ' + e.message.substring(0, 30) };
    }
}

function readCSV(filePath) {
    return new Promise((resolve, reject) => {
        const results = [];
        fs.createReadStream(filePath)
          .pipe(csvParser())
          .on('data', (data) => results.push(data))
          .on('end', () => resolve(results))
          .on('error', (err) => reject(err));
    });
}

async function writeCSV(filePath, headersArray, records) {
    const csvWriter = createObjectCsvWriter({
        path: filePath,
        header: headersArray.map(h => ({id: h, title: h}))
    });
    await csvWriter.writeRecords(records);
}

// ===== Google Sheets API Helpers =====

async function getGoogleSheetsClient() {
    const credPath = path.join(__dirname, 'google_credentials.json');
    if (!fs.existsSync(credPath)) {
        console.error('[Sheets] google_credentials.json not found. See SHEETS_API_SETUP.md for setup instructions.');
        process.exit(1);
    }
    const credentials = JSON.parse(fs.readFileSync(credPath, 'utf-8'));
    const auth = new google.auth.GoogleAuth({
        credentials,
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
    });
    const sheets = google.sheets({ version: 'v4', auth });
    return sheets;
}

async function readSheet(sheets, spreadsheetId, sheetName) {
    const response = await sheets.spreadsheets.values.get({
        spreadsheetId,
        range: sheetName,
    });
    const values = response.data.values || [];
    if (values.length === 0) return { headers: [], rows: [] };
    
    const headers = values[0];
    const rows = values.slice(1);
    console.log(`[Sheets] Read ${rows.length} rows, ${headers.length} columns.`);
    return { headers, rows };
}

async function updateSheetRow(sheets, spreadsheetId, sheetName, rowNum, { statusCol, reasonCol, dateCol, status, reason, date }) {
    // Convert column index to A1 notation letter
    const colLetter = (idx) => {
        let result = '';
        idx += 1; // 1-based
        while (idx > 0) {
            result = String.fromCharCode(65 + ((idx - 1) % 26)) + result;
            idx = Math.floor((idx - 1) / 26);
        }
        return result;
    };

    const updates = [];
    if (statusCol >= 0) updates.push({ range: `${sheetName}!${colLetter(statusCol)}${rowNum}`, values: [[status]] });
    if (reasonCol >= 0) updates.push({ range: `${sheetName}!${colLetter(reasonCol)}${rowNum}`, values: [[reason]] });
    if (dateCol >= 0)   updates.push({ range: `${sheetName}!${colLetter(dateCol)}${rowNum}`, values: [[date]] });

    if (updates.length > 0) {
        await sheets.spreadsheets.values.batchUpdate({
            spreadsheetId,
            requestBody: {
                valueInputOption: 'USER_ENTERED',
                data: updates,
            },
        });
    }
}

main().catch(err => {
    console.error('Fatal error:', err);
    process.exit(1);
});
