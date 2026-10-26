"""
Shared page chrome for the 2026 redesign: the floating nav, the phone menu
sheet and the compact footer, as HTML strings.

The hand-written pages carry the same markup inline. Pages built by a script
(scripts/generate_comparisons.py) import it from here so there is one copy to
change. Styles live in /assets/ff26.css and behaviour in /assets/ff26.js.
"""

APP_STORE = "https://apps.apple.com/us/app/foodieflow-meal-planner/id6760259767"
PLAY_STORE = "https://play.google.com/store/apps/details?id=com.foodieflow.app"

FONTS = (
    '<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:'
    'opsz,wght@12..96,500..800&family=Inter:wght@400;500;600;700&display=swap" '
    'rel="stylesheet" />'
)

NAV_LINKS = [
    ("features", "Features", "/#features"),
    ("pro", "Pro", "/#pro"),
    ("compare", "Compare", "/compare/"),
    ("blog", "Blog", "/blog/"),
    ("support", "Support", "/support/"),
]

SHEET_LINKS = [
    ("features", "Features", "/#features"),
    ("how", "How it works", "/#how-it-works"),
    ("pro", "Pro Chef", "/#pro"),
    ("compare", "Compare apps", "/compare/"),
    ("blog", "Blog", "/blog/"),
    ("support", "Support", "/support/"),
]

ARROW = (
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M5 12h14M13 6l6 6-6 6"/></svg>'
)
CHEVRON = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9AA0A8" '
    'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M9 6l6 6-6 6"/></svg>'
)


def nav(current=""):
    """Floating nav plus the phone menu sheet. `current` is a NAV_LINKS key."""
    def here(key):
        return ' aria-current="page"' if key == current else ""

    links = "\n".join(
        f'        <a href="{href}"{here(key)}>{label}</a>' for key, label, href in NAV_LINKS
    )
    sheet_links = "\n".join(
        f'      <a href="{href}"{here(key)}>{label}{CHEVRON}</a>' for key, label, href in SHEET_LINKS
    )
    return f"""<div class="ff-top">
  <div class="ff-wrap">
    <nav id="main-nav" class="ff-nav" aria-label="Main">
      <a class="ff-brand" href="/" aria-label="FoodieFlow home"><img src="/favicon.png" alt="" width="40" height="40" /><span>FoodieFlow</span></a>
      <div class="ff-navlinks">
{links}
      </div>
      <div class="ff-navend">
        <a class="ff-btn ff-btn--sm" href="/#download">Get the app {ARROW}</a>
        <button class="ff-menu-btn" type="button" aria-label="Open menu" aria-expanded="false" aria-controls="ff-sheet"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M4 8h16M4 16h16"/></svg></button>
      </div>
    </nav>
  </div>
</div>

<div class="ff-sheet" id="ff-sheet" hidden>
  <div class="ff-sheet__scrim" data-close></div>
  <section class="ff-sheet__panel" role="dialog" aria-modal="true" aria-label="Menu">
    <span class="ff-sheet__grip" aria-hidden="true"></span>
    <div class="ff-sheet__head">
      <span class="ff-brand"><img src="/favicon.png" alt="" width="36" height="36" /><span>FoodieFlow</span></span>
      <button class="ff-sheet__close" type="button" aria-label="Close menu" data-close><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button>
    </div>
    <div class="ff-sheet__links" role="navigation" aria-label="Menu links">
{sheet_links}
    </div>
    <div class="ff-sheet__stores">
      <a href="{APP_STORE}" target="_blank" rel="noopener noreferrer">App Store</a>
      <a href="{PLAY_STORE}" target="_blank" rel="noopener noreferrer">Google Play</a>
    </div>
    <p class="ff-sheet__note">Free to download. Pro Chef from <span class="rc-price-inline">£3.99</span> a month.</p>
  </section>
</div>
"""


def footer(year="2026"):
    """Compact footer used on every page except the homepage."""
    return f"""<footer class="ff-footer">
  <div class="ff-footer__compact">
    <span><img src="/favicon.png" alt="" width="28" height="28" loading="lazy" /><span>© <span data-year>{year}</span> AWD Labs</span></span>
    <div class="ff-footer__links" role="navigation" aria-label="Footer">
      <a href="/compare/">Compare</a>
      <a href="/food-waste-calculator/">Food waste calculator</a>
      <a href="/support/">Support</a>
      <a href="/privacy/">Privacy</a>
      <a href="/terms/">Terms</a>
    </div>
  </div>
</footer>
"""


SCRIPTS = '<script src="/assets/ff26.js" defer></script>\n<script src="/pricing.js"></script>\n'
