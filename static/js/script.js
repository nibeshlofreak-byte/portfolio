// script.js - Interactive Cosmic Portfolio
document.addEventListener('DOMContentLoaded', () => {
    console.log('Cosmic Portfolio loaded successfully.');

    // Smooth navigation highlighting
    const navLinks = document.querySelectorAll('.navbar a');
    const sections = document.querySelectorAll('section, header');

    window.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop - 120;
            if (window.scrollY >= sectionTop) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            if (link.getAttribute('href') && link.getAttribute('href').includes(current) && current) {
                navLinks.forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            }
        });
    });
});
