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
// Make it globally accessible
window.toggleSemester = toggleSemester;


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
                chat_history: chatHistory
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

    } catch (err) {
        removeTypingIndicator();
        addMessage('bot', `⚠️ Error: ${err.message || 'Could not reach the AI advisor.'}`);
    } finally {
        chatSendBtn.disabled = false;
        chatInput.focus();
    }
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
