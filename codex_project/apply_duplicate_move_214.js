const fs = require('fs');
const crypto = require('crypto');

const SPREADSHEET_ID = '1hpKYD_DHreNBNzGKrjCHYU3rrkPTINcAaVOJKuC9IAY';
const CREDENTIALS_PATH = 'C:/Users/hangy/.gemini/antigravity/scratch/form_automation/google_credentials.json';
const SOURCE_SHEET_NAME = '\u30b7\u30fc\u30c81';
const DUPLICATE_SHEET_NAME = '\u91cd\u8907\u5206';
const DRY_RUN = process.argv.includes('--dry-run');

const duplicateRows = [
  6, 8, 9, 10, 37, 42, 58, 81, 83, 86, 98, 128, 133, 135, 142, 170, 174, 175,
  181, 188, 303, 320, 376, 383, 395, 397, 408, 410, 416, 418, 419, 435, 445,
  447, 449, 459, 470, 583, 607, 608, 620, 644, 649, 705, 711, 715, 752, 762,
  766, 769, 770, 783, 791, 817, 861, 863, 871, 891, 897, 900, 902, 916, 932,
  983, 1025, 1063, 1078, 1082, 1083, 1086, 1091, 1094, 1100, 1114, 1119, 1127,
  1150, 1156, 1163, 1164, 1170, 1177, 1222, 1236, 1241, 1284, 1298, 1322, 1330,
  1332, 1341, 1353, 1355, 1356, 1411, 1422, 1437, 1438, 1448, 1459, 1485, 1508,
  1515, 1528, 1596, 1598, 1609, 1632, 1722, 1756, 1791, 1847, 1852, 1927, 1928,
  2010, 2041, 2065, 2072, 2099, 2100, 2141, 2155, 2190, 2206, 2226, 2248, 2297,
  2356, 2359, 2370, 2373, 2439, 2524, 2543, 2546, 2580, 2581, 2584, 2587, 2611,
  2678, 2688, 2742, 2764, 2768, 2773, 2776, 2793, 2805, 2817, 2827, 2832, 2837,
  2838, 2845, 2872, 2893, 2907, 2908, 2919, 2920, 2941, 2944, 2960, 2975, 2981,
  2994, 3009, 3041, 3051, 3055, 3058, 3066, 3127, 3132, 3144, 3155, 3157, 3166,
  3176, 3183, 3200, 3221, 3223, 3231, 3236, 3246, 3275, 3289, 3296, 3301, 3310,
  3399, 3411, 3442, 3472, 3524, 3542, 3645, 3711, 3721, 3778, 3781, 3783, 3797,
  3801, 3809, 3815, 3961, 3968, 4128, 4380, 4397
];

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

async function getMetadata(token) {
  return sheetsFetch(token, '?fields=properties.title,sheets.properties');
}

async function getDataLastRow(token, sheetName) {
  const data = await sheetsFetch(token, `/values/${encodeURIComponent(`${quoteSheetName(sheetName)}!A:AC`)}`);
  return data.values ? data.values.length : 0;
}

async function main() {
  if (new Set(duplicateRows).size !== duplicateRows.length) {
    throw new Error('duplicateRows contains duplicate row numbers.');
  }

  const token = await getAccessToken();
  let metadata = await getMetadata(token);
  const source = metadata.sheets.find((sheet) => sheet.properties.title === SOURCE_SHEET_NAME);
  if (!source) throw new Error(`Source sheet not found: ${SOURCE_SHEET_NAME}`);

  let duplicate = metadata.sheets.find((sheet) => sheet.properties.title === DUPLICATE_SHEET_NAME);
  const sourceRows = source.properties.gridProperties.rowCount || 0;
  const sourceColumns = source.properties.gridProperties.columnCount || 0;
  const maxTargetRow = Math.max(...duplicateRows);
  if (maxTargetRow > sourceRows) {
    throw new Error(`Max duplicate row ${maxTargetRow} exceeds source row count ${sourceRows}.`);
  }

  const sourceDataLastRow = await getDataLastRow(token, SOURCE_SHEET_NAME);
  const duplicateDataLastRow = duplicate ? await getDataLastRow(token, DUPLICATE_SHEET_NAME) : 0;

  if (DRY_RUN) {
    console.log(JSON.stringify({
      mode: 'dry-run',
      spreadsheetTitle: metadata.properties.title,
      sourceSheet: SOURCE_SHEET_NAME,
      sourceSheetId: source.properties.sheetId,
      sourceGridRows: sourceRows,
      sourceDataLastRow,
      sourceColumns,
      duplicateSheet: DUPLICATE_SHEET_NAME,
      duplicateExists: Boolean(duplicate),
      duplicateDataLastRow,
      rowsToMove: duplicateRows.length,
      firstRows: duplicateRows.slice(0, 10),
      lastRows: duplicateRows.slice(-10),
    }, null, 2));
    return;
  }

  const requests = [];
  if (!duplicate) {
    requests.push({
      addSheet: {
        properties: {
          title: DUPLICATE_SHEET_NAME,
          gridProperties: { rowCount: Math.max(1000, duplicateRows.length + 1), columnCount: sourceColumns },
        },
      },
    });
    await sheetsFetch(token, ':batchUpdate', {
      method: 'POST',
      body: JSON.stringify({ requests }),
    });
    metadata = await getMetadata(token);
    duplicate = metadata.sheets.find((sheet) => sheet.properties.title === DUPLICATE_SHEET_NAME);
    if (!duplicate) throw new Error(`Failed to create duplicate sheet: ${DUPLICATE_SHEET_NAME}`);
    requests.length = 0;
  }

  const duplicateSheetId = duplicate.properties.sheetId;
  let nextDestinationRow = await getDataLastRow(token, DUPLICATE_SHEET_NAME);
  const requiredDuplicateRows = Math.max(1, nextDestinationRow) + duplicateRows.length;
  const duplicateGridRows = duplicate.properties.gridProperties.rowCount || 0;
  if (duplicateGridRows < requiredDuplicateRows) {
    requests.push({
      updateSheetProperties: {
        properties: {
          sheetId: duplicateSheetId,
          gridProperties: { rowCount: requiredDuplicateRows },
        },
        fields: 'gridProperties.rowCount',
      },
    });
  }

  if (nextDestinationRow === 0) {
    requests.push({
      copyPaste: {
        source: { sheetId: source.properties.sheetId, startRowIndex: 0, endRowIndex: 1 },
        destination: { sheetId: duplicateSheetId, startRowIndex: 0, endRowIndex: 1 },
        pasteType: 'PASTE_NORMAL',
      },
    });
    nextDestinationRow = 1;
  }

  duplicateRows.slice().sort((a, b) => a - b).forEach((rowNumber, index) => {
    const destinationRow = nextDestinationRow + index;
    requests.push({
      copyPaste: {
        source: {
          sheetId: source.properties.sheetId,
          startRowIndex: rowNumber - 1,
          endRowIndex: rowNumber,
        },
        destination: {
          sheetId: duplicateSheetId,
          startRowIndex: destinationRow,
          endRowIndex: destinationRow + 1,
        },
        pasteType: 'PASTE_NORMAL',
      },
    });
  });

  duplicateRows.slice().sort((a, b) => b - a).forEach((rowNumber) => {
    requests.push({
      deleteDimension: {
        range: {
          sheetId: source.properties.sheetId,
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

  const afterMetadata = await getMetadata(token);
  const afterSourceLastRow = await getDataLastRow(token, SOURCE_SHEET_NAME);
  const afterDuplicateLastRow = await getDataLastRow(token, DUPLICATE_SHEET_NAME);
  console.log(JSON.stringify({
    mode: 'applied',
    spreadsheetTitle: afterMetadata.properties.title,
    movedRows: duplicateRows.length,
    sourceDataLastRowBefore: sourceDataLastRow,
    sourceDataLastRowAfter: afterSourceLastRow,
    duplicateDataLastRowBefore: duplicateDataLastRow,
    duplicateDataLastRowAfter: afterDuplicateLastRow,
  }, null, 2));
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
