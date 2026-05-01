// Rewrite client_registry.js with industry field
const fs = require('fs');

const JETPRODUCE_NAME = '\u30b8\u30a7\u30c3\u30c8\u30d7\u30ed\u30c7\u30e5\u30fc\u30b9';
const EIWA_NAME       = '\u82f1\u548c\u587e';
const SOUTH           = '\u5357\u6821';
const NORTH           = '\u5317\u6821';

const MARKESMILE      = 'MARKESMILE\uff08\u52a0\u53e4\u5ddd\uff09';
const UMIGAWA         = '\u3046\u307f\u304c\u308f\uff08\u52a0\u53e4\u5ddd\uff09';
const HASHIMOTO       = '\u30cf\u30b7\u30e2\u30c8\u30c7\u30b6\u30a4\u30f3\uff08\u52a0\u53e4\u5ddd\uff09';

const MANABI          = '\u500b\u5225\u6307\u5c0e\u307e\u306a\u3073\u30d7\u30e9\u30b9 \u6771\u52a0\u53e4\u5ddd';
const EGZE            = '\u6559\u80b2\u7a7a\u9593\u30a8\u30b0\u30bc \u6771\u52a0\u53e4\u5ddd';
const EDIC            = '\u30a8\u30c7\u30a3\u30c3\u30af \u6771\u52a0\u53e4\u5ddd\u6821';

const SHEET_URL = 'https://docs.google.com/spreadsheets/d/1NNQItK0YcRDiM03YGuMSafbp-wk2WAeGTE7sFtn62pI/edit?usp=sharing';

const data = {
  CLIENTS: [
    {
      slug: 'jetproduce',
      name: JETPRODUCE_NAME,
      industry: '\u30a6\u30a7\u30d6\u30de\u30fc\u30b1\u30c6\u30a3\u30f3\u30b0',
      competitors: [
        { name: MARKESMILE, isSelf: false, fallbackReviewCount: 8,  fallbackRating: 4.9 },
        { name: UMIGAWA,    isSelf: false, fallbackReviewCount: 3,  fallbackRating: 5.0 },
        { name: HASHIMOTO,  isSelf: false, fallbackReviewCount: 6,  fallbackRating: 4.8 },
      ],
    },
    {
      slug: 'eiwa-juku-south',
      name: EIWA_NAME,
      campus: SOUTH,
      industry: '\u5869',
      competitors: [
        { name: MANABI, isSelf: false, fallbackReviewCount: 22, fallbackRating: 4.7 },
        { name: EGZE,   isSelf: false, fallbackReviewCount: 15, fallbackRating: 5.0 },
        { name: EDIC,   isSelf: false, fallbackReviewCount: 6,  fallbackRating: 4.8 },
      ],
    },
    {
      slug: 'eiwa-juku-north',
      name: EIWA_NAME,
      campus: NORTH,
      industry: '\u5869',
      competitors: [
        { name: MANABI, isSelf: false, fallbackReviewCount: 22, fallbackRating: 4.7 },
        { name: EGZE,   isSelf: false, fallbackReviewCount: 15, fallbackRating: 5.0 },
        { name: EDIC,   isSelf: false, fallbackReviewCount: 6,  fallbackRating: 4.8 },
      ],
    },
  ],
  SHEET_URL,
};

// Verify data
data.CLIENTS.forEach(c => {
  console.log(c.slug, '|', c.name, c.campus||'', '|', c.industry);
  c.competitors.forEach(comp => console.log('  -', comp.name));
});
