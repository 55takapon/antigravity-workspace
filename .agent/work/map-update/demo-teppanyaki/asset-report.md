# 画像アセットレポート

## 納品一覧

| ファイル | 用途 | 寸法 | 容量 | alt案 |
|:--|:--|--:|--:|:--|
| `images/hero-couple.webp` | First View | 1536 × 864 | 105,536 bytes | 鉄板カウンター越しに迎える50代の店主夫婦 |
| `images/teppan-seasonal.webp` | Menu | 1200 × 800 | 95,262 bytes | 鉄板で焼き上げる肉と季節の野菜 |
| `images/counter-interior.webp` | Counter / Space | 1200 × 800 | 100,122 bytes | 8席ほどの落ち着いた鉄板カウンター |
| `images/owners-portrait.webp` | Concept | 1200 × 800 | 85,618 bytes | 小さな鉄板焼き店を営む50代の夫婦 |

すべて WebP、sRGB相当のRGB画像。ヒーローは300KB目安以内、通常画像は200KB以内。

## 表現チェック

- 4点を目視確認済み。
- 人物画像は、顔、腕、手、指、衣服の接続に目立つ破綻なし。
- 料理画像の手とヘラの接続に目立つ破綻なし。
- 夫婦写真はヒーロー画像を参照して再生成し、同じ夫婦・衣装・店内として認識できる状態に統一。
- 読める文字、ロゴ、ウォーターマークなし。
- 炎、赤提灯、派手な赤・オレンジ、黒金・大理石の過度な高級演出なし。
- 墨黒、生成り、焦がし茶、鈍い銅色と自然な湯気で、静かで気取らない温かさに統一。
- 店内画像は約8席の小さなカウンターとして成立し、家具や厨房設備に大きな構造破綻なし。

## 実装メモ

- ヒーローは左側にコピー用の暗い余白がある。CSSの `object-position` はPCで `center center`、狭幅で夫婦側へ調整する。
- ヒーロー以外は `loading="lazy"`、全画像に `width` / `height` または `aspect-ratio` を指定する。
- 生成画像の人物・店舗・料理はすべて架空。実在店の事実や実在人物の写真として扱わない。
- 内観奥に小さな紙状の意匠があるが、読める文字情報ではなく、住所・価格・営業時間などの情報源として使用しない。

## SHA-256

```text
C6807AF058F3264D7C4A6632AE8600A1324606A0149798BBDBE38E1E70788876  hero-couple.webp
3216DB6FD89DC1C8C89EB1C3E3D14F95A47B66BE9819D24C2918397BAD2B78C4  teppan-seasonal.webp
344ADF3C08ABADD8F31961609FC6B21229059E10745B51E03D8429296B5080E7  counter-interior.webp
FE438009A2DB888836741BF2FE3A8C8D934A6D128C75E8A0890A7D3D03040A26  owners-portrait.webp
```
