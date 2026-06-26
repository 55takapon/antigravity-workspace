/* =============================================
   AI活用診断 LP - JavaScript
   機能: ハンバーガーメニュー / FAQアコーディオン / フェードイン
   ============================================= */

document.addEventListener('DOMContentLoaded', () => {
  initHamburger();
  initFAQ();
  initFadeIn();
});


/* --- ハンバーガーメニュー --- */
function initHamburger() {
  const hamburger = document.getElementById('js-hamburger');
  const mobileMenu = document.getElementById('js-mobile-menu');

  if (!hamburger || !mobileMenu) return;

  hamburger.addEventListener('click', () => {
    const isOpen = hamburger.classList.toggle('is-active');
    mobileMenu.classList.toggle('is-open', isOpen);
    document.body.style.overflow = isOpen ? 'hidden' : '';
    hamburger.setAttribute('aria-expanded', String(isOpen));
  });

  // メニュー内リンククリックで閉じる
  mobileMenu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      hamburger.classList.remove('is-active');
      mobileMenu.classList.remove('is-open');
      document.body.style.overflow = '';
      hamburger.setAttribute('aria-expanded', 'false');
    });
  });
}


/* --- FAQアコーディオン --- */
function initFAQ() {
  const questions = document.querySelectorAll('.faq-question');

  questions.forEach(question => {
    question.addEventListener('click', () => {
      const item = question.closest('.faq-item');
      const answer = item.querySelector('.faq-answer');
      const isOpen = item.classList.contains('is-open');

      // 他のFAQを閉じる
      document.querySelectorAll('.faq-item.is-open').forEach(openItem => {
        if (openItem !== item) {
          openItem.classList.remove('is-open');
          const openAnswer = openItem.querySelector('.faq-answer');
          openAnswer.style.maxHeight = '0';
          openItem.querySelector('.faq-question').setAttribute('aria-expanded', 'false');
        }
      });

      // 開閉トグル
      if (isOpen) {
        item.classList.remove('is-open');
        answer.style.maxHeight = '0';
        question.setAttribute('aria-expanded', 'false');
      } else {
        item.classList.add('is-open');
        answer.style.maxHeight = answer.scrollHeight + 'px';
        question.setAttribute('aria-expanded', 'true');
      }
    });
  });
}


/* --- スクロールフェードイン --- */
function initFadeIn() {
  const targets = document.querySelectorAll('.fade-in');

  if (!targets.length) return;

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
      threshold: 0.15,
      rootMargin: '0px 0px -40px 0px',
    }
  );

  targets.forEach(target => observer.observe(target));
}
