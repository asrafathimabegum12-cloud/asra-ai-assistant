const BADGE_CATALOG = [
  {
    badge_id: 'planner-pro',
    title: 'Planner Pro',
    description: 'Complete 3 study tasks.',
    total: 3,
  },
  {
    badge_id: 'practice-starter',
    title: 'Practice Starter',
    description: 'Complete your first technical quiz.',
    total: 1,
  },
  {
    badge_id: 'mock-ready',
    title: 'Mock Interview Ready',
    description: 'Complete 1 mock interview session.',
    total: 1,
  },
  {
    badge_id: 'notetaker',
    title: 'Notetaker',
    description: 'Save 3 personal notes.',
    total: 3,
  },
];

async function renderAchievements() {
  const userId = getCurrentUserId();
  const target = document.getElementById('achievementList');
  if (!target) return;

  try {
    const [achievementData, plannerData, testData, interviewData, notesData] = await Promise.all([
      apiFetch(`${API_BASE}/api/achievements/${encodeURIComponent(userId)}`),
      apiFetch(`${API_BASE}/api/study-planner/${encodeURIComponent(userId)}`),
      apiFetch(`${API_BASE}/api/tests/performance/${encodeURIComponent(userId)}`),
      apiFetch(`${API_BASE}/api/interviews/${encodeURIComponent(userId)}`),
      apiFetch(`${API_BASE}/api/notes/${encodeURIComponent(userId)}`),
    ]);

    const earned = achievementData.achievements || [];
    const earnedMap = {};
    earned.forEach((item) => {
      earnedMap[item.badge_id] = item;
    });

    const liveProgress = {
      'planner-pro': (plannerData.tasks || []).filter((task) => task.completed).length,
      'practice-starter': testData.completed_tests || 0,
      'mock-ready': (interviewData.history || []).length,
      notetaker: (notesData.notes || []).length,
    };

    target.innerHTML = BADGE_CATALOG.map((badge) => {
      const saved = earnedMap[badge.badge_id];
      const earnedBadge = Boolean(saved);
      const progress = saved
        ? (saved.progress || liveProgress[badge.badge_id] || 0)
        : (liveProgress[badge.badge_id] || 0);
      const total = saved?.total || badge.total || 1;
      const percent = Math.min(100, Math.round((progress / Math.max(1, total)) * 100));
      return `
        <div class="badge-card ${earnedBadge ? 'earned' : 'locked'}">
          <div class="badge-header">
            <strong>${saved?.title || badge.title}</strong>
            <span class="badge-pill">${earnedBadge ? 'Earned' : 'Locked'}</span>
          </div>
          <p>${saved?.description || badge.description}</p>
          <div class="progress-track small"><span style="width:${percent}%"></span></div>
          <small>${progress}/${total} complete</small>
        </div>
      `;
    }).join('');
  } catch (error) {
    target.innerHTML = `<div class="empty-state">${error.message || 'Badges unavailable.'}</div>`;
  }
}

renderAchievements();
