async function generateRoadmap() {
  const role = document.getElementById('roadmapRoleSelect').value;
  const container = document.getElementById('roadmapContainer');
  const userId = getCurrentUserId();

  try {
    const data = await apiFetch(`${API_BASE}/api/roadmaps/${encodeURIComponent(userId)}`);
    const existing = data.roadmaps || [];
    const latest = existing.find((item) => item.target_role === role) || null;

    if (!latest) {
      const payload = {
        target_role: role,
        skills: [],
        technologies: [],
        projects: [],
        milestones: [
          { title: 'Build a beginner project in this track', done: false },
          { title: 'Practice the required technical skills', done: false },
          { title: 'Publish your portfolio and review results', done: false },
        ],
      };
      const generated = await apiFetch(`${API_BASE}/api/roadmaps/${encodeURIComponent(userId)}`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      renderRoadmap(generated.roadmap);
      return;
    }

    renderRoadmap(latest);
  } catch (error) {
    container.innerHTML = `<div class="empty-state">${error.message || 'Roadmap generation failed.'}</div>`;
  }
}

function renderRoadmap(roadmap) {
  const container = document.getElementById('roadmapContainer');
  const milestones = roadmap.milestones || [];
  const doneCount = milestones.filter((item) => item.done).length;
  const percent = milestones.length ? Math.round((doneCount / milestones.length) * 100) : 0;
  const milestoneMarkup = milestones.map((milestone, index) => `
    <label class="task-check milestone-item ${milestone.done ? 'done' : ''}">
      <input type="checkbox" data-roadmap-id="${roadmap.roadmap_id}" data-index="${index}" ${milestone.done ? 'checked' : ''} />
      <span>${milestone.title}</span>
    </label>
  `).join('');

  container.innerHTML = `
    <div class="info-card">
      <div class="info-header">
        <strong>${roadmap.target_role}</strong>
        <span class="mini-badge light">${percent}% complete</span>
      </div>
      <div class="progress-wrap">
        <div class="progress-track"><span style="width:${percent}%"></span></div>
        <small>${doneCount} of ${milestones.length} milestones complete</small>
      </div>
      <p><strong>Skills:</strong> ${(roadmap.skills || []).join(', ') || 'Not specified'}</p>
      <p><strong>Tech:</strong> ${(roadmap.technologies || []).join(', ') || 'Not specified'}</p>
      <p><strong>Projects:</strong> ${(roadmap.projects || []).join(', ') || 'Not specified'}</p>
      <div class="milestone-list">${milestoneMarkup}</div>
    </div>
  `;

  container.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
    checkbox.addEventListener('change', async () => {
      const params = new URLSearchParams({
        roadmap_id: checkbox.dataset.roadmapId,
        milestone_index: checkbox.dataset.index,
        done: checkbox.checked,
      });
      try {
        await apiFetch(`${API_BASE}/api/roadmaps/${encodeURIComponent(getCurrentUserId())}/milestones?${params.toString()}`, {
          method: 'PATCH',
        });
        await generateRoadmap();
      } catch (error) {
        alert(error.message || 'Unable to update roadmap milestone.');
      }
    });
  });
}

document.getElementById('generateRoadmapBtn')?.addEventListener('click', generateRoadmap);
generateRoadmap();
