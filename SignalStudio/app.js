/* ============================================
   Signal Studio — Website JS
   Carousel, signal canvases, scroll animations
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

    // ===== NAVBAR SCROLL =====
    const navbar = document.getElementById('navbar');
    window.addEventListener('scroll', () => {
        navbar.classList.toggle('scrolled', window.scrollY > 40);
    });

    // ===== MOBILE MENU =====
    const mobileBtn = document.getElementById('mobileMenuBtn');
    const navLinks = document.querySelector('.nav-links');
    if (mobileBtn && navLinks) {
        mobileBtn.addEventListener('click', () => {
            const isOpen = navLinks.style.display === 'flex';
            navLinks.style.display = isOpen ? 'none' : 'flex';
            navLinks.style.position = isOpen ? '' : 'absolute';
            navLinks.style.top = isOpen ? '' : '64px';
            navLinks.style.left = isOpen ? '' : '0';
            navLinks.style.right = isOpen ? '' : '0';
            navLinks.style.flexDirection = isOpen ? '' : 'column';
            navLinks.style.padding = isOpen ? '' : '20px 24px';
            navLinks.style.background = isOpen ? '' : 'var(--bg-panel)';
            navLinks.style.borderBottom = isOpen ? '' : '1px solid var(--border)';
            navLinks.style.gap = isOpen ? '' : '16px';
        });
    }

    // ===== CAROUSEL =====
    const slides = document.querySelectorAll('.carousel-slide');
    const dotsContainer = document.getElementById('carouselDots');
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    let currentSlide = 0;

    // Create dots
    slides.forEach((_, i) => {
        const dot = document.createElement('button');
        dot.className = 'carousel-dot' + (i === 0 ? ' active' : '');
        dot.setAttribute('aria-label', `Слайд ${i + 1}`);
        dot.addEventListener('click', () => goToSlide(i));
        dotsContainer.appendChild(dot);
    });

    function goToSlide(index) {
        slides[currentSlide].classList.remove('active');
        dotsContainer.children[currentSlide].classList.remove('active');
        currentSlide = (index + slides.length) % slides.length;
        slides[currentSlide].classList.add('active');
        dotsContainer.children[currentSlide].classList.add('active');
    }

    if (prevBtn) prevBtn.addEventListener('click', () => goToSlide(currentSlide - 1));
    if (nextBtn) nextBtn.addEventListener('click', () => goToSlide(currentSlide + 1));

    // Auto-advance every 5s
    let autoPlay = setInterval(() => goToSlide(currentSlide + 1), 5000);
    const carousel = document.getElementById('carousel');
    if (carousel) {
        carousel.addEventListener('mouseenter', () => clearInterval(autoPlay));
        carousel.addEventListener('mouseleave', () => {
            autoPlay = setInterval(() => goToSlide(currentSlide + 1), 5000);
        });
    }

    // ===== SCROLL ANIMATIONS =====
    const observerOptions = { threshold: 0.15, rootMargin: '0px 0px -40px 0px' };
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const delay = entry.target.dataset.delay || 0;
                setTimeout(() => {
                    entry.target.classList.add('visible');
                }, parseInt(delay));
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    document.querySelectorAll('.feature-card').forEach(card => observer.observe(card));

    // ===== SIGNAL WAVEFORM CANVASES =====
    const signalTypes = {
        sinusoidal: (x) => Math.sin(2 * Math.PI * 2 * x),
        triangular: (x) => 2 * Math.abs(2 * (x * 2 - Math.floor(x * 2 + 0.5))) - 1,
        rectangular: (x) => (x * 2 % 1 < 0.3) ? 1 : -1,
        meander: (x) => Math.sin(2 * Math.PI * 2 * x) >= 0 ? 1 : -1,
        sawtooth: (x) => 2 * (x * 2 - Math.floor(x * 2 + 0.5)),
        noise: () => (Math.random() * 2 - 1),
        pulse: (x) => (x * 2 % 1 < 0.2) ? 1 : 0,
        dc: () => 0.5,
        chirp: (x) => Math.sin(2 * Math.PI * (2 + 6 * x) * x),
        trapezoidal: (x) => {
            const p = (x * 2) % 1;
            if (p < 0.125) return -1 + 2 * p / 0.125;
            if (p < 0.5) return 1;
            if (p < 0.625) return 1 - 2 * (p - 0.5) / 0.125;
            return -1;
        },
        gaussian: (x) => {
            const period = 0.5;
            const sigma = period / 6;
            const xp = (x % period + period) % period;
            return Math.exp(-0.5 * ((xp - period / 2) / sigma) ** 2);
        }
    };

    document.querySelectorAll('.signal-canvas').forEach(canvas => {
        const type = canvas.dataset.type;
        if (!type || !signalTypes[type]) return;

        const dpr = window.devicePixelRatio || 1;
        const rect = canvas.getBoundingClientRect();
        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        const ctx = canvas.getContext('2d');
        ctx.scale(dpr, dpr);
        const w = rect.width;
        const h = rect.height;

        // Background
        ctx.fillStyle = '#000814';
        ctx.fillRect(0, 0, w, h);

        // Grid
        ctx.strokeStyle = 'rgba(24, 144, 255, 0.08)';
        ctx.lineWidth = 0.5;
        for (let gy = 0; gy < h; gy += h / 4) {
            ctx.beginPath();
            ctx.moveTo(0, gy);
            ctx.lineTo(w, gy);
            ctx.stroke();
        }

        // Waveform
        const fn = signalTypes[type];
        ctx.strokeStyle = '#00ff41';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        const cycles = type === 'dc' ? 1 : 2.5;
        for (let px = 0; px < w; px++) {
            const x = (px / w) * cycles;
            let y;
            if (type === 'noise') {
                // Use deterministic "random" based on position
                y = Math.sin(px * 0.7) * Math.cos(px * 1.3) * Math.sin(px * 3.7) + 
                    Math.sin(px * 11.3) * 0.3 + Math.cos(px * 7.1) * 0.4;
            } else {
                y = fn(x);
            }
            const py = h / 2 - y * (h * 0.38);
            if (px === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
        }
        ctx.stroke();
    });

    // ===== SMOOTH SCROLL FOR NAV LINKS =====
    document.querySelectorAll('a[href^="#"]').forEach(link => {
        link.addEventListener('click', (e) => {
            const target = document.querySelector(link.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                // Close mobile menu if open
                if (navLinks && navLinks.style.display === 'flex' && window.innerWidth <= 968) {
                    navLinks.style.display = 'none';
                }
            }
        });
    });
});