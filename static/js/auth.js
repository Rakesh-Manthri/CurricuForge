/* ================================================
   auth.js — Sign Up & Sign In form handling
   ================================================ */

const authError = document.getElementById('authError');
const submitBtn = document.getElementById('submitBtn');

function showError(msg) {
    authError.textContent = msg;
    authError.classList.add('show');
    authError.style.animation = 'none';
    authError.offsetHeight; // trigger reflow
    authError.style.animation = 'fadeInUp 0.3s ease';
}

function hideError() {
    authError.classList.remove('show');
}


// ══════════════════════════════════════════════════════════════════════
//  SIGN UP
// ══════════════════════════════════════════════════════════════════════
const signupForm = document.getElementById('signupForm');
if (signupForm) {
    // Password strength indicator
    const pwInput = document.getElementById('password');
    const pwStrength = document.getElementById('pwStrength');

    if (pwInput && pwStrength) {
        pwInput.addEventListener('input', () => {
            const pw = pwInput.value;
            let strength = 0;
            if (pw.length >= 6) strength += 25;
            if (pw.length >= 10) strength += 25;
            if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) strength += 25;
            if (/[0-9]/.test(pw) || /[^A-Za-z0-9]/.test(pw)) strength += 25;

            pwStrength.style.width = strength + '%';
            if (strength <= 25) {
                pwStrength.style.background = '#ef4444';
            } else if (strength <= 50) {
                pwStrength.style.background = '#f59e0b';
            } else if (strength <= 75) {
                pwStrength.style.background = '#06b6d4';
            } else {
                pwStrength.style.background = '#10b981';
            }
        });
    }

    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();

        const fullName = document.getElementById('fullName').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirmPassword').value;

        // Validation
        if (!fullName) { showError('Please enter your full name.'); return; }
        if (!email) { showError('Please enter your email address.'); return; }
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) { showError('Please enter a valid email address.'); return; }
        if (password.length < 6) { showError('Password must be at least 6 characters.'); return; }
        if (password !== confirmPassword) { showError('Passwords do not match.'); return; }

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<div class="spinner" style="width:18px;height:18px;margin:0 auto;"></div>';

        try {
            const res = await fetch('/api/auth/signup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ full_name: fullName, email, password })
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || 'Sign up failed.');
            }

            // Store user info
            localStorage.setItem('cf_user', JSON.stringify(data.user));

            // Redirect to generate page
            window.location.href = '/generate';

        } catch (err) {
            showError(err.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Create Account';
        }
    });
}


// ══════════════════════════════════════════════════════════════════════
//  SIGN IN
// ══════════════════════════════════════════════════════════════════════
const signinForm = document.getElementById('signinForm');
if (signinForm) {
    signinForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        hideError();

        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;

        if (!email) { showError('Please enter your email address.'); return; }
        if (!password) { showError('Please enter your password.'); return; }

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<div class="spinner" style="width:18px;height:18px;margin:0 auto;"></div>';

        try {
            const res = await fetch('/api/auth/signin', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || 'Sign in failed.');
            }

            // Store user info
            localStorage.setItem('cf_user', JSON.stringify(data.user));

            // Redirect to generate page
            window.location.href = '/generate';

        } catch (err) {
            showError(err.message);
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = 'Sign In';
        }
    });
}
