#!/usr/bin/env python3
"""
Programmatic SEO — Stage 1: Competitor Comparison Pages.

Reads data/competitors.json and generates:
  - /compare/index.html                          (hub page)
  - /compare/foodieflow-vs-<slug>/index.html     (one page per competitor)
  - /sitemap.xml                                 (all indexable pages)
  - /robots.txt                                  (points crawlers at the sitemap)

The site is a static, hand-authored HTML site served from GitHub Pages, so
these pages are generated once and committed. Re-run this script after editing
the data file to regenerate every page:

    python3 scripts/generate_comparisons.py

Pages use the 2026 design layer (/assets/ff26.css and /assets/ff26.js) and the
shared nav and footer in scripts/site_chrome.py, so they match the hand-written
pages.

The sitemap and robots.txt are only rewritten with --sitemap. The sitemap this
builds lists the comparison pages and STATIC_PAGES only, so running it as-is
would drop the blog posts and tools that were added to sitemap.xml by hand.

"Last updated" on the pages comes from comparison_matrix.last_verified in the
data file. Change it when the competitor details are re-checked, not on every
run, so the date says when the facts were last confirmed.
"""

import html
import json
import os
import sys
from datetime import date

import site_chrome as chrome

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, "data", "competitors.json")
SITE_URL = "https://foodieflow.app"
TODAY = date.today()

# Static, indexable pages that already exist in the repo, for the sitemap.
STATIC_PAGES = ["/", "/download/", "/support/", "/privacy/", "/terms/"]


def esc(text):
    return html.escape(str(text), quote=True)


# --- Page CSS ---------------------------------------------------------------
# Tokens, nav, footer, buttons and motion come from /assets/ff26.css. These are
# only the pieces specific to the comparison pages.
STYLES = """
    .crumbs { padding-top: 28px; font-size: 13px; color: var(--muted); display: flex; flex-wrap: wrap; gap: 6px; }
    .crumbs a { color: var(--muted) !important; text-decoration: none; }
    .crumbs a:hover { color: var(--ink) !important; }
    .c-head { padding-top: 56px; padding-bottom: 72px; display: flex; flex-direction: column; align-items: center; gap: 26px; text-align: center; }
    .c-head h1 { max-width: 900px; }
    .c-head .ff-lede { max-width: 640px; }
    .marks { display: flex; align-items: center; gap: 18px; }
    .marks img, .marks .mono { width: 88px; height: 88px; border-radius: 26px; box-shadow: 0 20px 40px -20px rgba(14,17,22,.4); }
    .marks img { background: #fff; }
    .marks .mono { background: var(--paper-2); color: var(--ink-3); display: flex; align-items: center; justify-content: center; font-family: var(--display); font-size: 34px; font-weight: 700; }
    .marks .mono.sm { width: 64px; height: 64px; border-radius: 20px; font-size: 24px; }
    .marks i { font-style: normal; font-family: var(--display); font-size: 22px; font-weight: 700; color: var(--muted); }
    .ctas { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }

    .sec { padding-bottom: 96px; }
    .table-card { border-radius: 40px; background: #fff; padding: 12px 12px 20px; box-shadow: 0 1px 2px rgba(14,17,22,.04); }
    .scroll { overflow-x: auto; }
    table.matrix { width: 100%; border-collapse: separate; border-spacing: 0; }
    table.matrix caption { text-align: left; padding: 20px 24px 8px; font-family: var(--display); font-size: 26px; font-weight: 700; letter-spacing: -.6px; }
    table.matrix thead th { padding: 12px 8px 16px; font-size: 14px; font-weight: 600; color: var(--muted); text-align: center; white-space: nowrap; }
    table.matrix thead th:first-child { text-align: left; padding-left: 24px; }
    table.matrix thead th.us span { height: 40px; padding: 0 16px; border-radius: 20px; background: var(--ink); color: #fff; display: inline-flex; align-items: center; gap: 8px; }
    table.matrix thead th.us img { width: 22px; height: 22px; border-radius: 7px; background: #fff; }
    table.matrix tbody th[scope="colgroup"] { padding: 22px 24px 8px; text-align: left; font-size: 13px; font-weight: 600; color: var(--muted); }
    table.matrix td { height: 60px; padding: 0 8px; text-align: center; }
    table.matrix td.label { text-align: left; padding: 14px 24px; font-size: 16px; font-weight: 500; border-radius: 18px 0 0 18px; }
    table.matrix td:last-child { border-radius: 0 18px 18px 0; }
    table.matrix tr.alt td { background: #FAFAF8; }
    table.matrix tbody tr:not(.grp) { transition: background-color .25s; }
    table.matrix tbody tr:not(.grp):hover td { background: var(--blue-lt); }
    table.matrix col.c { width: 180px; }
    .yes, .yes-us, .no { width: 32px; height: 32px; border-radius: 16px; display: inline-flex; align-items: center; justify-content: center; vertical-align: middle; }
    .yes-us { background: var(--blue); color: #fff; }
    .yes { background: var(--line); color: var(--ink); }
    .no { color: var(--faint); }
    .yes svg, .yes-us svg, .no svg { width: 16px; height: 16px; fill: none; stroke: currentColor; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
    html.ff-js .table-card.is-in .yes-us { animation: tick .5s var(--ease) both; animation-delay: var(--t, 0s); }
    @keyframes tick { from { transform: scale(.4); opacity: 0; } to { transform: none; opacity: 1; } }
    .updated { margin: 18px 8px 0; font-size: 13px; color: var(--muted); }

    .grid3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 20px; }
    .why { border-radius: 32px; background: #fff; padding: 32px; display: flex; flex-direction: column; gap: 14px; }
    .why.dark { background: var(--ink); color: #fff; }
    .why h3 { margin: 0; font-family: var(--display); font-size: 26px; font-weight: 700; letter-spacing: -.6px; line-height: 1.1; }
    .why p { margin: 0; font-size: 15px; line-height: 1.6; color: var(--ink-3); }
    .why.dark p { color: rgba(255,255,255,.72); }
    .why.dark .ff-tile { background: rgba(245,185,53,.16); color: var(--amber); }
    .sec h2.big { margin: 0 0 32px; font-family: var(--display); font-size: 52px; font-weight: 700; letter-spacing: -1.8px; line-height: 1; }

    .split { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 20px; align-items: start; }
    .fair { border-radius: 36px; background: var(--paper-2); padding: 44px; display: flex; flex-direction: column; gap: 16px; }
    .fair small { font-size: 13px; font-weight: 600; color: var(--ink-3); }
    .fair h3 { margin: 0; font-family: var(--display); font-size: 34px; font-weight: 700; letter-spacing: -1px; line-height: 1.05; }
    .fair ul { margin: 0; padding: 0; list-style: none; display: flex; flex-direction: column; gap: 12px; font-size: 16px; line-height: 1.5; color: var(--ink-2); }
    .fair li { display: flex; gap: 10px; }
    .fair li::before { content: ""; width: 6px; height: 6px; border-radius: 3px; background: var(--ink); margin-top: 9px; flex-shrink: 0; }
    .faq { border-radius: 36px; background: #fff; padding: 12px 28px; }

    .more-card { border-radius: 28px; background: #fff; padding: 24px 24px 24px 28px; display: flex; align-items: center; justify-content: space-between; gap: 16px; text-decoration: none; color: var(--ink) !important; }
    .more-card span.t { display: flex; flex-direction: column; gap: 2px; }
    .more-card small { font-size: 13px; color: var(--muted); }
    .more-card b { font-family: var(--display); font-size: 24px; font-weight: 700; letter-spacing: -.5px; }
    .more-card p { margin: 6px 0 0; font-size: 14px; line-height: 1.5; color: var(--muted); }
    .more-card .go { width: 44px; height: 44px; border-radius: 22px; background: var(--paper); display: flex; align-items: center; justify-content: center; flex-shrink: 0; transition: transform .3s var(--ease); }
    .more-card:hover .go { transform: translateX(4px); }
    .more-card.dark { background: var(--ink); color: #fff !important; }
    .more-card.dark small, .more-card.dark p { color: rgba(255,255,255,.65); }
    .more-card.dark .go { background: rgba(255,255,255,.12); }
    .more h2 { margin: 0 0 24px; font-family: var(--display); font-size: 32px; font-weight: 700; letter-spacing: -1px; }

    @media (max-width: 1020px) {
      .grid3, .split { grid-template-columns: 1fr; }
      table.matrix col.c { width: 110px; }
    }
    @media (max-width: 640px) {
      .c-head { padding-top: 32px; padding-bottom: 48px; }
      .marks img, .marks .mono { width: 64px; height: 64px; border-radius: 20px; font-size: 26px; }
      .marks .mono.sm { width: 52px; height: 52px; font-size: 20px; }
      .marks { gap: 12px; }
      .table-card { border-radius: 28px; padding: 6px 4px 12px; }
      table.matrix caption { padding: 16px 14px 6px; font-size: 22px; }
      table.matrix thead th:first-child, table.matrix tbody th[scope="colgroup"] { padding-left: 14px; }
      table.matrix td.label { padding: 12px 8px 12px 14px; font-size: 14px; }
      table.matrix col.c { width: 72px; }
      table.matrix thead th { font-size: 12px; white-space: normal; }
      table.matrix thead th.us span { height: 32px; padding: 0 10px; font-size: 12px; }
      table.matrix thead th.us img { display: none; }
      table.matrix.wide { min-width: 520px; }
      .sec { padding-bottom: 64px; }
      .sec h2.big { font-size: 36px; letter-spacing: -1.2px; }
      .fair, .why { padding: 28px; border-radius: 28px; }
      .faq { padding: 4px 20px; border-radius: 28px; }
    }
    @media (prefers-reduced-motion: reduce) {
      html.ff-js .table-card.is-in .yes-us { animation: none; }
      .more-card .go { transition: none; }
    }
"""

# --- Shared fragments -------------------------------------------------------

def head(title, description, canonical, jsonld=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}" />
  <link rel="canonical" href="{esc(canonical)}" />
  <meta name="theme-color" content="#F3F3F0" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{esc(canonical)}" />
  <meta property="og:site_name" content="FoodieFlow" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:image" content="{SITE_URL}/logo.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:image" content="{SITE_URL}/logo.png" />
  <link rel="icon" href="/favicon.png" type="image/png" />
  <link rel="apple-touch-icon" href="/favicon.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  {chrome.FONTS}
  <link rel="stylesheet" href="/assets/ff26.css" />
{jsonld}  <style>{STYLES}</style>
</head>
<body class="ff-page">

{chrome.nav("compare")}"""


def tail():
    return f"""
{chrome.footer(TODAY.year)}
{chrome.SCRIPTS}<script>
  /* Stagger the FoodieFlow ticks down the table as it scrolls in. */
  document.querySelectorAll('.table-card .yes-us').forEach(function (el, i) {{
    el.style.setProperty('--t', Math.min(i, 30) * 0.03 + 's');
  }});
</script>
</body>
</html>
"""


ARROW_BTN = (
    '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
    'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M5 12h14M13 6l6 6-6 6"/></svg>'
)
CHEV = (
    '<span class="ff-acc__chev"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" '
    'stroke="currentColor" stroke-width="2.6" stroke-linecap="round" aria-hidden="true">'
    '<path d="M6 9l6 6 6-6"/></svg></span>'
)

# Icons for the three "why people switch" cards: fridge, sparkle, link.
REASON_ICONS = [
    ("green", '<rect x="6" y="3" width="12" height="18" rx="2.5"/><path d="M6 10h12M9 6.5v1M9 13v2"/>'),
    ("amber", '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/>'),
    ("blue", '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>'),
]


# Ticks and dashes carry a text label (role="img"), so the tables stay readable
# to crawlers and screen readers rather than being a grid of bare shapes.
def matrix_cell(value, is_us=False):
    if value:
        cls = "yes-us" if is_us else "yes"
        return (f'<td><span class="{cls}" role="img" aria-label="Yes"><svg viewBox="0 0 24 24" aria-hidden="true">'
                '<path d="M5 12.5l4.5 4.5L19 7.5"/></svg></span></td>')
    return ('<td><span class="no" role="img" aria-label="No"><svg viewBox="0 0 24 24" aria-hidden="true">'
            '<path d="M6 12h12"/></svg></span></td>')


def matrix_body(rows, columns):
    """Rows grouped under a heading row each, zebra-striped within a group."""
    out, group, i = [], None, 0
    span = len(columns) + 2
    for row in rows:
        if row.get("group") != group:
            group, i = row.get("group"), 0
            if out:
                out.append("          </tbody>")
            out.append("          <tbody>")
            out.append(f'            <tr class="grp"><th scope="colgroup" colspan="{span}">{esc(group)}</th></tr>')
        cells = "".join(matrix_cell(row.get(s, False)) for s in columns)
        alt = ' class="alt"' if i % 2 == 0 else ""
        out.append(
            f'            <tr{alt}><td class="label">{esc(row["label"])}</td>'
            f'{matrix_cell(row.get("foodieflow", False), is_us=True)}{cells}</tr>'
        )
        i += 1
    out.append("          </tbody>")
    return "\n".join(out)


def matrix_head(names):
    others = "".join(f'<th scope="col">{esc(n)}</th>' for n in names)
    return (
        '<thead><tr><th scope="col"><span class="ff-sr">Feature</span></th>'
        '<th scope="col" class="us"><span><img src="/favicon.png" alt="" width="22" height="22" />FoodieFlow</span></th>'
        f"{others}</tr></thead>"
    )


def price_span(text):
    # Wrap the price so pricing.js can swap in the visitor's App Store price.
    return text.replace("£3.99", '<span class="rc-price-inline">£3.99</span>')


def render_comparison(data, comp, others):
    name = comp["name"]
    slug = comp["slug"]
    canonical = f"{SITE_URL}/compare/foodieflow-vs-{slug}/"

    title = f"{name} Alternative: FoodieFlow vs {name} Compared"
    description = (
        f"Looking for a {name} alternative? We compared FoodieFlow and {name} on meal "
        f"ideas, weekly planning, shopping lists, recipe import and price."
    )

    reasons = []
    for i, r in enumerate(comp["switch_reasons"]):
        tone, icon = REASON_ICONS[i % len(REASON_ICONS)]
        dark = " dark" if i == 1 else ""
        reasons.append(f"""      <article class="why{dark} ff-lift" data-reveal>
        <span class="ff-tile ff-tile--{tone}"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{icon}</svg></span>
        <h3>{esc(r['title'])}</h3>
        <p>{esc(r['body'])}</p>
      </article>""")

    strengths = "\n".join(f"          <li>{esc(s)}</li>" for s in comp["competitor_strengths"])

    faq_items, faq_ld = [], []
    for i, f in enumerate(comp["faqs"]):
        faq_items.append(f"""        <div class="ff-acc__item">
          <button class="ff-acc__q" type="button" aria-expanded="{'true' if i == 0 else 'false'}">{esc(f['q'])}{CHEV}</button>
          <div class="ff-acc__a"><div><p>{price_span(esc(f['a']))}</p></div></div>
        </div>""")
        faq_ld.append({"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}})

    more = [f"""      <a class="more-card ff-lift" href="/compare/foodieflow-vs-{o['slug']}/" data-reveal>
        <span class="t"><small>FoodieFlow vs</small><b>{esc(o['name'])}</b></span>
        <span class="go">{ARROW_BTN}</span>
      </a>""" for o in others]
    more.append(f"""      <a class="more-card dark ff-lift" href="/blog/best-meal-planning-apps-2026/" data-reveal>
        <span class="t"><small>All 8 apps, side by side</small><b>Best apps of 2026</b></span>
        <span class="go">{ARROW_BTN}</span>
      </a>""")

    jsonld_obj = [
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
                {"@type": "ListItem", "position": 2, "name": "Compare", "item": f"{SITE_URL}/compare/"},
                {"@type": "ListItem", "position": 3, "name": f"FoodieFlow vs {name}", "item": canonical},
            ],
        },
        {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq_ld},
    ]
    jsonld = '  <script type="application/ld+json">' + json.dumps(jsonld_obj, ensure_ascii=False) + "</script>\n"

    matrix = data["comparison_matrix"]
    body = f"""
<main>
<nav class="ff-wrap crumbs" aria-label="Breadcrumb">
  <a href="/">Home</a><span aria-hidden="true">›</span><a href="/compare/">Compare</a><span aria-hidden="true">›</span><span>FoodieFlow vs {esc(name)}</span>
</nav>

<header class="ff-wrap c-head">
  <div class="marks ff-pop">
    <img src="/favicon.png" alt="FoodieFlow" width="88" height="88" />
    <i>vs</i>
    <span class="mono" role="img" aria-label="{esc(name)}">{esc(name[0])}</span>
  </div>
  <span class="ff-eyebrow ff-rise">App comparison</span>
  <h1 class="ff-h1 ff-rise">Looking for a {esc(name)} alternative?</h1>
  <p class="ff-lede ff-rise-2">{esc(comp['summary'])} FoodieFlow plans around your own recipes and what is already in your kitchen. Here is how they compare.</p>
  <div class="ctas ff-rise-3">
    <a class="ff-btn" href="/#download">Try FoodieFlow free</a>
    <a class="ff-btn ff-btn--light" href="#compare">See the comparison</a>
  </div>
</header>

<section id="compare" class="ff-wrap sec">
  <div class="table-card" data-reveal>
    <div class="scroll">
      <table class="matrix">
        <caption>Feature by feature</caption>
        <colgroup><col /><col class="c" /><col class="c" /></colgroup>
        {matrix_head([name])}
{matrix_body(matrix["rows"], [slug])}
      </table>
    </div>
  </div>
  <p class="updated">Comparison last updated {esc(matrix['last_verified'])}. Competitor features and pricing change over time, so please check current details on each provider's site.</p>
</section>

<section class="ff-wrap sec">
  <h2 class="big">Why people switch.</h2>
  <div class="grid3">
{chr(10).join(reasons)}
  </div>
</section>

<section class="ff-wrap sec">
  <div class="split">
    <div class="fair" data-reveal>
      <small>To be fair</small>
      <h3>Where {esc(name)} shines</h3>
      <ul>
{strengths}
      </ul>
    </div>
    <div class="faq ff-acc" data-reveal>
{chr(10).join(faq_items)}
    </div>
  </div>
</section>

<section class="ff-wrap sec more">
  <h2>More comparisons</h2>
  <div class="grid3">
{chr(10).join(more)}
  </div>
</section>
</main>
"""
    return head(title, description, canonical, jsonld) + body + tail()


def render_hub(data):
    canonical = f"{SITE_URL}/compare/"
    title = "FoodieFlow vs Mealime, Paprika & Plan to Eat (2026)"
    description = (
        "Which meal planning app is best? FoodieFlow, Mealime, Paprika and Plan to Eat "
        "compared side by side on meal ideas, weekly plans, shopping lists and recipe import."
    )
    comps = data["competitors"]
    name_by_slug = {c["slug"]: c["name"] for c in comps}
    matrix = data["comparison_matrix"]
    cols = matrix["columns"]

    cards = [f"""      <a class="more-card ff-lift" href="/compare/foodieflow-vs-{c['slug']}/" data-reveal>
        <span class="t"><small>FoodieFlow vs</small><b>{esc(c['name'])}</b><p>{esc(c['category'])}</p></span>
        <span class="go">{ARROW_BTN}</span>
      </a>""" for c in comps]

    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": f"FoodieFlow vs {c['name']}",
             "url": f"{SITE_URL}/compare/foodieflow-vs-{c['slug']}/"}
            for i, c in enumerate(comps)
        ],
    }
    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
            {"@type": "ListItem", "position": 2, "name": "Compare", "item": canonical},
        ],
    }
    jsonld = '  <script type="application/ld+json">' + json.dumps([breadcrumb, item_list], ensure_ascii=False) + "</script>\n"
    monos = "\n    ".join(
        f'<span class="mono sm" role="img" aria-label="{esc(name_by_slug[s])}">{esc(name_by_slug[s][0])}</span>' for s in cols
    )
    colgroup = "<colgroup><col />" + '<col class="c" />' * (len(cols) + 1) + "</colgroup>"

    body = f"""
<main>
<nav class="ff-wrap crumbs" aria-label="Breadcrumb">
  <a href="/">Home</a><span aria-hidden="true">›</span><span>Compare</span>
</nav>

<header class="ff-wrap c-head">
  <div class="marks ff-pop">
    <img src="/favicon.png" alt="FoodieFlow" width="88" height="88" />
    <i>vs</i>
    {monos}
  </div>
  <span class="ff-eyebrow ff-rise">Comparisons</span>
  <h1 class="ff-h1 ff-rise">FoodieFlow vs the alternatives.</h1>
  <p class="ff-lede ff-rise-2">Thinking of switching meal planning apps? Here is FoodieFlow next to Mealime, Paprika and Plan to Eat, including the smart planning and recipe import features you won't find elsewhere.</p>
  <div class="ctas ff-rise-3">
    <a class="ff-btn" href="/#download">Try FoodieFlow free</a>
    <a class="ff-btn ff-btn--light" href="#compare">See the comparison</a>
  </div>
</header>

<section id="compare" class="ff-wrap sec">
  <div class="table-card" data-reveal>
    <div class="scroll">
      <table class="matrix wide">
        <caption>How FoodieFlow compares</caption>
        {colgroup}
        {matrix_head([name_by_slug.get(s, s) for s in cols])}
{matrix_body(matrix["rows"], cols)}
      </table>
    </div>
  </div>
  <p class="updated">Comparisons last updated {esc(matrix['last_verified'])}. Competitor features and pricing change over time, so please check current details on each provider's site.</p>
</section>

<section class="ff-wrap sec more">
  <h2>Read the full comparisons</h2>
  <div class="grid3">
{chr(10).join(cards)}
  </div>
</section>
</main>
"""
    return head(title, description, canonical, jsonld) + body + tail()


def render_sitemap(data):
    urls = list(STATIC_PAGES)
    urls.append("/compare/")
    for c in data["competitors"]:
        urls.append(f"/compare/foodieflow-vs-{c['slug']}/")
    lastmod = TODAY.isoformat()
    entries = []
    for u in urls:
        priority = "1.0" if u == "/" else ("0.8" if u.startswith("/compare") else "0.6")
        entries.append(
            f"  <url>\n    <loc>{SITE_URL}{u}</loc>\n"
            f"    <lastmod>{lastmod}</lastmod>\n"
            f"    <priority>{priority}</priority>\n  </url>"
        )
    body = "\n".join(entries)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n"
    )


ROBOTS = f"""User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

Sitemap: {SITE_URL}/sitemap.xml
"""


def write(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print(f"  wrote {os.path.relpath(path, ROOT)}")


def main():
    with open(DATA_FILE, encoding="utf-8") as fh:
        data = json.load(fh)

    comps = data["competitors"]
    print("Generating comparison pages...")
    for c in comps:
        others = [o for o in comps if o["slug"] != c["slug"]][:3]
        out = os.path.join(ROOT, "compare", f"foodieflow-vs-{c['slug']}", "index.html")
        write(out, render_comparison(data, c, others))

    write(os.path.join(ROOT, "compare", "index.html"), render_hub(data))
    if "--sitemap" in sys.argv[1:]:
        write(os.path.join(ROOT, "sitemap.xml"), render_sitemap(data))
        write(os.path.join(ROOT, "robots.txt"), ROBOTS)
        print(f"Done. {len(comps)} comparison pages + hub + sitemap + robots.")
    else:
        print(f"Done. {len(comps)} comparison pages + hub (sitemap untouched; pass --sitemap to rebuild it).")


if __name__ == "__main__":
    main()
