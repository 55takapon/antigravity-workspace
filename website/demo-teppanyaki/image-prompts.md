# 画像生成プロンプト

生成方式: built-in `image_gen`  
共通ユースケース: `photorealistic-natural`  
共通方針: 墨黒・鉄板グレー・生成り・焦がし茶・鈍い銅色。高級ステーキハウスにも大衆居酒屋にも寄せず、自然な湯気と小さな店の距離感を重視する。

## `hero-couple.webp`

```text
Use case: photorealistic-natural
Asset type: Japanese restaurant website hero image, wide landscape composition designed for a full-bleed first view
Primary request: A warm candid editorial photograph of a Japanese married couple in their mid-50s welcoming guests from behind the teppan counter of their very small teppanyaki restaurant. They are the only proprietors. Both look natural, approachable, quietly smiling, and dressed in simple clean charcoal workwear and aprons. The couple and the near edge of the iron counter must both read clearly.
Scene/backdrop: intimate Japanese counter restaurant with only about 8 to 10 seats, blackened iron griddle, warm off-white plaster, restrained dark wood, a few copper utensils, subtle rising steam; no customers visible
Composition/framing: cinematic horizontal image, eye-level from the guest side of the counter; couple placed mainly in the right-center with generous darker negative space on the left for website copy; waist-up, hands visible naturally resting or working, both faces fully unobstructed; important subjects safe within a central crop for mobile
Lighting/mood: soft warm practical light with natural skin tones, calm evening atmosphere, welcoming and unpretentious, slight steam catching the light, not dramatically dark
Color palette: sumi black, iron gray, warm ecru, toasted brown, muted copper; restrained saturation
Style/medium: photorealistic high-end Japanese editorial food-and-hospitality photography, real skin texture, 35mm lens look, shallow but sufficient depth of field
Constraints: exactly two people, a Japanese woman and man both clearly around their 50s; anatomically correct faces, hands and fingers; realistic iron surface and steam; no visible menu text
Avoid: text, letters, logos, signs, watermark, extra people, duplicated limbs, distorted hands or fingers, over-smoothed skin, luxury steakhouse glamour, black-and-gold opulence, marble, red lanterns, izakaya clutter, excessive flames, orange color cast, staged stock-photo grin
```

## `teppan-seasonal.webp`

```text
Use case: photorealistic-natural
Asset type: Japanese teppanyaki restaurant website menu feature image, landscape close-up
Primary request: An appetizing but restrained close photograph of sliced beef and seasonal Japanese vegetables being cooked on a black iron teppan by an experienced chef. Include glossy seared beef, shiitake mushroom, asparagus, pumpkin and a few green vegetables, with fine natural steam rising.
Scene/backdrop: authentic compact Japanese teppanyaki counter; only the iron cooking surface and subtle dark background details visible
Composition/framing: cinematic horizontal close-up from a guest-side low three-quarter angle; food is the clear subject; one anatomically correct adult hand holding a metal spatula may enter naturally from the upper right, but no face or body; usable crop across desktop and mobile
Lighting/mood: soft directional warm light, realistic highlights on iron and food, calm intimate dinner atmosphere, no theatrical flames
Color palette: sumi black, iron gray, natural browned meat, muted vegetable greens, warm pumpkin, small copper highlights; controlled saturation
Style/medium: photorealistic Japanese editorial food photography, authentic textures, 50mm macro feel, shallow depth of field focused on the food
Constraints: realistic doneness and moisture, clean iron surface with subtle cooking marks, believable steam; anatomically correct hand and fingers if visible
Avoid: text, letters, logos, watermark, plates with branding, excessive sauce gloss, giant luxury steak, gold leaf, flames, sparks, red lantern ambience, orange color cast, crowded izakaya styling, distorted utensils, malformed hand or fingers
```

## `counter-interior.webp`

```text
Use case: photorealistic-natural
Asset type: Japanese teppanyaki restaurant website interior/space image, wide landscape
Primary request: A calm, inviting view of a very small Japanese teppanyaki restaurant with a single intimate counter and only 8 to 10 seats, prepared for evening service. The long black iron griddle is integrated behind the counter, with simple neatly spaced stools and no people.
Scene/backdrop: compact owner-operated neighborhood restaurant; warm off-white textured plaster, charcoal walls, restrained dark wood, aged but clean iron, a few muted copper kitchen objects, subtle linen details; modest and cared-for rather than rustic cluttered
Composition/framing: horizontal architectural editorial photograph from near the entrance looking diagonally along the counter; the horizontal counter edge leads into the scene; enough visual depth to show the small scale clearly; no signage or readable menus
Lighting/mood: layered soft warm practical lighting, quiet, comfortable and welcoming, subtle natural steam near the griddle, realistic shadow detail, not dim or theatrical
Color palette: sumi black, iron gray, ecru, toasted brown, muted copper; restrained orange and red
Style/medium: photorealistic Japanese hospitality interior photography, 24mm lens without exaggerated distortion, natural materials and believable construction
Constraints: visibly 8 to 10 individual seats total, plausible counter dimensions and circulation, tidy and functional working restaurant, no people
Avoid: text, letters, logos, signs, watermark, luxury hotel or steakhouse mood, black-and-gold opulence, marble, chandeliers, red lanterns, izakaya posters, clutter, rows of bottles, excessive flames, neon, wide cavernous dining room, warped furniture, impossible architecture
```

## `owners-portrait.webp`

`hero-couple.webp` の生成元画像を人物同一性の参照として使用した。

```text
Use case: identity-preserve
Asset type: Japanese teppanyaki restaurant website owner portrait, horizontal environmental portrait
Input image: identity and wardrobe reference for the same Japanese married couple and the same restaurant
Primary request: Create a new, natural environmental two-person portrait of exactly the same mid-50s Japanese husband and wife shown in the reference. Preserve both identities, apparent ages, hair, facial features, body proportions, charcoal workwear, and the understated restaurant atmosphere. Change the pose and framing only: they stand side by side behind the counter after preparing for service, turn slightly toward one another with relaxed subtle smiles, warm and familiar rather than posed.
Composition/framing: horizontal three-quarter portrait from mid-thigh upward; heads not cropped; all four hands clearly visible in simple relaxed positions, holding nothing; clean breathing room; eye-level 50mm lens
Scene/backdrop: the same compact teppanyaki counter, warm ecru plaster, charcoal wall, black iron griddle, restrained dark wood, subtle copper tools and light steam
Lighting/mood: soft warm side light, realistic skin texture, calm welcoming evening atmosphere
Constraints: exactly the same two people from the reference and no one else; preserve identity and wardrobe; anatomically correct faces, arms, hands and fingers; photorealistic editorial hospitality photography
Avoid: text, letters, logos, signs, watermark, extra people, changed identity, younger-looking faces, duplicated limbs, merged bodies, malformed hands or fingers, wedding-photo posing, exaggerated laughter, luxury steakhouse styling, black-and-gold opulence, red lanterns, clutter, excessive flames, orange color cast
```
