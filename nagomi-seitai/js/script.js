document.addEventListener('DOMContentLoaded', () => {
    const menuTrigger = document.getElementById('js-menu-trigger');
    const nav = document.getElementById('js-nav');
    const body = document.body;
    const navLinks = document.querySelectorAll('.header__nav-link');

    if (menuTrigger && nav) {
        menuTrigger.addEventListener('click', () => {
            body.classList.toggle('u-mobile-nav-open');
            
            // Interaction for hamburger icon lines could be added here
        });

        // Close menu when link is clicked
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                body.classList.remove('u-mobile-nav-open');
            });
        });
    }
});
