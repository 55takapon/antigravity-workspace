/**
 * AI活用診断 LP - Interactive Scripts
 * 
 * Features:
 * - Header scroll shadow
 * - Mobile menu toggle
 * - Smooth scroll navigation
 * - FAQ accordion
 * - Scroll-triggered fade-in animations
 */

document.addEventListener("DOMContentLoaded", () => {
  initHeaderScroll();
  initMobileMenu();
  initSmoothScroll();
  initFaqAccordion();
  initFadeInAnimation();
});

/**
 * Header - Add shadow on scroll
 */
function initHeaderScroll() {
  const header = document.getElementById("header");
  if (!header) return;

  const onScroll = () => {
    if (window.scrollY > 10) {
      header.classList.add("is-scrolled");
    } else {
      header.classList.remove("is-scrolled");
    }
  };

  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll(); // Initial check
}

/**
 * Mobile menu toggle
 */
function initMobileMenu() {
  const toggle = document.getElementById("menuToggle");
  const nav = document.getElementById("headerNav");
  if (!toggle || !nav) return;

  toggle.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("is-open");
    toggle.classList.toggle("is-active", isOpen);
    toggle.setAttribute("aria-expanded", String(isOpen));
    toggle.setAttribute("aria-label", isOpen ? "メニューを閉じる" : "メニューを開く");

    // Prevent body scroll when menu is open
    document.body.style.overflow = isOpen ? "hidden" : "";
  });

  // Close menu when a link is clicked
  nav.querySelectorAll(".header__nav-link, .header__cta").forEach((link) => {
    link.addEventListener("click", () => {
      nav.classList.remove("is-open");
      toggle.classList.remove("is-active");
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "メニューを開く");
      document.body.style.overflow = "";
    });
  });
}

/**
 * Smooth scroll for anchor links
 */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener("click", (e) => {
      const targetId = anchor.getAttribute("href");
      if (targetId === "#") return;

      const target = document.querySelector(targetId);
      if (!target) return;

      e.preventDefault();
      const headerHeight = document.getElementById("header")?.offsetHeight || 72;
      const targetPosition = target.getBoundingClientRect().top + window.scrollY - headerHeight;

      window.scrollTo({
        top: targetPosition,
        behavior: "smooth",
      });
    });
  });
}

/**
 * FAQ accordion
 */
function initFaqAccordion() {
  const faqItems = document.querySelectorAll(".faq__item");

  faqItems.forEach((item) => {
    const button = item.querySelector(".faq__question");
    const answer = item.querySelector(".faq__answer");
    const inner = item.querySelector(".faq__answer-inner");
    if (!button || !answer || !inner) return;

    button.addEventListener("click", () => {
      const isOpen = item.classList.contains("is-open");

      // Close all other items
      faqItems.forEach((otherItem) => {
        if (otherItem !== item && otherItem.classList.contains("is-open")) {
          otherItem.classList.remove("is-open");
          const otherBtn = otherItem.querySelector(".faq__question");
          const otherAnswer = otherItem.querySelector(".faq__answer");
          if (otherBtn) otherBtn.setAttribute("aria-expanded", "false");
          if (otherAnswer) otherAnswer.style.maxHeight = "0";
        }
      });

      // Toggle current item
      if (isOpen) {
        item.classList.remove("is-open");
        button.setAttribute("aria-expanded", "false");
        answer.style.maxHeight = "0";
      } else {
        item.classList.add("is-open");
        button.setAttribute("aria-expanded", "true");
        answer.style.maxHeight = inner.scrollHeight + 32 + "px";
      }
    });
  });
}

/**
 * Scroll-triggered fade-in animation using Intersection Observer
 */
function initFadeInAnimation() {
  const targets = document.querySelectorAll(".fade-in");
  if (!targets.length) return;

  // Check if user prefers reduced motion
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  if (prefersReducedMotion) {
    // If user prefers reduced motion, show all elements immediately
    targets.forEach((el) => el.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          // Add a small stagger delay based on the element's position in its parent
          const parent = entry.target.parentElement;
          if (parent) {
            const siblings = Array.from(parent.querySelectorAll(":scope > .fade-in"));
            const index = siblings.indexOf(entry.target);
            entry.target.style.transitionDelay = `${index * 0.08}s`;
          }
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    {
      root: null,
      rootMargin: "0px 0px -60px 0px",
      threshold: 0.1,
    }
  );

  targets.forEach((el) => observer.observe(el));
}
