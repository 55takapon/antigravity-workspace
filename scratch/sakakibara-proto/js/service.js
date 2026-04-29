/**
 * service.js
 * サービスページ専用スクリプト
 * - FAQ アコーディオン（スムーズなアニメーション付き）
 */

'use strict';

(function () {

  // -------------------------------------------------------------------------
  // FAQ Accordion
  //
  // WAI-ARIA: aria-expanded / aria-controls / hidden を制御
  // アニメーション: スライドダウン / スライドアップを requestAnimationFrame で実装
  // -------------------------------------------------------------------------

  const faqItems = document.querySelectorAll('.p-svc-faq__item');
  const DURATION = 280; // ms

  /**
   * 高さのスライドアニメーション
   * @param {HTMLElement} el 対象要素
   * @param {number} from  開始px
   * @param {number} to    終了px
   * @param {Function} onComplete 完了後コールバック
   */
  function slideAnimate(el, from, to, onComplete) {
    const start = performance.now();

    el.classList.add('is-animating');
    el.style.height = from + 'px';
    el.style.overflow = 'hidden';

    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / DURATION, 1);
      // easeOutQuart
      const ease = 1 - Math.pow(1 - progress, 4);
      const current = from + (to - from) * ease;
      el.style.height = current + 'px';

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        el.classList.remove('is-animating');
        el.style.height = '';
        el.style.overflow = '';
        if (onComplete) onComplete();
      }
    }

    requestAnimationFrame(step);
  }

  /**
   * アコーディオンを開く
   */
  function openAnswer(btn, answer) {
    // hidden を外し、実際の高さを取得するために display: block
    answer.removeAttribute('hidden');
    answer.style.height = '0';
    answer.style.overflow = 'hidden';

    const targetHeight = answer.scrollHeight;

    btn.setAttribute('aria-expanded', 'true');

    slideAnimate(answer, 0, targetHeight, function () {
      answer.style.height = '';
      answer.style.overflow = '';
    });
  }

  /**
   * アコーディオンを閉じる
   */
  function closeAnswer(btn, answer) {
    const currentHeight = answer.scrollHeight;

    btn.setAttribute('aria-expanded', 'false');

    slideAnimate(answer, currentHeight, 0, function () {
      answer.setAttribute('hidden', '');
      answer.style.height = '';
    });
  }

  // 各フォームアイテムにイベントリスナーをバインド
  faqItems.forEach(function (item) {
    const btn = item.querySelector('.p-svc-faq__question');
    if (!btn) return;

    const answerId = btn.getAttribute('aria-controls');
    const answer = document.getElementById(answerId);
    if (!answer) return;

    btn.addEventListener('click', function () {
      const isExpanded = btn.getAttribute('aria-expanded') === 'true';

      if (isExpanded) {
        closeAnswer(btn, answer);
      } else {
        openAnswer(btn, answer);
      }
    });

    // キーボードアクセシビリティ: Enter / Space で開閉
    btn.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        btn.click();
      }
    });
  });

})();
