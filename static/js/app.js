/* ===== BOXcric — Shared Frontend JS ===== */

// --- Dark/Light Theme ---
(function() {
  var saved = localStorage.getItem('boxcric_theme');
  if (saved === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  } else if (!saved) {
    // Auto-detect system preference
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }
})();

function toggleTheme() {
  var current = document.documentElement.getAttribute('data-theme');
  var next = current === 'dark' ? 'light' : 'dark';
  if (next === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
  } else {
    document.documentElement.removeAttribute('data-theme');
  }
  localStorage.setItem('boxcric_theme', next);
  updateThemeIcon();
}

function updateThemeIcon() {
  var btn = document.getElementById('themeBtn');
  if (!btn) return;
  var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  btn.textContent = isDark ? '☀️' : '🌙';
  btn.title = isDark ? 'Switch to light mode' : 'Switch to dark mode';
}

// Update icon on load
document.addEventListener('DOMContentLoaded', updateThemeIcon);

// --- Utility ---
function el(id) { return document.getElementById(id); }

// --- API Helper ---
async function api(url, method = 'GET', body = null) {
  const opts = { method, headers: { 'Content-Type': 'application/json' } };
  if (body) opts.body = JSON.stringify(body);
  try {
    const res = await fetch(url, opts);
    return await res.json();
  } catch (e) {
    console.error('API error:', e);
    return null;
  }
}

// --- Toast notifications ---
function toast(message, type = 'info') {
  const container = el('toastContainer');
  if (!container) return;
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.textContent = message;
  container.appendChild(t);
  setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateX(100%)'; }, 2500);
  setTimeout(() => t.remove(), 3000);
}

// --- Status badge ---
function statusBadge(status) {
  const map = {
    live: ['badge-live', '● LIVE'],
    completed: ['badge-completed', 'COMPLETED'],
    scheduled: ['badge-scheduled', 'UPCOMING'],
    toss: ['badge-toss', 'TOSS DONE'],
    innings_break: ['badge-innings-break', 'INNINGS BREAK'],
    abandoned: ['badge-completed', 'ABANDONED']
  };
  const [cls, label] = map[status] || ['badge-scheduled', status.toUpperCase()];
  return `<span class="badge ${cls}">${label}</span>`;
}

// --- Match card builder ---
function matchCard(m, teams, basePath) {
  basePath = basePath || '/match';
  const t1 = teams.find(t => t.id === m.team1_id) || { name: 'Team 1', short_name: 'T1' };
  const t2 = teams.find(t => t.id === m.team2_id) || { name: 'Team 2', short_name: 'T2' };
  const inn1 = m.innings ? m.innings.find(i => i.innings_number === 1) : null;
  const inn2 = m.innings ? m.innings.find(i => i.innings_number === 2) : null;

  // Determine which team batted in which innings
  let t1Score = '', t2Score = '', t1Overs = '', t2Overs = '';
  if (inn1) {
    if (inn1.batting_team_id === m.team1_id) {
      t1Score = `${inn1.total_runs}/${inn1.total_wickets}`;
      t1Overs = `(${inn1.total_overs}.${inn1.total_balls})`;
    } else {
      t2Score = `${inn1.total_runs}/${inn1.total_wickets}`;
      t2Overs = `(${inn1.total_overs}.${inn1.total_balls})`;
    }
  }
  if (inn2) {
    if (inn2.batting_team_id === m.team1_id) {
      t1Score = `${inn2.total_runs}/${inn2.total_wickets}`;
      t1Overs = `(${inn2.total_overs}.${inn2.total_balls})`;
    } else {
      t2Score = `${inn2.total_runs}/${inn2.total_wickets}`;
      t2Overs = `(${inn2.total_overs}.${inn2.total_balls})`;
    }
  }

  const statusClass = m.status === 'live' ? 'live' : m.status === 'completed' ? 'completed' : 'scheduled';
  const t1Winner = m.winner_id === m.team1_id ? 'winner' : '';
  const t2Winner = m.winner_id === m.team2_id ? 'winner' : '';

  let resultHtml = '';
  if (m.result_summary) {
    const cls = m.result_summary.includes('Tied') ? 'tied' : 'won';
    resultHtml = `<div class="match-result ${cls}">${m.result_summary}</div>`;
  } else if (m.status === 'live') {
    resultHtml = `<div class="match-result live-text">● Match in progress</div>`;
  }

  const dateStr = m.date ? new Date(m.date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' }) : '';
  const s1 = t1.short_name || t1.name.slice(0, 3).toUpperCase();
  const s2 = t2.short_name || t2.name.slice(0, 3).toUpperCase();

  return `<a href="${basePath}/${m.id}" class="match-card ${statusClass}">
    <div class="match-card-header">
      <span>${m.title || t1.name + ' vs ' + t2.name}</span>
      <span>${statusBadge(m.status)}</span>
    </div>
    <div class="match-card-body">
      <div class="match-teams">
        <div class="match-team-row">
          <div class="team-info">
            <div class="team-logo">${s1}</div>
            <div class="team-name ${t1Winner}">${t1.name}</div>
          </div>
          <div class="team-score">${t1Score} <span class="overs">${t1Overs}</span></div>
        </div>
        <div class="match-team-row">
          <div class="team-info">
            <div class="team-logo">${s2}</div>
            <div class="team-name ${t2Winner}">${t2.name}</div>
          </div>
          <div class="team-score">${t2Score} <span class="overs">${t2Overs}</span></div>
        </div>
      </div>
    </div>
    ${resultHtml}
  </a>`;
}

// --- Empty state ---
function emptyState(icon, title, message) {
  return `<div class="empty-state">
    <div class="empty-icon">${icon}</div>
    <h3>${title}</h3>
    <p>${message}</p>
  </div>`;
}

// --- Modal helpers ---
function openModal(title, bodyHtml, onConfirm) {
  // Create a generic modal
  let backdrop = el('genericModal');
  if (!backdrop) {
    backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop';
    backdrop.id = 'genericModal';
    backdrop.innerHTML = `<div class="modal">
      <div class="modal-header"><h3 id="genericModalTitle"></h3><button class="modal-close" onclick="closeModal()">&times;</button></div>
      <div class="modal-body" id="genericModalBody"></div>
      <div class="modal-footer"><button class="btn btn-outline" onclick="closeModal()">Cancel</button><button class="btn btn-primary" id="genericModalConfirm">Confirm</button></div>
    </div>`;
    document.body.appendChild(backdrop);
  }
  el('genericModalTitle').textContent = title;
  el('genericModalBody').innerHTML = bodyHtml;
  el('genericModalConfirm').onclick = onConfirm;
  backdrop.classList.add('open');
}

function closeModal() {
  const m = el('genericModal');
  if (m) m.classList.remove('open');
}

function confirmAction(message, onYes) {
  let backdrop = el('confirmPopup');
  if (!backdrop) {
    backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop';
    backdrop.id = 'confirmPopup';
    backdrop.innerHTML = `<div class="modal" style="max-width:380px">
      <div class="modal-body" style="text-align:center;padding:28px 24px">
        <div style="font-size:40px;margin-bottom:12px">⚠️</div>
        <p id="confirmMsg" style="font-size:15px;font-weight:600;margin-bottom:20px"></p>
        <div style="display:flex;gap:10px;justify-content:center">
          <button class="btn btn-outline" onclick="el('confirmPopup').classList.remove('open')" style="min-width:90px">Cancel</button>
          <button class="btn btn-primary" id="confirmYesBtn" style="min-width:90px;background:#e63946;border-color:#e63946">Yes, Do It</button>
        </div>
      </div>
    </div>`;
    document.body.appendChild(backdrop);
  }
  el('confirmMsg').textContent = message;
  el('confirmYesBtn').onclick = function() {
    backdrop.classList.remove('open');
    try { onYes(); } catch(e) { console.error(e); }
  };
  backdrop.classList.add('open');
}

// --- Hamburger (mobile nav) ---
function toggleNav() {
  const nav = el('mainNav');
  if (nav) nav.classList.toggle('open');
}

// --- PWA: Service Worker Registration ---
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    // Force update: unregister old SW, clear caches, then re-register
    navigator.serviceWorker.getRegistrations().then((regs) => {
      regs.forEach((reg) => reg.update());
    });
    caches.keys().then((keys) => {
      keys.forEach((key) => { if (key !== 'boxcric-v3') caches.delete(key); });
    });
    navigator.serviceWorker.register('/sw.js', { scope: '/' })
      .then((reg) => { reg.update(); })
      .catch((err) => console.log('SW registration failed:', err));
  });
}

// --- PWA: Install Prompt ---
let deferredPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  const banner = el('installBanner');
  if (banner) banner.classList.add('show');
});

document.addEventListener('DOMContentLoaded', () => {
  const installBtn = el('installBtn');
  const installDismiss = el('installDismiss');
  const banner = el('installBanner');

  if (installBtn) {
    installBtn.addEventListener('click', async () => {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      const { outcome } = await deferredPrompt.userChoice;
      if (outcome === 'accepted') {
        toast('BOXcric installed! 🏏', 'success');
      }
      deferredPrompt = null;
      if (banner) banner.classList.remove('show');
    });
  }

  if (installDismiss) {
    installDismiss.addEventListener('click', () => {
      if (banner) banner.classList.remove('show');
    });
  }
});

// --- Pull-to-refresh ---
let touchStartY = 0;
document.addEventListener('touchstart', (e) => {
  touchStartY = e.touches[0].clientY;
}, { passive: true });
document.addEventListener('touchend', (e) => {
  const touchEndY = e.changedTouches[0].clientY;
  if (window.scrollY === 0 && touchEndY - touchStartY > 120) {
    window.location.reload();
  }
}, { passive: true });

// --- Vibration on scoring ---
function haptic(ms) {
  if (navigator.vibrate) navigator.vibrate(ms || 30);
}
