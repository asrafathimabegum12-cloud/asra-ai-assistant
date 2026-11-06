async function loadInterviewBank() {
  const role = document.getElementById('questionBankRole').value;
  const difficulty = document.getElementById('questionBankDifficulty').value;
  const list = document.getElementById('questionBankList');
  if (!list) return;

  const userId = getCurrentUserId();

  try {
    const params = new URLSearchParams();
    if (role) params.set('role', role);
    if (difficulty) params.set('difficulty', difficulty);
    const [data, progressResponse] = await Promise.all([
      apiFetch(`${API_BASE}/api/interview-bank/questions?${params.toString()}`),
      apiFetch(`${API_BASE}/api/interview-bank/${encodeURIComponent(userId)}`),
    ]);
    const questions = data.questions || [];
    const progressMap = {};
    (progressResponse.progress || []).forEach((entry) => {
      progressMap[entry.question_id] = entry;
    });

    if (!questions.length) {
      list.innerHTML = '<div class="empty-state">No questions found for this filter.</div>';
      return;
    }

    list.innerHTML = questions.map((question) => {
      const progress = progressMap[question.id] || {};
      const saved = Boolean(progress.saved);
      const completed = Boolean(progress.completed);
      return `
      <div class="info-card">
        <div class="info-header">
          <strong>${question.role}</strong>
          <span class="mini-badge light">${question.difficulty}</span>
        </div>
        <p>${question.question}</p>
        <small>${question.topic}</small>
        <div class="inline-actions">
          <button class="btn btn-secondary small-btn" data-question-id="${question.id}" data-saved="${saved}" data-completed="${completed}" data-action="toggle-saved">${saved ? 'Saved' : 'Save'}</button>
          <button class="btn btn-secondary small-btn" data-question-id="${question.id}" data-saved="${saved}" data-completed="${completed}" data-action="toggle-complete">${completed ? 'Completed' : 'Mark done'}</button>
        </div>
      </div>
    `;
    }).join('');

    list.querySelectorAll('[data-action]').forEach((button) => {
      button.addEventListener('click', async () => {
        const action = button.dataset.action;
        const questionId = button.dataset.questionId;
        const currentlySaved = button.dataset.saved === 'true';
        const currentlyCompleted = button.dataset.completed === 'true';
        try {
          await apiFetch(`${API_BASE}/api/interview-bank/${encodeURIComponent(userId)}/progress`, {
            method: 'POST',
            body: JSON.stringify({
              user_id: userId,
              question_id: questionId,
              role,
              completed: action === 'toggle-complete' ? !currentlyCompleted : currentlyCompleted,
              saved: action === 'toggle-saved' ? !currentlySaved : currentlySaved,
            }),
          });
          await loadInterviewBank();
        } catch (error) {
          alert(error.message || 'Unable to update interview progress.');
        }
      });
    });
  } catch (error) {
    list.innerHTML = `<div class="empty-state">${error.message || 'Unable to load interview bank.'}</div>`;
  }
}

document.getElementById('loadQuestionBankBtn')?.addEventListener('click', loadInterviewBank);
loadInterviewBank();
