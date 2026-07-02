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

Design system (fonts, palette, nav, footer) mirrors the existing pages such as
/terms/index.html so the generated pages feel native to foodieflow.app.
"""

import html
import json
import os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, "data", "competitors.json")
SITE_URL = "https://foodieflow.app"
TODAY = date.today()
UPDATED_LABEL = TODAY.strftime("%B %Y")

# Static, indexable pages that already exist in the repo, for the sitemap.
STATIC_PAGES = ["/", "/beta/", "/support/", "/privacy/", "/terms/"]


def esc(text):
    return html.escape(str(text), quote=True)


# --- Shared CSS -------------------------------------------------------------
STYLES = """
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg:        hsl(210, 28%, 95%);
      --bg-warm:   hsl(210, 22%, 92%);
      --card:      hsl(0, 0%, 100%);
      --fore:      hsl(222, 47%, 13%);
      --muted:     hsl(215, 16%, 50%);
      --blue:      hsl(205, 68%, 50%);
      --blue-lt:   hsl(205, 55%, 90%);
      --amber:     hsl(205, 68%, 50%);
      --amber-dark:hsl(205, 75%, 40%);
      --gold:      hsl(42, 90%, 52%);
      --border:    hsl(210, 28%, 88%);
      --primary-dark: hsl(205, 70%, 40%);
      --secondary:    hsl(195, 60%, 94%);
      --good:      hsl(150, 55%, 42%);
      --bad:       hsl(0, 0%, 72%);
      --radius:    1.3rem;
      --nav-h:     64px;
    }
    html { scroll-behavior: smooth; }
    body { font-family: "PT Sans", sans-serif; background: var(--bg); color: var(--fore); min-height: 100vh; overflow-x: hidden; line-height: 1.5; }
    :focus-visible { outline: 2px solid var(--amber); outline-offset: 3px; border-radius: 4px; }
    a { color: inherit; }

    /* NAV — identical to the homepage header */
    nav {
      position: sticky; top: 0; z-index: 200;
      height: var(--nav-h);
      padding: 0 clamp(16px, 5vw, 80px);
      display: flex; align-items: center; justify-content: space-between;
      background: transparent;
      border-bottom: 1px solid transparent;
      transition: background 0.3s, border-color 0.3s, backdrop-filter 0.3s;
    }
    nav.scrolled {
      background: rgba(255,255,255,0.75);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom-color: rgba(0,0,0,0.08);
    }
    .logo { display: flex; align-items: center; text-decoration: none; }
    .logo img { height: 44px; width: auto; object-fit: contain; }
    .nav-links { display: flex; align-items: center; gap: 1.8rem; }
    .nav-links a { font-size: 0.88rem; color: var(--fore); text-decoration: none; font-weight: 700; opacity: 0.65; transition: color 0.2s, opacity 0.2s; }
    .nav-links a:hover { color: var(--blue); opacity: 1; }
    .nav-cta {
      display: inline-flex; align-items: center; min-height: 44px;
      background: var(--amber); color: #fff;
      padding: 10px 22px; border-radius: 8px;
      font-size: 0.88rem; font-weight: 700; text-decoration: none;
      transition: background 0.2s, transform 0.15s;
    }
    /* Beat `.nav-links a` specificity so the CTA text stays white, not grey. */
    .nav-links a.nav-cta { color: #fff; opacity: 1; }
    .nav-cta:hover { background: var(--amber-dark); transform: translateY(-1px); }
    .nav-hamburger { display: none; background: none; border: none; cursor: pointer; padding: 6px; min-height: 44px; min-width: 44px; align-items: center; justify-content: center; flex-direction: column; gap: 5px; }
    .nav-hamburger span { display: block; width: 22px; height: 2px; background: var(--fore); border-radius: 2px; transition: 0.25s; }
    .nav-hamburger.open span:nth-child(1) { transform: translateY(7px) rotate(45deg); }
    .nav-hamburger.open span:nth-child(2) { opacity: 0; }
    .nav-hamburger.open span:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }
    .mobile-menu { display: none; position: fixed; top: var(--nav-h); left: 0; right: 0; bottom: 0; background: rgba(249,248,245,0.97); backdrop-filter: blur(16px); z-index: 199; flex-direction: column; align-items: center; justify-content: center; gap: 2rem; }
    .mobile-menu.open { display: flex; }
    .mobile-menu a { font-size: 1.4rem; font-weight: 700; color: var(--fore); text-decoration: none; min-height: 44px; display: flex; align-items: center; transition: color 0.2s; }
    .mobile-menu a:hover { color: var(--amber); }
    .mobile-menu .mobile-cta { background: var(--amber); color: #fff; padding: 14px 36px; border-radius: 8px; font-size: 1rem; }
    .mobile-menu .mobile-cta:hover { background: var(--amber-dark); color: #fff; }

    /* LAYOUT */
    .wrap { max-width: 960px; margin: 0 auto; padding: 0 2rem; }
    .eyebrow { font-size: 0.72rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--blue); margin-bottom: 12px; }
    /* Breadcrumb is a <nav> for a11y but must NOT inherit the sticky header styles above. */
    nav.breadcrumb { position: static; z-index: auto; height: auto; display: block; background: transparent; backdrop-filter: none; -webkit-backdrop-filter: none; border-bottom: none; max-width: 960px; margin: 0 auto; padding: 20px 2rem 0; font-size: 0.8rem; color: var(--muted); }
    .breadcrumb a { text-decoration: none; color: var(--muted); border-bottom: 1px solid transparent; }
    .breadcrumb a:hover { color: var(--blue); border-bottom-color: var(--blue); }
    .breadcrumb span { color: var(--fore); }

    /* HERO */
    .hero { text-align: center; padding: 40px 2rem 8px; max-width: 780px; margin: 0 auto; }
    h1 { font-size: clamp(2rem, 5.5vw, 3.2rem); font-weight: 900; line-height: 1.08; letter-spacing: -0.02em; margin-bottom: 18px; }
    h1 .vs { color: var(--muted); font-weight: 700; }
    h1 .brand { color: var(--primary-dark); }
    .hero-sub { font-size: 1.05rem; color: var(--muted); line-height: 1.7; max-width: 560px; margin: 0 auto 26px; }
    .hero-ctas { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
    .btn-primary { display: inline-flex; align-items: center; min-height: 48px; background: var(--amber); color: #fff; padding: 13px 28px; border-radius: 10px; font-weight: 700; text-decoration: none; transition: background 0.2s, transform 0.15s; }
    .btn-primary:hover { background: var(--amber-dark); transform: translateY(-1px); }
    .btn-ghost { display: inline-flex; align-items: center; min-height: 48px; background: var(--card); color: var(--fore); padding: 13px 24px; border-radius: 10px; font-weight: 700; text-decoration: none; border: 1px solid var(--border); transition: border-color 0.2s; }
    .btn-ghost:hover { border-color: var(--blue); }

    /* SECTIONS */
    section.block { padding: 44px 0; }
    .section-title { font-size: clamp(1.4rem, 3.5vw, 2rem); font-weight: 900; letter-spacing: -0.01em; margin-bottom: 10px; text-align: center; }
    .section-sub { text-align: center; color: var(--muted); max-width: 560px; margin: 0 auto 30px; }

    /* COMPARISON TABLE */
    /* Card backdrop matches the highlighted column so the rounded blue border
       has no white slivers at its corners; individual cells set their own bg. */
    .table-card { background: hsl(205, 55%, 97%); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
    table.compare { width: 100%; border-collapse: collapse; }
    table.compare th, table.compare td { padding: 14px 18px; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.92rem; }
    table.compare thead th { background: var(--secondary); font-weight: 700; font-size: 0.82rem; }
    table.compare thead th.col-us { color: var(--primary-dark); }
    table.compare tbody tr:last-child td { border-bottom: none; }
    table.compare td.feat { font-weight: 700; }
    table.compare td.val { color: var(--muted); }
    table.compare td.col-us { background: hsl(205,55%,97%); font-weight: 700; color: var(--fore); }
    .v-yes { color: var(--good); font-weight: 700; }
    .v-no { color: var(--bad); font-weight: 700; }
    .v-part { color: var(--gold); font-weight: 700; }

    /* MATRIX (hub) — Lucide tick / grey X */
    .matrix-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
    table.matrix { width: 100%; border-collapse: separate; border-spacing: 0; min-width: 560px; }
    table.matrix th, table.matrix td { padding: 13px 12px; border-bottom: 1px solid var(--border); text-align: center; }
    table.matrix tbody td { background: var(--card); }
    table.matrix thead th { background: var(--secondary); font-size: 0.82rem; font-weight: 700; }
    table.matrix thead th.col-us, table.matrix td.col-us { background: hsl(205,55%,97%); }
    table.matrix thead th.col-us { color: var(--primary-dark); }
    table.matrix th.rowlabel, table.matrix td.rowlabel { text-align: left; font-weight: 700; font-size: 0.9rem; }
    table.matrix tbody tr:last-child td { border-bottom: none; }
    /* Highlight the FoodieFlow column with a smooth, rounded blue border. */
    table.matrix .col-us { border-left: 2px solid var(--blue); border-right: 2px solid var(--blue); }
    table.matrix thead th.col-us { border-top: 2px solid var(--blue); border-top-left-radius: 12px; border-top-right-radius: 12px; }
    table.matrix tbody tr:last-child td.col-us { border-bottom: 2px solid var(--blue); border-bottom-left-radius: 12px; border-bottom-right-radius: 12px; }
    .lucide { width: 22px; height: 22px; fill: none; stroke-width: 2.4; stroke-linecap: round; stroke-linejoin: round; vertical-align: middle; }
    .lucide.tick { stroke: var(--good); }
    .lucide.cross { stroke: var(--bad); }
    .matrix-legend { display: flex; gap: 22px; justify-content: center; flex-wrap: wrap; margin-top: 18px; font-size: 0.84rem; color: var(--muted); }
    .matrix-legend span { display: inline-flex; align-items: center; gap: 7px; }
    .matrix-legend .lucide { width: 17px; height: 17px; }

    /* SWITCH REASONS */
    .reason-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .reason-card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 22px 24px; }
    .reason-card .r-icon { width: 34px; height: 34px; border-radius: 9px; background: var(--secondary); display: grid; place-items: center; margin-bottom: 12px; }
    .reason-card .r-icon svg { width: 17px; height: 17px; stroke: var(--primary-dark); fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
    .reason-card h3 { font-size: 1.02rem; font-weight: 700; margin-bottom: 6px; }
    .reason-card p { color: var(--muted); font-size: 0.92rem; line-height: 1.65; }

    /* FAIR / STRENGTHS */
    .fair-card { background: var(--secondary); border-radius: var(--radius); padding: 26px 30px; max-width: 720px; margin: 0 auto; }
    .fair-card h3 { font-size: 1.05rem; font-weight: 700; margin-bottom: 14px; }
    .fair-card ul { list-style: none; display: flex; flex-direction: column; gap: 10px; }
    .fair-card li { padding-left: 26px; position: relative; color: var(--primary-dark); font-size: 0.95rem; line-height: 1.6; }
    .fair-card li::before { content: "✓"; position: absolute; left: 0; font-weight: 700; color: var(--good); }

    /* FAQ */
    .faq-list { max-width: 720px; margin: 0 auto; display: flex; flex-direction: column; gap: 10px; }
    .faq-item { background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 0 22px; }
    .faq-item summary { cursor: pointer; list-style: none; padding: 18px 0; font-weight: 700; display: flex; justify-content: space-between; align-items: center; gap: 12px; }
    .faq-item summary::-webkit-details-marker { display: none; }
    .faq-item summary .chev { width: 18px; height: 18px; stroke: var(--muted); fill: none; stroke-width: 2; flex-shrink: 0; transition: transform 0.2s; }
    .faq-item[open] summary .chev { transform: rotate(180deg); }
    .faq-item p { color: var(--muted); line-height: 1.7; padding: 0 0 18px; font-size: 0.94rem; }

    /* CTA */
    .cta-section { background: hsl(222,47%,10%); border-radius: var(--radius); padding: 48px 32px; text-align: center; max-width: 820px; margin: 0 auto; }
    .cta-section h2 { color: #fff; font-size: clamp(1.5rem, 4vw, 2.1rem); font-weight: 900; margin-bottom: 12px; }
    .cta-section p { color: rgba(255,255,255,0.65); max-width: 460px; margin: 0 auto 26px; }
    .store-btns { display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
    .store-btn { display: inline-flex; align-items: center; gap: 10px; background: #fff; color: var(--fore); padding: 12px 22px; border-radius: 10px; font-weight: 700; text-decoration: none; transition: transform 0.15s; }
    .store-btn:hover { transform: translateY(-2px); }
    .cta-note { color: rgba(255,255,255,0.5); font-size: 0.82rem; margin-top: 18px; }

    /* OTHER COMPARISONS — flex so 2 or 3 cards stay centred */
    .other-grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 14px; }
    .other-card { flex: 1 1 240px; max-width: 320px; background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 18px 20px; text-decoration: none; color: var(--fore); transition: border-color 0.2s, transform 0.15s; }
    .other-card:hover { border-color: var(--blue); transform: translateY(-2px); }
    .other-card .oc-vs { font-size: 0.76rem; color: var(--muted); font-weight: 700; }
    .other-card .oc-name { font-size: 1rem; font-weight: 700; margin-top: 2px; }
    .other-card .oc-arrow { color: var(--blue); font-weight: 700; font-size: 0.84rem; margin-top: 8px; display: inline-block; }

    .updated { text-align: center; font-size: 0.78rem; color: var(--muted); margin-top: 34px; }

    /* FOOTER */
    footer { border-top: 1px solid var(--border); padding: 40px 2.5rem 28px; background: var(--card); margin-top: 20px; }
    .footer-inner { max-width: 1160px; margin: 0 auto; display: grid; grid-template-columns: 2fr 1fr 1fr 1fr; gap: 40px; margin-bottom: 36px; }
    .footer-brand img { height: 44px; margin-bottom: 12px; }
    .footer-brand p { font-size: 0.84rem; color: var(--muted); line-height: 1.65; max-width: 240px; }
    .footer-col h4 { font-size: 0.77rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--fore); margin-bottom: 14px; }
    .footer-col a { display: block; font-size: 0.84rem; color: var(--muted); text-decoration: none; margin-bottom: 8px; transition: color 0.2s; }
    .footer-col a:hover { color: var(--blue); }
    .footer-bottom { max-width: 1160px; margin: 0 auto; padding-top: 22px; border-top: 1px solid var(--border); text-align: center; }
    .footer-bottom span { font-size: 0.77rem; color: var(--muted); }

    @media (max-width: 900px) {
      nav { padding: 0 1.5rem; }
      .nav-links { display: none; }
      .nav-hamburger { display: flex; }
      .reason-grid { grid-template-columns: 1fr; }
      .footer-inner { grid-template-columns: 1fr 1fr; }
    }
    @media (max-width: 600px) {
      .wrap { padding: 0 1.25rem; }
      .breadcrumb { padding: 16px 1.25rem 0; }
      table.compare th, table.compare td { padding: 11px 12px; font-size: 0.84rem; }
      .footer-inner { grid-template-columns: 1fr; }
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
  <meta name="theme-color" content="#2a7c8a" />
  <meta property="og:type" content="website" />
  <meta property="og:url" content="{esc(canonical)}" />
  <meta property="og:title" content="{esc(title)}" />
  <meta property="og:description" content="{esc(description)}" />
  <meta property="og:image" content="{SITE_URL}/logo.png" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:image" content="{SITE_URL}/logo.png" />
  <link rel="icon" href="/favicon.png" type="image/png" />
  <link rel="apple-touch-icon" href="/favicon.png" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=PT+Sans:ital,wght@0,400;0,700;1,400&display=swap" rel="stylesheet" />
{jsonld}  <style>{STYLES}</style>
</head>
<body>
"""

NAV = """<!-- NAV -->
<nav id="main-nav">
  <a href="/" class="logo"><img src="/logo.png" alt="FoodieFlow" /></a>
  <div class="nav-links">
    <a href="/#features">Features</a>
    <a href="/#how-it-works">How it works</a>
    <a href="/#pro">Pricing</a>
    <a href="/compare/">Compare</a>
    <a href="/beta" class="nav-cta">Join the Beta</a>
  </div>
  <button class="nav-hamburger" id="hamburger" aria-label="Open menu"><span></span><span></span><span></span></button>
</nav>
<div class="mobile-menu" id="mobile-menu">
  <a href="/#features" class="mobile-nav-link">Features</a>
  <a href="/#how-it-works" class="mobile-nav-link">How it works</a>
  <a href="/#pro" class="mobile-nav-link">Pricing</a>
  <a href="/compare/" class="mobile-nav-link">Compare</a>
  <a href="/beta" class="mobile-cta mobile-nav-link">Join the Beta</a>
</div>
"""

FOOTER = f"""<!-- FOOTER -->
<footer>
  <div class="footer-inner">
    <div class="footer-brand">
      <img src="/logo.png" alt="FoodieFlow" />
      <p>Meal planning made simple. Organise your meals, discover new recipes, and shop smarter — all in one app.</p>
    </div>
    <div class="footer-col">
      <h4>Product</h4>
      <a href="/#features">Features</a>
      <a href="/#how-it-works">How it works</a>
      <a href="/compare/">Compare</a>
      <a href="/#download">Download</a>
    </div>
    <div class="footer-col">
      <h4>Company</h4>
      <a href="/privacy">Privacy Policy</a>
      <a href="/terms">Terms of Use</a>
    </div>
    <div class="footer-col">
      <h4>Contact</h4>
      <a href="/support">Support</a>
    </div>
  </div>
  <div class="footer-bottom">
    <span>&copy; {TODAY.year} FoodieFlow. All rights reserved. FoodieFlow is an independent software product.</span>
  </div>
</footer>

<script>
  /* Nav scroll effect — identical to the homepage. */
  var mainNav = document.getElementById('main-nav');
  if (mainNav) {{
    var onScroll = function () {{ mainNav.classList.toggle('scrolled', window.scrollY > 80); }};
    window.addEventListener('scroll', onScroll, {{ passive: true }});
    onScroll();
  }}
  var btn = document.getElementById('hamburger');
  var menu = document.getElementById('mobile-menu');
  if (btn) {{
    btn.addEventListener('click', function () {{
      btn.classList.toggle('open');
      menu.classList.toggle('open');
      document.body.style.overflow = menu.classList.contains('open') ? 'hidden' : '';
    }});
    document.querySelectorAll('.mobile-nav-link').forEach(function (link) {{
      link.addEventListener('click', function () {{
        btn.classList.remove('open');
        menu.classList.remove('open');
        document.body.style.overflow = '';
      }});
    }});
  }}
</script>
</body>
</html>
"""

STORE_BUTTONS = """    <div class="store-btns">
      <a href="https://testflight.apple.com/join/kZ1grhwj" class="store-btn" target="_blank" rel="noopener noreferrer">
        <svg width="18" height="22" viewBox="0 0 814 1000" fill="#111" aria-hidden="true"><path d="M788.1 340.9c-5.8 4.5-108.2 62.2-108.2 190.5 0 148.4 130.3 200.9 134.2 202.2-.6 3.2-20.7 71.9-68.7 141.9-42.8 61.6-87.5 123.1-155.5 123.1s-85.5-39.5-164-39.5c-76 0-103.7 40.8-165.9 40.8s-105-57.8-155.5-127.4C46 790.7 0 663 0 541.8c0-207.5 135.4-317.3 269-317.3 70.1 0 128.4 46.4 172.5 46.4 42.8 0 109.6-49 192.5-49 30.9 0 113.8 2.6 168.9 98.3zm-234.8-181.4c31.3-36.9 53.7-88.1 53.7-139.3 0-7.1-.6-14.3-1.9-20.1-50.6 1.9-110.8 33.7-147.1 75.8-28.5 32.4-55.1 83.6-55.1 135.5 0 7.8 1.3 15.6 1.9 18.1 3.2.6 8.4 1.3 13.6 1.3 45.4 0 102.5-30.4 134.9-71.3z"/></svg>
        App Store
      </a>
      <a href="https://play.google.com/store/apps/details?id=com.foodieflow.app" class="store-btn" target="_blank" rel="noopener noreferrer">
        <svg width="18" height="20" viewBox="0 0 24 24" aria-hidden="true"><path d="M3.18 23.76a2 2 0 0 0 2.08-.21l11.39-6.58-3.22-3.22L3.18 23.76z" fill="#111"/><path d="M21.28 10.4 17.64 8.3 14.1 11.86l3.54 3.54 3.64-2.1a2 2 0 0 0 0-3.46z" fill="#111"/><path d="M3.18.24A2 2 0 0 0 2 2v20a2 2 0 0 0 1.18 1.76L13.38 12 3.18.24z" fill="#111"/><path d="M5.26.45 16.65 7.03 13.38 10.3 3.18.24A2 2 0 0 1 5.26.45z" fill="#111"/></svg>
        Google Play
      </a>
    </div>"""

# Small icon set reused across "reason" cards.
REASON_ICONS = [
    '<path d="M5 8h14M5 8a2 2 0 1 1 0-4h14a2 2 0 1 1 0 4M5 8v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8M9 12h6"/>',
    '<path d="M12 3l1.9 5.8H20l-4.9 3.6 1.9 5.8L12 14.6 7 18.2l1.9-5.8L4 8.8h6.1z"/>',
    '<path d="M20 7L9 18l-5-5"/>',
]


# Lucide icons (https://lucide.dev): "check" and "x".
TICK_SVG = (
    '<svg class="lucide tick" viewBox="0 0 24 24" role="img" aria-label="Yes">'
    '<path d="M20 6 9 17l-5-5"/></svg>'
)
CROSS_SVG = (
    '<svg class="lucide cross" viewBox="0 0 24 24" role="img" aria-label="No">'
    '<path d="M18 6 6 18"/><path d="M6 6l12 12"/></svg>'
)


def matrix_cell(value, is_us=False):
    icon = TICK_SVG if value else CROSS_SVG
    cls = ' class="col-us"' if is_us else ""
    return f"<td{cls}>{icon}</td>"


def val_class(value):
    v = value.strip().lower()
    if v in ("yes",):
        return "v-yes"
    if v in ("no",):
        return "v-no"
    if v in ("limited", "basic", "partial"):
        return "v-part"
    return ""


def render_comparison(data, comp, others):
    name = comp["name"]
    slug = comp["slug"]
    canonical = f"{SITE_URL}/compare/foodieflow-vs-{slug}/"

    title = f"FoodieFlow vs {name}: Which Meal Planning App Wins? (2026)"
    description = (
        f"FoodieFlow vs {name} compared feature by feature — smart meal suggestions, "
        f"weekly planning, automatic shopping lists, recipe import and pantry awareness. "
        f"See why people switch to FoodieFlow."
    )

    # Comparison table rows — same matrix as the hub, two columns (us vs this competitor).
    rows = []
    for row in data["comparison_matrix"]["rows"]:
        rows.append(
            f'          <tr><td class="rowlabel">{esc(row["label"])}</td>'
            f'{matrix_cell(row.get("foodieflow", False), is_us=True)}'
            f'{matrix_cell(row.get(slug, False))}</tr>'
        )
    table_rows = "\n".join(rows)

    # Reason cards
    reason_cards = []
    for i, r in enumerate(comp["switch_reasons"]):
        icon = REASON_ICONS[i % len(REASON_ICONS)]
        reason_cards.append(f"""      <div class="reason-card">
        <div class="r-icon"><svg viewBox="0 0 24 24" aria-hidden="true">{icon}</svg></div>
        <h3>{esc(r['title'])}</h3>
        <p>{esc(r['body'])}</p>
      </div>""")
    reason_html = "\n".join(reason_cards)

    # Strengths
    strengths = "\n".join(f"        <li>{esc(s)}</li>" for s in comp["competitor_strengths"])

    # FAQ + JSON-LD
    faq_items = []
    faq_ld = []
    for f in comp["faqs"]:
        faq_items.append(f"""      <details class="faq-item">
        <summary>{esc(f['q'])}<svg class="chev" viewBox="0 0 24 24" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg></summary>
        <p>{esc(f['a'])}</p>
      </details>""")
        faq_ld.append({
            "@type": "Question",
            "name": f["q"],
            "acceptedAnswer": {"@type": "Answer", "text": f["a"]},
        })
    faq_html = "\n".join(faq_items)

    # Other comparisons
    other_cards = []
    for o in others:
        other_cards.append(f"""      <a class="other-card" href="/compare/foodieflow-vs-{o['slug']}/">
        <span class="oc-vs">FoodieFlow vs</span>
        <div class="oc-name">{esc(o['name'])}</div>
        <span class="oc-arrow">Compare &rarr;</span>
      </a>""")
    other_html = "\n".join(other_cards)

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
    jsonld = (
        '  <script type="application/ld+json">'
        + json.dumps(jsonld_obj, ensure_ascii=False)
        + "</script>\n"
    )

    body = f"""{NAV}
<nav class="breadcrumb" aria-label="Breadcrumb">
  <a href="/">Home</a> &rsaquo; <a href="/compare/">Compare</a> &rsaquo; <span>FoodieFlow vs {esc(name)}</span>
</nav>

<header class="hero">
  <p class="eyebrow">App comparison</p>
  <h1>FoodieFlow <span class="vs">vs</span> {esc(name)}</h1>
  <p class="hero-sub">{esc(comp['summary'])} Here's how the two apps compare — and why meal planners are switching to FoodieFlow.</p>
  <div class="hero-ctas">
    <a href="/beta" class="btn-primary">Try FoodieFlow free</a>
    <a href="#compare" class="btn-ghost">See the comparison</a>
  </div>
</header>

<section class="block" id="compare">
  <div class="wrap">
    <h2 class="section-title">Feature comparison</h2>
    <p class="section-sub">FoodieFlow and {esc(name)} side by side, feature for feature.</p>
    <div class="table-card">
      <div class="matrix-scroll">
        <table class="matrix">
          <thead>
            <tr><th class="rowlabel">Feature</th><th class="col-us">FoodieFlow</th><th>{esc(name)}</th></tr>
          </thead>
          <tbody>
{table_rows}
          </tbody>
        </table>
      </div>
    </div>
    <div class="matrix-legend">
      <span>{TICK_SVG} Included</span>
      <span>{CROSS_SVG} Not available</span>
    </div>
  </div>
</section>

<section class="block" style="background:var(--bg-warm)">
  <div class="wrap">
    <h2 class="section-title">Why people switch to FoodieFlow</h2>
    <p class="section-sub">Three things FoodieFlow does that make the daily "what's for dinner?" question disappear.</p>
    <div class="reason-grid">
{reason_html}
    </div>
  </div>
</section>

<section class="block">
  <div class="wrap">
    <h2 class="section-title">Where {esc(name)} shines</h2>
    <p class="section-sub">No app is right for everyone. Here's where {esc(name)} is genuinely strong.</p>
    <div class="fair-card">
      <h3>{esc(name)} is a great pick if you value:</h3>
      <ul>
{strengths}
      </ul>
    </div>
  </div>
</section>

<section class="block" style="background:var(--bg-warm)">
  <div class="wrap">
    <h2 class="section-title">FoodieFlow vs {esc(name)} — FAQ</h2>
    <div class="faq-list">
{faq_html}
    </div>
  </div>
</section>

<section class="block">
  <div class="wrap">
    <div class="cta-section">
      <h2>Ready to make meal planning simple?</h2>
      <p>Join FoodieFlow free and let the Smart Assistant plan your week around what's already in your kitchen.</p>
{STORE_BUTTONS}
      <p class="cta-note">Free to download. No card required.</p>
    </div>
  </div>
</section>

<section class="block" style="background:var(--bg-warm)">
  <div class="wrap">
    <h2 class="section-title">Compare FoodieFlow with other apps</h2>
    <p class="section-sub">See how FoodieFlow stacks up against other popular meal planning tools.</p>
    <div class="other-grid">
{other_html}
    </div>
    <p class="updated">Comparison last updated {UPDATED_LABEL}. Competitor features and pricing change over time — please verify current details on each provider's site.</p>
  </div>
</section>
"""

    return head(title, description, canonical, jsonld) + body + FOOTER


def render_hub(data):
    canonical = f"{SITE_URL}/compare/"
    title = "FoodieFlow vs the Alternatives — Meal Planning App Comparison (2026)"
    description = (
        "See FoodieFlow vs Mealime, Paprika and Plan to Eat in one table. Smart Meal "
        "Assistant, one-tap weekly plans, pantry-aware shopping lists and recipe import "
        "from web links and video — compared feature by feature."
    )
    comps = data["competitors"]
    name_by_slug = {c["slug"]: c["name"] for c in comps}

    # --- Head-to-head matrix (FoodieFlow vs the 3 named competitors) ---
    matrix = data["comparison_matrix"]
    cols = matrix["columns"]
    header_cells = "".join(f'<th>{esc(name_by_slug.get(s, s))}</th>' for s in cols)
    matrix_rows = []
    for row in matrix["rows"]:
        cells = "".join(matrix_cell(row.get(s, False)) for s in cols)
        matrix_rows.append(
            f'          <tr><td class="rowlabel">{esc(row["label"])}</td>'
            f'{matrix_cell(row.get("foodieflow", False), is_us=True)}{cells}</tr>'
        )
    matrix_body = "\n".join(matrix_rows)

    # --- Links to every full comparison (so no page is orphaned) ---
    cards = []
    for c in comps:
        cards.append(f"""      <a class="other-card" href="/compare/foodieflow-vs-{c['slug']}/">
        <span class="oc-vs">FoodieFlow vs</span>
        <div class="oc-name">{esc(c['name'])}</div>
        <p style="color:var(--muted);font-size:0.86rem;margin-top:8px;line-height:1.55">{esc(c['category'])}</p>
        <span class="oc-arrow">Read comparison &rarr;</span>
      </a>""")
    cards_html = "\n".join(cards)

    item_list = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "name": f"FoodieFlow vs {c['name']}",
                "url": f"{SITE_URL}/compare/foodieflow-vs-{c['slug']}/",
            }
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
    jsonld = (
        '  <script type="application/ld+json">'
        + json.dumps([breadcrumb, item_list], ensure_ascii=False)
        + "</script>\n"
    )

    body = f"""{NAV}
<nav class="breadcrumb" aria-label="Breadcrumb">
  <a href="/">Home</a> &rsaquo; <span>Compare</span>
</nav>

<header class="hero">
  <p class="eyebrow">Comparisons</p>
  <h1>FoodieFlow vs <span class="brand">the alternatives</span></h1>
  <p class="hero-sub">Thinking of switching meal planning apps? Here's FoodieFlow next to Mealime, Paprika and Plan to Eat — including the smart-planning and recipe-import features you won't find elsewhere.</p>
  <div class="hero-ctas">
    <a href="/beta" class="btn-primary">Try FoodieFlow free</a>
  </div>
</header>

<section class="block">
  <div class="wrap">
    <h2 class="section-title">How FoodieFlow compares</h2>
    <p class="section-sub">An honest, head-to-head look at the features that matter most.</p>
    <div class="table-card">
      <div class="matrix-scroll">
        <table class="matrix">
          <thead>
            <tr><th class="rowlabel">Feature</th><th class="col-us">FoodieFlow</th>{header_cells}</tr>
          </thead>
          <tbody>
{matrix_body}
          </tbody>
        </table>
      </div>
    </div>
    <div class="matrix-legend">
      <span>{TICK_SVG} Included</span>
      <span>{CROSS_SVG} Not available</span>
    </div>
  </div>
</section>

<section class="block" style="background:var(--bg-warm)">
  <div class="wrap">
    <h2 class="section-title">Read the full comparisons</h2>
    <p class="section-sub">Full feature tables and FAQs for each meal planning app.</p>
    <div class="other-grid">
{cards_html}
    </div>
    <p class="updated">Comparisons last updated {UPDATED_LABEL}. Competitor features and pricing change over time — please verify current details on each provider's site.</p>
  </div>
</section>
"""

    return head(title, description, canonical, jsonld) + body + FOOTER


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
    write(os.path.join(ROOT, "sitemap.xml"), render_sitemap(data))
    write(os.path.join(ROOT, "robots.txt"), ROBOTS)
    print(f"Done. {len(comps)} comparison pages + hub + sitemap + robots.")


if __name__ == "__main__":
    main()
