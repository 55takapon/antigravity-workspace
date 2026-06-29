/* =============================================
   Cafe Liora — JavaScript
   ============================================= */

document.addEventListener('DOMContentLoaded', () => {
  'use strict';

  /* ---------- Header scroll ---------- */
  const header = document.getElementById('header');

  const handleHeaderScroll = () => {
    if (window.scrollY > 60) {
      header.classList.add('liora-header--scrolled');
    } else {
      header.classList.remove('liora-header--scrolled');
    }
  };

  window.addEventListener('scroll', handleHeaderScroll, { passive: true });
  handleHeaderScroll();


  /* ---------- Mobile navigation ---------- */
  const hamburger = document.getElementById('hamburger');
  const nav = document.getElementById('nav');

  hamburger.addEventListener('click', () => {
    const isOpen = nav.classList.toggle('is-open');
    hamburger.classList.toggle('is-active');
    hamburger.setAttribute('aria-expanded', isOpen);
    document.body.style.overflow = isOpen ? 'hidden' : '';

    // Force scrolled state when menu is open
    if (isOpen) {
      header.classList.add('liora-header--scrolled');
    } else {
      handleHeaderScroll();
    }
  });

  // Close nav when clicking a link
  nav.querySelectorAll('.liora-header__nav-link').forEach(link => {
    link.addEventListener('click', () => {
      nav.classList.remove('is-open');
      hamburger.classList.remove('is-active');
      hamburger.setAttribute('aria-expanded', 'false');
      document.body.style.overflow = '';
      handleHeaderScroll();
    });
  });


  /* ---------- Scroll reveal ---------- */
  const revealTargets = document.querySelectorAll(
    '.liora-concept__inner, ' +
    '.liora-menu__inner, ' +
    '.liora-morning__content, ' +
    '.liora-space__inner, ' +
    '.liora-news__inner, ' +
    '.liora-access__inner'
  );

  revealTargets.forEach(el => el.classList.add('liora-reveal'));

  const revealObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('liora-reveal--visible');
          revealObserver.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.15,
      rootMargin: '0px 0px -40px 0px',
    }
  );

  revealTargets.forEach(el => revealObserver.observe(el));


  /* ---------- Smooth scroll for anchor links ---------- */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;

      const targetElement = document.querySelector(targetId);
      if (!targetElement) return;

      e.preventDefault();
      const headerHeight = header.offsetHeight;
      const elementPosition = targetElement.getBoundingClientRect().top + window.scrollY;
      const offsetPosition = elementPosition - headerHeight - 16;

      window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth',
      });
    });
  });
});
