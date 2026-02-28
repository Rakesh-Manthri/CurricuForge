/* ================================================
   history.js — User curriculum history
   ================================================ */

const historyGrid = document.getElementById('historyGrid');
const historyStats = document.getElementById('historyStats');
const modalOverlay = document.getElementById('modalOverlay');
const modalBody = document.getElementById('modalBody');
const modalClose = document.getElementById('modalClose');

const levelLabels = {
    beginner: 'Beginner',
    undergraduate: 'Undergraduate',
    graduate: 'Graduate',
    expert: 'Expert'
};

const semColors = ['#6366f1', '#06b6d4', '#f59e0b', '#10b981', '#a855f7', '#ef4444'];


// ── Load history ────────────────────────────────────────────────────
async function loadHistory() {
    try {
        const res = await fetch('/api/curricula');
        const data = await res.json();
        const items = data.curricula || [];

        renderStats(items);
        renderGrid(items);
    } catch (err) {
        historyGrid.innerHTML = `
        <div class="history-empty">
            <div class="icon">⚠️</div>
            <div style="font-weight:600;color:#ef4444;">Failed to load history</div>
            <p class="text-sm" style="color:var(--text-muted);">${err.message}</p>
        </div>`;
    }
}


// ── Stats bar ───────────────────────────────────────────────────────
function renderStats(items) {
    const totalCurricula = items.length;
    const totalSemesters = items.reduce((a, c) => a + (c.num_semesters || 0), 0);
    const avgHours = totalCurricula > 0
        ? Math.round(items.reduce((a, c) => a + (c.weekly_hours || 0), 0) / totalCurricula)
        : 0;

    historyStats.innerHTML = `
    <div class="stat-box">
        <div class="value" style="color:#6366f1;">${totalCurricula}</div>
        <div class="label">Curricula Generated</div>
    </div>
    <div class="stat-box">
        <div class="value" style="color:#10b981;">${totalSemesters}</div>
        <div class="label">Total Semesters</div>
    </div>
    <div class="stat-box">
        <div class="value" style="color:#f59e0b;">${avgHours}</div>
        <div class="label">Avg Hrs/Week</div>
    </div>`;
}


// ── Card grid ───────────────────────────────────────────────────────
function renderGrid(items) {
    if (items.length === 0) {
        historyGrid.innerHTML = `
        <div class="history-empty">
            <div class="icon">📋</div>
            <div style="font-weight:600;color:var(--text-muted);font-size:1.05rem;">No Curricula Yet</div>
            <p class="text-sm" style="max-width:340px;margin:0.5rem auto;color:var(--text-muted);line-height:1.6;">
                You haven't generated any curricula yet. 
                <a href="/generate" style="color:var(--primary-start);font-weight:600;">Create your first one</a> to see it here.
            </p>
        </div>`;
        return;
    }

    let html = '';
    items.forEach(item => {
        const date = formatDate(item.created_at);
        const level = levelLabels[item.level] || item.level;
        const summary = item.summary
            ? item.summary.substring(0, 150) + (item.summary.length > 150 ? '...' : '')
            : 'No summary available.';

        html += `
        <div class="history-card" data-id="${item.id}">
            <div class="history-card-skill">
                🎓 ${item.skill}
            </div>
            <div class="history-card-meta">
                <span class="badge" style="background:rgba(99,102,241,0.1);color:#6366f1;">${level}</span>
                <span class="badge" style="background:rgba(16,185,129,0.1);color:#10b981;">${item.num_semesters} Semesters</span>
                <span class="badge" style="background:rgba(245,158,11,0.1);color:#f59e0b;">${item.weekly_hours} hrs/wk</span>
            </div>
            <div class="history-card-summary">${summary}</div>
            <div class="history-card-footer">
                <div class="history-card-date">📅 ${date}</div>
                <div class="history-card-actions">
                    <button class="history-action-btn" onclick="viewCurriculum(${item.id})">👀 View</button>
                    <button class="history-action-btn" onclick="downloadCurriculum(${item.id}, '${item.skill.replace(/'/g, "\\'")}')">📄 PDF</button>
                    <button class="history-action-btn primary" onclick="analyzeCurriculum(${item.id})">🔍 Analyze</button>
                </div>
            </div>
        </div>`;
    });

    historyGrid.innerHTML = html;
}


// ── View curriculum in modal ────────────────────────────────────────
async function viewCurriculum(id) {
    modalBody.innerHTML = `
    <div style="text-align:center;padding:3rem;">
        <div class="spinner" style="margin:0 auto 1rem;"></div>
        <div style="color:var(--text-muted);">Loading curriculum...</div>
    </div>`;
    modalOverlay.classList.add('active');

    try {
        const res = await fetch(`/api/curricula/${id}`);
        if (!res.ok) throw new Error('Failed to load');
        const cur = await res.json();

        let html = '';

        // Title
        html += `
        <div style="margin-bottom:1.25rem;">
            <div style="font-size:1.25rem;font-weight:800;color:var(--text-heading);">🎓 ${cur.skill}</div>
            <div style="font-size:0.8rem;color:var(--text-muted);margin-top:0.25rem;">
                ${levelLabels[cur.level] || cur.level} · ${cur.num_semesters} Semesters · ${cur.weekly_hours} hrs/week
                ${cur.industry ? ` · ${cur.industry}` : ''}
            </div>
        </div>`;

        // Summary
        if (cur.summary) {
            html += `
            <div style="padding:1rem;border-left:3px solid var(--primary-start);background:rgba(99,102,241,0.03);border-radius:0 10px 10px 0;margin-bottom:1.25rem;">
                <div style="font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:var(--primary-start);margin-bottom:0.3rem;">Summary</div>
                <div style="font-size:0.875rem;color:var(--text-body);line-height:1.65;">${cur.summary}</div>
            </div>`;
        }

        // Semesters
        if (cur.semesters && cur.semesters.length > 0) {
            cur.semesters.forEach((sem, idx) => {
                const clr = semColors[idx % semColors.length];
                html += `
                <div style="margin-bottom:1.25rem;">
                    <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.6rem;">
                        <span style="width:28px;height:28px;border-radius:50%;background:${clr};color:white;font-size:0.7rem;font-weight:700;display:inline-flex;align-items:center;justify-content:center;">${sem.semester_number}</span>
                        <span style="font-weight:700;font-size:0.9rem;color:var(--text-heading);">${sem.title}</span>
                    </div>`;

                if (sem.courses && sem.courses.length > 0) {
                    html += `<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:0.6rem;">`;
                    sem.courses.forEach(c => {
                        const topics = Array.isArray(c.topics)
                            ? c.topics
                            : (typeof c.topics === 'string' ? JSON.parse(c.topics || '[]') : []);
                        html += `
                        <div style="padding:0.75rem;border:1px solid var(--border);border-radius:10px;border-top:2px solid ${clr};background:white;">
                            <div style="font-weight:600;font-size:0.8rem;color:var(--text-heading);margin-bottom:0.25rem;">📘 ${c.course_name}</div>
                            <div style="font-size:0.65rem;color:var(--text-muted);margin-bottom:0.4rem;">${c.credits} Credits · ${c.duration_weeks} Weeks</div>
                            ${c.description ? `<div style="font-size:0.75rem;color:var(--text-body);line-height:1.5;margin-bottom:0.35rem;">${c.description}</div>` : ''}
                            ${topics.length > 0 ? `<div style="display:flex;flex-wrap:wrap;gap:0.2rem;">${topics.map(t => `<span style="padding:0.1rem 0.35rem;background:${clr}15;color:${clr};border-radius:4px;font-size:0.6rem;font-weight:600;">${t}</span>`).join('')}</div>` : ''}
                        </div>`;
                    });
                    html += `</div>`;
                }
                html += `</div>`;
            });
        }

        modalBody.innerHTML = html;

    } catch (err) {
        modalBody.innerHTML = `
        <div style="text-align:center;padding:2rem;color:#ef4444;">
            <div style="font-size:2rem;margin-bottom:0.5rem;">⚠️</div>
            Failed to load curriculum details.
        </div>`;
    }
}


// ── Analyze — load into session and redirect ────────────────────────
async function analyzeCurriculum(id) {
    try {
        const res = await fetch(`/api/curricula/${id}`);
        if (!res.ok) throw new Error('Failed to load');
        const cur = await res.json();

        // Build the format expected by analysis page
        const curriculum = {
            summary: cur.summary || '',
            semesters: (cur.semesters || []).map(s => ({
                number: s.semester_number,
                title: s.title,
                courses: (s.courses || []).map(c => ({
                    name: c.course_name,
                    credits: c.credits,
                    duration: c.duration_weeks,
                    description: c.description || '',
                    topics: Array.isArray(c.topics) ? c.topics : JSON.parse(c.topics || '[]')
                }))
            }))
        };

        const params = {
            skill: cur.skill,
            level: cur.level,
            semesters: cur.num_semesters,
            hours: cur.weekly_hours,
            industry: cur.industry || ''
        };

        sessionStorage.setItem('cf_curriculum', JSON.stringify(curriculum));
        sessionStorage.setItem('cf_params', JSON.stringify(params));

        window.location.href = '/analysis';
    } catch (err) {
        showNotification('Error', 'Could not load curriculum for analysis.', 'error');
    }
}


// ── Download PDF ────────────────────────────────────────────────────
async function downloadCurriculum(id, skillName) {
    try {
        showNotification('Generating PDF', 'Please wait...', 'info');

        const res = await fetch(`/api/curricula/${id}`);
        if (!res.ok) throw new Error('Failed to load');
        const cur = await res.json();

        // Build the format expected by /export-pdf
        const curriculum = {
            summary: cur.summary || '',
            semesters: (cur.semesters || []).map(s => ({
                number: s.semester_number,
                title: s.title,
                courses: (s.courses || []).map(c => ({
                    name: c.course_name,
                    credits: c.credits,
                    duration: c.duration_weeks,
                    description: c.description || '',
                    topics: Array.isArray(c.topics) ? c.topics : JSON.parse(c.topics || '[]')
                }))
            }))
        };

        const params = {
            skill: cur.skill,
            level: cur.level,
            semesters: cur.num_semesters,
            hours: cur.weekly_hours,
            industry: cur.industry || ''
        };

        const pdfRes = await fetch('/export-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ curriculum, params })
        });

        if (!pdfRes.ok) throw new Error('PDF generation failed');

        const blob = await pdfRes.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `CurricuForge_${skillName.replace(/\s+/g, '_')}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);

        showNotification('Downloaded!', `${skillName} curriculum saved as PDF.`, 'success');
    } catch (err) {
        showNotification('Error', 'Could not generate PDF.', 'error');
    }
}


// ── Modal controls ──────────────────────────────────────────────────
modalClose.addEventListener('click', () => modalOverlay.classList.remove('active'));
modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) modalOverlay.classList.remove('active');
});
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') modalOverlay.classList.remove('active');
});


// ── Helpers ─────────────────────────────────────────────────────────
function formatDate(dateStr) {
    if (!dateStr) return 'Unknown';
    try {
        const d = new Date(dateStr + 'Z');
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    } catch {
        return dateStr;
    }
}

// Make functions globally accessible
window.viewCurriculum = viewCurriculum;
window.analyzeCurriculum = analyzeCurriculum;
window.downloadCurriculum = downloadCurriculum;


// ── Init ────────────────────────────────────────────────────────────
loadHistory();
