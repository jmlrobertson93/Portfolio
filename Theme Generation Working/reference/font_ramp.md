# Type Ramp

Confirmed deliberate (not incidental) — derived from the "Design Template Examples"
page and corrected against user intent 2026-08-13.

| Size | Scope | Applies to |
|---|---|---|
| 12 | global | Axis headers (categoryAxis / valueAxis fontSize) |
| 14 | global | Data visualisation labels (chart data labels), all slicer values, KPI callout label |
| 16 | per-visual title | Visualisation titles — deliberately paired with padding/divider/spacing to create a 16px background band, text vertically centered within it |
| 18 | textbox only | Dashboard subtitle |
| 24 | cardVisual only | KPI callout value (the standout number) |
| 32 | textbox only | Dashboard title |

## Notes

- 18 and 32 are textbox-specific (set via `paragraphs[].textRuns[].textStyle`, not a
  themeable `visualStyles` card) — textbox content isn't driven by the theme file at
  all, so these sizes are a documented convention for manually building title/subtitle
  textboxes, not something to encode in `theme.json`.
- 16 (visual titles) needs its exact card identified — likely `visualStyles.*.*.title`
  fontSize, but the padding/divider/spacing band around it that makes it "16px" is a
  separate set of properties (background, divider, spacing cards) that must be
  captured together, not just the font size in isolation. Confirm against a real
  title-card extraction before finalizing.
- 24 (KPI value) and 14 (KPI label) are scoped to `cardVisual` only — hero KPI is the
  confirmed default style: centered, bold, 24pt value / 14pt label.
