#!/usr/bin/env python3
"""
Fetches FoodieFlow's live App Store rating from Apple's public lookup API
and writes it into the homepage hero, between the app-rating markers.
Called by .github/workflows/update-pricing.yml. No API key needed.

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
BLOCK_RE = re.compile(r"(<!-- app-rating:start[^>]*-->\n).*?(\n[ \t]*<!-- app-rating:end -->)", re.S)

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

# ── 2. Build the hero block ──────────────────────────────────────────────────
pad = " " * 8
if count:
    filled = round(average)
    stars = "\n".join(
        f'{pad}    <svg class="star-svg{"" if i < filled else " is-empty"}" viewBox="0 0 24 24">{STAR}</svg>'
        for i in range(5)
    )
    noun = "rating" if count == 1 else "ratings"
    block = (
        f'{pad}<div class="hero-rating">\n'
        f'{pad}  <div class="stars" role="img" aria-label="Rated {average:.1f} out of 5 on the App Store">\n'
        f"{stars}\n"
        f"{pad}  </div>\n"
        f'{pad}  <a class="rating-text" href="{APP_URL}" target="_blank" rel="noopener">{average:.1f} from {count} App Store {noun}</a>\n'
        f'{pad}  <span class="rating-div" aria-hidden="true"></span>\n'
        f'{pad}  <span class="rating-platform">Available on iOS &amp; Android</span>\n'
        f"{pad}</div>"
    )
else:
    # No ratings yet, so show no stars rather than an empty or made-up score.
    block = (
        f'{pad}<div class="hero-rating">\n'
        f'{pad}  <span class="rating-platform">Available on iOS &amp; Android</span>\n'
        f"{pad}</div>"
    )

# ── 3. Write it into the page ────────────────────────────────────────────────
html = open(PAGE, encoding="utf-8").read()
if not BLOCK_RE.search(html):
    print(f"ERROR: app-rating markers not found in {PAGE}.")
    sys.exit(1)
updated = BLOCK_RE.sub(lambda m: m.group(1) + block + m.group(2), html, count=1)
if updated == html:
    print("Rating unchanged.")
else:
    open(PAGE, "w", encoding="utf-8").write(updated)
    print(f"Updated {PAGE}.")
