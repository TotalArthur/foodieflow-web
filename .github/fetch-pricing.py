#!/usr/bin/env python3
"""
Fetches the current Pro Monthly price from RevenueCat v2 REST API
and writes pricing.json.  Called by .github/workflows/update-pricing.yml.

Uses only the Python standard library — no pip install required.
"""
import json, os, sys, re, datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

SECRET = os.environ.get("RC_SECRET", "").strip()
if not SECRET:
    print("ERROR: REVENUECAT_SECRET_KEY secret is not configured in GitHub Secrets.")
    sys.exit(1)

BASE    = "https://api.revenuecat.com"
HEADERS = {"Authorization": f"Bearer {SECRET}", "Content-Type": "application/json"}


def rc_get(path):
    req = Request(f"{BASE}{path}", headers=HEADERS)
    try:
        with urlopen(req, timeout=20) as resp:
            data = json.load(resp)
            print(f"  GET {path} → 200")
            return data
    except HTTPError as exc:
        body = exc.read().decode(errors="replace")[:600]
        print(f"  GET {path} → HTTP {exc.code}: {body}")
        sys.exit(1)
    except URLError as exc:
        print(f"  GET {path} → network error: {exc.reason}")
        sys.exit(1)


# ── 1. Get project ID ────────────────────────────────────────────────────────
print("Fetching projects...")
projects = rc_get("/v2/projects")
items = projects.get("items", [])
if not items:
    print(f"ERROR: No projects found. Response: {json.dumps(projects)[:400]}")
    sys.exit(1)
project_id = items[0]["id"]
print(f"Project: {project_id}  ({items[0].get('name', '')})")

# ── 2. Get offerings ─────────────────────────────────────────────────────────
print("Fetching offerings...")
offerings = rc_get(f"/v2/projects/{project_id}/offerings?environment=production")
offering_items = offerings.get("items", [])
print(f"Offerings found: {len(offering_items)}")

# ── 3. Find the current (default) offering ───────────────────────────────────
current = next((o for o in offering_items if o.get("is_current")), None)
if not current:
    current = next((o for o in offering_items if o.get("lookup_key") == "default"), None)
if not current and offering_items:
    current = offering_items[0]
if not current:
    print("ERROR: No offering found")
    sys.exit(1)
print(f"Offering: {current.get('lookup_key')}  (is_current={current.get('is_current')})")

# ── 4. Find the $rc_monthly package ─────────────────────────────────────────
packages = current.get("packages", [])
pkg = next((p for p in packages if p.get("lookup_key") == "$rc_monthly"), None)
if not pkg:
    print(f"Available packages: {[p.get('lookup_key') for p in packages]}")
    pkg = packages[0] if packages else None
if not pkg:
    print("ERROR: No package found")
    sys.exit(1)
print(f"Package: {pkg.get('lookup_key')}")

# ── 5. Find the iOS (App Store) product ─────────────────────────────────────
products = pkg.get("products", []) or []
print(f"Products ({len(products)}):")
for p in products:
    print(f"  store={p.get('app', {}).get('store')}  id={p.get('store_identifier')}")

ios = next((p for p in products if p.get("app", {}).get("store") == "app_store"), None)
product = ios or (products[0] if products else None)
if not product:
    print("ERROR: No product found in package")
    sys.exit(1)
print(f"Using product: {product.get('store_identifier')}")

# ── 6. Extract price (try multiple field paths for robustness) ───────────────
opt = product.get("default_purchase_option") or {}
print(f"Purchase option keys: {sorted(opt.keys())}")

price, currency = None, None

# Path A: pricing_phases[-1].price  (most common RevenueCat v2 shape)
phases = opt.get("pricing_phases") or []
if phases:
    p_obj = phases[-1].get("price") or {}
    if p_obj.get("amount") is not None:
        currency = p_obj["currency"]
        price    = round(p_obj["amount"] / 100, 2)
        print(f"Price (path A – pricing_phases): {currency} {price}")

# Path B: direct price dict on the option
if price is None:
    p_obj = opt.get("price") or {}
    if isinstance(p_obj, dict) and p_obj.get("amount") is not None:
        currency = p_obj["currency"]
        price    = round(p_obj["amount"] / 100, 2)
        print(f"Price (path B – direct price): {currency} {price}")
    elif isinstance(p_obj, (int, float)):
        currency = "GBP"
        price    = float(p_obj)
        print(f"Price (path B – raw float): {currency} {price}")

# Path C: parse the human-readable price_description string, e.g. "£3.99/month"
if price is None:
    desc = opt.get("price_description", "")
    print(f"price_description: {repr(desc)}")
    m = re.search(r"(£|€|\$|US\$|CA\$|A\$|NZ\$)(\d+[.,]\d{1,2})", desc)
    if m:
        sym_map = {"£": "GBP", "€": "EUR", "$": "USD",
                   "US$": "USD", "CA$": "CAD", "A$": "AUD", "NZ$": "NZD"}
        currency = sym_map.get(m.group(1), "GBP")
        price    = float(m.group(2).replace(",", "."))
        print(f"Price (path C – description): {currency} {price}")

if price is None:
    print("ERROR: Could not extract price from any known field.")
    print("Full default_purchase_option:")
    print(json.dumps(opt, indent=2))
    sys.exit(1)

# ── 7. Write pricing.json ────────────────────────────────────────────────────
data = {
    "base_currency": currency,
    "base_amount":   price,
    "period":        "month",
    "last_updated":  datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
}
with open("pricing.json", "w") as f:
    json.dump(data, f, indent=2)
    f.write("\n")

print(f"\n✓  pricing.json updated → {currency} {price}/month")
