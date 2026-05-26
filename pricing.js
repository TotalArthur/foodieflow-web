/* Dynamic pricing — fetches base price from /pricing.json (kept fresh by
   GitHub Actions) and converts to the visitor's local currency via
   IP-geolocation + live exchange rates. */
(async function initDynamicPricing() {
  const priceBox  = document.getElementById('rc-price-container');
  const inlineEls = document.querySelectorAll('.rc-price-inline');
  if (!priceBox && !inlineEls.length) return;

  const NO_FRACTION = new Set(['JPY','KRW','IDR','VND','CLP','HUF','ISK','UGX','TWD']);

  function makeFmt(currency) {
    return new Intl.NumberFormat(navigator.language || 'en', {
      style: 'currency',
      currency,
      minimumFractionDigits: NO_FRACTION.has(currency) ? 0 : 2,
      maximumFractionDigits: NO_FRACTION.has(currency) ? 0 : 2,
    });
  }

  /* Round to nearest App Store-style .99 ending; whole numbers for ¥ / ₩ etc. */
  function storeTier(raw, currency) {
    if (NO_FRACTION.has(currency)) return Math.round(raw);
    return Math.floor(raw) + 0.99;
  }

  try {
    const [pricingResult, geoResult] = await Promise.allSettled([
      fetch('/pricing.json').then(r => r.ok ? r.json() : Promise.reject('pricing.json unavailable')),
      fetch('https://ipapi.co/json/').then(r => r.ok ? r.json() : Promise.reject('geo unavailable')),
    ]);

    const pricing = pricingResult.status === 'fulfilled' ? pricingResult.value : null;
    if (!pricing?.base_amount) return; /* nothing configured yet — keep fallback HTML */

    const geo      = geoResult.status === 'fulfilled' ? geoResult.value : null;
    let currency   = geo?.currency || pricing.base_currency;
    let amount     = pricing.base_amount;

    if (currency !== pricing.base_currency) {
      try {
        const res  = await fetch(`https://api.frankfurter.app/latest?from=${pricing.base_currency}&to=${currency}`);
        const data = res.ok ? await res.json() : null;
        const rate = data?.rates?.[currency];
        if (rate) {
          amount = storeTier(amount * rate, currency);
        } else {
          currency = pricing.base_currency; /* unsupported currency — fall back */
        }
      } catch {
        currency = pricing.base_currency;
      }
    }

    const f      = makeFmt(currency);
    const parts  = f.formatToParts(amount);
    const symbol = parts.find(p => p.type === 'currency')?.value || currency;
    const num    = parts
      .filter(p => ['integer','decimal','fraction','group'].includes(p.type))
      .map(p => p.value).join('');

    if (priceBox) {
      priceBox.innerHTML = `<sup>${symbol}</sup>${num}<sub>/month</sub>`;
    }
    inlineEls.forEach(el => { el.textContent = f.format(amount); });

  } catch (e) {
    console.warn('[FoodieFlow] Dynamic pricing unavailable:', e.message);
  }
})();
