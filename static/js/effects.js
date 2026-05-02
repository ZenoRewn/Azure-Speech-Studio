/**
 * Visual effects: cursor-follow glow on .glass, number tickers,
 * SVG gradient injection for .ring-progress.
 */

window.Effects = (() => {
  function initGlassHover() {
    const cards = document.querySelectorAll('.glass');
    cards.forEach(card => {
      card.addEventListener('pointermove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top) / rect.height) * 100;
        card.style.setProperty('--mx', x + '%');
        card.style.setProperty('--my', y + '%');
      });
    });
  }

  /** Tween the numeric text of elements marked with .ticker[data-target]. */
  function animateTicker(el, toValue, duration = 800) {
    const from = parseFloat(el.dataset.current || el.textContent || '0') || 0;
    const to = parseFloat(toValue);
    if (!isFinite(to)) return;
    const start = performance.now();
    const decimals = (String(toValue).split('.')[1] || '').length;
    function tick(now) {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      const v = from + (to - from) * eased;
      el.textContent = decimals > 0 ? v.toFixed(decimals) : String(Math.round(v));
      if (t < 1) requestAnimationFrame(tick);
      else el.dataset.current = to;
    }
    requestAnimationFrame(tick);
  }

  /** Wrap a number in a ticker element so subsequent updates animate. */
  function setTicker(elementId, value) {
    const el = document.getElementById(elementId);
    if (!el) return;
    if (!el.classList.contains('ticker')) el.classList.add('ticker');
    animateTicker(el, value);
  }

  /** Initialise the shared SVG gradient used by .ring-progress. */
  function injectRingGradient() {
    if (document.getElementById('ring-gradient-svg')) return;
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('id', 'ring-gradient-svg');
    svg.setAttribute('width', '0');
    svg.setAttribute('height', '0');
    svg.style.position = 'absolute';
    svg.innerHTML = `
      <defs>
        <linearGradient id="ring-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#60a5fa"/>
          <stop offset="100%" stop-color="#c084fc"/>
        </linearGradient>
      </defs>`;
    document.body.appendChild(svg);
  }

  /** Render/update a circular progress ring (0-100) inside a .ring-progress container. */
  function setRing(container, percent, label) {
    if (typeof container === 'string') container = document.getElementById(container);
    if (!container) return;
    const size = container.clientWidth || 72;
    const r = size / 2 - 6;
    const c = 2 * Math.PI * r;
    const offset = c * (1 - Math.max(0, Math.min(100, percent)) / 100);
    if (!container.querySelector('svg')) {
      container.innerHTML = `
        <svg viewBox="0 0 ${size} ${size}">
          <circle class="ring-track" cx="${size/2}" cy="${size/2}" r="${r}"></circle>
          <circle class="ring-fill" cx="${size/2}" cy="${size/2}" r="${r}"
                  stroke-dasharray="${c}" stroke-dashoffset="${c}"></circle>
        </svg>
        <div class="ring-label"></div>`;
    }
    container.querySelector('.ring-fill').setAttribute('stroke-dashoffset', offset);
    const lbl = container.querySelector('.ring-label');
    if (lbl) lbl.textContent = label == null ? Math.round(percent) + '%' : label;
  }

  function init() {
    injectRingGradient();
    initGlassHover();
  }

  return { init, animateTicker, setTicker, setRing, initGlassHover };
})();
