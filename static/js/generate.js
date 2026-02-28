/* ================================================
   generate.js — Multi-step form & AI output
   ================================================ */

let currentStep = 0;
let maxStepReached = 0;
const totalSteps = 3;

const steps = document.querySelectorAll('.form-step');
const tabs = document.querySelectorAll('.step-tab');
const progressBar = document.getElementById('progressBar');
const nextBtn = document.getElementById('nextBtn');
const prevBtn = document.getElementById('prevBtn');
const outputBody = document.getElementById('outputBody');
const exportBtn = document.getElementById('exportBtn');

// Store last generated data for PDF export
let lastCurriculum = null;
let lastParams = null;

function goToStep(index) {
    if (index > maxStepReached) return;

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
        const semesters = parseInt(document.getElementById('semesters').value);

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

        if (isNaN(semesters) || semesters < 1 || semesters > 12) {
            document.getElementById('semesters').focus();
            showNotification("Invalid Semesters", "Please enter a value between 1 and 12.", "error");
            return;
        }

        const hours = parseInt(document.getElementById('hours').value);
        if (isNaN(hours) || hours <= 0) {
            document.getElementById('hours').focus();
            showNotification("Invalid Hours", "Weekly learning hours must be greater than 0.", "error");
            return;
        }
    }
    if (currentStep < totalSteps - 1) {
        if (currentStep + 1 > maxStepReached) {
            maxStepReached = currentStep + 1;
            tabs[maxStepReached].classList.remove('disabled');
        }
        goToStep(currentStep + 1);
    } else {
        generateCurriculum();
    }
});

prevBtn.addEventListener('click', () => {
    if (currentStep > 0) goToStep(currentStep - 1);
});

tabs.forEach((tab, i) => {
    tab.addEventListener('click', () => {
        if (i <= maxStepReached) goToStep(i);
    });
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

    outputBody.innerHTML = `
    <div class="loading-overlay">
      <div class="spinner" style="border-color:rgba(99,102,241,0.3); border-top-color:var(--primary-start);"></div>
      <div>
        <div style="font-weight:600; color:var(--text-heading); margin-bottom:0.4rem;">Multi-Agent Workflow Running</div>
        <div class="text-sm text-muted" style="line-height:1.8;">
            <span style="color:#10b981;">●</span> Agent A — Planning courses & structure<br>
            <span style="color:#f59e0b;">○</span> Agent B — Filling topics & descriptions<br>
            <span style="color:#6366f1;">○</span> Agent C — Industry review
        </div>
      </div>
    </div>`;

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.detail || 'Server error');

        renderOutput(result, payload);
        lastCurriculum = result.curriculum;
        lastParams = payload;
        lastReview = result.agent_review || '';
        // Store for analysis page
        sessionStorage.setItem('cf_curriculum', JSON.stringify(result.curriculum));
        sessionStorage.setItem('cf_params', JSON.stringify(payload));
        sessionStorage.setItem('cf_review', result.agent_review || '');
        exportBtn.classList.remove('hidden');
        const analysisBtn = document.getElementById('analysisBtn');
        if (analysisBtn) analysisBtn.classList.remove('hidden');
        showNotification("Curriculum Generated", "Your tailored syllabus is ready for review.");
    } catch (err) {
        outputBody.innerHTML = `
      <div class="placeholder-empty">
        <div class="icon">⚠️</div>
        <div style="font-weight:600; color:#ef4444;">Generation Error</div>
        <p class="text-sm" style="max-width:320px;">${err.message || 'Could not reach the backend.'}</p>
      </div>`;
    } finally {
        nextBtn.disabled = false;
        nextBtn.innerHTML = 'Generate Curriculum';
        nextBtn.style.background = 'linear-gradient(135deg, #10b981, #06b6d4)';
    }
}


// ══════════════════════════════════════════════════════════════════════
//  RENDER — Semesters vertical, courses horizontal
// ══════════════════════════════════════════════════════════════════════
function renderOutput(result, payload) {
    const levelLabels = {
        beginner: 'Beginner / K-12',
        undergraduate: 'Undergraduate',
        graduate: 'Graduate',
        expert: 'Expert / Professional'
    };

    let html = '';

    if (result.status !== "success" || !result.curriculum) {
        outputBody.innerHTML = `
        <div style="padding:1.25rem; border:1px solid #fee2e2; background:#fef2f2; border-radius:12px; color:#991b1b;">
            <strong>⚠️ Error:</strong> ${result.detail || result.message || 'Failed to generate curriculum.'}
        </div>`;
        return;
    }

    const cur = result.curriculum;

    // ── Curriculum Overview ──────────────────────────────────────
    html += `
    <div style="padding:1.25rem; background:linear-gradient(135deg,rgba(99,102,241,0.06),rgba(6,182,212,0.06)); border:1px solid rgba(99,102,241,0.12); border-radius:14px;">
        <div style="font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:var(--primary-start); margin-bottom:0.75rem;">📋 Curriculum Parameters</div>
        <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(140px, 1fr)); gap:0.75rem; font-size:0.875rem;">
            <div><span style="color:var(--text-muted); font-size:0.75rem;">Subject</span><br><strong style="color:var(--text-heading);">${payload.skill}</strong></div>
            <div><span style="color:var(--text-muted); font-size:0.75rem;">Level</span><br><strong style="color:var(--text-heading);">${levelLabels[payload.level]}</strong></div>
            <div><span style="color:var(--text-muted); font-size:0.75rem;">Semesters</span><br><strong style="color:var(--text-heading);">${payload.semesters}</strong></div>
            <div><span style="color:var(--text-muted); font-size:0.75rem;">Hrs/Week</span><br><strong style="color:var(--text-heading);">${payload.hours}</strong></div>
            ${payload.industry ? `<div><span style="color:var(--text-muted); font-size:0.75rem;">Industry</span><br><strong style="color:var(--text-heading);">${payload.industry}</strong></div>` : ''}
        </div>
    </div>`;

    // ── Professional Summary ─────────────────────────────────────
    html += `
    <div style="margin-top:1.25rem; padding:1.25rem; border-left:4px solid var(--primary-start); background:var(--surface); border-radius:0 12px 12px 0; box-shadow:var(--shadow-sm);">
        <div style="font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--primary-start); margin-bottom:0.4rem;">✨ Professional Summary</div>
        <div style="font-size:0.9375rem; color:var(--text-body); line-height:1.7;">${cur.summary}</div>
    </div>`;

    // ── Stats bar ────────────────────────────────────────────────
    let totalCourses = 0, totalCredits = 0;
    cur.semesters.forEach(s => {
        if (s.courses) {
            totalCourses += s.courses.length;
            s.courses.forEach(c => totalCredits += (c.credits || 3));
        }
    });

    html += `
    <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:0.75rem; margin-top:1.25rem;">
        ${statCard(cur.semesters.length, 'Semesters', '#6366f1')}
        ${statCard(totalCourses, 'Total Courses', '#10b981')}
        ${statCard(totalCredits, 'Total Credits', '#f59e0b')}
    </div>`;

    // ── Section divider ─────────────────────────────────────────
    html += `
    <div style="display:flex; align-items:center; gap:0.75rem; margin:1.75rem 0 1.25rem;">
        <div style="height:1px; flex:1; background:var(--border);"></div>
        <span style="font-size:0.8rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:var(--text-subtle);">Semester Breakdown</span>
        <div style="height:1px; flex:1; background:var(--border);"></div>
    </div>`;

    // ── Semesters (vertical) → Courses (horizontal) ─────────────
    cur.semesters.forEach(semester => {
        const color = semesterColor(semester.number);

        // Semester header
        html += `
        <div style="margin-bottom:1.75rem;">
            <div style="display:flex; align-items:center; gap:0.75rem; margin-bottom:1rem;">
                <span style="width:36px; height:36px; border-radius:50%; background:${color.gradient}; color:white; font-size:0.875rem; font-weight:800; display:inline-flex; align-items:center; justify-content:center; box-shadow:0 3px 10px ${color.shadow}; flex-shrink:0;">${semester.number}</span>
                <div>
                    <div style="font-size:1rem; font-weight:700; color:var(--text-heading);">${semester.title}</div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${semester.courses ? semester.courses.length : 0} courses</div>
                </div>
            </div>`;

        // Courses container — RESPONSIVE GRID
        if (semester.courses && semester.courses.length > 0) {
            html += `<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(min(100%, 280px), 1fr)); gap:0.875rem;">`;

            semester.courses.forEach(course => {
                const tagClr = tagColor(semester.number);
                html += `
                <div style="padding:1.125rem; border:1px solid var(--border); border-radius:12px; background:var(--surface); box-shadow:var(--shadow-sm); display:flex; flex-direction:column; border-top:3px solid ${color.accent}; transition:transform 0.2s ease, box-shadow 0.2s ease;" onmouseenter="this.style.transform='translateY(-2px)';this.style.boxShadow='0 8px 25px rgba(0,0,0,0.08)';" onmouseleave="this.style.transform='';this.style.boxShadow='var(--shadow-sm)';">
                    
                    <!-- Course name -->
                    <div style="font-weight:700; color:var(--text-heading); font-size:0.875rem; margin-bottom:0.5rem; line-height:1.4;">
                        📘 ${course.name}
                    </div>

                    <!-- Badges -->
                    <div style="display:flex; gap:0.35rem; margin-bottom:0.75rem; flex-wrap:wrap;">
                        <span style="padding:0.15rem 0.5rem; background:rgba(99,102,241,0.1); border-radius:20px; font-size:0.65rem; font-weight:700; color:var(--primary-start);">${course.credits || 3} Credits</span>
                        <span style="padding:0.15rem 0.5rem; background:rgba(16,185,129,0.1); border-radius:20px; font-size:0.65rem; font-weight:700; color:#10b981;">${course.duration || 15} Weeks</span>
                    </div>

                    <!-- Description -->
                    ${course.description ? `<div style="font-size:0.8125rem; color:var(--text-body); line-height:1.6; margin-bottom:0.75rem; flex:1;">${course.description}</div>` : '<div style="flex:1;"></div>'}

                    <!-- Topics -->
                    ${course.topics && course.topics.length > 0 ? `
                    <div>
                        <div style="font-size:0.65rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:var(--text-muted); margin-bottom:0.4rem;">Topics</div>
                        <div style="display:flex; flex-wrap:wrap; gap:0.3rem;">
                            ${course.topics.map(t => `<span class="topic-tag topic-tag-${tagClr} active" style="font-size:0.675rem; padding:0.15rem 0.45rem;">${t}</span>`).join('')}
                        </div>
                    </div>` : ''}
                </div>`;
            });

            html += `</div>`; // close courses grid
        }

        html += `</div>`; // close semester
    });

    // ── Agent Review ─────────────────────────────────────────────
    if (result.agent_review) {
        const isApproved = result.agent_review.toLowerCase().includes('approved');
        html += `
        <div style="margin-top:0.5rem; padding:1rem 1.25rem; border-radius:12px; border:1px solid ${isApproved ? 'rgba(16,185,129,0.2)' : 'rgba(245,158,11,0.2)'}; background:${isApproved ? 'rgba(16,185,129,0.04)' : 'rgba(245,158,11,0.04)'};">
            <div style="font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:${isApproved ? '#10b981' : '#f59e0b'}; margin-bottom:0.5rem;">
                ${isApproved ? '✅' : '📋'} Agent C — Industry Review
            </div>
            <div style="font-size:0.84rem; color:var(--text-body); line-height:1.65; white-space:pre-line;">${result.agent_review}</div>
        </div>`;
    }

    // ── DB ID ────────────────────────────────────────────────────
    if (result.db_id) {
        html += `<div style="margin-top:0.75rem; text-align:center; font-size:0.75rem; color:var(--text-muted);">💾 Saved to database · ID: ${result.db_id}</div>`;
    }

    outputBody.innerHTML = html;
}


// ── Helpers ──────────────────────────────────────────────────────────
function statCard(value, label, color) {
    return `<div style="padding:0.875rem; background:linear-gradient(135deg,${color}11,transparent); border:1px solid ${color}22; border-radius:12px; text-align:center;">
        <div style="font-size:1.5rem; font-weight:800; color:${color};">${value}</div>
        <div style="font-size:0.675rem; color:var(--text-muted); font-weight:600; text-transform:uppercase; letter-spacing:0.04em;">${label}</div>
    </div>`;
}

function semesterColor(num) {
    const colors = [
        { gradient: 'linear-gradient(135deg, #6366f1, #818cf8)', accent: '#6366f1', shadow: 'rgba(99,102,241,0.25)' },
        { gradient: 'linear-gradient(135deg, #06b6d4, #22d3ee)', accent: '#06b6d4', shadow: 'rgba(6,182,212,0.25)' },
        { gradient: 'linear-gradient(135deg, #f59e0b, #fbbf24)', accent: '#f59e0b', shadow: 'rgba(245,158,11,0.25)' },
        { gradient: 'linear-gradient(135deg, #10b981, #34d399)', accent: '#10b981', shadow: 'rgba(16,185,129,0.25)' },
        { gradient: 'linear-gradient(135deg, #a855f7, #c084fc)', accent: '#a855f7', shadow: 'rgba(168,85,247,0.25)' },
        { gradient: 'linear-gradient(135deg, #ef4444, #f87171)', accent: '#ef4444', shadow: 'rgba(239,68,68,0.25)' },
    ];
    return colors[(num - 1) % colors.length];
}

function tagColor(semester) {
    const colors = ['purple', 'cyan', 'amber', 'emerald', 'purple', 'cyan'];
    return colors[(semester - 1) % colors.length];
}

// ── Export PDF ───────────────────────────────────────────────────────
if (exportBtn) {
    exportBtn.addEventListener('click', async () => {
        if (!lastCurriculum || !lastParams) {
            showNotification("No Curriculum", "Generate a curriculum first before exporting.", "error");
            return;
        }

        exportBtn.innerHTML = '<div class="spinner"></div> Generating PDF...';
        exportBtn.disabled = true;

        try {
            const response = await fetch('/export-pdf', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    curriculum: lastCurriculum,
                    params: lastParams
                })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || 'PDF generation failed');
            }

            // Download the PDF
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `CurricuForge_${lastParams.skill.replace(/\s+/g, '_')}.pdf`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            showNotification("PDF Downloaded", "Your curriculum PDF has been saved.");
        } catch (err) {
            showNotification("Export Error", err.message || "Failed to generate PDF.", "error");
        } finally {
            exportBtn.innerHTML = 'Export PDF';
            exportBtn.disabled = false;
        }
    });
}
