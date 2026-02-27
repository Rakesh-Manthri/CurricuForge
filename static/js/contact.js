/* ================================================
   contact.js — Contact form handling
   ================================================ */

const contactForm = document.getElementById('contactForm');
const submitBtn = document.getElementById('contactSubmitBtn');
const successToast = document.getElementById('successToast');

// Tag toggles
document.querySelectorAll('#contactTags .topic-tag').forEach(tag => {
    tag.addEventListener('click', () => tag.classList.toggle('active'));
});

if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const name = document.getElementById('contactName').value.trim();
        const email = document.getElementById('contactEmail').value.trim();
        const message = document.getElementById('contactMessage').value.trim();

        // Inline validation
        if (!name || !email || !message) {
            [['contactName', name], ['contactEmail', email], ['contactMessage', message]].forEach(([id, val]) => {
                if (!val) {
                    const el = document.getElementById(id);
                    el.style.borderColor = '#ef4444';
                    el.style.boxShadow = '0 0 0 3px rgba(239,68,68,0.12)';
                    el.addEventListener('input', () => {
                        el.style.borderColor = '';
                        el.style.boxShadow = '';
                    }, { once: true });
                }
            });
            return;
        }

        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<div class="spinner"></div> Sending...';
        submitBtn.disabled = true;

        // Simulate submission (replace with real endpoint)
        await new Promise(r => setTimeout(r, 1400));

        successToast.classList.add('show');
        contactForm.reset();
        document.querySelectorAll('#contactTags .topic-tag').forEach(t => t.classList.remove('active'));
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;

        setTimeout(() => successToast.classList.remove('show'), 5000);
    });
}
