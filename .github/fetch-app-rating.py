#!/usr/bin/env python3
"""
Fetches FoodieFlow's live App Store rating from Apple's public lookup API
and writes it into the homepage, between the app-rating markers.
Called by .github/workflows/update-pricing.yml. No API key needed.

The homepage shows the rating in two places, each between its own markers:
  app-rating          the hero's check row ("5.0 from 3 App Store ratings")
  app-rating-summary  the score card beside the reviews

Uses only the Python standard library, so no pip install is needed.
"""
import json, os, re, sys
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

APP_ID   = "6760259767"
COUNTRY  = os.environ.get("APP_STORE_COUNTRY", "gb").lower()
APP_URL  = f"https://apps.apple.com/{COUNTRY}/app/foodieflow-meal-planner/id{APP_ID}"
PAGE     = "index.html"
STAR     = '<path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>'


def block_re(name):
    return re.compile(rf"(<!-- {name}:start[^>]*-->\n).*?(\n[ \t]*<!-- {name}:end -->)", re.S)


def stars(average, size):
    filled = round(average)
    return "".join(
        f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="currentColor"'
        f'{"" if i < filled else " class=\"is-empty\""}>{STAR}</svg>'
        for i in range(5)
    )


# ── 1. Ask Apple for the rating ──────────────────────────────────────────────
url = f"https://itunes.apple.com/lookup?id={APP_ID}&country={COUNTRY}"
try:
    with urlopen(url, timeout=20) as resp:
        results = json.load(resp).get("results", [])
except (HTTPError, URLError) as exc:
    print(f"ERROR: App Store lookup failed: {exc}")
    sys.exit(1)

if not results:
    print(f"ERROR: App {APP_ID} not found on the {COUNTRY.upper()} App Store.")
    sys.exit(1)

average = float(results[0].get("averageUserRating") or 0)
count   = int(results[0].get("userRatingCount") or 0)
print(f"App Store ({COUNTRY.upper()}): {average:.2f} from {count} ratings")

# ── 2. Build the blocks ──────────────────────────────────────────────────────
# With no ratings yet both blocks are left empty, rather than showing an empty
# or made-up score.
noun = "rating" if count == 1 else "ratings"
blocks = {"app-rating": "", "app-rating-summary": ""}
if count:
    blocks["app-rating"] = (
        f'      <li><span class="stars" role="img" aria-label="Rated {average:.1f} out of 5 on the App Store">'
        f"{stars(average, 13)}</span>"
        f'<a href="{APP_URL}" target="_blank" rel="noopener noreferrer">{average:.1f} from {count} App Store {noun}</a></li>'
    )
    blocks["app-rating-summary"] = (
        f'    <a class="rating-sum" href="{APP_URL}" target="_blank" rel="noopener noreferrer" data-reveal>\n'
        f"      <b>{average:.1f}</b>\n"
        f'      <span><span class="stars" role="img" aria-label="Rated {average:.1f} out of 5">{stars(average, 14)}</span>'
        f"From {count} App Store {noun}</span>\n"
        f"    </a>"
    )

# ── 3. Write them into the page ──────────────────────────────────────────────
html = open(PAGE, encoding="utf-8").read()
updated = html
for name, block in blocks.items():
    rx = block_re(name)
    if not rx.search(updated):
        print(f"ERROR: {name} markers not found in {PAGE}.")
        sys.exit(1)
    updated = rx.sub(lambda m: m.group(1) + block + m.group(2), updated, count=1)

if updated == html:
    print("Rating unchanged.")
else:
    open(PAGE, "w", encoding="utf-8").write(updated)
    print(f"Updated {PAGE}.")
