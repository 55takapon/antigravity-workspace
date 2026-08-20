(() => {
  "use strict";

  const year = document.querySelector("[data-current-year]");
  if (year) year.textContent = String(new Date().getFullYear());

  const mobileCta = document.querySelector("[data-mobile-cta]");
  const inlineCtas = [...document.querySelectorAll(".ja-cta")];
  const footer = document.querySelector(".ja-footer");

  if (!mobileCta || !inlineCtas.length) return;

  if (!("IntersectionObserver" in window)) {
    mobileCta.classList.remove("is-hidden");
    return;
  }

  const visibleCtas = new Map();
  const visibleRatio = 0.8;
  const visibilityTargets = footer ? [...inlineCtas, footer] : inlineCtas;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        const shouldHide = entry.target === footer
          ? entry.isIntersecting
          : entry.intersectionRatio >= visibleRatio;
        visibleCtas.set(entry.target, shouldHide);
      });
      mobileCta.classList.toggle(
        "is-hidden",
        [...visibleCtas.values()].some(Boolean)
      );
    },
    { threshold: [0, visibleRatio, 1] }
  );

  visibilityTargets.forEach((target) => observer.observe(target));
})();
