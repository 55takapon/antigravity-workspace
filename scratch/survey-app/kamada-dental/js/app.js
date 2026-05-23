/* ============================================
   Survey App — Logic & Configuration
   ============================================ */

// ========================================
// 🔧 CONFIG — ここを変更するだけでカスタマイズ可能
// ========================================
const CONFIG = {
  // --- 店舗情報 ---
  shopName: "かまだ歯科医院",
  // 画像パス（img/logo.png 等）を設定すると円形ロゴ表示
  // 空文字 or null の場合は shopEmoji を表示
  shopLogo: "img/logo.png",
  shopEmoji: "🦷",

  // --- 分岐URL ---
  lowRatingUrl: "./review-guide.html",        // 星1-3 → ご感想ページ
  highRatingUrl: "./review-guide.html", // 星4-5 → ご感想ページ

  // --- 分岐閾値 ---
  // この値以下が lowRatingUrl へ遷移
  ratingThreshold: 3,

  // --- UIテキスト ---
  title: "アンケート",
  subtitle: "ご利用ありがとうございます。\nご感想をお聞かせください。",
  buttonText: "次へ",
  footer: "ご協力ありがとうございます。",

  // --- 星のラベル ---
  ratingLabels: {
    1: "不満",
    2: "やや不満",
    3: "普通",
    4: "満足",
    5: "とても満足",
  },
};

// ========================================
// App State
// ========================================
let selectedRating = 0;

// ========================================
// DOM References
// ========================================
const dom = {};

// ========================================
// Initialize
// ========================================
document.addEventListener("DOMContentLoaded", () => {
  cacheDom();
  renderConfig();
  bindEvents();
});

function cacheDom() {
  dom.shopLogoContainer = document.getElementById("shop-logo-container");
  dom.shopName = document.getElementById("shop-name");
  dom.surveyTitle = document.getElementById("survey-title");
  dom.surveySubtitle = document.getElementById("survey-subtitle");
  dom.starRating = document.getElementById("star-rating");
  dom.ratingLabel = document.getElementById("rating-label");
  dom.submitBtn = document.getElementById("submit-btn");
  dom.submitBtnText = document.getElementById("submit-btn-text");
  dom.footer = document.getElementById("survey-footer-text");
  dom.stars = document.querySelectorAll(".star-rating__star");
}

// ========================================
// Render Config
// ========================================
function renderConfig() {
  if (CONFIG.shopLogo) {
    dom.shopLogoContainer.innerHTML = `<img 
      src="${CONFIG.shopLogo}" 
      alt="${CONFIG.shopName}" 
      class="shop-logo"
      id="shop-logo-img"
    >`;
  } else {
    dom.shopLogoContainer.innerHTML = `<div class="shop-logo-emoji" aria-hidden="true">${CONFIG.shopEmoji}</div>`;
  }

  dom.shopName.textContent = CONFIG.shopName;
  dom.surveyTitle.textContent = CONFIG.title;
  dom.surveySubtitle.innerHTML = CONFIG.subtitle.replace(/\n/g, '<br>');
  dom.submitBtnText.textContent = CONFIG.buttonText;
  dom.footer.textContent = CONFIG.footer;
}

// ========================================
// Event Bindings
// ========================================
function bindEvents() {
  dom.stars.forEach((star) => {
    star.addEventListener("click", () => handleStarClick(star));
    star.addEventListener("mouseenter", () => handleStarHover(star));
    star.addEventListener("mouseleave", () => clearStarHover());
  });

  dom.starRating.addEventListener("touchend", (e) => {
    e.preventDefault();
    const touch = e.changedTouches[0];
    const target = document.elementFromPoint(touch.clientX, touch.clientY);
    const star = target?.closest(".star-rating__star");
    if (star) handleStarClick(star);
  });

  dom.submitBtn.addEventListener("click", handleSubmit);
  document.addEventListener("keydown", handleKeyboard);
}

// ========================================
// Star Rating Logic
// ========================================
function handleStarClick(star) {
  const rating = parseInt(star.dataset.rating, 10);
  selectedRating = rating;
  updateStarDisplay(rating);
  updateRatingLabel(rating);
  updateSubmitButton();
}

function handleStarHover(star) {
  if (selectedRating > 0) return;
  const hoverRating = parseInt(star.dataset.rating, 10);
  dom.stars.forEach((s) => {
    const r = parseInt(s.dataset.rating, 10);
    s.classList.toggle("is-hovered", r <= hoverRating);
  });
}

function clearStarHover() {
  dom.stars.forEach((s) => s.classList.remove("is-hovered"));
}

function updateStarDisplay(rating) {
  dom.stars.forEach((star) => {
    const r = parseInt(star.dataset.rating, 10);
    star.classList.remove("is-active");
    if (r <= rating) {
      setTimeout(() => { star.classList.add("is-active"); }, (r - 1) * 60);
    }
  });
}

function updateRatingLabel(rating) {
  const label = CONFIG.ratingLabels[rating] || "";
  dom.ratingLabel.textContent = label;
  dom.ratingLabel.classList.toggle("is-visible", rating > 0);
}

function updateSubmitButton() {
  dom.submitBtn.disabled = selectedRating === 0;
}

// ========================================
// Submit / Navigation
// ========================================
function handleSubmit() {
  if (selectedRating === 0) return;

  // 全星評価でreview-guide.htmlにratingパラメータ付きで遷移
  window.location.href = "./review-guide.html?rating=" + selectedRating;
}

// ========================================
// Keyboard Navigation
// ========================================
function handleKeyboard(e) {
  if (e.key === "Enter" && selectedRating > 0) { handleSubmit(); return; }

  if (e.key === "ArrowRight" || e.key === "ArrowUp") {
    e.preventDefault();
    const next = Math.min(selectedRating + 1, 5);
    if (next > 0) { selectedRating = next; updateStarDisplay(next); updateRatingLabel(next); updateSubmitButton(); }
  }

  if (e.key === "ArrowLeft" || e.key === "ArrowDown") {
    e.preventDefault();
    const prev = Math.max(selectedRating - 1, 1);
    selectedRating = prev; updateStarDisplay(prev); updateRatingLabel(prev); updateSubmitButton();
  }
}
