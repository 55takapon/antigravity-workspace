document.addEventListener('DOMContentLoaded', () => {
    // Menu Toggle
    const menuBtn = document.querySelector('.header__menu-btn');
    const headerNav = document.querySelector('.header__nav');
    const navLinks = document.querySelectorAll('.header__nav-item a');

    if (menuBtn && headerNav) {
        menuBtn.addEventListener('click', () => {
            const isExpanded = menuBtn.getAttribute('aria-expanded') === 'true';
            menuBtn.setAttribute('aria-expanded', !isExpanded);
            menuBtn.classList.toggle('active');
            headerNav.classList.toggle('active');
            document.body.classList.toggle('no-scroll'); // Prevent background scrolling
        });

        // Close menu when clicking a link
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                menuBtn.classList.remove('active');
                headerNav.classList.remove('active');
                menuBtn.setAttribute('aria-expanded', 'false');
                document.body.classList.remove('no-scroll');
            });
        });
    }

    // Scroll Animation Observer
    const observerOptions = {
        root: null,
        rootMargin: '0px',
        threshold: 0.2
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target); // Only animate once
            }
        });
    }, observerOptions);

    const animatedElements = document.querySelectorAll('.section__title, .section__subtitle, .concept__lead, .concept__desc, .menu__item, .access__row');
    animatedElements.forEach(el => observer.observe(el));
});
