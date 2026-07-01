const CLIENTS = [
  {
    "slug": "jetproduce",
    "name": "ジェットプロデュース",
    "industry": "ウェブマーケティング",
    "competitors": [
      {
        "name": "MARKESMILE（加古川）",
        "isSelf": false,
        "fallbackReviewCount": 8,
        "fallbackRating": 4.9
      },
      {
        "name": "うみがわ（加古川）",
        "isSelf": false,
        "fallbackReviewCount": 3,
        "fallbackRating": 5
      },
      {
        "name": "ハシモトデザイン（加古川）",
        "isSelf": false,
        "fallbackReviewCount": 6,
        "fallbackRating": 4.8
      }
    ]
  },
  {
    "slug": "eiwa-juku-south",
    "name": "英和塾",
    "campus": "南校",
    "industry": "塾",
    "competitors": [
      {
        "name": "個別指導まなびプラス 東加古川",
        "isSelf": false,
        "fallbackReviewCount": 22,
        "fallbackRating": 4.7
      },
      {
        "name": "教育空間エグゼ 東加古川",
        "isSelf": false,
        "fallbackReviewCount": 15,
        "fallbackRating": 5
      },
      {
        "name": "エディック 東加古川校",
        "isSelf": false,
        "fallbackReviewCount": 6,
        "fallbackRating": 4.8
      }
    ]
  },
  {
    "slug": "eiwa-juku-north",
    "name": "英和塾",
    "campus": "北校",
    "industry": "塾",
    "competitors": [
      {
        "name": "個別指導まなびプラス 東加古川",
        "isSelf": false,
        "fallbackReviewCount": 22,
        "fallbackRating": 4.7
      },
      {
        "name": "教育空間エグゼ 東加古川",
        "isSelf": false,
        "fallbackReviewCount": 15,
        "fallbackRating": 5
      },
      {
        "name": "エディック 東加古川校",
        "isSelf": false,
        "fallbackReviewCount": 6,
        "fallbackRating": 4.8
      }
    ]
  },
  {
    "slug": "pet-sitter",
    "name": "ペットシッターにゃんぽん",
    "industry": "サービス",
    "competitors": [
      {
        "name": "Mermaid",
        "isSelf": false,
        "fallbackReviewCount": 44,
        "fallbackRating": 5
      },
      {
        "name": "【犬猫専門】ペットシッターズ東京ベイ",
        "isSelf": false,
        "fallbackReviewCount": 35,
        "fallbackRating": 4.9
      },
      {
        "name": "ペットシッターおうちでいっしょ",
        "isSelf": false,
        "fallbackReviewCount": 10,
        "fallbackRating": 5
      }
    ]
  },
  {
    "slug": "meet-dental",
    "name": "ミート歯科",
    "industry": "歯科",
    "competitors": [
      {
        "name": "岩田歯科医院",
        "isSelf": false,
        "fallbackReviewCount": 50,
        "fallbackRating": 4
      },
      {
        "name": "山本歯科医院",
        "isSelf": false,
        "fallbackReviewCount": 41,
        "fallbackRating": 4.3
      },
      {
        "name": "おおきデンタルクリニック",
        "isSelf": false,
        "fallbackReviewCount": 27,
        "fallbackRating": 4
      }
    ]
  },
  {
    "slug": "kamada-dental",
    "name": "医療法人社団　かまだ歯科医院",
    "industry": "歯科",
    "competitors": [
      {
        "name": "岩田歯科医院",
        "isSelf": false,
        "fallbackReviewCount": 50,
        "fallbackRating": 4
      },
      {
        "name": "山本歯科医院",
        "isSelf": false,
        "fallbackReviewCount": 41,
        "fallbackRating": 4.3
      },
      {
        "name": "MV宝殿歯科",
        "isSelf": false,
        "fallbackReviewCount": 31,
        "fallbackRating": 3.3
      }
    ]
  },
  {
    "slug": "shibamoto-office",
    "name": "芝本司法書士事務所",
    "industry": "司法書士",
    "competitors": [
      {
        "name": "司法書士・行政書士丸山雅史事務所",
        "isSelf": false,
        "fallbackReviewCount": 6,
        "fallbackRating": 5
      },
      {
        "name": "司法書士かたひら法務事務所",
        "isSelf": false,
        "fallbackReviewCount": 4,
        "fallbackRating": 5
      },
      {
        "name": "司法書士宮本秀晃事務所",
        "isSelf": false,
        "fallbackReviewCount": 3,
        "fallbackRating": 4.7
      }
    ]
  },
  {
    "slug": "sakakibara-tax",
    "name": "榊原税理士事務所",
    "industry": "税理士",
    "competitors": [
      {
        "name": "税理士法人松本 大阪オフィス",
        "isSelf": false,
        "fallbackReviewCount": 201,
        "fallbackRating": 5
      },
      {
        "name": "川村会計事務所",
        "isSelf": false,
        "fallbackReviewCount": 44,
        "fallbackRating": 5
      },
      {
        "name": "浦野会計事務所",
        "isSelf": false,
        "fallbackReviewCount": 25,
        "fallbackRating": 4.5
      }
    ]
  },
  {
    "slug": "iami",
    "name": "アイアムアイ",
    "industry": "飲食",
    "skipRules": ["posts"],
    "competitors": [
      {
        "name": "ほっこり串焼酒場 あし跡",
        "isSelf": false,
        "fallbackReviewCount": 127,
        "fallbackRating": 4.3
      },
      {
        "name": "ととや",
        "isSelf": false,
        "fallbackReviewCount": 94,
        "fallbackRating": 4.1
      },
      {
        "name": "ミートDEビアー とりこ店",
        "isSelf": false,
        "fallbackReviewCount": 48,
        "fallbackRating": 4.7
      }
    ]
  },
  {
    "slug": "michi",
    "name": "みち",
    "industry": "飲食",
    "competitors": [
      {
        "name": "美郷",
        "isSelf": false,
        "fallbackReviewCount": 88,
        "fallbackRating": 4.3
      },
      {
        "name": "まごみ",
        "isSelf": false,
        "fallbackReviewCount": 87,
        "fallbackRating": 4.1
      },
      {
        "name": "お好み焼 はよし本店",
        "isSelf": false,
        "fallbackReviewCount": 84,
        "fallbackRating": 4
      }
    ]
  },
  {
    "slug": "koukenbi",
    "name": "幸健美歯科クリニック",
    "industry": "歯科",
    "competitors": [
      {
        "name": "クリニック知事公館前",
        "isSelf": false,
        "fallbackReviewCount": 84,
        "fallbackRating": 4.8
      },
      {
        "name": "さっぽろ駅前歯科クリニック",
        "isSelf": false,
        "fallbackReviewCount": 57,
        "fallbackRating": 4.8
      },
      {
        "name": "丸山歯科医院",
        "isSelf": false,
        "fallbackReviewCount": 14,
        "fallbackRating": 3.6
      }
    ]
  },
  {
    "slug": "unaginokagura-kyoto",
    "name": "鰻の神楽 京都店",
    "industry": "飲食店",
    "competitors": [
      { "name": "ほっこり串焼酒場 あし跡", "isSelf": false, "fallbackReviewCount": 127, "fallbackRating": 4.3 },
      { "name": "ととや", "isSelf": false, "fallbackReviewCount": 94, "fallbackRating": 4.1 },
      { "name": "ミートDEビアー とりこ店", "isSelf": false, "fallbackReviewCount": 48, "fallbackRating": 4.7 }
    ]
  },
  {
    "slug": "happycars-izumikishiwada",
    "name": "ハッピーカーズ 和泉岸和田店",
    "industry": "車買取",
    "competitors": [
      { "name": "MARKESMILE（加古川）", "isSelf": false, "fallbackReviewCount": 8, "fallbackRating": 4.9 },
      { "name": "うみがわ（加古川）", "isSelf": false, "fallbackReviewCount": 3, "fallbackRating": 5 },
      { "name": "ハシモトデザイン（加古川）", "isSelf": false, "fallbackReviewCount": 6, "fallbackRating": 4.8 }
    ]
  }
];
const SHEET_URL = "https://docs.google.com/spreadsheets/d/1NNQItK0YcRDiM03YGuMSafbp-wk2WAeGTE7sFtn62pI/edit?usp=sharing";
module.exports = { CLIENTS, SHEET_URL };