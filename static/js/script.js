document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('generatorForm');
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
});
