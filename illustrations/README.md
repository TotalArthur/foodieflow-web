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
| `planner.png` | Flow 2 — Weekly Planner | From `raw/PlannerIcon.png`. |
| `dietary.png` | Flow 4 — Dietary Preferences | From `raw/DietaryIcon.png`. |
| `import.png` | Flow 5 — Import Recipe | From `raw/ImportIcon.png`. |
| `household.png` | Flow 6 — Household Mode | From `raw/HouseholdIcon.png`. |

`fridge.png` is no longer referenced: Flow 2 used it as a stand-in until the
calendar mascot existed. It is kept in case a future row wants it.

The four mascots above are drawn edge to edge, unlike the chef and the trolley
which carry empty space at their margins. The layout tucks illustrations behind
the phone, so those four get a much shallower overlap — at the default depth the
phone eats a third of the calendar and a whole diner.

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
