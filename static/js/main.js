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

// ---------- Auth-aware Navbar ----------
(async function updateNavbarAuth() {
    try {
        const res = await fetch('/api/auth/me');
        const data = await res.json();
        const navActions = document.querySelector('.nav-actions');
        const ctaBtn = navActions ? navActions.querySelector('.nav-cta') : null;

        if (data.user && ctaBtn) {
            const initials = data.user.full_name.split(' ').map(w => w[0]).join('').toUpperCase().slice(0, 2);

            ctaBtn.outerHTML = `
            <div class="nav-user-menu" style="position:relative;">
                <button class="nav-user-btn" id="navUserBtn" style="display:flex;align-items:center;gap:0.5rem;background:linear-gradient(135deg,rgba(99,102,241,0.08),rgba(6,182,212,0.08));border:1px solid rgba(99,102,241,0.15);border-radius:10px;padding:0.35rem 0.8rem;cursor:pointer;font-family:inherit;">
                    <span style="width:28px;height:28px;border-radius:50%;background:var(--gradient-primary);color:white;font-size:0.7rem;font-weight:700;display:inline-flex;align-items:center;justify-content:center;">${initials}</span>
                    <span style="font-size:0.8rem;font-weight:600;color:var(--text-heading);">${data.user.full_name.split(' ')[0]}</span>
                    <span style="font-size:0.6rem;color:var(--text-muted);">▼</span>
                </button>
                <div class="nav-user-dropdown" id="navUserDropdown" style="display:none;position:absolute;top:calc(100% + 6px);right:0;background:var(--surface);border:1px solid var(--border);border-radius:12px;box-shadow:0 10px 30px rgba(0,0,0,0.15);padding:0.5rem;min-width:180px;z-index:100;">
                    <div style="padding:0.5rem 0.75rem;border-bottom:1px solid var(--border);margin-bottom:0.25rem;">
                        <div style="font-size:0.8rem;font-weight:600;color:var(--text-heading);">${data.user.full_name}</div>
                        <div style="font-size:0.7rem;color:var(--text-muted);">${data.user.email}</div>
                    </div>
                    <a href="/generate" style="display:block;padding:0.4rem 0.75rem;font-size:0.8rem;color:var(--text-body);text-decoration:none;border-radius:8px;" onmouseenter="this.style.background='rgba(99,102,241,0.08)'" onmouseleave="this.style.background=''">🎓 Generate</a>
                    <a href="/history" style="display:block;padding:0.4rem 0.75rem;font-size:0.8rem;color:var(--text-body);text-decoration:none;border-radius:8px;" onmouseenter="this.style.background='rgba(99,102,241,0.08)'" onmouseleave="this.style.background=''">📁 History</a>
                    <a href="/analysis" style="display:block;padding:0.4rem 0.75rem;font-size:0.8rem;color:var(--text-body);text-decoration:none;border-radius:8px;" onmouseenter="this.style.background='rgba(99,102,241,0.08)'" onmouseleave="this.style.background=''">🔍 Analysis</a>
                    <button id="navSignOutBtn" style="display:block;width:100%;text-align:left;padding:0.4rem 0.75rem;font-size:0.8rem;color:#ef4444;background:none;border:none;cursor:pointer;border-radius:8px;font-family:inherit;margin-top:0.25rem;border-top:1px solid var(--border);padding-top:0.5rem;" onmouseenter="this.style.background='rgba(239,68,68,0.08)'" onmouseleave="this.style.background=''">🚪 Sign Out</button>
                </div>
            </div>`;

            // Toggle dropdown
            const userBtn = document.getElementById('navUserBtn');
            const dropdown = document.getElementById('navUserDropdown');
            if (userBtn && dropdown) {
                userBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
                });
                document.addEventListener('click', () => dropdown.style.display = 'none');
            }

            // Sign out
            const signOutBtn = document.getElementById('navSignOutBtn');
            if (signOutBtn) {
                signOutBtn.addEventListener('click', async () => {
                    await fetch('/api/auth/signout', { method: 'POST' });
                    localStorage.removeItem('cf_user');
                    sessionStorage.removeItem('cf_welcomed');
                    window.location.href = '/';
                });
            }

            // Welcome toast (show once per session)
            if (!sessionStorage.getItem('cf_welcomed')) {
                sessionStorage.setItem('cf_welcomed', '1');
                setTimeout(() => {
                    showNotification('Welcome back!', `Signed in as ${data.user.full_name}`, 'success');
                }, 300);
            }
        } else if (!data.user && ctaBtn) {
            // Check if we're on signup/signin page — show the opposite link
            const path = window.location.pathname;
            if (path === '/signup') {
                ctaBtn.href = '/signin';
                ctaBtn.textContent = 'Sign In →';
            } else if (path === '/signin') {
                ctaBtn.href = '/signup';
                ctaBtn.textContent = 'Sign Up →';
            } else {
                ctaBtn.href = '/signin';
                ctaBtn.textContent = 'Sign In →';
            }
        }
    } catch (e) {
        console.warn('Auth check failed:', e);
    }
})();
