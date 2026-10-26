/* FoodieFlow 2026 design layer: nav, phone menu sheet, scroll reveal,
   accordions and the footer year. Loaded with `defer` on every page that
   links /assets/ff26.css. */
(function () {
  var root = document.documentElement;
  root.classList.add('ff-js');
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Firmer bar once the page moves. */
  var nav = document.getElementById('main-nav');
  if (nav) {
    var onScroll = function () { nav.classList.toggle('scrolled', window.scrollY > 40); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* Phone menu sheet. It slides up over a blurred page, closes on the scrim,
     the close button, Escape or any link, and hands focus back to the button. */
  var sheet = document.getElementById('ff-sheet');
  var opener = document.querySelector('.ff-menu-btn');
  if (sheet && opener) {
    var panel = sheet.querySelector('.ff-sheet__panel');
    var links = sheet.querySelectorAll('.ff-sheet__links a');
    links.forEach(function (a, i) { a.style.transitionDelay = (0.08 + i * 0.04) + 's'; });

    var onKey = function (e) {
      if (e.key === 'Escape') { close(); return; }
      if (e.key !== 'Tab') return;
      var f = panel.querySelectorAll('a[href], button');
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    var open = function () {
      sheet.hidden = false;
      void sheet.offsetWidth;
      sheet.classList.add('is-open');
      root.classList.add('ff-locked');
      opener.setAttribute('aria-expanded', 'true');
      document.addEventListener('keydown', onKey);
      var first = sheet.querySelector('.ff-sheet__close');
      if (first) first.focus();
    };
    var close = function () {
      if (!sheet.classList.contains('is-open')) return;
      sheet.classList.remove('is-open');
      root.classList.remove('ff-locked');
      opener.setAttribute('aria-expanded', 'false');
      document.removeEventListener('keydown', onKey);
      opener.focus();
      setTimeout(function () { if (!sheet.classList.contains('is-open')) sheet.hidden = true; }, reduceMotion ? 0 : 450);
    };
    opener.addEventListener('click', open);
    sheet.querySelectorAll('[data-close], .ff-sheet__links a, .ff-sheet__stores a').forEach(function (el) {
      el.addEventListener('click', close);
    });
    window.addEventListener('resize', function () { if (window.innerWidth > 1020) close(); });
  }

  /* Accordions: one open at a time within a group. */
  document.querySelectorAll('.ff-acc').forEach(function (group) {
    group.addEventListener('click', function (e) {
      var q = e.target.closest('.ff-acc__q');
      if (!q || !group.contains(q)) return;
      var willOpen = q.getAttribute('aria-expanded') !== 'true';
      group.querySelectorAll('.ff-acc__q').forEach(function (o) { o.setAttribute('aria-expanded', 'false'); });
      q.setAttribute('aria-expanded', willOpen ? 'true' : 'false');
    });
  });

  /* Scroll reveal. Items in the same parent stagger slightly. */
  var reveals = document.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        io.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    reveals.forEach(function (el) {
      if (!el.style.getPropertyValue('--d')) {
        var sibs = [].filter.call(el.parentNode.children, function (c) { return c.hasAttribute('data-reveal'); });
        var i = sibs.indexOf(el);
        if (i > 0) el.style.setProperty('--d', Math.min(i, 6) * 0.08 + 's');
      }
      io.observe(el);
    });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-in'); });
  }

  /* Footer year. */
  document.querySelectorAll('[data-year]').forEach(function (el) { el.textContent = new Date().getFullYear(); });
})();
