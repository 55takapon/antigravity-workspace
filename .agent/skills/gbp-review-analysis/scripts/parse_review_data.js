/**
 * parse_review_data.js
 * 複数形式の口コミデータを統一フォーマットに変換するパーサー
 * 
 * Usage:
 *   node parse_review_data.js --input "path/to/file" --format txt|json|consolidated
 *   node parse_review_data.js --input "path/to/file.txt" --format txt --name "bomnal_chicken"
 * 
 * 統一出力フォーマット:
 *   {
 *     "businessName": "ビジネス名",
 *     "collectedAt": "2026-05-04T05:30:00+09:00",
 *     "totalCount": 38,
 *     "reviews": [
 *       { "name": "投稿者", "rating": 5, "date": "1か月前", "text": "...", "hasOwnerReply": false, "ownerReplyText": "" }
 *     ]
 *   }
 */

const fs = require('fs');
const path = require('path');

// === JST日付生成 ===
function getJSTDateStr() {
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return jst.toISOString().slice(0, 10).replace(/-/g, '');
}

function getJSTISOString() {
  const now = new Date();
  const jst = new Date(now.getTime() + 9 * 60 * 60 * 1000);
  return jst.toISOString().replace('Z', '+09:00');
}

// === テキストファイルパーサー（区切り線区切り形式） ===
function parseTxtFormat(content) {
  const sep = '-'.repeat(50);
  const rawBlocks = content.split(sep).filter(b => b.trim());
  const reviews = [];

  for (const block of rawBlocks) {
    const lines = block.trim().split('\n').map(l => l.replace(/\r$/, ''));
    if (lines.length < 2) continue;

    const name = lines[0].trim();
    const ratingDateLine = lines[1].trim();

    // "5 stars - 1 か月前" or "5 stars - 最終編集: 2 年前"
    let rating = 0;
    let date = 'Unknown';
    const match = ratingDateLine.match(/^(\d)\s*stars?\s*-\s*(.+)$/i);
    if (match) {
      rating = parseInt(match[1], 10);
      date = match[2].trim();
    }

    // 3行目以降がテキスト
    const fullText = lines.slice(2).join('\n').trim();

    // オーナー返信を分離
    let text = fullText;
    let hasOwnerReply = false;
    let ownerReplyText = '';

    const replyMarker = 'オーナーからの返信:';
    const replyIdx = fullText.indexOf(replyMarker);
    if (replyIdx !== -1) {
      text = fullText.substring(0, replyIdx).trim();
      ownerReplyText = fullText.substring(replyIdx + replyMarker.length).trim();
      hasOwnerReply = true;
    }

    if (text) {
      reviews.push({ name, rating, date, text, hasOwnerReply, ownerReplyText });
    }
  }

  return reviews;
}

// === consolidated JSON形式パーサー ===
function parseConsolidatedFormat(content) {
  const data = JSON.parse(content);
  const allReviews = [];

  // { "bomnal_chicken": [...], "izakaya_iami": [...], "total_count": N } 形式
  for (const [key, value] of Object.entries(data)) {
    if (key === 'total_count' || !Array.isArray(value)) continue;

    for (const r of value) {
      let rating = 0;
      if (typeof r.rating === 'string') {
        const m = r.rating.match(/(\d)/);
        if (m) rating = parseInt(m[1], 10);
      } else if (typeof r.rating === 'number') {
        rating = r.rating;
      }

      // オーナー返信を分離
      let text = (r.text || '').trim();
      let hasOwnerReply = false;
      let ownerReplyText = '';

      const replyMarker = 'オーナーからの返信:';
      const replyIdx = text.indexOf(replyMarker);
      if (replyIdx !== -1) {
        ownerReplyText = text.substring(replyIdx + replyMarker.length).trim();
        text = text.substring(0, replyIdx).trim();
        hasOwnerReply = true;
      }

      allReviews.push({
        name: (r.name || 'Unknown').trim(),
        rating,
        date: (r.date || 'Unknown').trim(),
        text,
        hasOwnerReply,
        ownerReplyText
      });
    }
  }

  return allReviews;
}

// === 標準JSONパーサー（scrape_reviews.js出力） ===
function parseStandardJson(content) {
  const data = JSON.parse(content);
  const reviews = Array.isArray(data) ? data : (data.reviews || []);

  return reviews.map(r => ({
    name: (r.name || 'Unknown').trim(),
    rating: typeof r.rating === 'number' ? r.rating : parseInt((r.rating || '0').match(/\d/)?.[0] || '0', 10),
    date: (r.date || 'Unknown').trim(),
    text: (r.text || '').trim(),
    hasOwnerReply: r.hasOwnerReply || false,
    ownerReplyText: (r.ownerReplyText || '').trim()
  })).filter(r => r.text);
}

// === メイン処理 ===
function main() {
  const args = process.argv.slice(2);
  const inputIdx = args.indexOf('--input');
  const formatIdx = args.indexOf('--format');
  const nameIdx = args.indexOf('--name');

  if (inputIdx === -1) {
    console.error('Usage: node parse_review_data.js --input <file> [--format txt|json|consolidated] [--name <business_name>]');
    process.exit(1);
  }

  const inputPath = args[inputIdx + 1];
  const format = formatIdx !== -1 ? args[formatIdx + 1] : 'auto';
  const businessName = nameIdx !== -1 ? args[nameIdx + 1] : path.basename(inputPath, path.extname(inputPath));

  if (!fs.existsSync(inputPath)) {
    console.error(`File not found: ${inputPath}`);
    process.exit(1);
  }

  const content = fs.readFileSync(inputPath, 'utf-8');

  // 形式の自動判定
  let detectedFormat = format;
  if (format === 'auto') {
    if (inputPath.endsWith('.txt')) {
      detectedFormat = 'txt';
    } else if (inputPath.endsWith('.json')) {
      try {
        const parsed = JSON.parse(content);
        if (parsed.total_count !== undefined) {
          detectedFormat = 'consolidated';
        } else {
          detectedFormat = 'json';
        }
      } catch {
        detectedFormat = 'txt';
      }
    }
  }

  console.log(`Parsing ${inputPath} as ${detectedFormat} format...`);

  let reviews;
  switch (detectedFormat) {
    case 'txt':
      reviews = parseTxtFormat(content);
      break;
    case 'consolidated':
      reviews = parseConsolidatedFormat(content);
      break;
    case 'json':
    default:
      reviews = parseStandardJson(content);
      break;
  }

  const output = {
    businessName,
    collectedAt: getJSTISOString(),
    totalCount: reviews.length,
    reviews
  };

  const dateStr = getJSTDateStr();
  const outputName = `review_data_${businessName}_${dateStr}.json`;
  const outputPath = path.join(__dirname, '..', outputName);

  fs.writeFileSync(outputPath, JSON.stringify(output, null, 2), 'utf-8');
  console.log(`✅ Parsed ${reviews.length} reviews → ${outputPath}`);

  return output;
}

// CLI実行 or モジュールとして読み込み
if (require.main === module) {
  main();
}

module.exports = { parseTxtFormat, parseConsolidatedFormat, parseStandardJson };
