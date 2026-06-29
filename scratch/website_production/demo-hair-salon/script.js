document.addEventListener('DOMContentLoaded', () => {
    // Mobile Menu Toggle
    const hamburger = document.getElementById('js-hamburger');
    const navSp = document.getElementById('js-nav-sp');
    const navLinks = navSp.querySelectorAll('a');

    if (hamburger && navSp) {
        hamburger.addEventListener('click', () => {
            const isActive = navSp.classList.contains('is-active');
            
            if (isActive) {
                navSp.classList.remove('is-active');
                hamburger.setAttribute('aria-expanded', 'false');
            } else {
                navSp.classList.add('is-active');
                hamburger.setAttribute('aria-expanded', 'true');
            }
        });

        // Close menu when a link is clicked
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navSp.classList.remove('is-active');
                hamburger.setAttribute('aria-expanded', 'false');
            });
        });
    }

    // Smooth Scrolling for Anchor Links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            
            const targetElement = document.querySelector(targetId);
            if (targetElement) {
                const headerOffset = 70; // Height of the fixed header
                const elementPosition = targetElement.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                window.scrollTo({
                    top: offsetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
});
