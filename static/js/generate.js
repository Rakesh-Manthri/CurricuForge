/* ================================================
   generate.js — Multi-step form & AI output
   ================================================ */

let currentStep = 0;
const totalSteps = 3;

const steps = document.querySelectorAll('.form-step');
const tabs = document.querySelectorAll('.step-tab');
const progressBar = document.getElementById('progressBar');
const nextBtn = document.getElementById('nextBtn');
const prevBtn = document.getElementById('prevBtn');
const outputBody = document.getElementById('outputBody');
const exportBtn = document.getElementById('exportBtn');

function goToStep(index) {
    steps.forEach((s, i) => s.classList.toggle('hidden', i !== index));
    tabs.forEach((t, i) => t.classList.toggle('active', i === index));
    prevBtn.style.visibility = index === 0 ? 'hidden' : 'visible';
    const progress = ((index + 1) / totalSteps) * 100;
    progressBar.style.width = progress + '%';

    if (index === totalSteps - 1) {
        nextBtn.textContent = 'Generate Curriculum';
        nextBtn.style.background = 'linear-gradient(135deg, #10b981, #06b6d4)';
        nextBtn.style.boxShadow = '0 4px 15px rgba(16,185,129,0.35)';
    } else {
        nextBtn.textContent = 'Next Step';
        nextBtn.style.background = '';
        nextBtn.style.boxShadow = '';
    }
    currentStep = index;
}

nextBtn.addEventListener('click', () => {
    if (currentStep === 0) {
        const skill = document.getElementById('skill').value.trim();
        if (!skill) {
            document.getElementById('skill').focus();
            document.getElementById('skill').style.borderColor = '#ef4444';
            document.getElementById('skill').style.boxShadow = '0 0 0 3px rgba(239,68,68,0.15)';
            setTimeout(() => {
                document.getElementById('skill').style.borderColor = '';
                document.getElementById('skill').style.boxShadow = '';
            }, 2000);
            return;
        }
    }
    if (currentStep < totalSteps - 1) {
        goToStep(currentStep + 1);
    } else {
        generateCurriculum();
    }
});

prevBtn.addEventListener('click', () => {
    if (currentStep > 0) goToStep(currentStep - 1);
});

tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => goToStep(i));
});

async function generateCurriculum() {
    const skill = document.getElementById('skill').value.trim();
    const level = document.getElementById('level').value;
    const semesters = parseInt(document.getElementById('semesters').value);
    const hours = parseInt(document.getElementById('hours').value);
    const goals = document.getElementById('goals').value;
    const priorKnowledge = document.getElementById('priorKnowledge').value;
    const style = document.getElementById('style').value;
    const industry = document.getElementById('industry').value;
    const notes = document.getElementById('notes').value;

    const selectedTopics = [...document.querySelectorAll('#topicTagCloud .topic-tag.active')]
        .map(t => t.dataset.topic);

    const payload = { skill, level, semesters, hours, goals, priorKnowledge, style, industry, selectedTopics, notes };

    nextBtn.disabled = true;
    nextBtn.innerHTML = '<div class="spinner"></div> Generating...';

    // Show loading state in output panel
    outputBody.innerHTML = `
    <div class="loading-overlay">
      <div class="spinner" style="border-color:rgba(99,102,241,0.3); border-top-color:var(--primary-start);"></div>
      <div>
        <div style="font-weight:600; color:var(--text-heading); margin-bottom:0.2rem;">IBM Granite 3.3 2B is working...</div>
        <div class="text-sm text-muted">Analyzing parameters and crafting your curriculum</div>
      </div>
    </div>`;

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        renderOutput(result, payload);
        exportBtn.classList.remove('hidden');
    } catch (err) {
        outputBody.innerHTML = `
      <div class="placeholder-empty">
        <div class="icon">⚠️</div>
        <div style="font-weight:600; color:#ef4444;">Connection Error</div>
        <p class="text-sm" style="max-width:280px;">Could not reach the backend. Is the Flask server running? Is Ollama active?</p>
      </div>`;
    } finally {
        nextBtn.disabled = false;
        nextBtn.innerHTML = 'Generate Curriculum';
        nextBtn.style.background = 'linear-gradient(135deg, #10b981, #06b6d4)';
    }
}

function parseSemesterData(text, semesterIndex) {
    // Regex for <<SEMESTER X>> blocks
    const pattern = new RegExp(`<<SEMESTER ${semesterIndex}>>([\\s\\S]*?)(?=<<SEMESTER|$)`, 'i');
    const match = text.match(pattern);

    if (!match || !match[1]) return null;

    const content = match[1];

    // Extract Title
    let title = 'Semester ' + semesterIndex;
    const titleMatch = content.match(/TITLE:\s*(.*?)(?=\n|TOPICS:|DETAILS:|$)/i);
    if (titleMatch) title = titleMatch[1].trim();

    // Extract Topics: Split by commas, semi-colons, or newlines
    let topics = [];
    const topicsMatch = content.match(/TOPICS:\s*(.*?)(?=\n|DETAILS:|$)/i);
    if (topicsMatch) {
        topics = topicsMatch[1]
            .split(/[,\n;]/)
            .map(t => t.trim().replace(/^[\d.-]+/, '').trim()) // remove numbering if present
            .filter(t => t.length > 2 && t.length < 100);
    }

    // Extract Details
    let details = '';
    const detailsMatch = content.match(/DETAILS:\s*([\s\S]*?)$/i);
    if (detailsMatch) details = detailsMatch[1].trim();

    return { title, topics, details };
}

function renderOutput(result, payload) {
    const levelLabels = {
        beginner: 'Beginner / K-12',
        undergraduate: 'Undergraduate',
        graduate: 'Graduate',
        expert: 'Expert / Professional'
    };

    const aiText = result.message || '';
    console.log("Raw AI Text:", aiText); // Useful for debugging

    // Extract overview from <<OVERVIEW>> tag
    const overviewMatch = aiText.match(/<<OVERVIEW>>([\s\S]*?)(?=<<SEMESTER|$)/i);
    const summary = (overviewMatch && overviewMatch[1]) ? overviewMatch[1].trim() : 'Curriculum generated.';

    let semesterHTML = '';
    const semCount = payload.semesters || 2;

    for (let i = 1; i <= semCount; i++) {
        const data = parseSemesterData(aiText, i);

        const displayTitle = data ? data.title : `Semester ${i}`;
        const displayTopics = (data && data.topics.length > 0) ? data.topics : ['General Core Topics', 'Foundations', 'Skills Training'];
        const displayDetails = data ? data.details : 'Focus on core principles and fundamental techniques relevant to the subject area.';

        semesterHTML += `
      <div class="semester-card">
        <h4 style="margin-bottom:0.5rem;">
          <span style="width:28px;height:28px;border-radius:50%;background:var(--gradient-primary);color:white;font-size:0.75rem;font-weight:700;display:inline-flex;align-items:center;justify-content:center;">${i}</span>
          ${displayTitle}
        </h4>
        <div style="font-size:0.875rem; color:var(--text-body); margin-bottom:1rem; line-height:1.6; padding-left:2.25rem; opacity:0.9;">
          ${displayDetails}
        </div>
        <div class="tag-cloud" style="padding-left:2.25rem;">
          ${displayTopics.map(t => `<span class="topic-tag topic-tag-${tagColor(i)} active">${t}</span>`).join('')}
        </div>
      </div>`;
    }

    outputBody.innerHTML = `
    <div style="display:flex; flex-direction:column; gap:1.25rem;">
      <div style="padding:1rem 1.25rem; background:linear-gradient(135deg,rgba(99,102,241,0.06),rgba(6,182,212,0.06)); border:1px solid rgba(99,102,241,0.12); border-radius:12px;">
        <div style="font-size:0.75rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--primary-start);margin-bottom:0.75rem;">Curriculum Overview</div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.75rem; font-size:0.875rem; margin-bottom:1rem;">
          <div><span style="color:var(--text-muted);">Subject:</span> <strong style="color:var(--text-heading);">${payload.skill}</strong></div>
          <div><span style="color:var(--text-muted);">Level:</span> <strong style="color:var(--text-heading);">${levelLabels[payload.level]}</strong></div>
          <div><span style="color:var(--text-muted);">Semesters:</span> <strong style="color:var(--text-heading);">${payload.semesters}</strong></div>
          <div><span style="color:var(--text-muted);">Hrs/week:</span> <strong style="color:var(--text-heading);">${payload.hours}</strong></div>
        </div>
        <div style="padding:0.875rem; background:white; border:1px solid var(--border); border-radius:10px; font-size:0.9rem; color:var(--text-body); line-height:1.6; border-left:4px solid var(--primary-start);">
          ${summary}
        </div>
      </div>
      <div style="font-size:0.8125rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-subtle);">Detailed Semester Breakdown</div>
      ${semesterHTML}
    </div>`;
}

function tagColor(semester) {
    const colors = ['purple', 'cyan', 'amber', 'emerald', 'purple', 'cyan'];
    return colors[(semester - 1) % colors.length];
}

// Export button (placeholder)
if (exportBtn) {
    exportBtn.addEventListener('click', () => {
        exportBtn.innerHTML = '<div class="spinner"></div> Generating PDF...';
        exportBtn.disabled = true;
        setTimeout(() => {
            exportBtn.innerHTML = 'Export PDF';
            exportBtn.disabled = false;
            alert('PDF export will be available once the AI backend is connected.');
        }, 1500);
    });
}
