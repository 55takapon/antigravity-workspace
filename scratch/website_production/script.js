/**
 * Esthe Salon Lunea — Script
 * ハンバーガーメニュー、ヘッダースクロール変化、スクロールアニメーション
 */

document.addEventListener('DOMContentLoaded', () => {
  // ===== Hamburger Menu =====
  const hamburger = document.getElementById('hamburger');
  const nav = document.getElementById('nav');
  const header = document.getElementById('header');

  const closeMenu = () => {
    hamburger.classList.remove('is-open');
    nav.classList.remove('is-open');
    hamburger.setAttribute('aria-expanded', 'false');
    document.body.style.overflow = '';
  };

  const openMenu = () => {
    hamburger.classList.add('is-open');
    nav.classList.add('is-open');
    hamburger.setAttribute('aria-expanded', 'true');
    document.body.style.overflow = 'hidden';
  };

  hamburger.addEventListener('click', () => {
    const isOpen = hamburger.classList.contains('is-open');
    if (isOpen) {
      closeMenu();
    } else {
      openMenu();
    }
  });

  // ナビリンク・CTAをクリックしたらメニューを閉じる
  nav.querySelectorAll('.lunea-header__nav-link, .lunea-header__cta').forEach(link => {
    link.addEventListener('click', closeMenu);
  });

  // Escキーでメニューを閉じる
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && nav.classList.contains('is-open')) {
      closeMenu();
      hamburger.focus();
    }
  });

  // ===== Header Scroll Effect =====
  const scrollThreshold = 80;

  const updateHeader = () => {
    if (window.scrollY > scrollThreshold) {
      header.classList.add('is-scrolled');
    } else {
      header.classList.remove('is-scrolled');
    }
  };

  window.addEventListener('scroll', updateHeader, { passive: true });
  updateHeader();

  // ===== Scroll Fade-in Animation =====
  const fadeTargets = document.querySelectorAll(
    '.lunea-concept, .lunea-menu__header, .lunea-menu__category, .lunea-menu__image-col, ' +
    '.lunea-space__content, .lunea-flow__header, .lunea-flow__step, .lunea-flow__image-col, ' +
    '.lunea-voice__header, .lunea-voice__item, .lunea-reservation__inner'
  );

  fadeTargets.forEach(el => {
    el.classList.add('lunea-fade-in');
  });

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      },
      {
        threshold: 0.1,
        rootMargin: '0px 0px -40px 0px',
      }
    );

    fadeTargets.forEach(el => observer.observe(el));
  } else {
    // Fallback: just show everything
    fadeTargets.forEach(el => el.classList.add('is-visible'));
  }

  // ===== Smooth scroll for anchor links (Safari fallback) =====
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', (e) => {
      const targetId = anchor.getAttribute('href');
      if (targetId === '#') {
        e.preventDefault();
        return;
      }

      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        e.preventDefault();
        const headerHeight = header.offsetHeight;
        const targetPosition = targetEl.getBoundingClientRect().top + window.scrollY - headerHeight;

        window.scrollTo({
          top: targetPosition,
          behavior: 'smooth',
        });
      }
    });
  });
});
