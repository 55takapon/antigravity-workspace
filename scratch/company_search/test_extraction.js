function extractCleanSentence(s, pattern) {
    const match = s.match(pattern);
    if (!match) return s;
    
    let startIdx = match.index;
    let endIdx = match.index + match[0].length;
    
    // 左側境界：空白、タブ、改行、スラッシュ、パイプ。
    let leftBoundary = 0;
    for (let i = startIdx - 1; i >= 0; i--) {
        if (/[ 　\t\n\/／|｜]/.test(s[i])) {
            leftBoundary = i + 1;
            break;
        }
        if (s[i] === '※' || s[i] === '▼' || s[i] === '■' || s[i] === '・' || s[i] === '【') {
            leftBoundary = i; // 記号を含める
            break;
        }
    }
    
    // 右側境界：句点は含める。空白などはそこで切る。
    let rightBoundary = s.length;
    for (let i = endIdx; i < s.length; i++) {
        if (/[。！？]/.test(s[i])) {
            rightBoundary = i + 1;
            break;
        }
        if (/[ 　\t\n\/／|｜]/.test(s[i])) {
            // 例外: 直前がコンマや読点の場合はスペースで切らない（英語や箇条書き対策）
            // が、シンプルにここで切る
            rightBoundary = i;
            break;
        }
    }
    
    let clean = s.substring(leftBoundary, rightBoundary).trim();
    if (clean.length < 5) return s.trim();
    return clean;
}

const cases = [
    {
        text: "トお申込 無償テスト申込 ダウンロード お問い合わせ 03-6280-4915 お問い合わせ ホーム お問い合わせ ※当社への売り込み、営業内容のお問い合わせはお断りしています。 お名前必須 会社名必須 部署名必須 役職名任意",
        pattern: /売り込み/
    },
    {
        text: "株式会社スタジオスピーク お問い合わせ 営業メールはお断りいたします。新サービスのご提案も一切受け付けておりません。 当社に関するお問い合わせなどをお受けしています。 すべての項 /",
        pattern: /営業(?:メール|電話|目的|関連|関係)/
    }
];

cases.forEach(c => {
    console.log("-------------------");
    console.log("Target:", c.text);
    console.log("Extracted:", extractCleanSentence(c.text, c.pattern));
});
