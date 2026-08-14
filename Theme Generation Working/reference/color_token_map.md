# Colour Token Map

Source of truth for how `ThemeDataColor.ColorId` (used throughout every `visual.json`)
resolves to a role. Verified empirically against the Power BI Desktop colour picker
grid (Theme colors > Name and colors > Color 1-8), not assumed from array position.

## Why ColorId isn't a direct index into `dataColors`

The Desktop colour picker's "Theme colors" swatch grid has 10 columns:
`[white, black, Color1, Color2, ..., Color8]`. `ColorId` is the column index in that
grid, not the index into the theme JSON's `dataColors` array. That means every
`ColorId` is offset by +2 relative to the 0-based `dataColors` array position.

## Resolved mapping

| ColorId | Grid column | Hex | Theme `dataColors` index | Role |
|---|---|---|---|---|
| 0 | white | `#FFFFFF` | n/a | background |
| 1 | black | `#000000` | n/a | unused (text uses ColorId 9 instead) |
| 2 | Color 1 | `#0095DD` | `dataColors[0]` | primary visualisation colour (charts) |
| 3 | Color 2 | `#FFAA33` | `dataColors[1]` | secondary visualisation colour (charts) |
| 4 | Color 3 | `#00539F` | `dataColors[2]` | primary structural colour (title backgrounds) |
| 5 | Color 4 | `#FF9500` | `dataColors[3]` | secondary structural colour (help / future nav highlight) |
| 6 | Color 5 | `#E33A02` | `dataColors[4]` | negative sentiment |
| 7 | Color 6 | `#FCBB00` | `dataColors[5]` | medium sentiment |
| 8 | Color 7 | `#1AAB40` | `dataColors[6]` | positive sentiment |
| 9 | Color 8 | `#4E4C4C` | `dataColors[7]` | all text |

## Implication for the theme JSON

- `dataColors` array (theme file, 0-indexed) stays exactly as the 8 hex values above,
  in that order — this is what Power BI Desktop's Color 1-8 pickers write to.
- Any `visualStyles` colour property that should carry "all text" needs to reference
  `dataColors[7]` (`#4E4C4C`) via a `ThemeDataColor` expression with `ColorId: 9`
  when read back from a `visual.json` extraction — but when we hand-author theme JSON
  directly (not round-tripped from a visual.json), we should just write the literal
  hex or a `ThemeDataColor` with the correct `ColorId`, matching this table.
- `good` / `neutral` / `bad` top-level theme properties should be set to
  `#1AAB40` / `#FCBB00` / `#E33A02` respectively, matching the sentiment roles above,
  so KPI conditional formatting and the sentiment colour pickers inherit correctly.

## Open item

`Sentiment colors` section in the theme editor (visible but not yet expanded in the
screenshot reviewed 2026-08-13) still needs checking — confirm it aligns with
good=`#1AAB40`, neutral=`#FCBB00`, bad=`#E33A02` rather than defaulting to something else.
