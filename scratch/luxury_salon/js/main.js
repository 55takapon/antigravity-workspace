document.addEventListener('DOMContentLoaded', () => {
    // Hamburger Menu
    const hamburger = document.querySelector('.header__hamburger');
    const mobileMenu = document.querySelector('.header__mobile-menu');
    const mobileLinks = document.querySelectorAll('.header__mobile-menu-item a');

    hamburger.addEventListener('click', () => {
        hamburger.classList.toggle('is-active');
        mobileMenu.classList.toggle('is-active');
    });

    mobileLinks.forEach(link => {
        link.addEventListener('click', () => {
            hamburger.classList.remove('is-active');
            mobileMenu.classList.remove('is-active');
        });
    });

    // Scroll Fade-in Animation
    const fadeElements = document.querySelectorAll('.u-fade-in, .u-fade-up');

    const observerOptions = {
        root: null,
        rootMargin: '0px 0px -100px 0px',
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    fadeElements.forEach(el => {
        observer.observe(el);
    });

    // Initial Hero Animation
    setTimeout(() => {
        const heroText = document.querySelectorAll('.hero__message-vertical .u-fade-in');
        heroText.forEach(el => el.classList.add('is-visible'));
    }, 500);
});
