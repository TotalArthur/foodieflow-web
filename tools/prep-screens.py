#!/usr/bin/env python3
"""Prepare the app screenshots: build one resized variant per rendered size.

The screenshots ship at whatever resolution the phone exported them at, and the
layout then draws them inside a ~170-240px phone frame. On a Retina laptop that
is roughly a 1.4x downscale and looks fine. On a large 1x desktop monitor the
same markup asks the browser to squeeze a 900px-wide image into 169 CSS pixels
-- a 5x downscale, done once, on the GPU, with a bilinear filter. Fine UI
detail (1px rules, small label text, progress bars) aliases into a crawling,
pixelated mess. Zooming in makes it *better*, because zoom raises the device
pixel ratio and pulls the ratio back towards 1:1, which is the giveaway that
the source is oversized rather than undersized.

The illustrations already avoid this: they are resized offline to roughly twice
their rendered size before they are committed. This does the same for the
screenshots, except a screenshot appears at several sizes across the page, so
one fixed width will not do. Each source gets a ladder of widths instead, and
the markup hands the ladder to the browser as `srcset` + `sizes` so every
display picks the variant closest to its own pixel grid.

Resizing here rather than in the browser also buys a better filter: Lanczos
over the whole image, plus a light unsharp pass to put back the edge contrast
any downscale costs.

Usage: python3 tools/prep-screens.py [--check]
"""
import sys
from pathlib import Path

from PIL import Image, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "screens"

# Width rungs, in CSS pixels of the widest variant. Chosen to cover every
# rendered slot below at 1x, 2x and 3x without shipping near-duplicate files:
# 180 covers the small frames at 1x, 240 the large ones, 360 the small frames at
# 2x, 540 the large frames at 2x and the small ones at 3x, 900 the blog figures
# at 2x. Rungs above a source's own width are dropped -- upscaling invents
# nothing.
RUNGS = (180, 240, 360, 540, 900)

# Every slot each screenshot is rendered into, as CSS pixels of *drawn* width.
# The phone frames are wider in aspect than a 9:19.5 screenshot, so `object-fit:
# cover` always scales to the slot width and crops the height; the width alone
# decides how many pixels the browser needs. Values are the inner width of the
# frame -- the outer width minus its two paddings.
SCREENS = {
    "home": (
        "HomeScreen.png",
        ["hero front phone 212 (170 <=767px)"],
    ),
    "shopping-list": (
        "ShoppingList.png",
        [
            "hero back phone 169 (139 <=767px)",
            "flow 3 phone 220 (180 <=767px)",
            "how-it-works phone 236 (196 <=1023px, 176 <=767px)",
            "blog figure up to 420",
        ],
    ),
    "foodie-assistant": (
        "FoodieAssistant.PNG",
        [
            "flow 1 phone 220 (180 <=767px)",
            "how-it-works phone 236 (196 <=1023px, 176 <=767px)",
            "blog figure up to 420",
        ],
    ),
    "weekly-planner": (
        "WeeklyPlanner.png",
        [
            "flow 2 phone 220 (180 <=767px)",
            "how-it-works phone 236 (196 <=1023px, 176 <=767px)",
        ],
    ),
    "dietary-preferences": (
        "DietaryPreferences.PNG",
        [
            "flow 4 phone 220 (180 <=767px)",
            "how-it-works phone 236 (196 <=1023px, 176 <=767px)",
        ],
    ),
    # 220x478 at source -- the only screenshot the layout has to *upscale*. The
    # ladder stops at the source width, so the blog figure still stretches it;
    # re-export this screen at 1320x2868 like AddNewRecipeScreen.png to fix that
    # properly.
    "meal-library": (
        "MealLibrary.png",
        ["hero recipe card thumbnail 38", "blog figure up to 420"],
    ),
    "leftovers-recipe-box": ("LeftoversRecipeBox.jpg", ["blog figure up to 420"]),
    "leftovers-meal-plan": ("LeftoversMealPlan.jpg", ["blog figure up to 420"]),
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


def variants_for(source: Image.Image) -> list[int]:
    """The rungs this source can actually fill, plus the source width itself.

    The source width is kept as the top rung only when it clears the rung below
    by a useful margin -- a 600px source next to a 540px rung is not worth a
    second file.
    """
    widths = [w for w in RUNGS if w <= source.width]
    if not widths or source.width >= widths[-1] * 1.15:
        widths.append(source.width)
    return widths


def render(src_path: Path, slug: str, check: bool) -> list[tuple[Path, int, int]]:
    source = Image.open(src_path)
    if source.mode not in ("RGB", "L"):
        source = source.convert("RGB")

    jpeg = src_path.suffix.lower() in (".jpg", ".jpeg")
    suffix = ".jpg" if jpeg else ".png"

    built = []
    for width in variants_for(source):
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

    for slug, (source_name, slots) in SCREENS.items():
        src_path = ROOT / source_name
        if not src_path.exists():
            raise SystemExit(f"missing source: {source_name}")

        built = render(src_path, slug, check)
        rungs = ", ".join(f"{w}x{h}" for _, w, h in built)
        print(f"{source_name} -> screens/{slug}-* [{rungs}]")
        for slot in slots:
            print(f"    slot: {slot}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args not in ([], ["--check"]):
        sys.exit(__doc__)
    main(check=bool(args))
