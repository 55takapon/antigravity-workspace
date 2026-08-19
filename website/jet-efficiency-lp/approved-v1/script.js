(() => {
  "use strict";

  const year = document.querySelector("[data-current-year]");
  if (year) year.textContent = String(new Date().getFullYear());

  const mobileCta = document.querySelector("[data-mobile-cta]");
  const inlineCtas = [...document.querySelectorAll(".ja-cta")];

  if (!mobileCta || !inlineCtas.length || !("IntersectionObserver" in window)) return;

  const visibleCtas = new Set();

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) visibleCtas.add(entry.target);
        else visibleCtas.delete(entry.target);
      });
      mobileCta.classList.toggle("is-hidden", visibleCtas.size > 0);
    },
    { threshold: 0.12 }
  );

  inlineCtas.forEach((cta) => observer.observe(cta));
})();
