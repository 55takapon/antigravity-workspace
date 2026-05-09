# 構造化データ（JSON-LD）サンプルコード集

> `site-seo-launch` SKILL.md STEP 3 の詳細資料

---

## 司法書士事務所（LegalService）

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "LegalService",
  "name": "柴本司法書士事務所",
  "description": "加古川市の司法書士事務所。相続登記・遺言・会社設立・債務整理を専門とする。",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "〇〇町△△番地",
    "addressLocality": "加古川市",
    "addressRegion": "兵庫県",
    "postalCode": "675-XXXX",
    "addressCountry": "JP"
  },
  "telephone": "079-XXX-XXXX",
  "openingHours": "Mo-Fr 09:00-18:00",
  "url": "https://example.com",
  "image": "https://example.com/images/logo.png",
  "areaServed": [
    { "@type": "City", "name": "加古川市" },
    { "@type": "City", "name": "姫路市" },
    { "@type": "City", "name": "明石市" }
  ],
  "sameAs": [
    "https://www.instagram.com/xxxxx/",
    "https://line.me/R/ti/p/@xxxxx",
    "https://www.google.com/maps/place/xxxxx"
  ],
  "founder": {
    "@type": "Person",
    "name": "柴本 太郎",
    "jobTitle": "司法書士",
    "description": "司法書士登録番号 第XXXX号。兵庫県司法書士会所属。"
  }
}
</script>
```

---

## 税理士事務所（AccountingService）

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "AccountingService",
  "name": "{事務所名}",
  "description": "{地域名}の税理士事務所。{主要サービス}。",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "{住所}",
    "addressLocality": "{市区町村}",
    "addressRegion": "{都道府県}",
    "postalCode": "{郵便番号}",
    "addressCountry": "JP"
  },
  "telephone": "{電話番号}",
  "openingHours": "Mo-Fr 09:00-17:30",
  "url": "{サイトURL}",
  "image": "{ロゴURL}",
  "areaServed": { "@type": "City", "name": "{市区町村}" },
  "sameAs": []
}
</script>
```

---

## FAQPage スキーマ（Q&Aページ用）

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "相続登記は義務ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。2024年4月1日より相続登記が義務化されました。相続を知った日から3年以内に登記申請が必要です。"
      }
    },
    {
      "@type": "Question",
      "name": "初回相談は無料ですか？",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "はい。当事務所では初回のご相談を無料で承っております。お電話またはお問い合わせフォームからご連絡ください。"
      }
    }
  ]
}
</script>
```

---

## 確認方法

設置後、以下のツールでエラーがないか必ず確認する：
- [Google リッチリザルトテスト](https://search.google.com/test/rich-results)
- [Schema.org バリデーター](https://validator.schema.org/)
