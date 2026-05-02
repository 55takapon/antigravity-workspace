const { google } = require('googleapis');
const path = require('path');
const CREDENTIALS_PATH = path.join(__dirname, '..', 'form_automation', 'google_credentials.json');

async function checkUnique() {
    const auth = new google.auth.GoogleAuth({ keyFile: CREDENTIALS_PATH, scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly'] });
    const sheets = google.sheets({ version: 'v4', auth });
    
    const books = {
        'Book1': '1kTO8ySjfmbIbHWWUUqUAKOAPVfxKV3djwpfSx8ccEWk',
        'Book2': '1tedNT_Sk-YdVjMv4Cn0R8TJGTkjqiOK_rm4SJkaAjIQ'
    };
    
    const uniqueDomains = new Set();
    const uniqueNames = new Set();
    let totalRaw = 0;
    
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
            
            // For Exclude list: Name is B(col 1), URL is D(col 3). For others: Name is C(col 2), URL is E(col 4)
            const isExclude = sheetName === '除外リスト';
            const nameCol = isExclude ? 1 : 2;
            const urlCol = isExclude ? 3 : 4;
            const maxCol = Math.max(nameCol, urlCol) + 1;
            const colRange = `A:${String.fromCharCode(65 + maxCol - 1)}`;
            
            try {
                const res = await sheets.spreadsheets.values.get({ spreadsheetId: bookId, range: `${sheetName}!${colRange}` });
                const rows = res.data.values || [];
                
                for (let i = 1; i < rows.length; i++) {
                    const name = (rows[i][nameCol] || '').trim();
                    const url = (rows[i][urlCol] || '').trim();
                    if (!name && !url) continue;
                    
                    totalRaw++;
                    const domain = normalizeDomain(url);
                    if (domain) uniqueDomains.add(domain);
                    if (name) uniqueNames.add(name.toLowerCase());
                }
            } catch(err) {
                console.error(`Error reading ${bookName}!${sheetName}`, err.message);
            }
        }
    }
    console.log(`Total raw rows: ${totalRaw}`);
    console.log(`Unique Domains: ${uniqueDomains.size}`);
    console.log(`Unique Names: ${uniqueNames.size}`);
}

checkUnique().catch(console.error);
