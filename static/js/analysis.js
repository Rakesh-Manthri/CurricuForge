/* ================================================
   analysis.js — Curriculum deep-dive & AI chat
   ================================================ */

// ── Load curriculum from sessionStorage ─────────────────────────────
let curriculum = null;
let params = null;
let chatHistory = [];

try {
    curriculum = JSON.parse(sessionStorage.getItem('cf_curriculum'));
    params = JSON.parse(sessionStorage.getItem('cf_params'));
} catch (e) {
    console.warn('No curriculum data found in session.');
}

const courseDetailBody = document.getElementById('courseDetailBody');
const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const chatSendBtn = document.getElementById('chatSendBtn');
const quickActions = document.getElementById('quickActions');


// ══════════════════════════════════════════════════════════════════════
//  SECTION 1: DETAILED COURSE BREAKDOWN
// ══════════════════════════════════════════════════════════════════════
function renderCourseDetails() {
    if (!curriculum || !curriculum.semesters || curriculum.semesters.length === 0) {
        courseDetailBody.innerHTML = `
        <div class="no-data">
            <div class="icon">📋</div>
            <div style="font-weight:600;color:var(--text-muted);">No Curriculum Loaded</div>
            <p class="text-sm" style="max-width:300px;margin:0.5rem auto;">
                <a href="/generate" style="color:var(--primary-start);font-weight:600;">Generate a curriculum</a> first, then click Analyze to explore it here.
            </p>
        </div>`;
        return;
    }

    let html = '';

    // Stats summary
    let totalCourses = 0, totalCredits = 0;
    curriculum.semesters.forEach(s => {
        if (s.courses) {
            totalCourses += s.courses.length;
            s.courses.forEach(c => totalCredits += (c.credits || 3));
        }
    });

    html += `
    <div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0.5rem; margin-bottom:1.25rem;">
        <div style="padding:0.6rem;text-align:center;background:rgba(99,102,241,0.06);border-radius:10px;border:1px solid rgba(99,102,241,0.12);">
            <div style="font-size:1.25rem;font-weight:800;color:var(--primary-start);">${curriculum.semesters.length}</div>
            <div style="font-size:0.625rem;color:var(--text-muted);font-weight:600;text-transform:uppercase;">Semesters</div>
        </div>
        <div style="padding:0.6rem;text-align:center;background:rgba(16,185,129,0.06);border-radius:10px;border:1px solid rgba(16,185,129,0.12);">
            <div style="font-size:1.25rem;font-weight:800;color:#10b981;">${totalCourses}</div>
            <div style="font-size:0.625rem;color:var(--text-muted);font-weight:600;text-transform:uppercase;">Courses</div>
        </div>
        <div style="padding:0.6rem;text-align:center;background:rgba(245,158,11,0.06);border-radius:10px;border:1px solid rgba(245,158,11,0.12);">
            <div style="font-size:1.25rem;font-weight:800;color:#f59e0b;">${totalCredits}</div>
            <div style="font-size:0.625rem;color:var(--text-muted);font-weight:600;text-transform:uppercase;">Credits</div>
        </div>
    </div>`;

    // Render each semester
    const semColors = [
        { bg: 'linear-gradient(135deg,#6366f1,#818cf8)', accent: '#6366f1', light: 'rgba(99,102,241,0.08)' },
        { bg: 'linear-gradient(135deg,#06b6d4,#22d3ee)', accent: '#06b6d4', light: 'rgba(6,182,212,0.08)' },
        { bg: 'linear-gradient(135deg,#f59e0b,#fbbf24)', accent: '#f59e0b', light: 'rgba(245,158,11,0.08)' },
        { bg: 'linear-gradient(135deg,#10b981,#34d399)', accent: '#10b981', light: 'rgba(16,185,129,0.08)' },
        { bg: 'linear-gradient(135deg,#a855f7,#c084fc)', accent: '#a855f7', light: 'rgba(168,85,247,0.08)' },
        { bg: 'linear-gradient(135deg,#ef4444,#f87171)', accent: '#ef4444', light: 'rgba(239,68,68,0.08)' },
    ];

    curriculum.semesters.forEach((sem, idx) => {
        const color = semColors[idx % semColors.length];
        const courseCount = sem.courses ? sem.courses.length : 0;

        html += `
        <div class="semester-section">
            <div class="semester-header" onclick="toggleSemester('sem-${sem.number}', this)">
                <span class="semester-badge" style="background:${color.bg};">${sem.number}</span>
                <div>
                    <div class="semester-title-text">${sem.title}</div>
                    <div style="font-size:0.7rem;color:var(--text-muted);">${courseCount} course${courseCount !== 1 ? 's' : ''}</div>
                </div>
                <span class="semester-toggle open">▼</span>
            </div>
            <div class="semester-courses" id="sem-${sem.number}">`;

        if (sem.courses && sem.courses.length > 0) {
            sem.courses.forEach((course, ci) => {
                html += `
                <div class="course-detail-card" style="border-left-color:${color.accent};">
                    <div class="course-detail-name">📘 ${course.name}</div>
                    <div class="course-meta">
                        <span class="badge" style="background:rgba(99,102,241,0.1);color:var(--primary-start);">${course.credits || 3} Credits</span>
                        <span class="badge" style="background:rgba(16,185,129,0.1);color:#10b981;">${course.duration || 15} Weeks</span>
                    </div>`;

                if (course.description) {
                    html += `<div class="course-detail-desc">${course.description}</div>`;
                }

                if (course.topics && course.topics.length > 0) {
                    html += `
                    <div style="margin-top:0.4rem;">
                        <div style="font-size:0.625rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:var(--text-muted);margin-bottom:0.35rem;">Topics Covered</div>
                        <ul class="course-topics-list">
                            ${course.topics.map(t => `<li>${t}</li>`).join('')}
                        </ul>
                    </div>`;
                }

                html += `</div>`;
            });
        }

        html += `</div></div>`;
    });

    courseDetailBody.innerHTML = html;
}

// Toggle semester collapse/expand
function toggleSemester(id, headerEl) {
    const el = document.getElementById(id);
    const toggle = headerEl.querySelector('.semester-toggle');
    if (el.style.display === 'none') {
        el.style.display = 'block';
        toggle.classList.add('open');
    } else {
        el.style.display = 'none';
        toggle.classList.remove('open');
    }
}
window.toggleSemester = toggleSemester;


// ══════════════════════════════════════════════════════════════════════
//  EDIT MODE — Curriculum Customization
// ══════════════════════════════════════════════════════════════════════
let editMode = false;

function toggleEditMode() {
    if (!curriculum || !curriculum.semesters) return;
    editMode = !editMode;

    const toggleBtn = document.getElementById('editToggleBtn');
    const saveBtn = document.getElementById('saveChangesBtn');

    if (editMode) {
        toggleBtn.innerHTML = '👁️ View Mode';
        toggleBtn.style.background = 'rgba(99,102,241,0.08)';
        toggleBtn.style.color = '#6366f1';
        toggleBtn.style.borderColor = '#6366f1';
        saveBtn.style.display = 'inline-flex';
        renderEditMode();
    } else {
        toggleBtn.innerHTML = '✏️ Customize';
        toggleBtn.style.background = 'white';
        toggleBtn.style.color = 'var(--text-body)';
        toggleBtn.style.borderColor = 'var(--border)';
        saveBtn.style.display = 'none';
        renderCourseDetails();
    }
}
window.toggleEditMode = toggleEditMode;

function renderEditMode() {
    const semColors = [
        { bg: 'linear-gradient(135deg,#6366f1,#818cf8)', accent: '#6366f1' },
        { bg: 'linear-gradient(135deg,#06b6d4,#22d3ee)', accent: '#06b6d4' },
        { bg: 'linear-gradient(135deg,#f59e0b,#fbbf24)', accent: '#f59e0b' },
        { bg: 'linear-gradient(135deg,#10b981,#34d399)', accent: '#10b981' },
        { bg: 'linear-gradient(135deg,#a855f7,#c084fc)', accent: '#a855f7' },
        { bg: 'linear-gradient(135deg,#ef4444,#f87171)', accent: '#ef4444' },
    ];

    let html = `
    <div style="padding:0.6rem 0.75rem;background:rgba(99,102,241,0.05);border:1px solid rgba(99,102,241,0.12);border-radius:10px;margin-bottom:1.25rem;font-size:0.78rem;color:var(--text-body);">
        ✏️ <strong>Edit Mode</strong> — Modify course names, credits, descriptions, and topics. Add or remove courses. Click <strong>💾 Save</strong> when done.
    </div>`;

    curriculum.semesters.forEach((sem, sIdx) => {
        const color = semColors[sIdx % semColors.length];
        html += `
        <div class="semester-section" data-sem-idx="${sIdx}">
            <div class="semester-header" onclick="toggleSemester('edit-sem-${sem.number}', this)">
                <span class="semester-badge" style="background:${color.bg};">${sem.number}</span>
                <div>
                    <div class="semester-title-text">${sem.title}</div>
                    <div style="font-size:0.7rem;color:var(--text-muted);">${sem.courses ? sem.courses.length : 0} course(s)</div>
                </div>
                <span class="semester-toggle open">▼</span>
            </div>
            <div class="semester-courses" id="edit-sem-${sem.number}">`;

        if (sem.courses && sem.courses.length > 0) {
            sem.courses.forEach((course, cIdx) => {
                const topicsStr = (course.topics || []).join(', ');
                html += `
                <div class="course-detail-card editing" style="border-left-color:${color.accent};position:relative;" data-sem="${sIdx}" data-course="${cIdx}">
                    <button class="remove-course-btn" onclick="removeCourse(${sIdx}, ${cIdx})" title="Remove course">✕</button>
                    <div class="edit-row">
                        <label>Name</label>
                        <input class="edit-input edit-course-name" value="${escapeHtml(course.name)}" style="font-weight:600;">
                    </div>
                    <div class="edit-row">
                        <label>Credits</label>
                        <input class="edit-input edit-course-credits" type="number" value="${course.credits || 3}" min="1" max="10" style="max-width:60px;">
                        <label style="min-width:50px;">Weeks</label>
                        <input class="edit-input edit-course-duration" type="number" value="${course.duration || 15}" min="1" max="52" style="max-width:60px;">
                    </div>
                    <div style="margin-bottom:0.35rem;">
                        <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;color:var(--text-muted);margin-bottom:0.2rem;">Description</div>
                        <textarea class="edit-textarea edit-course-desc" rows="2">${escapeHtml(course.description || '')}</textarea>
                    </div>
                    <div>
                        <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;color:var(--text-muted);margin-bottom:0.2rem;">Topics (comma-separated)</div>
                        <input class="edit-input edit-course-topics" value="${escapeHtml(topicsStr)}" placeholder="e.g. HTML, CSS, JavaScript">
                    </div>
                </div>`;
            });
        }

        html += `
                <button class="add-course-btn" onclick="addCourse(${sIdx})">+ Add Course</button>
            </div>
        </div>`;
    });

    courseDetailBody.innerHTML = html;
}

function removeCourse(semIdx, courseIdx) {
    if (!curriculum.semesters[semIdx]) return;
    curriculum.semesters[semIdx].courses.splice(courseIdx, 1);
    renderEditMode();
    showNotification('Removed', 'Course removed. Click Save to keep changes.', 'info');
}
window.removeCourse = removeCourse;

function addCourse(semIdx) {
    if (!curriculum.semesters[semIdx]) return;
    if (!curriculum.semesters[semIdx].courses) curriculum.semesters[semIdx].courses = [];
    curriculum.semesters[semIdx].courses.push({
        name: 'New Course',
        credits: 3,
        duration: 15,
        description: '',
        topics: []
    });
    renderEditMode();
    showNotification('Added', 'New course added. Fill in the details and Save.', 'info');
}
window.addCourse = addCourse;

function saveChanges() {
    // Collect data from all edit fields
    const cards = document.querySelectorAll('.course-detail-card.editing');
    cards.forEach(card => {
        const semIdx = parseInt(card.dataset.sem);
        const courseIdx = parseInt(card.dataset.course);
        if (curriculum.semesters[semIdx] && curriculum.semesters[semIdx].courses[courseIdx]) {
            const c = curriculum.semesters[semIdx].courses[courseIdx];
            c.name = card.querySelector('.edit-course-name').value.trim() || 'Untitled';
            c.credits = parseInt(card.querySelector('.edit-course-credits').value) || 3;
            c.duration = parseInt(card.querySelector('.edit-course-duration').value) || 15;
            c.description = card.querySelector('.edit-course-desc').value.trim();
            const topicsVal = card.querySelector('.edit-course-topics').value.trim();
            c.topics = topicsVal ? topicsVal.split(',').map(t => t.trim()).filter(t => t) : [];
        }
    });

    // Persist to sessionStorage
    sessionStorage.setItem('cf_curriculum', JSON.stringify(curriculum));

    // Exit edit mode and re-render
    editMode = false;
    const toggleBtn = document.getElementById('editToggleBtn');
    const saveBtn = document.getElementById('saveChangesBtn');
    toggleBtn.innerHTML = '✏️ Customize';
    toggleBtn.style.background = 'white';
    toggleBtn.style.color = 'var(--text-body)';
    toggleBtn.style.borderColor = 'var(--border)';
    saveBtn.style.display = 'none';
    renderCourseDetails();

    showNotification('Saved!', 'Your curriculum changes have been saved.', 'success');
}
window.saveChanges = saveChanges;

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}


// ══════════════════════════════════════════════════════════════════════
//  SECTION 2: CHAT WITH AI ADVISOR
// ══════════════════════════════════════════════════════════════════════
function buildCurriculumContext() {
    if (!curriculum || !params) return 'No curriculum loaded.';

    let ctx = `Curriculum for: ${params.skill}\n`;
    ctx += `Level: ${params.level}\n`;
    ctx += `Semesters: ${params.semesters}\n`;
    ctx += `Hours/week: ${params.hours}\n`;
    if (params.industry) ctx += `Industry: ${params.industry}\n`;
    if (params.goals) ctx += `Goals: ${params.goals}\n`;
    ctx += `\nSummary: ${curriculum.summary}\n\n`;

    curriculum.semesters.forEach(sem => {
        ctx += `\n--- SEMESTER ${sem.number}: ${sem.title} ---\n`;
        if (sem.courses) {
            sem.courses.forEach(c => {
                ctx += `\nCourse: ${c.name}\n`;
                ctx += `Credits: ${c.credits || 3}, Duration: ${c.duration || 15} weeks\n`;
                if (c.topics && c.topics.length) ctx += `Topics: ${c.topics.join(', ')}\n`;
                if (c.description) ctx += `Description: ${c.description}\n`;
            });
        }
    });

    return ctx;
}

function addMessage(role, content) {
    const msg = document.createElement('div');
    msg.className = `chat-msg ${role}`;

    if (role === 'bot') {
        msg.innerHTML = `<div class="msg-label">AI Advisor</div>${formatMessage(content)}`;
    } else {
        msg.textContent = content;
    }

    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addTypingIndicator() {
    const msg = document.createElement('div');
    msg.className = 'chat-msg typing';
    msg.id = 'typingIndicator';
    msg.innerHTML = '<div class="msg-label" style="color:var(--text-muted);">AI Advisor</div>Thinking...';
    chatMessages.appendChild(msg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
    const el = document.getElementById('typingIndicator');
    if (el) el.remove();
}

function formatMessage(text) {
    // Basic markdown-like formatting
    return text
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code style="background:rgba(99,102,241,0.08);padding:0.1rem 0.3rem;border-radius:4px;font-size:0.8rem;">$1</code>')
        .replace(/\n/g, '<br>');
}

async function sendMessage(message) {
    if (!message.trim()) return;

    addMessage('user', message);
    chatHistory.push({ role: 'user', content: message });

    chatInput.value = '';
    chatInput.style.height = 'auto';
    chatSendBtn.disabled = true;
    addTypingIndicator();

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                curriculum_context: buildCurriculumContext(),
                chat_history: chatHistory,
                curriculum_data: curriculum
            })
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Chat request failed');
        }

        const data = await response.json();
        removeTypingIndicator();
        addMessage('bot', data.reply);
        chatHistory.push({ role: 'assistant', content: data.reply });

        // Check if the AI returned a curriculum update
        if (data.curriculum_update && Array.isArray(data.curriculum_update)) {
            applyCurriculumUpdate(data.curriculum_update);
        }

    } catch (err) {
        removeTypingIndicator();
        addMessage('bot', `⚠️ Error: ${err.message || 'Could not reach the AI advisor.'}`);
    } finally {
        chatSendBtn.disabled = false;
        chatInput.focus();
    }
}

function applyCurriculumUpdate(updatedSemesters) {
    curriculum.semesters = updatedSemesters;

    // Persist to sessionStorage
    sessionStorage.setItem('cf_curriculum', JSON.stringify(curriculum));

    // If in edit mode, exit it first
    if (editMode) {
        editMode = false;
        const toggleBtn = document.getElementById('editToggleBtn');
        const saveBtn = document.getElementById('saveChangesBtn');
        if (toggleBtn) {
            toggleBtn.innerHTML = '✏️ Customize';
            toggleBtn.style.background = 'white';
            toggleBtn.style.color = 'var(--text-body)';
            toggleBtn.style.borderColor = 'var(--border)';
        }
        if (saveBtn) saveBtn.style.display = 'none';
    }

    // Re-render the course details
    renderCourseDetails();

    // Show "changes applied" banner in chat
    const banner = document.createElement('div');
    banner.className = 'chat-msg bot';
    banner.style.background = 'rgba(16,185,129,0.08)';
    banner.style.border = '1px solid rgba(16,185,129,0.2)';
    banner.innerHTML = `
        <div style="display:flex;align-items:center;gap:0.4rem;font-weight:700;color:#10b981;font-size:0.8rem;">
            ✅ Curriculum Updated
        </div>
        <div style="font-size:0.78rem;color:var(--text-body);margin-top:0.25rem;">
            The changes have been applied to the course details panel on the left. You can further edit using the ✏️ Customize button.
        </div>`;
    chatMessages.appendChild(banner);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    showNotification('Curriculum Updated!', 'The AI has modified your curriculum. Review the changes in the Course Details panel.', 'success');
}

// ── Event listeners ─────────────────────────────────────────────────
chatSendBtn.addEventListener('click', () => {
    sendMessage(chatInput.value);
});

chatInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage(chatInput.value);
    }
});

// Auto-resize textarea
chatInput.addEventListener('input', () => {
    chatInput.style.height = 'auto';
    chatInput.style.height = Math.min(chatInput.scrollHeight, 100) + 'px';
});

// Quick action chips
quickActions.querySelectorAll('.quick-chip').forEach(chip => {
    chip.addEventListener('click', () => {
        const msg = chip.dataset.msg;
        if (msg) sendMessage(msg);
    });
});


// ── Initialize ──────────────────────────────────────────────────────
renderCourseDetails();
