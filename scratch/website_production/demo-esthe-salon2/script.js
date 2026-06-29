/* ============================================================
   Esthe Salon Lunea — Script
   ============================================================ */
document.addEventListener("DOMContentLoaded", () => {
  "use strict";

  /* ── Sticky Header ── */
  const header = document.querySelector(".lunea-header");
  const SCROLL_THRESHOLD = 60;

  const handleScroll = () => {
    if (window.scrollY > SCROLL_THRESHOLD) {
      header.classList.add("is-scrolled");
    } else {
      header.classList.remove("is-scrolled");
    }
  };

  window.addEventListener("scroll", handleScroll, { passive: true });
  handleScroll();

  /* ── Hamburger Menu ── */
  const hamburger = document.querySelector(".lunea-hamburger");
  const mobileMenu = document.querySelector(".lunea-mobile-menu");
  const mobileLinks = document.querySelectorAll(".lunea-mobile-menu__link");

  const toggleMenu = () => {
    const isOpen = hamburger.classList.toggle("is-active");
    mobileMenu.classList.toggle("is-open", isOpen);
    document.body.style.overflow = isOpen ? "hidden" : "";
    hamburger.setAttribute("aria-expanded", isOpen);
  };

  const closeMenu = () => {
    hamburger.classList.remove("is-active");
    mobileMenu.classList.remove("is-open");
    document.body.style.overflow = "";
    hamburger.setAttribute("aria-expanded", "false");
  };

  hamburger.addEventListener("click", toggleMenu);

  mobileLinks.forEach((link) => {
    link.addEventListener("click", closeMenu);
  });

  // Close on Escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && mobileMenu.classList.contains("is-open")) {
      closeMenu();
    }
  });

  /* ── Intersection Observer (Fade-in) ── */
  const fadeTargets = document.querySelectorAll(".lunea-fade-target");

  if ("IntersectionObserver" in window && fadeTargets.length > 0) {
    const fadeObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            fadeObserver.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.15,
        rootMargin: "0px 0px -40px 0px",
      }
    );

    fadeTargets.forEach((el) => fadeObserver.observe(el));
  }

  /* ── Smooth scroll for anchor links (fallback) ── */
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const targetId = anchor.getAttribute("href");
      if (targetId === "#") return;

      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        const headerHeight = header.offsetHeight;
        const targetPos =
          target.getBoundingClientRect().top + window.scrollY - headerHeight - 16;

        window.scrollTo({
          top: targetPos,
          behavior: "smooth",
        });
      }
    });
  });
});
