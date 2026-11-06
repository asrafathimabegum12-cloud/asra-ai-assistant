const editProfileForm = document.getElementById('editProfileForm');

if (editProfileForm) {
  const profileStatus = document.getElementById('profileStatus');
  const saveProfileBtn = document.getElementById('saveProfileBtn');
  const resumeStatus = document.getElementById('resumeStatus');
  const resumeInput = document.getElementById('resume_file');
  const skipResumeCheckbox = document.getElementById('skip_resume');
  const editResumeBtn = document.getElementById('editResumeBtn');
  const removeResumeBtn = document.getElementById('removeResumeBtn');
  const resumeEditorPanel = document.getElementById('resumeEditorPanel');
  const resumeEditText = document.getElementById('resumeEditText');
  const resumeEditorStatus = document.getElementById('resumeEditorStatus');
  const saveResumeBtn = document.getElementById('saveResumeBtn');
  const cancelResumeEditBtn = document.getElementById('cancelResumeEditBtn');
  let currentProfile = null;
  const profileOverview = document.getElementById('profileOverview');
  const editProfileToggleBtn = document.getElementById('editProfileToggleBtn');
  const profileIntro = document.getElementById('profileIntro');

  function profileDisplayValue(value) {
    if (Array.isArray(value)) return value.filter(Boolean).join(', ') || 'Not provided';
    if (value === null || value === undefined || value === '') return 'Not provided';
    if (typeof value === 'object') return Object.values(value).filter(Boolean).join(', ') || 'Not provided';
    return String(value);
  }

  function renderProfileOverview(profile) {
    if (!profileOverview) return;
    const groups = [
      ['Personal Information', profile.personal_information || {}],
      ['Education', profile.education || {}],
      ['Career Information', profile.career_information || {}],
      ['Skills', profile.skills || {}],
      ['Career Goals', profile.career_goals || {}],
      ['Resume', profile.resume_information || {}]
    ];
    profileOverview.replaceChildren();

    groups.forEach(([heading, values]) => {
      const section = document.createElement('section');
      section.className = 'mini-panel';
      section.style.marginTop = '16px';

      const title = document.createElement('h3');
      title.textContent = heading;
      section.appendChild(title);

      const grid = document.createElement('div');
      grid.className = 'form-grid';

      Object.entries(values).forEach(([key, value]) => {
        if (heading === 'Resume' && ['storage_path', 'file_size_bytes'].includes(key)) return;
        const field = document.createElement('div');
        field.className = 'field-group';

        const label = document.createElement('strong');
        label.textContent = key.replace(/_/g, ' ').replace(/\b\w/g, letter => letter.toUpperCase());

        const detail = document.createElement('p');
        detail.textContent = profileDisplayValue(value);
        detail.style.margin = '6px 0 0';

        field.append(label, detail);
        grid.appendChild(field);
      });

      if (!grid.children.length) {
        const empty = document.createElement('p');
        empty.textContent = 'No information provided yet.';
        section.appendChild(empty);
      } else {
        section.appendChild(grid);
      }
      profileOverview.appendChild(section);
    });
  }

  function showProfileOverview() {
    if (editProfileForm) editProfileForm.style.display = 'none';
    if (profileOverview) profileOverview.style.display = 'block';
    if (editProfileToggleBtn) editProfileToggleBtn.textContent = 'Edit Profile';
    if (profileIntro) profileIntro.textContent = 'Your saved profile information appears below. Use Edit Profile to make changes.';
  }

  if (editProfileToggleBtn) {
    editProfileToggleBtn.addEventListener('click', () => {
      const isEditing = editProfileForm.style.display !== 'none';
      if (isEditing) {
        showProfileOverview();
      } else {
        if (profileOverview) profileOverview.style.display = 'none';
        editProfileForm.style.display = 'block';
        editProfileToggleBtn.textContent = 'Cancel Editing';
        if (profileIntro) profileIntro.textContent = 'Update any field you want to change, then select Save Changes.';
      }
    });
  }
  let removeResumeRequested = false;

  function setStatus(element, message, type = 'info', allowHtml = false) {
    if (!element) {
      return;
    }

    if (allowHtml) {
      element.innerHTML = message;
    } else {
      element.textContent = message;
    }

    const colors = {
      info: '#4f46e5',
      success: '#13795b',
      error: '#b42318',
    };

    element.style.color = colors[type] || colors.info;
    element.style.fontWeight = '600';
  }

  function parseCsv(value) {
    if (value === null || value === undefined || value === '') {
      return [];
    }

    return String(value)
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function formatCsv(value) {
    if (!Array.isArray(value)) {
      return value || '';
    }

    return value.filter(Boolean).join(', ');
  }

  function populateProfileForm(profile) {
    const personal = profile.personal_information || {};
    const education = profile.education || {};
    const career = profile.career_information || {};
    const skills = profile.skills || {};
    const goals = profile.career_goals || {};

    const fields = {
      edit_full_name: personal.full_name || '',
      edit_preferred_name: personal.preferred_name || '',
      edit_email: personal.email || '',
      edit_phone_number: personal.phone_number || '',
      edit_date_of_birth: personal.date_of_birth || '',
      edit_gender: personal.gender || '',
      edit_current_city: personal.current_city || '',
      edit_country: personal.country || '',
      edit_highest_education_level: education.highest_education_level || '',
      edit_degree_course: education.degree_course || '',
      edit_specialization_branch: education.specialization_branch || '',
      edit_college_university: education.college_university || '',
      edit_graduation_year: education.graduation_year || '',
      edit_current_education_status: education.current_education_status || '',
      edit_current_status: career.current_status || '',
      edit_target_job_role: career.target_job_role || '',
      edit_preferred_industry: career.preferred_industry || '',
      edit_preferred_work_location: career.preferred_work_location || '',
      edit_experience_level: career.experience_level || '',
      edit_current_company: career.current_company || '',
      edit_current_job_role: career.current_job_role || '',
      edit_programming_languages: formatCsv(skills.programming_languages),
      edit_technical_skills: formatCsv(skills.technical_skills),
      edit_tools_technologies: formatCsv(skills.tools_technologies),
      edit_soft_skills: formatCsv(skills.soft_skills),
      edit_short_term_career_goal: goals.short_term_career_goal || '',
      edit_long_term_career_goal: goals.long_term_career_goal || '',
      edit_target_role: goals.target_role || '',
      edit_target_companies: formatCsv(goals.target_companies),
      edit_areas_to_improve: formatCsv(goals.areas_to_improve),
    };

    Object.entries(fields).forEach(([id, value]) => {
      const input = document.getElementById(id);
      if (input) {
        input.value = value ?? '';
      }
    });

    const preferredStyles = Array.isArray(goals.preferred_learning_style) ? goals.preferred_learning_style : [];
    const learningStyleInputs = document.querySelectorAll('input[name="preferred_learning_style"]');
    learningStyleInputs.forEach((input) => {
      input.checked = preferredStyles.includes(input.value);
    });

    removeResumeRequested = false;

    if (resumeInput) {
      resumeInput.value = '';
    }

    if (skipResumeCheckbox) {
      skipResumeCheckbox.checked = false;
    }

    if (removeResumeBtn) {
      removeResumeBtn.disabled = !(profile.resume_information && profile.resume_information.file_name);
    }

    if (resumeStatus) {
      const fileName = profile.resume_information && profile.resume_information.file_name;
      if (fileName) {
        setStatus(resumeStatus, `Current resume: ${fileName}`, 'success');
      } else {
        setStatus(resumeStatus, 'No resume is currently stored for this profile.', 'info');
      }
    }
  }

  function buildPayload() {
    const personal = {
      full_name: document.getElementById('edit_full_name').value.trim(),
      preferred_name: document.getElementById('edit_preferred_name').value.trim(),
      email: document.getElementById('edit_email').value.trim(),
      phone_number: document.getElementById('edit_phone_number').value.trim(),
      date_of_birth: document.getElementById('edit_date_of_birth').value,
      gender: document.getElementById('edit_gender').value,
      current_city: document.getElementById('edit_current_city').value.trim(),
      country: document.getElementById('edit_country').value.trim(),
    };

    const education = {
      highest_education_level: document.getElementById('edit_highest_education_level').value,
      degree_course: document.getElementById('edit_degree_course').value.trim(),
      specialization_branch: document.getElementById('edit_specialization_branch').value.trim(),
      college_university: document.getElementById('edit_college_university').value.trim(),
      graduation_year: document.getElementById('edit_graduation_year').value,
      current_education_status: document.getElementById('edit_current_education_status').value,
    };

    const career = {
      current_status: document.getElementById('edit_current_status').value,
      target_job_role: document.getElementById('edit_target_job_role').value.trim(),
      preferred_industry: document.getElementById('edit_preferred_industry').value.trim(),
      preferred_work_location: document.getElementById('edit_preferred_work_location').value.trim(),
      experience_level: document.getElementById('edit_experience_level').value,
      current_company: document.getElementById('edit_current_company').value.trim() || null,
      current_job_role: document.getElementById('edit_current_job_role').value.trim() || null,
    };

    const skills = {
      programming_languages: parseCsv(document.getElementById('edit_programming_languages').value),
      technical_skills: parseCsv(document.getElementById('edit_technical_skills').value),
      tools_technologies: parseCsv(document.getElementById('edit_tools_technologies').value),
      soft_skills: parseCsv(document.getElementById('edit_soft_skills').value),
    };

    const careerGoals = {
      short_term_career_goal: document.getElementById('edit_short_term_career_goal').value.trim(),
      long_term_career_goal: document.getElementById('edit_long_term_career_goal').value.trim(),
      target_role: document.getElementById('edit_target_role').value.trim(),
      target_companies: parseCsv(document.getElementById('edit_target_companies').value),
      areas_to_improve: parseCsv(document.getElementById('edit_areas_to_improve').value),
      preferred_learning_style: Array.from(document.querySelectorAll('input[name="preferred_learning_style"]:checked')).map((item) => item.value),
    };

    const resumeInformation = currentProfile && currentProfile.resume_information
      ? { ...currentProfile.resume_information }
      : {
          uploaded: false,
          file_name: null,
          file_type: null,
          file_size_bytes: null,
          processed: false,
          storage_path: null,
        };

    return {
      personal_information: personal,
      education,
      career_information: career,
      skills,
      career_goals: careerGoals,
      resume_information: resumeInformation,
    };
  }

  async function loadResumeForEditing() {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
      setStatus(resumeEditorStatus, 'Select a saved profile before editing the resume.', 'error');
      return;
    }

    if (!resumeEditText) {
      return;
    }

    const fileName = currentProfile && currentProfile.resume_information && currentProfile.resume_information.file_name;
    if (!fileName) {
      setStatus(resumeEditorStatus, 'No resume file is stored for this profile yet. Upload a resume first.', 'error');
      if (resumeEditorPanel) {
        resumeEditorPanel.style.display = 'block';
      }
      return;
    }

    setStatus(resumeEditorStatus, 'Loading the current resume text...', 'info');
    try {
      const response = await fetch(`http://127.0.0.1:8018/api/users/${encodeURIComponent(userId)}/resume`);
      const result = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(result.detail || 'Unable to load the current resume text.');
      }

      resumeEditText.value = result.text || '';
      if (resumeEditorPanel) {
        resumeEditorPanel.style.display = 'block';
      }
      setStatus(resumeEditorStatus, `Loaded: ${result.filename || fileName}`, 'success');
    } catch (error) {
      console.error('Resume load for edit error:', error);
      setStatus(resumeEditorStatus, error.message || 'The current resume could not be opened for editing.', 'error');
      if (resumeEditorPanel) {
        resumeEditorPanel.style.display = 'block';
      }
    }
  }

  async function saveEditedResume() {
    const userId = localStorage.getItem('user_id');
    if (!userId) {
      setStatus(resumeEditorStatus, 'Select a saved profile before saving the edited resume.', 'error');
      return;
    }

    if (!resumeEditText) {
      return;
    }

    const editedText = resumeEditText.value.trim();
    if (!editedText) {
      setStatus(resumeEditorStatus, 'Resume content cannot be empty. Add your summary, skills, and experience before saving.', 'error');
      return;
    }

    if (saveResumeBtn) {
      saveResumeBtn.disabled = true;
      saveResumeBtn.textContent = 'Saving...';
    }
    setStatus(resumeEditorStatus, 'Generating the updated DOCX resume...', 'info');

    try {
      const formData = new FormData();
      formData.append('resume_text', editedText);

      const response = await fetch(`http://127.0.0.1:8018/api/users/${encodeURIComponent(userId)}/resume`, {
        method: 'POST',
        body: formData,
      });

      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(result.detail || 'Unable to save the updated resume.');
      }

      currentProfile = currentProfile || {};
      currentProfile.resume_information = {
        uploaded: true,
        file_name: result.filename || 'resume_edited.docx',
        file_type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        file_size_bytes: null,
        processed: false,
        storage_path: null,
      };

      setStatus(resumeEditorStatus, result.message || 'Resume saved successfully.', 'success');
      setStatus(resumeStatus, `Current resume: ${currentProfile.resume_information.file_name}`, 'success');
      if (resumeEditorPanel) {
        resumeEditorPanel.style.display = 'none';
      }
      if (resumeInput) {
        resumeInput.value = '';
      }
      if (skipResumeCheckbox) {
        skipResumeCheckbox.checked = false;
      }
      if (removeResumeBtn) {
        removeResumeBtn.disabled = false;
      }
    } catch (error) {
      console.error('Resume save error:', error);
      setStatus(resumeEditorStatus, error.message || 'The updated resume could not be saved.', 'error');
    } finally {
      if (saveResumeBtn) {
        saveResumeBtn.disabled = false;
        saveResumeBtn.textContent = 'Save Resume';
      }
    }
  }

  async function loadUserProfile() {
    const userId = localStorage.getItem('user_id');

    if (!userId) {
      const message = 'No saved profile is selected. <a href="users.html">Choose an existing saved profile</a> to edit, or complete the profile setup first.';
      console.error('Profile fetch diagnostic: missing localStorage.user_id');
      setStatus(profileStatus, message, 'error', true);
      return;
    }

    const profileUrl = `http://127.0.0.1:8018/api/users/${encodeURIComponent(userId)}`;

    setStatus(profileStatus, 'Loading your saved profile...', 'info');
    saveProfileBtn.disabled = true;
    saveProfileBtn.textContent = 'Loading...';

    try {
      const response = await fetch(profileUrl);
      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        console.error('Profile fetch diagnostic:', {
          userId,
          url: profileUrl,
          status: response.status,
          statusText: response.statusText,
          responseBody: data && typeof data === 'object' ? { success: data.success, detail: data.detail, keys: Object.keys(data) } : data,
        });

        const message = 'This saved profile could not be found. <a href="users.html">Choose an existing saved profile</a> to continue editing.';
        setStatus(profileStatus, message, 'error', true);
        throw new Error(data.detail || 'Unable to load your saved profile.');
      }

      const profileData = data && typeof data === 'object' && 'profile' in data ? data.profile : data;
      if (!profileData || typeof profileData !== 'object') {
        console.error('Profile fetch diagnostic: empty profile payload', {
          userId,
          url: profileUrl,
          responseBody: data && typeof data === 'object' ? { success: data.success, keys: Object.keys(data) } : data,
        });
        throw new Error('The profile response did not include usable profile data.');
      }

      currentProfile = profileData;
      populateProfileForm(currentProfile);
      renderProfileOverview(currentProfile);
      showProfileOverview();
      setStatus(profileStatus, 'Your saved profile has been loaded.', 'success');
    } catch (error) {
      console.error('Profile load error:', {
        message: error && error.message ? error.message : String(error),
        userId,
        url: profileUrl,
      });
      setStatus(profileStatus, error.message || 'Could not load your saved profile.', 'error');
    } finally {
      saveProfileBtn.disabled = false;
      saveProfileBtn.textContent = 'Save Changes';
    }
  }

  editProfileForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const userId = localStorage.getItem('user_id');
    if (!userId) {
      const message = 'No saved profile is selected. <a href="users.html">Choose an existing saved profile</a> before saving changes.';
      console.error('Profile save diagnostic: missing localStorage.user_id');
      setStatus(profileStatus, message, 'error', true);
      return;
    }

    const payload = buildPayload();
    const formData = new FormData();
    formData.append('profile', JSON.stringify(payload));

    if (removeResumeRequested) {
      formData.append('remove_resume', 'true');
    }

    if (resumeInput && resumeInput.files && resumeInput.files[0] && !skipResumeCheckbox.checked) {
      formData.append('resume', resumeInput.files[0]);
      removeResumeRequested = false;
    }

    saveProfileBtn.disabled = true;
    saveProfileBtn.textContent = 'Saving...';
    setStatus(profileStatus, 'Saving your changes...', 'info');

    try {
      const response = await fetch(`http://127.0.0.1:8018/api/users/${encodeURIComponent(userId)}`, {
        method: 'PUT',
        body: formData,
      });

      const result = await response.json().catch(() => ({}));

      if (!response.ok) {
        console.error('Profile save diagnostic:', {
          userId,
          url: `http://127.0.0.1:8018/api/users/${encodeURIComponent(userId)}`,
          status: response.status,
          statusText: response.statusText,
          responseBody: result && typeof result === 'object' ? { success: result.success, detail: result.detail, keys: Object.keys(result) } : result,
        });
        throw new Error(result.detail || 'Profile update failed.');
      }

      currentProfile = currentProfile || {};
      if (removeResumeRequested) {
        currentProfile.resume_information = {
          uploaded: false,
          file_name: null,
          file_type: null,
          file_size_bytes: null,
          processed: false,
          storage_path: null,
        };
      } else if (resumeInput && resumeInput.files && resumeInput.files[0]) {
        currentProfile.resume_information = payload.resume_information;
      }

      currentProfile = { ...currentProfile, ...payload };
      renderProfileOverview(currentProfile);
      showProfileOverview();
      setStatus(profileStatus, result.message || 'Profile updated successfully.', 'success');

      if (resumeInput && resumeInput.files && resumeInput.files[0]) {
        setStatus(resumeStatus, `New resume uploaded: ${resumeInput.files[0].name}`, 'success');
      } else if (removeResumeRequested) {
        setStatus(resumeStatus, 'Resume removed successfully.', 'success');
      } else if (currentProfile.resume_information && currentProfile.resume_information.file_name) {
        setStatus(resumeStatus, `Current resume: ${currentProfile.resume_information.file_name}`, 'success');
      } else {
        setStatus(resumeStatus, 'No replacement resume selected. Your current resume will be kept.', 'info');
      }

      resumeInput.value = '';
      removeResumeRequested = false;
      if (skipResumeCheckbox) {
        skipResumeCheckbox.checked = false;
      }
    } catch (error) {
      console.error('Profile update error:', error);
      setStatus(profileStatus, error.message || 'Your profile could not be saved.', 'error');
    } finally {
      saveProfileBtn.disabled = false;
      saveProfileBtn.textContent = 'Save Changes';
    }
  });

  if (resumeInput) {
    resumeInput.addEventListener('change', () => {
      removeResumeRequested = false;
      if (resumeInput.files && resumeInput.files[0]) {
        const file = resumeInput.files[0];
        const allowedExts = ['.pdf', '.docx'];
        const extension = file.name.includes('.') ? file.name.slice(file.name.lastIndexOf('.')).toLowerCase() : '';
        if (!allowedExts.includes(extension)) {
          resumeInput.value = '';
          setStatus(resumeStatus, 'Only PDF and DOCX resume files are supported.', 'error');
          return;
        }
        setStatus(resumeStatus, `Selected resume: ${file.name}`, 'info');
        if (skipResumeCheckbox) {
          skipResumeCheckbox.checked = false;
        }
      } else if (currentProfile && currentProfile.resume_information && currentProfile.resume_information.file_name) {
        setStatus(resumeStatus, `Current resume: ${currentProfile.resume_information.file_name}`, 'success');
      } else {
        setStatus(resumeStatus, 'No replacement resume selected. Your current resume will be kept.', 'info');
      }
    });
  }

  if (skipResumeCheckbox) {
    skipResumeCheckbox.addEventListener('change', () => {
      if (skipResumeCheckbox.checked) {
        resumeInput.value = '';
        removeResumeRequested = false;
        setStatus(resumeStatus, 'No replacement resume selected. Your current resume will be kept.', 'info');
      }
    });
  }

  if (editResumeBtn) {
    editResumeBtn.addEventListener('click', () => {
      const userId = localStorage.getItem('user_id');
      if (!userId) {
        setStatus(resumeStatus, 'Select a saved profile before editing a resume.', 'error');
        return;
      }

      if (!currentProfile || !currentProfile.resume_information || !currentProfile.resume_information.file_name) {
        setStatus(resumeStatus, 'No uploaded resume is available for this profile yet. Upload one first, or use the Upload Resume option.', 'info');
        return;
      }

      loadResumeForEditing();
    });
  }

  if (saveResumeBtn) {
    saveResumeBtn.addEventListener('click', saveEditedResume);
  }

  if (cancelResumeEditBtn) {
    cancelResumeEditBtn.addEventListener('click', () => {
      if (resumeEditorPanel) {
        resumeEditorPanel.style.display = 'none';
      }
      if (resumeEditText) {
        resumeEditText.value = '';
      }
      setStatus(resumeEditorStatus, 'Load the current resume to edit it.', 'info');
    });
  }

  if (removeResumeBtn) {
    removeResumeBtn.addEventListener('click', () => {
      const fileName = currentProfile && currentProfile.resume_information && currentProfile.resume_information.file_name;
      if (!fileName) {
        setStatus(resumeStatus, 'There is no resume to remove.', 'info');
        return;
      }

      const confirmed = window.confirm(`Remove the current resume file, "${fileName}"? This cannot be undone.`);
      if (!confirmed) {
        return;
      }

      removeResumeRequested = true;
      if (resumeInput) {
        resumeInput.value = '';
      }
      if (skipResumeCheckbox) {
        skipResumeCheckbox.checked = false;
      }
      setStatus(resumeStatus, `Resume marked for removal: ${fileName}`, 'info');
    });
  }

  loadUserProfile();
}

