/* ================================================
   contact.js — Contact form handling
   ================================================ */

const contactForm = document.getElementById('contactForm');
const submitBtn = document.getElementById('contactSubmitBtn');

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
            showNotification("Missing Fields", "Please fill in all required fields.", "error");
            return;
        }

        // Email regex validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            const el = document.getElementById('contactEmail');
            el.focus();
            el.style.borderColor = '#ef4444';
            el.style.boxShadow = '0 0 0 3px rgba(239,68,68,0.12)';
            showNotification("Invalid Email", "Please enter a valid email address.", "error");
            return;
        }

        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<div class="spinner"></div> Sending...';
        submitBtn.disabled = true;

        const subject = document.getElementById('contactSubject').value;
        const selectedTags = [...document.querySelectorAll('#contactTags .topic-tag.active')]
            .map(t => t.dataset.tag);

        try {
            const response = await fetch('/api/contact', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, email, subject, message, tags: selectedTags })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'Failed to send message.');
            }

            showNotification("Message Sent", "We've received your message and will get back to you soon!");
            contactForm.reset();
            document.querySelectorAll('#contactTags .topic-tag').forEach(t => t.classList.remove('active'));
        } catch (err) {
            showNotification("Send Failed", err.message || "Could not send the message. Please try again.", "error");
        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    });
}
