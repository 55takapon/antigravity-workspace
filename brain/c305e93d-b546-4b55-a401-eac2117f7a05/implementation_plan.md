# Layout Fixes and Refinements

## Goal Description
Fix reported layout regressions and improve specific sections as requested.

## Proposed Changes
### Assets
#### [NEW] Component Images
- `images/column_thumb.png`: Sample eye-catching image for tax columns.

### CSS (`style.css`)
- **Representative Message**: Restore/Fix flex layout for 2 columns.
- **Tax Column**: Ensure grid layout (3 columns) works and add styling for thumbnail images.
- **Flow**: Style as vertical or step-based flow (similar to SWELL) with clear numbering and connectors.
- **Contact**: Revert to the original "boxed" design if it was lost.

### HTML (`index.html`)
- **Tax Column**: Add `images/column_thumb.png` to column items.

## Verification Plan
### Manual Verification
- Check Representative section is 2 columns.
- Check Tax Column section is 3 columns with images.
- Check Flow section looks like a step flow.
- Check Contact section looks like the original design.
- Preview in browser.
