const { google } = require('googleapis');
const fs = require('fs');
const path = require('path');

const CREDENTIALS_PATH = path.join(__dirname, '..', 'form_automation', 'google_credentials.json');

async function exportLightweightList() {
    const auth = new google.auth.GoogleAuth({ keyFile: CREDENTIALS_PATH, scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'] });
    const sheets = google.sheets({ version: 'v4', auth });
    
    const books = {
        'Book1': '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk',
        'Book2': '1tedNT_Sk-YdVjMv4Cn0R8TJGTkjqiOK_rm4SJkaAjIQ'
    };
    
    const uniqueDomains = new Set();
    
    const normalizeDomain = (url) => {
        if (!url) return '';
        try {
            const u = new URL(url.startsWith('http') ? url : 'http://' + url);
            let host = u.hostname.toLowerCase();
            if (host.startsWith('www.')) host = host.substring(4);
            return host;
        } catch(e) { return url.toLowerCase(); }
    };
    
    for (const [bookName, bookId] of Object.entries(books)) {
        const spreadsheet = await sheets.spreadsheets.get({ spreadsheetId: bookId });
        const sheetNames = spreadsheet.data.sheets.map(s => s.properties.title);
        
        for (const sheetName of sheetNames) {
            if (['260325test', 'list-format', 'フォーマット'].includes(sheetName)) continue;
            
            const isExclude = sheetName === '除外リスト';
            const nameCol = isExclude ? 1 : 2;
            const urlCol = isExclude ? 3 : 4;
            const maxCol = Math.max(nameCol, urlCol) + 1;
            const colRange = `A:${String.fromCharCode(65 + maxCol - 1)}`;
            
            try {
                const res = await sheets.spreadsheets.values.get({ spreadsheetId: bookId, range: `${sheetName}!${colRange}` });
                const rows = res.data.values || [];
                for (let i = 1; i < rows.length; i++) {
                    const url = (rows[i][urlCol] || '').trim();
                    const domain = normalizeDomain(url);
                    if (domain) uniqueDomains.add(domain);
                }
            } catch(err) {
                // Ignore empty sheets or read errors
            }
        }
    }
    
    const outPath = path.join(__dirname, 'exclude_domains.txt');
    fs.writeFileSync(outPath, Array.from(uniqueDomains).sort().join('\n'), 'utf8');
    console.log(`Exported ${uniqueDomains.size} domains to ${outPath}`);
}

exportLightweightList().catch(console.error);
