(() => {
  const menuButton = document.querySelector(".menu-toggle");
  const mobileNavigation = document.querySelector(".mobile-navigation");

  if (!menuButton || !mobileNavigation) {
    return;
  }

  const focusableSelector = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';
  let previouslyFocused = null;

  const isOpen = () => menuButton.getAttribute("aria-expanded") === "true";

  const openMenu = () => {
    previouslyFocused = document.activeElement;
    document.body.classList.add("nav-open");
    menuButton.setAttribute("aria-expanded", "true");
    menuButton.setAttribute("aria-label", "メニューを閉じる");
    mobileNavigation.setAttribute("aria-hidden", "false");

    const firstFocusable = mobileNavigation.querySelector(focusableSelector);
    if (firstFocusable) {
      window.requestAnimationFrame(() => firstFocusable.focus());
    }
  };

  const closeMenu = ({ restoreFocus = true } = {}) => {
    document.body.classList.remove("nav-open");
    menuButton.setAttribute("aria-expanded", "false");
    menuButton.setAttribute("aria-label", "メニューを開く");
    mobileNavigation.setAttribute("aria-hidden", "true");

    if (restoreFocus && previouslyFocused instanceof HTMLElement) {
      previouslyFocused.focus();
    }
  };

  menuButton.addEventListener("click", () => {
    if (isOpen()) {
      closeMenu();
    } else {
      openMenu();
    }
  });

  mobileNavigation.addEventListener("click", (event) => {
    if (event.target.closest("a")) {
      closeMenu({ restoreFocus: false });
    }
  });

  document.addEventListener("keydown", (event) => {
    if (!isOpen()) {
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      closeMenu();
      return;
    }

    if (event.key !== "Tab") {
      return;
    }

    const focusable = [menuButton, ...mobileNavigation.querySelectorAll(focusableSelector)];
    if (!focusable.length) {
      event.preventDefault();
      menuButton.focus();
      return;
    }

    const first = focusable[0];
    const last = focusable[focusable.length - 1];

    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });

  const desktopMedia = window.matchMedia("(min-width: 960px)");
  desktopMedia.addEventListener("change", (event) => {
    if (event.matches && isOpen()) {
      closeMenu({ restoreFocus: false });
    }
  });
})();
