const header = document.querySelector("[data-header]");
const menuButton = document.querySelector(".menu-button");
const menuLabel = menuButton.querySelector(".visually-hidden");
const nav = document.querySelector(".global-nav");

const setHeaderState = () => {
  header.classList.toggle("is-scrolled", window.scrollY > 24);
};

const closeMenu = ({ returnFocus = false } = {}) => {
  menuButton.setAttribute("aria-expanded", "false");
  menuLabel.textContent = "メニューを開く";
  nav.classList.remove("is-open");
  document.body.style.overflow = "";
  if (returnFocus) menuButton.focus();
};

menuButton.addEventListener("click", () => {
  const willOpen = menuButton.getAttribute("aria-expanded") !== "true";
  menuButton.setAttribute("aria-expanded", String(willOpen));
  menuLabel.textContent = willOpen ? "メニューを閉じる" : "メニューを開く";
  nav.classList.toggle("is-open", willOpen);
  document.body.style.overflow = willOpen ? "hidden" : "";
  if (willOpen) nav.querySelector("a").focus();
});

nav.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => closeMenu()));
document.addEventListener("keydown", (event) => {
  if (!nav.classList.contains("is-open")) return;

  if (event.key === "Escape") {
    closeMenu({ returnFocus: true });
    return;
  }

  if (event.key === "Tab") {
    const focusable = [menuButton, ...nav.querySelectorAll("a")];
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }
});
window.addEventListener("scroll", setHeaderState, { passive: true });
window.addEventListener("resize", () => {
  if (window.innerWidth >= 960) closeMenu();
});
setHeaderState();

if (!window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12 });

  document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));
} else {
  document.querySelectorAll(".reveal").forEach((element) => element.classList.add("is-visible"));
}
