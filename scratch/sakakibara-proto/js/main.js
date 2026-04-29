/**
 * SAKAKIBARA CONSULTING - Main JavaScript
 *
 * Features:
 * - Hamburger menu toggle
 * - Header scroll behavior (shadow on scroll)
 * - Smooth scroll for anchor links
 * - Scroll-triggered fade-in animations (IntersectionObserver)
 * - Active navigation highlight
 */

;(function () {
  "use strict";

  /* =======================================================================
   * DOM References
   * ======================================================================= */

  const header     = document.getElementById("header");
  const hamburger  = document.getElementById("hamburger");
  const globalNav  = document.getElementById("globalNav");
  const navLinks   = document.querySelectorAll(".l-header__nav-link");
  const animTargets = document.querySelectorAll("[data-animate]");

  /* =======================================================================
   * Hamburger Menu
   * ======================================================================= */

  function toggleMenu() {
    const isOpen = hamburger.classList.toggle("is-active");
    globalNav.classList.toggle("is-open");
    document.body.classList.toggle("is-menu-open");
    hamburger.setAttribute("aria-expanded", String(isOpen));
    hamburger.setAttribute(
      "aria-label",
      isOpen ? "メニューを閉じる" : "メニューを開く"
    );
  }

  function closeMenu() {
    hamburger.classList.remove("is-active");
    globalNav.classList.remove("is-open");
    document.body.classList.remove("is-menu-open");
    hamburger.setAttribute("aria-expanded", "false");
    hamburger.setAttribute("aria-label", "メニューを開く");
  }

  hamburger.addEventListener("click", toggleMenu);

  // Close menu on nav link click (mobile)
  navLinks.forEach(function (link) {
    link.addEventListener("click", function () {
      if (globalNav.classList.contains("is-open")) {
        closeMenu();
      }
    });
  });

  // Close menu on Escape key
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && globalNav.classList.contains("is-open")) {
      closeMenu();
      hamburger.focus();
    }
  });

  /* =======================================================================
   * Header Scroll Behavior
   * ======================================================================= */

  var scrollTicking = false;

  function onScroll() {
    if (!scrollTicking) {
      window.requestAnimationFrame(function () {
        updateHeaderState();
        scrollTicking = false;
      });
      scrollTicking = true;
    }
  }

  function updateHeaderState() {
    var scrollTop = window.scrollY || document.documentElement.scrollTop;
    if (scrollTop > 10) {
      header.classList.add("is-scrolled");
    } else {
      header.classList.remove("is-scrolled");
    }
  }

  window.addEventListener("scroll", onScroll, { passive: true });
  updateHeaderState();

  /* =======================================================================
   * Smooth Scroll for Anchor Links
   * ======================================================================= */

  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener("click", function (e) {
      var targetId = this.getAttribute("href");
      if (targetId === "#") return;

      var targetEl = document.querySelector(targetId);
      if (!targetEl) return;

      e.preventDefault();

      var headerHeight = header.offsetHeight;
      var targetPosition =
        targetEl.getBoundingClientRect().top + window.scrollY - headerHeight;

      window.scrollTo({
        top: targetPosition,
        behavior: "smooth",
      });
    });
  });

  /* =======================================================================
   * Scroll-triggered Animations (IntersectionObserver)
   * ======================================================================= */

  if ("IntersectionObserver" in window) {
    var animObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            animObserver.unobserve(entry.target);
          }
        });
      },
      {
        root: null,
        rootMargin: "0px 0px -60px 0px",
        threshold: 0.1,
      }
    );

    animTargets.forEach(function (target) {
      animObserver.observe(target);
    });
  } else {
    // Fallback: show all elements immediately
    animTargets.forEach(function (target) {
      target.classList.add("is-visible");
    });
  }

  /* =======================================================================
   * Active Navigation Highlight
   * ======================================================================= */

  var sections = document.querySelectorAll("section[id]");

  if ("IntersectionObserver" in window) {
    var sectionObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            var currentId = entry.target.getAttribute("id");
            updateActiveNav(currentId);
          }
        });
      },
      {
        root: null,
        rootMargin: "-50% 0px -50% 0px",
        threshold: 0,
      }
    );

    sections.forEach(function (section) {
      sectionObserver.observe(section);
    });
  }

  function updateActiveNav(activeId) {
    navLinks.forEach(function (link) {
      var href = link.getAttribute("href");
      if (href === "#" + activeId) {
        link.classList.add("is-active");
      } else {
        link.classList.remove("is-active");
      }
    });
  }

})();
