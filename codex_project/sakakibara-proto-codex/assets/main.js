const menuButton = document.querySelector("[data-menu-button]");
const nav = document.querySelector("[data-nav]");

if (menuButton && nav) {
  menuButton.addEventListener("click", () => {
    const isOpen = menuButton.getAttribute("aria-expanded") === "true";
    menuButton.setAttribute("aria-expanded", String(!isOpen));
    nav.classList.toggle("is-open", !isOpen);
  });

  nav.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", () => {
      menuButton.setAttribute("aria-expanded", "false");
      nav.classList.remove("is-open");
    });
  });
}

document.querySelectorAll(".faq-item").forEach((item) => {
  item.addEventListener("toggle", () => {
    const summary = item.querySelector("summary");
    if (summary) {
      summary.setAttribute("aria-expanded", String(item.open));
    }
  });
});
