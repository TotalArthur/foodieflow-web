/* Static RevenueCat pricing — exact App Store prices keyed by ISO 3166-1 alpha-2
   country code. Falls back to US price if geolocation is unavailable. */
(async function initPricing() {
  const priceBox  = document.getElementById('rc-price-container');
  const inlineEls = document.querySelectorAll('.rc-price-inline');
  if (!priceBox && !inlineEls.length) return;

  const PRICES = {
    // United States & Canada
    US: '$3.99',   CA: '$4.99',
    // Europe
    AL: '$4.99',   AT: '€3.99',   BY: '$4.99',   BE: '€3.99',
    BA: '€3.99',   BG: '€3.99',   HR: '€3.99',   CY: '€3.99',
    CZ: 'Kč 99.00',  DK: 'kr 39.00',  EE: '€3.99',   FI: '€3.99',
    FR: '€3.99',   DE: '€3.99',   GR: '€3.99',   HU: 'Ft 1,790.00',
    IS: '$4.99',   IE: '€3.99',   IT: '€3.99',   XK: '€3.99',
    LV: '€3.99',   LT: '€3.99',   LU: '€3.99',   MT: '€3.99',
    MD: '$4.99',   ME: '€3.99',   NL: '€3.99',   MK: '$3.99',
    NO: 'kr 49.00',  PL: 'zł 19.99',  PT: '€3.99',   RO: 'lei 19.99',
    RU: '₽349.00', RS: '€3.99',   SK: '€3.99',   SI: '€3.99',
    ES: '€3.99',   SE: 'kr 49.00',  CH: 'CHF 3.00',  TR: '₺199.99',
    UA: '$4.99',   GB: '£3.99',
    // Africa, Middle East & India
    AF: '$3.99',   DZ: '$3.99',   AO: '$3.99',   AM: '$4.99',
    AZ: '$4.99',   BH: '$3.99',   BJ: '$4.99',   BW: '$3.99',
    BF: '$3.99',   CM: '$4.99',   CV: '$3.99',   TD: '$3.99',
    CD: '$3.99',   CG: '$3.99',   CI: '$4.99',   EG: 'E£199.99',
    SZ: '$3.99',   GA: '$3.99',   GM: '$3.99',   GE: '$4.99',
    GH: '$4.99',   GW: '$3.99',   IN: '₹399.00', IQ: '$3.99',
    IL: '₪14.90',  JO: '$3.99',   KE: '$4.99',   KW: '$3.99',
    LB: '$3.99',   LR: '$3.99',   LY: '$3.99',   MG: '$3.99',
    MW: '$3.99',   ML: '$3.99',   MR: '$3.99',   MU: '$4.99',
    MA: '$3.99',   MZ: '$3.99',   NA: '$3.99',   NE: '$3.99',
    NG: '₦6,900.00',  OM: '$3.99',   QA: 'QAR 14.99', RW: '$3.99',
    ST: '$3.99',   SA: 'SAR 17.99', SN: '$4.99',   SC: '$3.99',
    SL: '$3.99',   ZA: 'R 79.99',  TZ: 'TZS 11,900.00', TN: '$3.99',
    UG: '$4.99',   AE: 'AED 14.99', YE: '$3.99',   ZM: '$4.99',
    ZW: '$4.99',
    // Latin America & Caribbean
    AI: '$3.99',   AG: '$3.99',   AR: '$3.99',   BS: '$3.99',
    BB: '$4.99',   BZ: '$3.99',   BM: '$3.99',   BO: '$3.99',
    BR: 'R$24.90', VG: '$3.99',   KY: '$3.99',   CL: '$4,990.00',
    CO: '$19,900.00', CR: '$3.99', DM: '$3.99',   DO: '$3.99',
    EC: '$3.99',   SV: '$3.99',   GD: '$3.99',   GT: '$3.99',
    GY: '$3.99',   HN: '$3.99',   JM: '$3.99',   MX: '$89.00',
    MS: '$3.99',   NI: '$3.99',   PA: '$3.99',   PY: '$3.99',
    PE: 'PEN 17.90', KN: '$3.99', LC: '$3.99',   VC: '$3.99',
    SR: '$3.99',   TT: '$3.99',   TC: '$3.99',   UY: '$3.99',
    VE: '$3.99',
    // Asia Pacific
    AU: '$5.99',   BT: '$3.99',   BN: '$3.99',   KH: '$3.99',
    CN: '¥28.00',  FJ: '$3.99',   HK: '$32.00',  ID: 'Rp 69,000.00',
    JP: '¥600.00', KZ: '₸2,490.00', KR: '₩5,500.00', KG: '$3.99',
    LA: '$3.99',   MO: '$3.99',   MY: 'RM 19.90', MV: '$3.99',
    FM: '$3.99',   MN: '$3.99',   MM: '$3.99',   NR: '$3.99',
    NP: '$4.99',   NZ: '$6.99',   PK: 'Rs 1,100.00', PW: '$3.99',
    PG: '$3.99',   PH: '₱249.00', SG: '$5.98',   SB: '$3.99',
    LK: '$3.99',   TW: '$120.00', TJ: '$3.99',   TH: '฿149.00',
    TO: '$3.99',   TM: '$3.99',   UZ: '$3.99',   VU: '$3.99',
    VN: '₫119,000.00',
  };

  /* Split "€3.99" → { symbol: "€", number: "3.99" } for the price-box superscript layout. */
  function parsePriceStr(str) {
    const idx = str.search(/\d/);
    if (idx <= 0) return { symbol: '', number: str };
    return { symbol: str.slice(0, idx).trim(), number: str.slice(idx) };
  }

  try {
    const geoRes = await fetch('https://ipapi.co/json/');
    const geo    = geoRes.ok ? await geoRes.json() : null;
    const code   = geo?.country_code || '';
    const price  = PRICES[code] || PRICES['US'];
    const { symbol, number } = parsePriceStr(price);

    if (priceBox) {
      priceBox.innerHTML = `<sup>${symbol}</sup>${number}<sub>/month</sub>`;
    }
    inlineEls.forEach(el => { el.textContent = price; });

  } catch (e) {
    console.warn('[FoodieFlow] Pricing lookup unavailable:', e.message);
  }
})();
