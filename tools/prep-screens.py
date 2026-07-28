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

# Width rungs, in CSS pixels. The ladder is deliberately tight at the bottom and
# loose at the top, because the two ends are not equally forgiving.
#
# At 1x every slot below lands within 10% of a rung, so the browser draws
# essentially pixel-for-pixel: 169->180, 212/221/236->240, 254/276->280,
# 306->320. That end matters most -- a 1x display has no spare pixels to hide a
# resample in, which is why this bug was only ever visible there.
#
# At 2x and 3x the rungs are further apart (480, 620, 900) and a slot can end up
# downscaling by as much as 1.4x. That is fine, and is precisely why nobody
# noticed the original bug on a Retina screen: at those densities the resample
# lands below the eye's resolution.
#
# Rungs above a source's own width are dropped -- upscaling invents nothing.
RUNGS = (180, 240, 280, 320, 480, 620, 900)

# Every slot each screenshot is rendered into, as CSS pixels of *drawn* width.
# The phone frames are wider in aspect than a 9:19.5 screenshot, so `object-fit:
# cover` always scales to the slot width and crops the height; the width alone
# decides how many pixels the browser needs. Values are the inner width of the
# frame -- the outer width minus its two paddings.
#
# An optional third entry adds rungs only that screenshot needs. The ladder above
# is built for phone-frame-sized slots and overshoots a small thumbnail badly.
SCREENS = {
    "home": (
        "HomeScreen.png",
        ["hero front phone 212 (170 <=767px, 276 >=1280px)"],
    ),
    "shopping-list": (
        "ShoppingList.png",
        [
            "hero back phone 169 (139 <=767px, 221 >=1280px)",
            "flow 3 phone 220 (180 <=767px, 254 >=1280px)",
            "how-it-works phone 236 (176 <=767px, 196 <=1023px, 306 >=1280px)",
            "blog figure up to 420",
        ],
    ),
    "foodie-assistant": (
        "FoodieAssistant.PNG",
        [
            "flow 1 phone 220 (180 <=767px, 254 >=1280px)",
            "how-it-works phone 236 (176 <=767px, 196 <=1023px, 306 >=1280px)",
            "blog figure up to 420",
        ],
    ),
    "weekly-planner": (
        "WeeklyPlanner.png",
        [
            "flow 2 phone 220 (180 <=767px, 254 >=1280px)",
            "how-it-works phone 236 (176 <=767px, 196 <=1023px, 306 >=1280px)",
        ],
    ),
    "dietary-preferences": (
        "DietaryPreferences.PNG",
        [
            "flow 4 phone 220 (180 <=767px, 254 >=1280px)",
            "how-it-works phone 236 (176 <=767px, 196 <=1023px, 306 >=1280px)",
        ],
    ),
    # 220x478 at source -- the only screenshot the layout has to *upscale*. The
    # ladder stops at the source width, so the blog figure still stretches it;
    # re-export this screen at 1320x2868 like AddNewRecipeScreen.png to fix that
    # properly.
    "meal-library": (
        "MealLibrary.png",
        ["hero recipe card thumbnail 38", "blog figure up to 420"],
        # The hero thumbnail is 38px. Without these it would pull the 180 rung
        # and downscale it nearly 5x -- the same fault this tool exists to fix,
        # just on a small enough element that it is easy to miss.
        (48, 120),
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


def variants_for(source: Image.Image, extra: tuple = ()) -> list[int]:
    """The rungs this source can actually fill, plus the source width itself.

    The source's own width is always kept as the top rung when it exceeds the
    ladder: the widest phone frame at 2x asks for 552px, which the fixed rungs
    would answer with 540 and a hair of upscaling. Every pixel a source has is
    worth offering.
    """
    widths = sorted(w for w in set(RUNGS) | set(extra) if w <= source.width)
    if not widths or source.width > widths[-1]:
        widths.append(source.width)
    return widths


def render(src_path: Path, slug: str, check: bool, extra: tuple = ()) -> list[tuple[Path, int, int]]:
    source = Image.open(src_path)
    if source.mode not in ("RGB", "L"):
        source = source.convert("RGB")

    jpeg = src_path.suffix.lower() in (".jpg", ".jpeg")
    suffix = ".jpg" if jpeg else ".png"

    built = []
    for width in variants_for(source, extra):
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

    for slug, entry in SCREENS.items():
        source_name, slots = entry[0], entry[1]
        extra = entry[2] if len(entry) > 2 else ()

        src_path = ROOT / source_name
        if not src_path.exists():
            raise SystemExit(f"missing source: {source_name}")

        built = render(src_path, slug, check, extra)
        rungs = ", ".join(f"{w}x{h}" for _, w, h in built)
        print(f"{source_name} -> screens/{slug}-* [{rungs}]")
        for slot in slots:
            print(f"    slot: {slot}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args not in ([], ["--check"]):
        sys.exit(__doc__)
    main(check=bool(args))
