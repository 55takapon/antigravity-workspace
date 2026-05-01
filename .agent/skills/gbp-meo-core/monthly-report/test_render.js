// Minimal test: does renderHTML receive competitors?
const { renderHTML } = require('./render_html');

const reportData = {
  header: { clientName: '英和塾（南校）', industry: '学習塾', category: '' },
  month: 4,
  mainKPIs: {},
  reviews: { '口コミ総数（累計）': 1, '平均評価（★）': 5 },
  posts: { '当月投稿数': 2 },
  queries: [],
  competitors: [
    { name: '個別指導まなびプラス 東加古川', isSelf: false, reviewCount: 22, rating: 4.7 },
    { name: '教育空間エグゼ 東加古川',       isSelf: false, reviewCount: 15, rating: 5.0 },
    { name: 'エディック 東加古川校',          isSelf: false, reviewCount: 6,  rating: 4.8 },
    { name: '英和塾（南校）',                isSelf: true,  reviewCount: 1,  rating: 5   },
  ],
  actionLog: { actions: '', results: '' },
  recommendations: [],
  trendViews: [{ month: '1月', value: 190 }, { month: '2月', value: 280 }, { month: '3月', value: 310 }, { month: '4月', value: 243 }],
  trendReviews: [],
  targetReviewCount: 30,
  customMessage: '',
  prevPerformance: {},
  prevReviews: {},
};

const html = renderHTML(reportData);
const benchIdx = html.indexOf('ベンチマーク参考');
console.log('=== Benchmark section ===');
console.log(html.substring(benchIdx, benchIdx + 600));
