document.addEventListener('DOMContentLoaded', function() {
    
    // Hamburger Menu
    const menuTrigger = document.querySelector('.js-menu-trigger');
    const nav = document.querySelector('.l-header__nav');
    const navLinks = document.querySelectorAll('.l-header__nav-link');

    if (menuTrigger && nav) {
        menuTrigger.addEventListener('click', function() {
            this.classList.toggle('is-active');
            nav.classList.toggle('is-active');
            
            // Toggle body overflow to prevent scrolling when menu is open
            if (this.classList.contains('is-active')) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }
        });

        // Close menu when a link is clicked
        navLinks.forEach(link => {
            link.addEventListener('click', function() {
                menuTrigger.classList.remove('is-active');
                nav.classList.remove('is-active');
                document.body.style.overflow = '';
            });
        });
    }

    // Header Background on Scroll (Optional enhancement if needed)
    // const header = document.querySelector('.l-header');
    // window.addEventListener('scroll', function() {
    //     if (window.scrollY > 100) {
    //         header.classList.add('is-scrolled');
    //     } else {
    //         header.classList.remove('is-scrolled');
    //     }
    // });

    // Smooth Scroll for anchor links (Polyfill-like behavior for offset)
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const href = this.getAttribute('href');
            const target = document.querySelector(href === "#" || href === "" ? 'html' : href);
            
            if (target) {
                const headerHeight = document.querySelector('.l-header').offsetHeight;
                const targetPosition = target.getBoundingClientRect().top + window.scrollY - headerHeight;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
});
