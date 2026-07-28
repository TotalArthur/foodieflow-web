# App screenshot variants

Generated files. Do not edit by hand — run the tool below and commit what it writes.

Each app screenshot is committed at the top of the repo at whatever resolution the
phone exported it (`HomeScreen.png`, `ShoppingList.png`, …). Those stay put: they
are the sources. This folder holds the resized variants the pages actually load.

## Why

The layout draws these screenshots inside phone frames 169–236 CSS pixels wide.
Pointing an `<img>` straight at a 900px-wide export means asking the browser to
downscale it 5x, in one bilinear step, on the GPU. Hairline dividers and small
label text alias into a crawling, pixelated mess.

The severity depends entirely on the display, which is why it looks like a
desktop-only bug:

| Display | Effective downscale into a 236px frame | Result |
| --- | --- | --- |
| Large 1x monitor at 100% zoom | 2.5x – 5.3x | visibly pixelated |
| Same monitor zoomed to 150% | 1.7x – 3.6x | better |
| Retina laptop (2x) | 1.3x – 2.7x | fine |

Zooming *in* improving matters is the tell: browser zoom raises the device pixel
ratio, which pulls the ratio back towards 1:1. The sources are too big for the
slot, not too small.

The illustrations in `illustrations/` never had this problem because they are
resized offline to roughly twice their rendered size before being committed. This
folder applies the same idea to the screenshots, with one difference: a screenshot
appears at several sizes across the site, so a single width will not do. Each
source gets a ladder of widths, handed to the browser as `srcset` + `sizes` so
every display picks the variant closest to its own pixel grid — and the resize
itself is Lanczos plus a light unsharp pass, which beats what the GPU does inline.

## Regenerating

After replacing or adding a source screenshot:

```sh
python3 tools/prep-screens.py          # rewrites every variant
python3 tools/prep-screens.py --check  # verifies each expected variant exists
```

The rung ladder and the list of slots each screenshot is rendered into live at the
top of that script. **If you change a phone frame's width in the CSS, update the
slot list there too** — the `sizes` attribute in the markup has to keep matching
the CSS, or the browser goes back to picking the wrong variant.

## Known gap

`MealLibrary.png` is only 220x478 at source, and the blog figures draw it up to
420px wide. The ladder stops at the source width, so that one is still stretched.
Re-export that screen at 1320x2868 (as `AddNewRecipeScreen.png` already is) and
rerun the tool to close it.
