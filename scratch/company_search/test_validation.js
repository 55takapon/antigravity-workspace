const { isValidCompanyName } = require('./crawler');

// 無効として除外されるべきパターン
const invalidTests = [
    '株式会社様を掲載しました',
    '株式会社との連携により',
    '求人会社',
    '株式会社おすすめ5選',
    '株式会社ランキング',
    '合同会社についてまとめ',
];

// 有効として通過すべきパターン
const validTests = [
    '株式会社テスト商事',
    '合同会社サンプル',
    'テスト株式会社',
    '株式会社HAKUHODO',
    '有限会社山田工務店',
];

console.log('=== 無効パターン（REJECTされるべき）===');
let allPass = true;
for (const t of invalidTests) {
    const result = isValidCompanyName(t);
    const ok = !result;
    if (!ok) allPass = false;
    console.log((ok ? '✅' : '❌') + ' ' + t + ' => ' + (result ? 'PASS(有効)' : 'REJECT(無効)'));
}

console.log('\n=== 有効パターン（PASSされるべき）===');
for (const t of validTests) {
    const result = isValidCompanyName(t);
    const ok = result;
    if (!ok) allPass = false;
    console.log((ok ? '✅' : '❌') + ' ' + t + ' => ' + (result ? 'PASS(有効)' : 'REJECT(無効)'));
}

console.log('\n' + (allPass ? '✅ 全テスト合格' : '❌ 一部テスト失敗'));
process.exit(allPass ? 0 : 1);
