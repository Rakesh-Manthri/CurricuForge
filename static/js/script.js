document.addEventListener('DOMContentLoaded', () => {
    // Curriculum Generator Logic
    const form = document.getElementById('generatorForm');
    if (form) {
        const submitBtn = form.querySelector('button[type="submit"]');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = {
                skill: document.getElementById('skill').value,
                level: document.getElementById('level').value,
                industry: document.getElementById('industry').value,
                semesters: document.getElementById('semesters').value,
                hours: document.getElementById('hours').value
            };

            // UI Feedback
            const originalText = submitBtn.innerText;
            submitBtn.innerText = 'Analyzing Parameters...';
            submitBtn.disabled = true;

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();

                if (result.status === 'success') {
                    alert('Success! In a real scenario, the AI would now be generating your curriculum. Check the console for data.');
                    console.log('AI Response:', result);
                }
            } catch (error) {
                console.error('Generation Error:', error);
                alert('Something went wrong during generation.');
            } finally {
                submitBtn.innerText = originalText;
                submitBtn.disabled = false;
            }
        });
    }

    // Contact Form Logic
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', (e) => {
            e.preventDefault();
            alert('Thank you for your message! This is a demo, so no email was actually sent.');
            contactForm.reset();
        });
    }
});
