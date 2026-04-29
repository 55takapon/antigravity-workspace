/**
 * script.js — 榊原税理士事務所 相続税対策LP
 * 機能：
 *  1. ヘッダースクロール制御
 *  2. FAQアコーディオン
 *  3. スクロールアニメーション（Intersection Observer）
 */

'use strict';

/* ============================================================
 * 1. ヘッダー: スクロール時にシャドウ追加
 * ============================================================ */
(function initHeader() {
  const header = document.getElementById('site-header');
  if (!header) return;

  const SCROLL_THRESHOLD = 40;

  function onScroll() {
    if (window.scrollY > SCROLL_THRESHOLD) {
      header.classList.add('is-scrolled');
    } else {
      header.classList.remove('is-scrolled');
    }
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll(); // 初回チェック
}());

/* ============================================================
 * 2. FAQアコーディオン
 * ============================================================ */
(function initFaq() {
  const faqList = document.getElementById('faq-list');
  if (!faqList) return;

  const buttons = faqList.querySelectorAll('.faq-item__btn');

  buttons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const isExpanded = btn.getAttribute('aria-expanded') === 'true';
      const answerId   = btn.getAttribute('aria-controls');
      const answer     = document.getElementById(answerId);

      if (!answer) return;

      // すでに開いているパネルを閉じる
      buttons.forEach(function (otherBtn) {
        if (otherBtn === btn) return;
        const otherId  = otherBtn.getAttribute('aria-controls');
        const otherAns = document.getElementById(otherId);
        if (otherAns && !otherAns.hidden) {
          otherBtn.setAttribute('aria-expanded', 'false');
          otherAns.hidden = true;
        }
      });

      // 対象パネルのトグル
      btn.setAttribute('aria-expanded', String(!isExpanded));
      answer.hidden = isExpanded;
    });
  });
}());

/* ============================================================
 * 3. スクロールアニメーション (Intersection Observer)
 * ============================================================ */
(function initScrollFade() {
  // アニメーション対象の要素を追加
  const targets = [
    '.section-header',
    '.problem-card',
    '.case-card',
    '.service-item',
    '.profile-layout',
    '.faq-item',
    '.cta-final__catch',
    '.cta-final__title',
    '.cta-final .btn',
    '.cta-final__reassurance',
  ];

  const elements = document.querySelectorAll(targets.join(', '));

  // prefers-reduced-motion 対応
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReducedMotion) {
    elements.forEach(function (el) {
      el.classList.add('is-visible');
    });
    return;
  }

  elements.forEach(function (el) {
    el.classList.add('js-fade');
  });

  // 遅延クラスを連番で付与（同じ親を持つ兄弟要素）
  const groups = ['.problems-grid', '.cases-layout', '.services-list', '.faq-list'];
  groups.forEach(function (selector) {
    const container = document.querySelector(selector);
    if (!container) return;
    const children = container.querySelectorAll('.js-fade');
    children.forEach(function (child, index) {
      const delayClass = 'js-fade--delay-' + ((index % 3) + 1);
      child.classList.add(delayClass);
    });
  });

  const observer = new IntersectionObserver(
    function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.12,
      rootMargin: '0px 0px -40px 0px',
    }
  );

  elements.forEach(function (el) {
    observer.observe(el);
  });
}());

/* ============================================================
 * 4. スムーススクロール（anchorリンク対応）
 * ============================================================ */
(function initSmoothScroll() {
  const headerHeight = parseInt(
    getComputedStyle(document.documentElement).getPropertyValue('--header-h'),
    10
  ) || 64;

  document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      const href   = anchor.getAttribute('href');
      const target = document.querySelector(href);
      if (!target) return;

      e.preventDefault();
      const offsetTop = target.getBoundingClientRect().top + window.scrollY - headerHeight - 16;
      window.scrollTo({ top: offsetTop, behavior: 'smooth' });
    });
  });
}());
