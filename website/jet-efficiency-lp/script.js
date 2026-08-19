(() => {
  'use strict';

  const root = document.querySelector('.jet-efficiency-lp');
  if (!root) return;

  const year = String(new Date().getFullYear());
  root.querySelectorAll('[data-current-year]').forEach((node) => {
    node.textContent = year;
  });

  root.querySelectorAll('[data-cta]').forEach((link) => {
    link.addEventListener('click', () => {
      const detail = { location: link.dataset.cta, href: link.href };
      window.dispatchEvent(new CustomEvent('jet-efficiency:cta-click', { detail }));

      if (Array.isArray(window.dataLayer)) {
        window.dataLayer.push({ event: 'lp_cta_click', cta_location: detail.location });
      }
    });
  });
})();
