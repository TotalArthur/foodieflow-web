#!/usr/bin/env python3
"""Prepare the app screenshots: build one resized variant per rendered size.

The screenshots are exported from the phone at 1320x2868, and the layout draws
them inside phone frames 145-318 CSS pixels wide. Pointing an `<img>` straight at
the export means asking the browser to do a 4-9x downscale in one bilinear step
on the GPU, and the fine UI detail -- hairline dividers, small label text --
aliases into a crawling, pixelated mess.

The severity tracks device pixel ratio, which is why this reads as a desktop-only
bug: a Retina display halves the ratio, and browser zoom raising the DPR is what
makes zooming *in* look better. The source is too big for the slot, not too
small.

The illustrations avoid this already -- prep-illustrations.py resizes them
offline before they are committed. This does the same for the screenshots, except
a screenshot appears at several sizes across the site, so one fixed width will
not do. Each source gets a ladder of widths, handed to the browser as `srcset` +
`sizes` so every display picks the variant closest to its own pixel grid.

Resizing here rather than in the browser also buys a better filter: Lanczos over
the whole image, plus a light unsharp pass to put back the edge contrast any
downscale costs.

Usage: python3 tools/prep-screens.py [--check]
"""
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "screens"

# Width rungs, in CSS pixels. The ladder is deliberately tight at the bottom and
# loose at the top, because the two ends are not equally forgiving.
#
# At 1x every slot below lands within ~1.15x of a rung, so the browser draws
# essentially pixel-for-pixel. That end matters most -- a 1x display has no spare
# pixels to hide a resample in, which is why this bug was only ever visible
# there.
#
# At 2x and 3x the rungs are further apart and a slot can end up downscaling by
# as much as 1.4x. That is fine, and is precisely why nobody noticed the original
# bug on a Retina screen: at those densities the resample lands below the eye's
# resolution.
RUNGS = (180, 240, 280, 320, 480, 620, 900)

# Phone frames are narrower in aspect than the 1320x2868 screenshot, so
# `object-fit: cover` always scales to the slot width and crops the height. The
# width alone decides how many pixels the browser needs, and the *narrowest*
# frame on the site sets how tall a crop may be before the frame starts eating
# its sides instead: 186/355 at the smallest how-it-works breakpoint, so 0.52.
NARROWEST_SLOT_ASPECT = 0.52


@dataclass
class Screen:
    """One source screenshot and everything the layout asks of it."""

    source: str
    # Every slot it is rendered into, as CSS pixels of drawn width -- the inner
    # width of the frame, i.e. the outer width minus its two bezels. Documentation
    # only, but it is what the `sizes` attributes in the markup have to match.
    slots: list[str]
    # Rungs only this screenshot needs. The ladder is built for phone-frame-sized
    # slots and overshoots a small thumbnail badly.
    extra_rungs: tuple = ()
    # (left, top, right, bottom) in source pixels, applied before resizing.
    crop: tuple = None
    # Widest rung worth building. A screenshot that only ever appears in a phone
    # frame tops out at 318 CSS px, so 620 already covers it at 2x; the 900 rung
    # exists for the blog figures, which draw up to 420 and so want 840 at 2x.
    # Building it for the others costs ~250KB each that nothing ever requests.
    max_rung: int = None


PHONE_FLOW = "flow phone 228 (188 <=767px, 264 >=1280px)"
PHONE_HOW = "how-it-works phone 246 (186 <=767px, 206 <=1023px, 318 >=1280px)"

SCREENS = {
    "home": Screen(
        source="raw/HomePage.PNG",
        slots=["hero front phone 220 (178 <=767px, 286 >=1280px)"],
        max_rung=620,
    ),
    "shopping-list": Screen(
        source="raw/ShoppingList.PNG",
        slots=[
            "hero back phone 175 (145 <=767px, 229 >=1280px)",
            PHONE_FLOW,
            PHONE_HOW,
            "blog figure up to 420",
        ],
    ),
    # Cropped to frame the Foodie Assistant sheet. The card sits at rows 554-2085
    # of the export; this is the tallest window that keeps it centred without
    # exceeding the frame aspect, so no phone frame ever crops the card's sides.
    "foodie-assistant": Screen(
        source="raw/FoodieAssistant.PNG",
        slots=[PHONE_FLOW, PHONE_HOW, "blog figure up to 420"],
        crop=(0, 49, 1320, 2589),
    ),
    "weekly-planner": Screen(
        source="raw/WeeklyPlanner.PNG",
        slots=[PHONE_FLOW, PHONE_HOW],
        max_rung=620,
    ),
    "dietary-preferences": Screen(
        source="raw/DietaryPreferences.PNG",
        slots=[PHONE_FLOW, PHONE_HOW],
        max_rung=620,
    ),
    "meal-library": Screen(
        source="raw/MealLibrary.PNG",
        slots=["hero recipe card thumbnail 38", "blog figure up to 420"],
        # The hero thumbnail is 38px. Without these it would pull the 180 rung
        # and downscale it nearly 5x -- the same fault this tool exists to fix,
        # just on a small enough element that it is easy to miss.
        extra_rungs=(48, 120),
    ),
    # Same treatment as the assistant sheet: the import card sits at rows
    # 618-1274, high enough in the frame that the window is pinned to the top of
    # the export rather than centred on the card.
    "import-recipe": Screen(
        source="raw/ImportRecipe.PNG",
        slots=[PHONE_FLOW, PHONE_HOW],
        crop=(0, 0, 1320, 2540),
        max_rung=620,
    ),
    "household-mode": Screen(
        source="raw/HouseholdMode.PNG",
        slots=[PHONE_FLOW],
        max_rung=620,
    ),
    # Blog-only, and still the pre-refresh exports -- there is no 1320px source
    # for these two.
    "leftovers-recipe-box": Screen(
        source="LeftoversRecipeBox.jpg", slots=["blog figure up to 420"]
    ),
    "leftovers-meal-plan": Screen(
        source="LeftoversMealPlan.jpg", slots=["blog figure up to 420"]
    ),
}

# A downscale spreads every edge over neighbouring pixels. Screenshots are all
# edges -- hairline dividers, small bold type -- so a light unsharp pass after
# the resize restores the contrast the filter averaged away. Deliberately gentle:
# anything stronger rings around the dark phone chrome.
UNSHARP = ImageFilter.UnsharpMask(radius=0.6, percent=55, threshold=3)

# Variants keep their source's format. A screenshot exported as PNG stays PNG so
# its flat UI fills stay exact; one exported as JPEG is re-encoded as JPEG,
# because re-wrapping an already-lossy photo-heavy frame in PNG costs several
# times the bytes for detail the source no longer holds. Chroma subsampling is
# off -- these frames are mostly coloured text on white, which 4:2:0 smears.
JPEG_OPTS = dict(quality=88, subsampling=0, progressive=True, optimize=True)


def variants_for(width: int, extra: tuple = (), max_rung: int = None) -> list[int]:
    """The rungs this source can fill.

    A source narrower than the top rung contributes its own width as the last
    one, so every pixel it does have is offered. A source wider than the ladder
    stops at the ladder: the 1320px exports would otherwise each ship a ~1MB
    variant to serve a 954px worst case that only a 3x tablet ever asks for.
    """
    ceiling = min(width, max_rung or width)
    widths = [w for w in sorted(set(RUNGS) | set(extra)) if w <= ceiling]
    if not widths:
        return [width]
    if width < RUNGS[-1] and width > widths[-1]:
        widths.append(width)
    return widths


def render(screen: Screen, slug: str, check: bool) -> list[tuple[Path, int, int]]:
    src_path = ROOT / screen.source
    source = Image.open(src_path)
    if source.mode not in ("RGB", "L"):
        source = source.convert("RGB")

    if screen.crop:
        left, top, right, bottom = screen.crop
        if right > source.width or bottom > source.height:
            raise SystemExit(f"{slug}: crop {screen.crop} exceeds {source.size}")
        aspect = (right - left) / (bottom - top)
        if aspect > NARROWEST_SLOT_ASPECT:
            raise SystemExit(
                f"{slug}: crop aspect {aspect:.3f} is wider than the narrowest "
                f"frame ({NARROWEST_SLOT_ASPECT}); the frame would crop its sides"
            )
        source = source.crop(screen.crop)

    jpeg = src_path.suffix.lower() in (".jpg", ".jpeg")
    suffix = ".jpg" if jpeg else ".png"

    built = []
    for width in variants_for(source.width, screen.extra_rungs, screen.max_rung):
        height = round(source.height * width / source.width)
        out_path = OUT_DIR / f"{slug}-{width}{suffix}"

        if width == source.width:
            img = source.copy()
        else:
            img = source.resize((width, height), Image.LANCZOS).filter(UNSHARP)

        if check:
            if not out_path.exists():
                raise SystemExit(f"missing variant: {out_path.relative_to(ROOT)}")
        else:
            img.save(out_path, **(JPEG_OPTS if jpeg else dict(optimize=True)))
        built.append((out_path, width, height))
    return built


def main(check: bool = False) -> None:
    if not check:
        OUT_DIR.mkdir(exist_ok=True)

    expected = set()
    for slug, screen in SCREENS.items():
        if not (ROOT / screen.source).exists():
            raise SystemExit(f"missing source: {screen.source}")

        built = render(screen, slug, check)
        expected.update(p.name for p, _, _ in built)
        rungs = ", ".join(f"{w}x{h}" for _, w, h in built)
        print(f"{screen.source} -> screens/{slug}-* [{rungs}]")
        for slot in screen.slots:
            print(f"    slot: {slot}")

    stale = sorted(
        p.name
        for p in OUT_DIR.iterdir()
        if p.suffix in (".png", ".jpg") and p.name not in expected
    )
    if stale:
        print(f"\nstale variants (no longer referenced by any screen): {stale}")
        if not check:
            for name in stale:
                (OUT_DIR / name).unlink()
            print("removed")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args not in ([], ["--check"]):
        sys.exit(__doc__)
    main(check=bool(args))
