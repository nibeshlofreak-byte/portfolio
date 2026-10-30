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

function saveEvaluatorFeedback() {
    const nameInput = document.getElementById('staticEvaluatorName');
    const scoreInput = document.getElementById('staticScore');
    const feedbackInput = document.getElementById('staticFeedback');

    if (!feedbackInput || !feedbackInput.value.trim()) {
        alert('Please enter evaluation comments before saving.');
        return;
    }

    const feedbackRecord = {
        name: (nameInput && nameInput.value.trim()) || 'Faculty Reviewer',
        score: scoreInput ? scoreInput.value : '10',
        feedback: feedbackInput.value.trim(),
        date: new Date().toLocaleString()
    };

    try {
        localStorage.setItem('evaluator_review', JSON.stringify(feedbackRecord));
    } catch (e) {
        console.warn('Storage not accessible:', e);
    }

    const notice = document.getElementById('feedbackSavedNotice');
    if (notice) {
        notice.style.display = 'block';
        setTimeout(() => {
            notice.style.display = 'none';
        }, 5000);
    }
}

