# App screenshot variants

Generated files. Do not edit by hand — run the tool below and commit what it writes.

Sources live in `raw/` at the resolution the phone exports them, 1320x2868. This
folder holds the resized variants the pages actually load.

## Why

The layout draws these screenshots inside phone frames 145–318 CSS pixels wide.
Pointing an `<img>` straight at a 1320px export means asking the browser to
downscale it 4–9x, in one bilinear step, on the GPU. Hairline dividers and small
label text alias into a crawling, pixelated mess.

The severity depends entirely on the display, which is why it looks like a
desktop-only bug:

| Display | Effective downscale into a 246px frame | Result |
| --- | --- | --- |
| Large 1x monitor at 100% zoom | 5.4x | visibly pixelated |
| Same monitor zoomed to 150% | 3.6x | better |
| Retina laptop (2x) | 2.7x | fine |

Zooming *in* improving matters is the tell: browser zoom raises the device pixel
ratio, which pulls the ratio back towards 1:1. The sources are too big for the
slot, not too small.

The illustrations in `illustrations/` never had this problem because they are
resized offline before being committed. This folder applies the same idea to the
screenshots, with one difference: a screenshot appears at several sizes across the
site, so a single width will not do. Each source gets a ladder of widths, handed
to the browser as `srcset` + `sizes` so every display picks the variant closest to
its own pixel grid — and the resize itself is Lanczos plus a light unsharp pass,
which beats what the GPU does inline.

The ladder is tight at the bottom and loose at the top. At 1x every slot lands
within ~1.15x of a rung, so the browser draws essentially pixel-for-pixel; at 2x
and 3x the rungs are further apart and a slot may downscale by up to 1.4x, which
is fine — that density is exactly where the original bug was invisible.

## The other half: frame size

Better resampling removes the artifacts but cannot raise the ceiling. A phone
frame 246 CSS pixels wide gets 246 device pixels on a 1x monitor no matter what is
fed to it. So `index.html` also grows the frames at `@media (min-width: 1280px)` —
hero 220→286, flow rows 228→264, how-it-works 246→318 — which is what actually
makes them legible on a large desktop display. The flow rows grow least: the
illustration sits beside the phone in a 468px column.

**The `sizes` attribute on each `<img>` lists these widths, and has to keep
matching the CSS.** If a frame's width or its bezel changes, update the `sizes`
attribute and the `slots` list in the tool together.

## Crops

Two screens are cropped before resizing, to frame a sheet that would otherwise sit
small inside a full-screen capture: the Foodie Assistant sheet and the Import
Recipe sheet.

A crop cannot be tighter than the frame it lands in. Phone frames are ~0.52 in
aspect and a floating sheet is much wider than that, so cropping to the sheet's
own bounds would leave `object-fit: cover` scaling to height and slicing the
sheet's left and right edges off. The crops are therefore full-width windows,
tall enough to satisfy the narrowest frame on the site, positioned so the sheet
sits well inside them. The tool asserts this and refuses a crop that is too wide.

## Regenerating

After replacing or adding a source screenshot:

```sh
python3 tools/prep-screens.py          # rewrites every variant, prunes stale ones
python3 tools/prep-screens.py --check  # verifies each expected variant exists
```

The rung ladder, the crops, and the list of slots each screenshot is rendered into
all live at the top of that script. A screenshot can declare extra rungs of its
own — `meal-library` does, because the hero recipe card draws it at 38px and the
phone-frame ladder would overshoot that by nearly 5x. It can also cap its ladder:
a screenshot that only ever appears in a phone frame stops at 620, since the 900
rung exists for blog figures drawing at 420 on a 2x display.

## Still on the old exports

`LeftoversRecipeBox.jpg` and `LeftoversMealPlan.jpg` are blog-only and remain
600px pre-refresh captures — there is no 1320px source for them. They predate the
app's visual refresh, so the blog post they illustrate shows the older UI.
