# Sakakibara Tax Accountant Office Website Plan

## Goal Description
Create a professional, responsive top page (first view) for "榊原税理士事務所" (Sakakibara Tax Accountant Office) that conveys trust and professionalism, adhering to Japanese corporate design standards.

## Design Concept
- **Theme**: Trust, Stability, Professionalism (Japanese Corporate Style).
- **Colors**:
  - Main: `#1F2A44` (Deep Navy)
  - Sub: `#BDAA4B` (Gold)
  - Base: `#F4F4F2` (Warm Gray)
- **Typography**:
  - Headings: 'Noto Serif JP', serif (for a traditional, established feel)
  - Body: 'Noto Sans JP', sans-serif (for readability)

## Proposed Changes

### [Root Directory]
#### [OVERWRITE] [index.html](file:///C:/Users/hangy/.gemini/antigravity/scratch/sakakibara-tax/index.html)
- Clean semantic HTML structure.
- Loading Google Fonts.
- Hero section with a catchphrase.

### [css]
#### [NEW] [style.css](file:///C:/Users/hangy/.gemini/antigravity/scratch/sakakibara-tax/css/style.css)
- CSS Variables for colors and fonts.
- Reset/Normalize styles.
- Responsive layout (Mobile first or Desktop down, ensuring both work).
- BEM naming convention or clear utility/component separation.

### [images]
#### [NEW] [hero.jpg](file:///C:/Users/hangy/.gemini/antigravity/scratch/sakakibara-tax/images/hero.jpg)
- Generated image reflecting a professional Japanese tax office atmosphere.

## Verification Plan

### Automated Tests
- None (Visual styling task).

### Manual Verification
1.  **Open** the `index.html` in the browser.
2.  **Visual Check**:
    - Verify colors match the specification.
    - Verify fonts are loaded correctly.
    - Check the hero image quality and placement.
3.  **Responsive Check**:
    - Use browser dev tools to resize from mobile (375px) to tablet (768px) to desktop (1200px+).
    - Ensure no horizontal scrolling or broken layout.
    - Check navigation menu behavior (hamburger menu or simplified list for mobile).
