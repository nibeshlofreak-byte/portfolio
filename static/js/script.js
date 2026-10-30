// script.js - Dynamic Cosmic Starfield & Clean Navigation
document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Dynamic Cosmic Starfield Canvas
    initStarfield();

    // 2. Smooth Navigation Highlighting
    initNavHighlight();
});

function initStarfield() {
    let canvas = document.getElementById('starfield-canvas');
    if (!canvas) {
        canvas = document.createElement('canvas');
        canvas.id = 'starfield-canvas';
        document.body.prepend(canvas);
    }

    const ctx = canvas.getContext('2d');
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    window.addEventListener('resize', () => {
        width = canvas.width = window.innerWidth;
        height = canvas.height = window.innerHeight;
        createStars();
    });

    const starCount = Math.floor((width * height) / 3600); // Dense starry night
    let stars = [];
    const colors = [
        '#ffffff', '#fdf4ff', '#e0e7ff', '#fef08a', '#fbcfe8', '#c7d2fe', '#fed7aa'
    ];

    function createStars() {
        stars = [];
        for (let i = 0; i < starCount; i++) {
            stars.push({
                x: Math.random() * width,
                y: Math.random() * height,
                radius: Math.random() * 1.5 + 0.4,
                color: colors[Math.floor(Math.random() * colors.length)],
                alpha: Math.random() * 0.7 + 0.3,
                speed: Math.random() * 0.02 + 0.006,
                phase: Math.random() * Math.PI * 2,
                sparkle: Math.random() > 0.82
            });
        }
    }
    createStars();

    // Occasional subtle meteors / shooting stars
    let meteors = [];
    function spawnMeteor() {
        if (meteors.length < 2 && Math.random() < 0.015) {
            meteors.push({
                x: Math.random() * width * 0.85,
                y: Math.random() * height * 0.4,
                length: Math.random() * 90 + 50,
                speed: Math.random() * 5 + 4,
                angle: Math.PI / 4 + (Math.random() - 0.5) * 0.25,
                opacity: 1,
                color: Math.random() > 0.5 ? '#f472b6' : '#a78bfa'
            });
        }
    }

    let time = 0;
    function render() {
        time += 0.03;
        ctx.clearRect(0, 0, width, height);

        // Render Stars
        for (let s of stars) {
            const flicker = Math.sin(time * s.speed * 60 + s.phase) * 0.35;
            const currentAlpha = Math.max(0.12, Math.min(1, s.alpha + flicker));
            ctx.fillStyle = s.color;
            ctx.globalAlpha = currentAlpha;
            ctx.beginPath();
            ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
            ctx.fill();

            // 4-point subtle flare on brightest stars
            if (s.sparkle && currentAlpha > 0.75) {
                ctx.strokeStyle = s.color;
                ctx.lineWidth = 0.5;
                ctx.globalAlpha = currentAlpha * 0.45;
                ctx.beginPath();
                ctx.moveTo(s.x - s.radius * 2.8, s.y);
                ctx.lineTo(s.x + s.radius * 2.8, s.y);
                ctx.moveTo(s.x, s.y - s.radius * 2.8);
                ctx.lineTo(s.x, s.y + s.radius * 2.8);
                ctx.stroke();
            }
        }

        // Render Meteors
        spawnMeteor();
        for (let i = meteors.length - 1; i >= 0; i--) {
            const m = meteors[i];
            m.x += Math.cos(m.angle) * m.speed;
            m.y += Math.sin(m.angle) * m.speed;
            m.opacity -= 0.012;

            if (m.opacity <= 0 || m.x > width || m.y > height) {
                meteors.splice(i, 1);
                continue;
            }

            const tailX = m.x - Math.cos(m.angle) * m.length;
            const tailY = m.y - Math.sin(m.angle) * m.length;

            const grad = ctx.createLinearGradient(m.x, m.y, tailX, tailY);
            grad.addColorStop(0, m.color);
            grad.addColorStop(1, 'transparent');

            ctx.globalAlpha = m.opacity;
            ctx.strokeStyle = grad;
            ctx.lineWidth = 1.6;
            ctx.beginPath();
            ctx.moveTo(m.x, m.y);
            ctx.lineTo(tailX, tailY);
            ctx.stroke();
        }

        ctx.globalAlpha = 1;
        requestAnimationFrame(render);
    }
    render();
}

function initNavHighlight() {
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
}

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
