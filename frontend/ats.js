const atsForm = document.getElementById('atsForm');
const atsResult = document.getElementById('atsResult');

if (atsForm) {
  atsForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const formData = new FormData();
    const file = document.getElementById('atsResumeInput').files[0];
    const jobDescription = document.getElementById('atsJobDescription').value.trim();
    if (!jobDescription) {
      atsResult.classList.remove('hidden');
      atsResult.innerHTML = '<div class="empty-state">Please paste the job description first.</div>';
      return;
    }

    formData.append('job_description', jobDescription);
    formData.append('user_id', getCurrentUserId());
    if (file) {
      formData.append('file', file);
    }

    atsResult.classList.remove('hidden');
    atsResult.innerHTML = '<div class="empty-state">Analyzing resume...</div>';

    try {
      const response = await fetch(`${API_BASE}/api/ats/check`, {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'ATS check failed.');

      const atsScore = Math.max(0, Math.min(100, Number(data.estimated_score) || 0));
      const matchedSkills = data.matched_skills || [];
      const missingSkills = data.missing_skills || [];
      const allSkillsCount = matchedSkills.length + missingSkills.length;
      const matchedPercent = allSkillsCount ? Math.round((matchedSkills.length / allSkillsCount) * 100) : 0;
      const missingPercent = allSkillsCount ? 100 - matchedPercent : 0;

      // Destroy the previous charts if the user checks another resume.
      if (window.atsScoreChart) window.atsScoreChart.destroy();
      if (window.atsSkillsChart) window.atsSkillsChart.destroy();

      atsResult.innerHTML = `
        <section class="ats-visual-summary">
          <article class="ats-chart-card">
            <h3>Estimated ATS match</h3>
            <div class="ats-doughnut-wrap">
              <canvas id="atsScoreChart" aria-label="Estimated ATS match percentage"></canvas>
              <div class="ats-doughnut-label">
                <strong>${atsScore}%</strong>
                <span>match</span>
              </div>
            </div>
            <p class="ats-chart-caption">Estimated match based on resume and job-description keywords.</p>
          </article>
          <article class="ats-chart-card">
            <h3>Skill keyword coverage</h3>
            <div class="ats-skill-percent-row">
              <span>Matched</span><strong>${matchedPercent}%</strong>
            </div>
            <div class="ats-percent-track"><span style="width:${matchedPercent}%"></span></div>
            <div class="ats-skill-percent-row">
              <span>Missing</span><strong>${missingPercent}%</strong>
            </div>
            <div class="ats-percent-track missing"><span style="width:${missingPercent}%"></span></div>
            <p class="ats-chart-caption">${matchedSkills.length} matched and ${missingSkills.length} missing skill keyword${allSkillsCount === 1 ? '' : 's'}${allSkillsCount ? ' detected in the job description' : ' detected'}.</p>
            <canvas id="atsSkillsChart" aria-label="Matched and missing skills chart"></canvas>
          </article>
        </section>
        <div class="info-block">
          <strong>Matched skills:</strong> ${matchedSkills.join(', ') || 'None found'}
        </div>
        <div class="info-block">
          <strong>Missing skills:</strong> ${missingSkills.join(', ') || 'No major gaps detected'}
        </div>
        <div class="info-block">
          <strong>Resume sections detected:</strong> ${(data.resume_sections || []).join(', ') || 'None detected'}
        </div>
        <div class="info-block">
          <strong>Improvement suggestions:</strong>
          <ul class="bullet-list">
            ${(data.improvement_suggestions || []).map((item) => `<li>${item}</li>`).join('') || '<li>No extra suggestions.</li>'}
          </ul>
        </div>
        <p class="match-note">${data.estimated_match_note || ''}</p>
      `;

      const scoreCanvas = document.getElementById('atsScoreChart');
      const skillsCanvas = document.getElementById('atsSkillsChart');

      if (window.Chart && scoreCanvas && skillsCanvas) {
        window.atsScoreChart = new Chart(scoreCanvas, {
          type: 'doughnut',
          data: {
            labels: ['Estimated match', 'Remaining'],
            datasets: [{
              data: [atsScore, 100 - atsScore],
              borderWidth: 0,
              hoverOffset: 4
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '78%',
            plugins: { legend: { display: false }, tooltip: { enabled: true } }
          }
        });

        window.atsSkillsChart = new Chart(skillsCanvas, {
          type: 'bar',
          data: {
            labels: ['Matched', 'Missing'],
            datasets: [{
              label: 'Skill keywords',
              data: [matchedSkills.length, missingSkills.length],
              borderWidth: 1
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            scales: {
              x: { beginAtZero: true, ticks: { precision: 0 } }
            },
            plugins: { legend: { display: false } }
          }
        });
      }
    } catch (error) {
      atsResult.innerHTML = `<div class="empty-state">${error.message || 'Unable to check ATS score.'}</div>`;
    }
  });
}

