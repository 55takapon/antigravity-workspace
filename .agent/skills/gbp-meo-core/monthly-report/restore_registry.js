const fs = require('fs');
const JUKU = String.fromCodePoint(0x587e);

const CLIENTS = [
  { slug: 'jetproduce', name: '\u30b8\u30a7\u30c3\u30c8\u30d7\u30ed\u30c7\u30e5\u30fc\u30b9', industry: '\u30a6\u30a7\u30d6\u30de\u30fc\u30b1\u30c6\u30a3\u30f3\u30b0', competitors: [
      { name: 'MARKESMILE\uff08\u52a0\u53e4\u5ddd\uff09', isSelf: false, fallbackReviewCount: 8,  fallbackRating: 4.9 },
      { name: '\u3046\u307f\u304c\u308f\uff08\u52a0\u53e4\u5ddd\uff09', isSelf: false, fallbackReviewCount: 3,  fallbackRating: 5.0 },
      { name: '\u30cf\u30b7\u30e2\u30c8\u30c7\u30b6\u30a4\u30f3\uff08\u52a0\u53e4\u5ddd\uff09', isSelf: false, fallbackReviewCount: 6,  fallbackRating: 4.8 },
  ] },
  { slug: 'eiwa-juku-south', name: '\u82f1\u548c'+JUKU, campus: '\u5357\u6821', industry: JUKU, competitors: [
      { name: '\u500b\u5225\u6307\u5c0e\u307e\u306a\u3073\u30d7\u30e9\u30b9 \u6771\u52a0\u53e4\u5ddd', isSelf: false, fallbackReviewCount: 22, fallbackRating: 4.7 },
      { name: '\u6559\u80b2\u7a7a\u9593\u30a8\u30b0\u30bc \u6771\u52a0\u53e4\u5ddd', isSelf: false, fallbackReviewCount: 15, fallbackRating: 5.0 },
      { name: '\u30a8\u30c7\u30a3\u30c3\u30af \u6771\u52a0\u53e4\u5ddd\u6821', isSelf: false, fallbackReviewCount: 6,  fallbackRating: 4.8 },
  ] },
  { slug: 'eiwa-juku-north', name: '\u82f1\u548c'+JUKU, campus: '\u5317\u6821', industry: JUKU, competitors: [
      { name: '\u500b\u5225\u6307\u5c0e\u307e\u306a\u3073\u30d7\u30e9\u30b9 \u6771\u52a0\u53e4\u5ddd', isSelf: false, fallbackReviewCount: 22, fallbackRating: 4.7 },
      { name: '\u6559\u80b2\u7a7a\u9593\u30a8\u30b0\u30bc \u6771\u52a0\u53e4\u5ddd', isSelf: false, fallbackReviewCount: 15, fallbackRating: 5.0 },
      { name: '\u30a8\u30c7\u30a3\u30c3\u30af \u6771\u52a0\u53e4\u5ddd\u6821', isSelf: false, fallbackReviewCount: 6,  fallbackRating: 4.8 },
  ] },
  { slug: 'pet-sitter', name: '\u30da\u30c3\u30c8\u30b7\u30c3\u30bf\u30fc \u306b\u3083\u3093\u307d\u3093', industry: '\u30b5\u30fc\u30d3\u30b9', competitors: [] },
  { slug: 'meat-shika', name: '\u533b\u7642\u6cd5\u4eba\u793e\u56e3 \u30df\u30fc\u30c8\u6b6f\u79d1', industry: '\u6b6f\u79d1', competitors: [] },
  { slug: 'kamada-shika', name: '\u304b\u307e\u3060\u6b6f\u79d1\u533b\u9662', industry: '\u6b6f\u79d1', competitors: [] },
  { slug: 'shibamoto-shihou', name: '\u829d\u672c\u53f8\u6cd5\u66f8\u58eb\u4e8b\u52d9\u6240', industry: '\u53f8\u6cd5\u66f8\u58eb', competitors: [] },
  { slug: 'sakakibara-zeirishi', name: '\u698a\u539f\u7a0e\u7406\u58eb\u4e8b\u52d9\u6240', industry: '\u7a0e\u7406\u58eb', competitors: [] },
  { slug: 'iam-i', name: '\u30a2\u30a4\u30a2\u30e0\u30a2\u30a4', industry: '\u30b5\u30fc\u30d3\u30b9', competitors: [] },
  { slug: 'michi', name: '\u307f\u3061', industry: '\u98f2\u98df', competitors: [] },
  { slug: 'koukenbi', name: '\u5e78\u5065\u7f8e\u6b6f\u79d1\u30af\u30ea\u30cb\u30c3\u30af', industry: '\u6b6f\u79d1', competitors: [] }
];

const lines = [];
lines.push('const CLIENTS = ' + JSON.stringify(CLIENTS, null, 2) + ';');
lines.push('const SHEET_URL = "https://docs.google.com/spreadsheets/d/1NNQItK0YcRDiM03YGuMSafbp-wk2WAeGTE7sFtn62pI/edit?usp=sharing";');
lines.push('module.exports = { CLIENTS, SHEET_URL };');

fs.writeFileSync('client_registry.js', lines.join('\n'), 'utf8');
console.log('Restored clients:', CLIENTS.map(c => c.name).join(', '));
