const fs = require('fs');
const crypto = require('crypto');

const SPREADSHEET_ID = '1hpKYD_DHreNBNzGKrjCHYU3rrkPTINcAaVOJKuC9IAY';
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const SHEET_NAME = '\u30b7\u30fc\u30c81';
const TARGET_START_ROW = 2;
const TARGET_END_ROW = 1812;
const ANCHOR_ROW = 1813;
const DRY_RUN = process.argv.includes('--dry-run');
const CORPORATE_WORDS = ['\u682a\u5f0f\u4f1a\u793e', '\u5408\u540c\u4f1a\u793e', '\u6709\u9650\u4f1a\u793e'];

function base64url(input) {
  return Buffer.from(input).toString('base64').replace(/=/g, '').replace(/\+/g, '-').replace(/\//g, '_');
}

async function getAccessToken() {
  const credentials = JSON.parse(fs.readFileSync(CREDENTIALS_PATH, 'utf8'));
  const now = Math.floor(Date.now() / 1000);
  const header = { alg: 'RS256', typ: 'JWT' };
  const claim = {
    iss: credentials.client_email,
    scope: 'https://www.googleapis.com/auth/spreadsheets',
    aud: 'https://oauth2.googleapis.com/token',
    exp: now + 3600,
    iat: now,
  };
  const signingInput = `${base64url(JSON.stringify(header))}.${base64url(JSON.stringify(claim))}`;
  const signature = crypto.sign('RSA-SHA256', Buffer.from(signingInput), credentials.private_key);
  const assertion = `${signingInput}.${base64url(signature)}`;
  const response = await fetch('https://oauth2.googleapis.com/token', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer',
      assertion,
    }),
  });
  const data = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(data));
  return data.access_token;
}

async function sheetsFetch(token, path, options = {}) {
  const response = await fetch(`https://sheets.googleapis.com/v4/spreadsheets/${SPREADSHEET_ID}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(data));
  return data;
}

function quoteSheetName(name) {
  return `'${name.replace(/'/g, "''")}'`;
}

function isTarget(row) {
  const company = (row[2] || '').trim();
  if (!company) return false;
  return !CORPORATE_WORDS.some((word) => company.includes(word));
}

async function main() {
  const token = await getAccessToken();
  const metadata = await sheetsFetch(token, '?fields=properties.title,sheets.properties');
  const sheet = metadata.sheets.find((entry) => entry.properties.title === SHEET_NAME);
  if (!sheet) throw new Error(`Sheet not found: ${SHEET_NAME}`);

  const sheetId = sheet.properties.sheetId;
  const columnCount = sheet.properties.gridProperties.columnCount || 29;
  const range = `${quoteSheetName(SHEET_NAME)}!A:AC`;
  const data = await sheetsFetch(token, `/values/${encodeURIComponent(range)}`);
  const values = data.values || [];
  const lastDataRow = values.length;
  const targetRows = [];
  const samples = [];

  for (let rowNumber = TARGET_START_ROW; rowNumber <= TARGET_END_ROW; rowNumber += 1) {
    const row = values[rowNumber - 1] || [];
    if (isTarget(row)) {
      targetRows.push(rowNumber);
      if (samples.length < 30) {
        samples.push({
          row: rowNumber,
          area: row[1] || '',
          company: row[2] || '',
          url: row[4] || '',
        });
      }
    }
  }

  const targetsAboveAnchor = targetRows.filter((rowNumber) => rowNumber < ANCHOR_ROW).length;
  const finalBlockStart = ANCHOR_ROW - targetsAboveAnchor;
  const finalBlockEnd = finalBlockStart + targetRows.length - 1;

  if (DRY_RUN) {
    console.log(JSON.stringify({
      mode: 'dry-run',
      spreadsheetTitle: metadata.properties.title,
      sheet: SHEET_NAME,
      lastDataRow,
      targetRange: `${TARGET_START_ROW}-${TARGET_END_ROW}`,
      anchorRow: ANCHOR_ROW,
      targetRows: targetRows.length,
      finalBlockStart,
      finalBlockEnd,
      firstTargetRows: targetRows.slice(0, 20),
      lastTargetRows: targetRows.slice(-20),
      samples,
    }, null, 2));
    return;
  }

  if (targetRows.length === 0) {
    console.log(JSON.stringify({ mode: 'applied', movedRows: 0 }, null, 2));
    return;
  }

  const requests = [];
  const insertStartIndex = ANCHOR_ROW - 1;
  const insertEndIndex = insertStartIndex + targetRows.length;

  requests.push({
    insertDimension: {
      range: {
        sheetId,
        dimension: 'ROWS',
        startIndex: insertStartIndex,
        endIndex: insertEndIndex,
      },
      inheritFromBefore: true,
    },
  });

  targetRows.forEach((rowNumber, index) => {
    const sourceRowAfterInsert = rowNumber >= ANCHOR_ROW ? rowNumber + targetRows.length : rowNumber;
    const destinationStartIndex = insertStartIndex + index;
    requests.push({
      copyPaste: {
        source: {
          sheetId,
          startRowIndex: sourceRowAfterInsert - 1,
          endRowIndex: sourceRowAfterInsert,
          startColumnIndex: 0,
          endColumnIndex: columnCount,
        },
        destination: {
          sheetId,
          startRowIndex: destinationStartIndex,
          endRowIndex: destinationStartIndex + 1,
          startColumnIndex: 0,
          endColumnIndex: columnCount,
        },
        pasteType: 'PASTE_NORMAL',
      },
    });
  });

  targetRows
    .map((rowNumber) => rowNumber >= ANCHOR_ROW ? rowNumber + targetRows.length : rowNumber)
    .sort((a, b) => b - a)
    .forEach((rowNumber) => {
      requests.push({
        deleteDimension: {
          range: {
            sheetId,
            dimension: 'ROWS',
            startIndex: rowNumber - 1,
            endIndex: rowNumber,
          },
        },
      });
    });

  await sheetsFetch(token, ':batchUpdate', {
    method: 'POST',
    body: JSON.stringify({ requests }),
  });

  const verify = await sheetsFetch(token, `/values/${encodeURIComponent(range)}`);
  const verifyValues = verify.values || [];
  const targetOutsideBlock = [];
  const nonTargetInsideBlock = [];
  verifyValues.forEach((row, index) => {
    const rowNumber = index + 1;
    const inBlock = rowNumber >= finalBlockStart && rowNumber <= finalBlockEnd;
    const target = isTarget(row);
    if (rowNumber >= 2 && rowNumber < finalBlockStart && target) targetOutsideBlock.push(rowNumber);
    if (inBlock && !target) nonTargetInsideBlock.push(rowNumber);
  });

  console.log(JSON.stringify({
    mode: 'applied',
    movedRows: targetRows.length,
    lastDataRowBefore: lastDataRow,
    lastDataRowAfter: verifyValues.length,
    movedBlockStartRow: finalBlockStart,
    movedBlockEndRow: finalBlockEnd,
    targetOutsideBlockCount: targetOutsideBlock.length,
    targetOutsideBlock: targetOutsideBlock.slice(0, 20),
    nonTargetInsideBlockCount: nonTargetInsideBlock.length,
    nonTargetInsideBlock: nonTargetInsideBlock.slice(0, 20),
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
