# Homepage illustrations

The homepage references these four files. They are loaded as CSS `background-image`,
so a missing file collapses to empty space rather than a broken-image icon — the
page stays intact, it just loses the artwork.

| File | Used by | Notes |
| --- | --- | --- |
| `kitchen-counter.png` | Hero base band | Stays opaque. The hero fades its top edge into the navy with a CSS gradient mask, so the artwork needs headroom above the counter. |
| `chef-mascot.png` | Flow 1 — Foodie Assistant | Needs a transparent background. |
| `fridge.png` | Flow 2 — Weekly Planner | Needs a transparent background. |
| `grocery-cart.png` | Flow 3 — Shopping list | Needs a transparent background. |

## Preparing a new export

Source exports arrive on a flat off-white backdrop. To strip it to transparency,
drop the original in `raw/` and run:

```sh
python3 tools/prep-illustrations.py raw/chef-mascot.png illustrations/chef-mascot.png
```

The script flood-fills inward from the border, so light areas *inside* the artwork
(the chef's jacket, a milk carton) keep their fill. It also trims surrounding
transparent padding so the art sits flush against the phone in the layout.

`kitchen-counter.png` is the exception — it is a full-bleed band, so copy it across
as-is without running the script.
