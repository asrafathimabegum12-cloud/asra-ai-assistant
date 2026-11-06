const API_BASE = 'http://127.0.0.1:8018';
const profilesContainer = document.getElementById('profilesContainer');
const loadingState = document.getElementById('loadingState');
const errorState = document.getElementById('errorState');
const emptyState = document.getElementById('emptyState');
const detailContent = document.getElementById('detailContent');
const refreshBtn = document.getElementById('refreshBtn');

const state = {
  profiles: [],
  selectedUserId: null,
};

function escapeHtml(value) {
  if (value === null || value === undefined || value === '') {
    return '—';
  }

  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function formatDate(value) {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

function showLoading(isLoading) {
  loadingState.classList.toggle('hidden', !isLoading);
}

function showError(message) {
  errorState.textContent = message || 'Something went wrong while loading profiles.';
  errorState.classList.remove('hidden');
}

function hideError() {
  errorState.classList.add('hidden');
  errorState.textContent = '';
}

function renderEmptyState() {
  emptyState.classList.toggle('hidden', state.profiles.length > 0);
}

function getEducationText(profile) {
  const education = profile?.education || {};
  const degree = education.degree_course || education.highest_education_level || 'Not available';
  const college = education.college_university ? ` • ${education.college_university}` : '';
  return `${degree}${college}`;
}

function renderProfileCards() {
  profilesContainer.innerHTML = '';

  if (!state.profiles.length) {
    renderEmptyState();
    return;
  }

  renderEmptyState();

  state.profiles.forEach((profile) => {
    const card = document.createElement('article');
    card.className = `profile-card ${state.selectedUserId === profile.user_id ? 'selected' : ''}`;
    card.tabIndex = 0;

    const educationText = escapeHtml(getEducationText(profile));
    const email = escapeHtml(profile.personal_information?.email || '—');
    const fullName = escapeHtml(profile.personal_information?.full_name || 'Unknown User');
    const targetRole = escapeHtml(profile.career_information?.target_job_role || 'Not specified');

    card.innerHTML = `
      <div class="profile-header">
        <h3>${fullName}</h3>
        <span class="badge">${escapeHtml(profile.user_id.slice(0, 8))}</span>
      </div>
      <div class="meta-grid">
        <div><strong>Email:</strong> ${email}</div>
        <div><strong>Education:</strong> ${educationText}</div>
        <div><strong>Target Role:</strong> ${targetRole}</div>
        <div><strong>Created:</strong> ${escapeHtml(formatDate(profile.created_at))}</div>
      </div>
    `;

    card.addEventListener('click', () => {
      state.selectedUserId = profile.user_id;
      localStorage.setItem('user_id', profile.user_id);
      renderProfileCards();
      showProfileDetail(profile);
    });

    profilesContainer.appendChild(card);
  });
}

function renderDetailField(label, value) {
  const safeValue = escapeHtml(value || '—');
  return `
    <div class="detail-grid">
      <strong>${escapeHtml(label)}:</strong>
      <span>${safeValue}</span>
    </div>
  `;
}

function renderListValue(title, value) {
  const values = Array.isArray(value) ? value.filter(Boolean) : [];
  return values.length ? `
    <div class="detail-card">
      <h4>${escapeHtml(title)}</h4>
      <div>${values.map((item) => `<span class="badge">${escapeHtml(item)}</span>`).join(' ')}</div>
    </div>
  ` : '';
}

function showProfileDetail(profile) {
  if (!profile) {
    detailContent.className = 'detail-content empty-detail';
    detailContent.textContent = 'Select a profile to view complete details.';
    return;
  }

  const personal = profile.personal_information || {};
  const education = profile.education || {};
  const career = profile.career_information || {};
  const skills = profile.skills || {};
  const goals = profile.career_goals || {};
  const resume = profile.resume_information || {};

  detailContent.className = 'detail-content';
  detailContent.innerHTML = `
    <div class="detail-card">
      <h3>${escapeHtml(personal.full_name || 'Unknown User')}</h3>
      <div class="detail-grid">
        ${renderDetailField('User ID', profile.user_id)}
        ${renderDetailField('Preferred Name', personal.preferred_name)}
        ${renderDetailField('Email', personal.email)}
        ${renderDetailField('Phone', personal.phone_number)}
        ${renderDetailField('City', personal.current_city)}
        ${renderDetailField('Country', personal.country)}
        ${renderDetailField('Created', formatDate(profile.created_at))}
      </div>
    </div>

    <div class="detail-card">
      <div class="form-actions">
        <a class="btn btn-primary" href="profile.html" data-user-id="${escapeHtml(profile.user_id)}">Edit this profile</a>
      </div>
    </div>

    <div class="detail-card">
      <h4>Education</h4>
      <div class="detail-grid">
        ${renderDetailField('Level', education.highest_education_level)}
        ${renderDetailField('Degree / Course', education.degree_course)}
        ${renderDetailField('Specialization', education.specialization_branch)}
        ${renderDetailField('College / University', education.college_university)}
        ${renderDetailField('Graduation Year', education.graduation_year)}
        ${renderDetailField('Current Status', education.current_education_status)}
      </div>
    </div>

    <div class="detail-card">
      <h4>Career Info</h4>
      <div class="detail-grid">
        ${renderDetailField('Current Status', career.current_status)}
        ${renderDetailField('Target Job Role', career.target_job_role)}
        ${renderDetailField('Preferred Industry', career.preferred_industry)}
        ${renderDetailField('Preferred Work Location', career.preferred_work_location)}
        ${renderDetailField('Experience Level', career.experience_level)}
        ${renderDetailField('Current Company', career.current_company)}
        ${renderDetailField('Current Job Role', career.current_job_role)}
      </div>
    </div>

    ${renderListValue('Programming Languages', skills.programming_languages)}
    ${renderListValue('Technical Skills', skills.technical_skills)}
    ${renderListValue('Tools / Technologies', skills.tools_technologies)}
    ${renderListValue('Soft Skills', skills.soft_skills)}

    <div class="detail-card">
      <h4>Career Goals</h4>
      <div class="detail-grid">
        ${renderDetailField('Short-term Goal', goals.short_term_career_goal)}
        ${renderDetailField('Long-term Goal', goals.long_term_career_goal)}
        ${renderDetailField('Target Role', goals.target_role)}
        ${renderDetailField('Target Companies', Array.isArray(goals.target_companies) ? goals.target_companies.join(', ') : goals.target_companies)}
        ${renderDetailField('Areas to Improve', Array.isArray(goals.areas_to_improve) ? goals.areas_to_improve.join(', ') : goals.areas_to_improve)}
        ${renderDetailField('Learning Style', Array.isArray(goals.preferred_learning_style) ? goals.preferred_learning_style.join(', ') : goals.preferred_learning_style)}
      </div>
    </div>

    <div class="detail-card">
      <h4>Resume Info</h4>
      <div class="detail-grid">
        ${renderDetailField('Resume Uploaded', resume.uploaded ? 'Yes' : 'No')}
        ${renderDetailField('File Name', resume.file_name)}
        ${renderDetailField('File Type', resume.file_type)}
        ${renderDetailField('File Size', resume.file_size_bytes ? `${resume.file_size_bytes} bytes` : '—')}
        ${renderDetailField('Processed', resume.processed ? 'Yes' : 'No')}
      </div>
    </div>
  `;

  const editButton = detailContent.querySelector('a[data-user-id]');
  if (editButton) {
    editButton.addEventListener('click', () => {
      const selectedId = editButton.dataset.userId;
      if (selectedId) {
        localStorage.setItem('user_id', selectedId);
      }
    });
  }
}

async function fetchProfiles() {
  showLoading(true);
  hideError();

  try {
    const response = await fetch(`${API_BASE}/api/users`);
    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || 'Unable to fetch profiles.');
    }

    state.profiles = Array.isArray(result.profiles) ? result.profiles : [];

    const storedUserId = localStorage.getItem('user_id');
    if (storedUserId && state.profiles.some((item) => item.user_id === storedUserId)) {
      state.selectedUserId = storedUserId;
    } else if (state.profiles.length > 0) {
      state.selectedUserId = state.profiles[0].user_id;
      localStorage.setItem('user_id', state.selectedUserId);
    } else {
      state.selectedUserId = null;
      detailContent.className = 'detail-content empty-detail';
      detailContent.textContent = 'Select a profile to view complete details.';
    }

    if (state.profiles.length > 0) {
      const selectedProfile = state.profiles.find((item) => item.user_id === state.selectedUserId) || state.profiles[0];
      showProfileDetail(selectedProfile);
    }

    renderProfileCards();
  } catch (error) {
    showError(error.message || 'Unable to load profiles.');
  } finally {
    showLoading(false);
  }
}

refreshBtn.addEventListener('click', fetchProfiles);

fetchProfiles();
