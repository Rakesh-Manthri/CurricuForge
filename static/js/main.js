/* ================================================
   main.js — Shared across all pages
   ================================================ */

// ---------- Hamburger Menu ----------
const hamburger = document.getElementById('hamburger');
const navLinks = document.getElementById('navLinks');
if (hamburger && navLinks) {
    hamburger.addEventListener('click', () => {
        navLinks.classList.toggle('open');
        const spans = hamburger.querySelectorAll('span');
        const isOpen = navLinks.classList.contains('open');
        spans[0].style.transform = isOpen ? 'rotate(45deg) translate(5px, 5px)' : '';
        spans[1].style.opacity = isOpen ? '0' : '1';
        spans[2].style.transform = isOpen ? 'rotate(-45deg) translate(5px, -5px)' : '';
    });
}

// ---------- Scroll-triggered reveal animations ----------
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

// ---------- Navbar scroll behavior ----------
const navbar = document.querySelector('.navbar');
if (navbar) {
    let lastScrollY = window.scrollY;
    navbar.style.transition = 'transform 0.3s ease-out, box-shadow 0.3s ease-out';

    window.addEventListener('scroll', () => {
        if (window.scrollY > 20) {
            navbar.style.boxShadow = '0 4px 20px rgba(99,102,241,0.08)';
        } else {
            navbar.style.boxShadow = 'none';
        }

        if (window.scrollY > lastScrollY && window.scrollY > 100) {
            navbar.style.transform = 'translateY(-100%)';
        } else {
            navbar.style.transform = 'translateY(0)';
        }
        lastScrollY = window.scrollY < 0 ? 0 : window.scrollY;
    }, { passive: true });
}

// ---------- Topic tag toggle (shared) ----------
document.querySelectorAll('.topic-tag[data-topic], .topic-tag[data-tag]').forEach(tag => {
    tag.addEventListener('click', () => tag.classList.toggle('active'));
});

// ---------- Dark Mode Toggle ----------
const themeToggle = document.getElementById('themeToggle');
const body = document.body;

// Check for saved theme preference
const savedTheme = localStorage.getItem('theme');
if (savedTheme === 'dark') {
    body.classList.add('dark-mode');
    if (themeToggle) themeToggle.innerHTML = '☀️';
}

if (themeToggle) {
    themeToggle.addEventListener('click', () => {
        body.classList.toggle('dark-mode');
        const isDark = body.classList.contains('dark-mode');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        themeToggle.innerHTML = isDark ? '☀️' : '🌙';
    });
}

// ---------- Animate hero numbers ----------
function animateCounters() {
    document.querySelectorAll('[data-count]').forEach(el => {
        const target = parseFloat(el.dataset.count);
        const isFloat = target % 1 !== 0;
        const duration = 1800;
        const start = performance.now();
        function update(now) {
            const elapsed = Math.min((now - start) / duration, 1);
            const ease = 1 - Math.pow(1 - elapsed, 3);
            el.textContent = isFloat
                ? (ease * target).toFixed(1)
                : Math.floor(ease * target).toLocaleString();
            if (elapsed < 1) requestAnimationFrame(update);
        }
        requestAnimationFrame(update);
    });
}

const heroObserver = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) {
        animateCounters();
        heroObserver.disconnect();
    }
}, { threshold: 0.3 });

const heroStats = document.querySelector('.hero-stats');
if (heroStats) heroObserver.observe(heroStats);

// ---------- Toast Notification (Shared) ----------
function showNotification(title, message, type = 'success') {
    let container = document.getElementById('notificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        container.className = 'notification-container';
        document.body.appendChild(container);
    }

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    const icon = type === 'success' ? '✨' : (type === 'error' ? '⚠️' : 'ℹ️');

    notification.innerHTML = `
        <div class="notification-icon">${icon}</div>
        <div class="notification-content">
            <div class="notification-title">${title}</div>
            <div class="notification-message">${message}</div>
        </div>
    `;
    container.appendChild(notification);

    // Slide in
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);

    // Slide out and remove
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 500);
    }, 4500);
}
