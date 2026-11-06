const form = document.getElementById('profileForm');

if (form) {
  const steps = Array.from(document.querySelectorAll('.form-step'));
  const nextBtn = document.getElementById('nextBtn');
  const backBtn = document.getElementById('backBtn');
  const submitBtn = document.getElementById('submitBtn');
  const stepCounter = document.getElementById('stepCounter');
  const progressFill = document.getElementById('progressFill');
  const stepDots = Array.from(document.querySelectorAll('.step-dot'));
  const skipResumeCheckbox = document.getElementById('skip_resume');
  const resumeInput = document.getElementById('resume_file');

  let currentStep = 0;

  function getCurrentStepFields() {
    const step = steps[currentStep];
    return Array.from(step.querySelectorAll('input, select, textarea'));
  }

  function validateStep() {
    const fields = getCurrentStepFields();
    let isValid = true;

    fields.forEach((field) => {
      if (field.disabled || field.type === 'checkbox') {
        return;
      }

      const isRequired = field.hasAttribute('required');
      if (isRequired && !field.value.trim()) {
        field.setAttribute('aria-invalid', 'true');
        field.style.borderColor = 'var(--danger)';
        isValid = false;
      } else {
        field.setAttribute('aria-invalid', 'false');
        field.style.borderColor = '';
      }
    });

    if (currentStep === 4) {
      const learningStyleChecked = document.querySelectorAll('input[name="preferred_learning_style"]:checked').length > 0;
      if (!learningStyleChecked) {
        isValid = false;
        document.getElementById('learningStylesGroup').style.borderColor = 'var(--danger)';
      } else {
        document.getElementById('learningStylesGroup').style.borderColor = 'var(--border)';
      }
    }

    return isValid;
  }

  function updateProgress() {
    const totalSteps = steps.length;
    const activeRatio = ((currentStep + 1) / totalSteps) * 100;
    progressFill.style.width = `${activeRatio}%`;
    stepCounter.textContent = `Step ${currentStep + 1} of ${totalSteps}`;

    stepDots.forEach((dot, index) => {
      dot.classList.remove('active', 'completed');
      if (index < currentStep) {
        dot.classList.add('completed');
      } else if (index === currentStep) {
        dot.classList.add('active');
      }
    });
  }

  function showStep(index) {
    steps.forEach((step, stepIndex) => {
      step.classList.toggle('active', stepIndex === index);
    });

    const isFirst = index === 0;
    const isLast = index === steps.length - 1;

    backBtn.hidden = isFirst;
    nextBtn.hidden = isLast;
    submitBtn.hidden = !isLast;

    updateProgress();
  }

  function collectFormData() {
    const formData = new FormData(form);
    const data = {
      personal_information: {
        full_name: formData.get('full_name'),
        preferred_name: formData.get('preferred_name'),
        email: formData.get('email'),
        phone_number: formData.get('phone_number'),
        date_of_birth: formData.get('date_of_birth'),
        gender: formData.get('gender'),
        current_city: formData.get('current_city'),
        country: formData.get('country')
      },
      education: {
        highest_education_level: formData.get('highest_education_level'),
        degree_course: formData.get('degree_course'),
        specialization_branch: formData.get('specialization_branch'),
        college_university: formData.get('college_university'),
        graduation_year: formData.get('graduation_year'),
        current_education_status: formData.get('current_education_status')
      },
      career_information: {
        current_status: formData.get('current_status'),
        target_job_role: formData.get('target_job_role'),
        preferred_industry: formData.get('preferred_industry'),
        preferred_work_location: formData.get('preferred_work_location'),
        experience_level: formData.get('experience_level'),
        current_company: formData.get('current_company') || null,
        current_job_role: formData.get('current_job_role') || null
      },
      skills: {
        programming_languages: parseMultiValue(formData.get('programming_languages')),
        technical_skills: parseMultiValue(formData.get('technical_skills')),
        tools_technologies: parseMultiValue(formData.get('tools_technologies')),
        soft_skills: parseMultiValue(formData.get('soft_skills'))
      },
      career_goals: {
        short_term_career_goal: formData.get('short_term_career_goal'),
        long_term_career_goal: formData.get('long_term_career_goal'),
        target_role: formData.get('target_role'),
        target_companies: parseMultiValue(formData.get('target_companies')),
        areas_to_improve: parseMultiValue(formData.get('areas_to_improve')),
        preferred_learning_style: Array.from(document.querySelectorAll('input[name="preferred_learning_style"]:checked')).map((item) => item.value)
      },
      resume_information: {
        uploaded: !!resumeInput.files[0] && !skipResumeCheckbox.checked,
        file_name: resumeInput.files[0] ? resumeInput.files[0].name : null,
        file_type: resumeInput.files[0] ? resumeInput.files[0].type || 'application/octet-stream' : null,
        file_size_bytes: resumeInput.files[0] ? resumeInput.files[0].size : null,
        processed: false,
        storage_path: null
      }
    };

    return data;
  }

  function parseMultiValue(value) {
    if (!value) return [];
    return String(value)
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);
  }

  function validateEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  function handleNext() {
    if (!validateStep()) {
      return;
    }

    if (currentStep === 0) {
      const emailField = document.getElementById('email');
      if (!validateEmail(emailField.value.trim())) {
        emailField.setAttribute('aria-invalid', 'true');
        emailField.style.borderColor = 'var(--danger)';
        return;
      }
    }

    currentStep = Math.min(currentStep + 1, steps.length - 1);
    showStep(currentStep);
  }

  nextBtn.addEventListener('click', handleNext);

  backBtn.addEventListener('click', () => {
    currentStep = Math.max(currentStep - 1, 0);
    showStep(currentStep);
  });

  skipResumeCheckbox.addEventListener('change', () => {
    resumeInput.disabled = skipResumeCheckbox.checked;
    if (skipResumeCheckbox.checked) {
      resumeInput.value = '';
    }
  });

  form.addEventListener('submit', async (event) => {
    event.preventDefault();

    if (!validateStep()) {
      return;
    }

    const emailField = document.getElementById('email');
    if (!validateEmail(emailField.value.trim())) {
      emailField.setAttribute('aria-invalid', 'true');
      emailField.style.borderColor = 'var(--danger)';
      return;
    }

    const payload = collectFormData();

    const formData = new FormData();
    formData.append('profile', JSON.stringify(payload));

    if (resumeInput.files[0] && !skipResumeCheckbox.checked) {
      formData.append('resume', resumeInput.files[0]);
    }

    try {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Submitting...';

      const response = await fetch('http://localhost:8018/api/users/profile', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Profile submission failed.');
      }
      localStorage.setItem('user_id', result.user_id);
      localStorage.setItem('user_profile', JSON.stringify(payload));
      alert(`Profile saved successfully! Your user ID is: ${result.user_id}`);
      form.reset();
      currentStep = 0;
      showStep(0);
    } catch (error) {
      alert(error.message || 'An unexpected error occurred.');
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Submit Profile';
    }
  });

  showStep(currentStep);
}

const practiceSection = document.getElementById('practice-tests-section');

if (practiceSection) {
  const practiceState = {
    subjects: [],
    subject: 'Python',
    questions: [],
    currentIndex: 0,
    selectedAnswers: {},
    result: null,
  };

  const practiceElements = {
    subjectTabs: document.getElementById('subjectTabs'),
    loading: document.getElementById('practiceLoading'),
    empty: document.getElementById('practiceEmpty'),
    error: document.getElementById('practiceError'),
    quiz: document.getElementById('quizContent'),
    subjectLabel: document.getElementById('questionSubject'),
    questionCounter: document.getElementById('questionCounter'),
    questionText: document.getElementById('questionText'),
    answerOptions: document.getElementById('answerOptions'),
    prevQuestion: document.getElementById('prevQuestion'),
    nextQuestion: document.getElementById('nextQuestion'),
    submitTestBtn: document.getElementById('submitTestBtn'),
    result: document.getElementById('testResult'),
    completedTests: document.getElementById('completedTests'),
    averageScore: document.getElementById('averageScore'),
    bestScore: document.getElementById('bestScore'),
    subjectSummary: document.getElementById('subjectSummary'),
    attemptHistory: document.getElementById('attemptHistory'),
  };

  function getOrCreateUserId() {
    let userId = localStorage.getItem('user_id');
    if (!userId) {
      userId = `guest-${crypto.randomUUID()}`;
      localStorage.setItem('user_id', userId);
    }
    return userId;
  }

  function setPracticeLoading(isLoading) {
    practiceElements.loading.classList.toggle('hidden', !isLoading);
    practiceElements.empty.classList.add('hidden');
    practiceElements.error.classList.add('hidden');
    practiceElements.quiz.classList.add('hidden');
    practiceElements.result.classList.add('hidden');
  }

  function setPracticeError(message) {
    practiceElements.error.textContent = message || 'Unable to load the practice test. Try again in a moment.';
    practiceElements.error.classList.remove('hidden');
    practiceElements.loading.classList.add('hidden');
    practiceElements.empty.classList.add('hidden');
    practiceElements.quiz.classList.add('hidden');
    practiceElements.result.classList.add('hidden');
  }

  function renderSubjectTabs() {
    practiceElements.subjectTabs.innerHTML = '';

    practiceState.subjects.forEach((subject) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = subject;
      button.className = `subject-tab ${subject === practiceState.subject ? 'active' : ''}`;
      button.addEventListener('click', async () => {
        practiceState.subject = subject;
        practiceState.currentIndex = 0;
        practiceState.selectedAnswers = {};
        practiceState.result = null;
        renderSubjectTabs();
        await loadQuestionsForSubject(subject);
      });
      practiceElements.subjectTabs.appendChild(button);
    });
  }

  function renderQuestion() {
    const question = practiceState.questions[practiceState.currentIndex];
    if (!question) {
      practiceElements.quiz.classList.add('hidden');
      practiceElements.empty.classList.remove('hidden');
      return;
    }

    practiceElements.questionCounter.textContent = `Question ${practiceState.currentIndex + 1}/${practiceState.questions.length}`;
    practiceElements.subjectLabel.textContent = practiceState.subject;
    practiceElements.questionText.textContent = question.question;
    practiceElements.answerOptions.innerHTML = '';

    question.options.forEach((option, index) => {
      const optionKey = String.fromCharCode(65 + index);
      const wrapper = document.createElement('label');
      wrapper.className = `practice-option ${practiceState.selectedAnswers[practiceState.currentIndex] === optionKey ? 'selected' : ''}`;

      const input = document.createElement('input');
      input.type = 'radio';
      input.name = `question-${practiceState.currentIndex}`;
      input.value = optionKey;
      input.checked = practiceState.selectedAnswers[practiceState.currentIndex] === optionKey;
      input.addEventListener('change', () => {
        practiceState.selectedAnswers[practiceState.currentIndex] = optionKey;
        renderQuestion();
      });

      const text = document.createElement('span');
      text.textContent = `${optionKey}. ${option}`;

      wrapper.appendChild(input);
      wrapper.appendChild(text);
      practiceElements.answerOptions.appendChild(wrapper);
    });

    const isFirstQuestion = practiceState.currentIndex === 0;
    const isLastQuestion = practiceState.currentIndex === practiceState.questions.length - 1;

    practiceElements.prevQuestion.disabled = isFirstQuestion;
    practiceElements.nextQuestion.classList.toggle('hidden', isLastQuestion);
    practiceElements.submitTestBtn.classList.toggle('hidden', !isLastQuestion);
  }
  
// Chart instances for Performance Analytics
let subjectPieChartInstance = null;
let subjectBarChartInstance = null;
let progressLineChartInstance = null;

function renderPerformanceCharts(data) {
  if (typeof Chart === 'undefined') {
    console.error('Chart.js is not loaded.');
    return;
  }

  const summary = data.subject_summary || {};
  const history = Array.isArray(data.history) ? data.history : [];

  // 1. Count attempts for each subject
  const subjectCounts = {};

  history.forEach(attempt => {
    const subject = attempt.subject || 'Other';
    subjectCounts[subject] = (subjectCounts[subject] || 0) + 1;
  });

  // 2. Calculate subject-wise average scores
  const subjects = Object.keys(summary);

  const averageScores = subjects.map(subject =>
    Number(summary[subject].average_score || 0)
  );

  // Destroy previous charts before refreshing
  if (subjectPieChartInstance) subjectPieChartInstance.destroy();
  if (subjectBarChartInstance) subjectBarChartInstance.destroy();
  if (progressLineChartInstance) progressLineChartInstance.destroy();

  // PIE CHART: Subject-wise test attempts
  const pieCanvas = document.getElementById('subjectPieChart');

  if (pieCanvas) {
    subjectPieChartInstance = new Chart(pieCanvas, {
      type: 'pie',
      data: {
        labels: Object.keys(subjectCounts),
        datasets: [{
          data: Object.values(subjectCounts)
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom'
          },
          title: {
            display: true,
            text: 'Test Attempts by Subject'
          }
        }
      }
    });
  }

  // BAR CHART: Average score by subject
  const barCanvas = document.getElementById('subjectBarChart');

  if (barCanvas) {
    subjectBarChartInstance = new Chart(barCanvas, {
      type: 'bar',
      data: {
        labels: subjects,
        datasets: [{
          label: 'Average Score (%)',
          data: averageScores,
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 100
          }
        }
      }
    });
  }

  // LINE CHART: Score improvement across attempts
  const lineCanvas = document.getElementById('progressLineChart');

  if (lineCanvas) {
    const orderedHistory = history.slice();

    if (orderedHistory.length > 0 &&
        orderedHistory.every(a => a.submitted_at)) {
      orderedHistory.sort(
        (a, b) => new Date(a.submitted_at) - new Date(b.submitted_at)
      );
    }

    const attemptLabels = orderedHistory.map((attempt, index) =>
      attempt.submitted_at
        ? new Date(attempt.submitted_at).toLocaleDateString()
        : `Attempt ${index + 1}`
    );

    const scores = orderedHistory.map(attempt =>
      Number(attempt.percentage || 0)
    );

    progressLineChartInstance = new Chart(lineCanvas, {
      type: 'line',
      data: {
        labels: attemptLabels,
        datasets: [{
          label: 'Test Score (%)',
          data: scores,
          tension: 0.3,
          fill: false,
          borderWidth: 3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            max: 100
          }
        }
      }
    });
  }
}


  async function fetchPerformance() {
    const userId = getOrCreateUserId();

    try {
      const response = await fetch(`http://127.0.0.1:8018/api/tests/performance/${encodeURIComponent(userId)}`);
      if (!response.ok) {
        throw new Error('Unable to load performance data.');
      }

      const data = await response.json();
      practiceElements.completedTests.textContent = String(data.completed_tests || 0);
      practiceElements.averageScore.textContent = `${data.average_score || 0}%`;
      practiceElements.bestScore.textContent = `${data.best_score || 0}%`;

      const summaryItems = Object.entries(data.subject_summary || {});
      practiceElements.subjectSummary.innerHTML = '';

      if (summaryItems.length === 0) {
        practiceElements.subjectSummary.innerHTML = '<div class="summary-item"><span>No subject attempts yet.</span></div>';
      } else {
        summaryItems.forEach(([subject, stats]) => {
          const row = document.createElement('div');
          row.className = 'summary-item';
          row.innerHTML = `<span>${subject}</span><strong>${stats.average_score || 0}%</strong>`;
          practiceElements.subjectSummary.appendChild(row);
        });
      }
      renderPerformanceCharts(data);

      const attempts = Array.isArray(data.history) ? data.history.slice().reverse() : [];
      practiceElements.attemptHistory.innerHTML = '';

      if (attempts.length === 0) {
        practiceElements.attemptHistory.innerHTML = '<div class="history-item"><span>No previous attempts yet.</span></div>';
        return;
      }

      attempts.slice(0, 5).forEach((attempt) => {
        const item = document.createElement('div');
        item.className = 'history-item';
        const submittedAt = attempt.submitted_at ? new Date(attempt.submitted_at).toLocaleString() : 'Recent';
        item.innerHTML = `
          <strong>${attempt.subject} — ${attempt.score}/${attempt.total_questions}</strong>
          <span>${attempt.percentage}%</span>
          <small>${submittedAt}</small>
        `;
        practiceElements.attemptHistory.appendChild(item);
      });
    } catch (error) {
      console.error('Performance tracker error:', error);
    }
  }

  async function loadQuestionsForSubject(subject) {
    setPracticeLoading(true);

    try {
      const response = await fetch(`http://127.0.0.1:8018/api/tests/questions?subject=${encodeURIComponent(subject)}`);
      if (!response.ok) {
        throw new Error('Failed to load test data.');
      }

      const data = await response.json();
      practiceState.questions = data.questions || [];
      practiceState.currentIndex = 0;
      practiceState.selectedAnswers = {};
      practiceState.result = null;

      if (!practiceState.questions.length) {
        practiceElements.empty.classList.remove('hidden');
        practiceElements.quiz.classList.add('hidden');
        practiceElements.result.classList.add('hidden');
        return;
      }

      practiceElements.empty.classList.add('hidden');
      practiceElements.quiz.classList.remove('hidden');
      practiceElements.result.classList.add('hidden');
      renderQuestion();
    } catch (error) {
      console.error('Load questions error:', error);
      setPracticeError('Unable to load the test bank for this subject.');
    } finally {
      practiceElements.loading.classList.add('hidden');
    }
  }

  async function loadPracticeData() {
    try {
      const response = await fetch('http://127.0.0.1:8018/api/tests/questions');
      if (!response.ok) {
        throw new Error('Practice tests are unavailable.');
      }

      const data = await response.json();
      practiceState.subjects = data.subjects || Object.keys(data.questions || {});
      if (!practiceState.subjects.length) {
        practiceElements.empty.classList.remove('hidden');
        return;
      }

      renderSubjectTabs();
      await loadQuestionsForSubject(practiceState.subject);
      await fetchPerformance();
    } catch (error) {
      console.error('Practice data error:', error);
      setPracticeError(error.message || 'The practice test area could not be loaded.');
    }
  }

  practiceElements.prevQuestion.addEventListener('click', () => {
    if (practiceState.currentIndex > 0) {
      practiceState.currentIndex -= 1;
      renderQuestion();
    }
  });

  practiceElements.nextQuestion.addEventListener('click', () => {
    if (practiceState.currentIndex < practiceState.questions.length - 1) {
      practiceState.currentIndex += 1;
      renderQuestion();
    }
  });

  practiceElements.submitTestBtn.addEventListener('click', async () => {
    const answers = practiceState.questions.map((_, index) => practiceState.selectedAnswers[index] || '');
    if (answers.some((answer) => !answer)) {
      alert('Please answer every question before submitting the test.');
      return;
    }

    const userId = getOrCreateUserId();
    practiceElements.submitTestBtn.disabled = true;
    practiceElements.submitTestBtn.textContent = 'Submitting...';

    try {
      const response = await fetch('http://127.0.0.1:8018/api/tests/submit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          subject: practiceState.subject,
          answers,
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Your test could not be submitted.');
      }

      practiceState.result = data;
      practiceElements.quiz.classList.add('hidden');
      practiceElements.result.classList.remove('hidden');
      practiceElements.result.innerHTML = `
        <h4>Test Complete</h4>
        <div class="result-score">${data.percentage}%</div>
        <div><strong>${data.score}/${data.total_questions}</strong> correct</div>
        <div class="review-list">
          ${data.review.map((item) => `
            <div class="review-item ${item.is_correct ? 'correct' : 'incorrect'}">
              <strong>${item.question}</strong>
              <div>Your answer: ${item.selected_value || item.selected_answer || 'No answer'}</div>
              <div>${item.is_correct ? 'Correct.' : `Correct answer: ${item.correct_answer}`}</div>
              <small>${item.explanation}</small>
            </div>
          `).join('')}
        </div>
      `;

      await fetchPerformance();
    } catch (error) {
      console.error('Submit test error:', error);
      alert(error.message || 'The test could not be submitted.');
    } finally {
      practiceElements.submitTestBtn.disabled = false;
      practiceElements.submitTestBtn.textContent = 'Submit Test';
    }
  });

  loadPracticeData();
}

const chatToggle = document.getElementById("chat-toggle");
const chatWindow = document.getElementById("chat-window");
const chatClose = document.getElementById("chat-close");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");


function getCurrentUserId() {
  let userId = localStorage.getItem('user_id');

  if (!userId) {
    userId = `guest-${crypto.randomUUID()}`;
    localStorage.setItem('user_id', userId);
  }

  return userId;
}

async function hydrateChatThread(messagesRoot) {
  const userId = getCurrentUserId();

  try {
    const response = await fetch(
      `http://127.0.0.1:8018/api/chat/${encodeURIComponent(userId)}`
    );

    if (!response.ok) return;

    const data = await response.json();
    messagesRoot.innerHTML = '';

    const history = data.history || [];

    if (history.length === 0) {
      const welcome = document.createElement('div');
      welcome.className = 'bot-message';
      welcome.textContent = 'Hi! I\'m your AI Tutor. Ask me anything you want to learn.';
      messagesRoot.appendChild(welcome);
      return;
    }

    history.forEach((item) => {
      const userMessage = document.createElement('div');
      userMessage.className = 'user-message';
      userMessage.textContent = item.message;
      messagesRoot.appendChild(userMessage);

      const botMessage = document.createElement('div');
      botMessage.className = 'bot-message';
      botMessage.textContent = item.reply;
      messagesRoot.appendChild(botMessage);
    });

    messagesRoot.scrollTop = messagesRoot.scrollHeight;
  } catch (error) {
    console.error('Could not load chat history:', error);
  }
}

if (chatToggle && chatWindow && chatClose && chatForm) {
  chatToggle.setAttribute('aria-expanded', 'false');
  chatWindow.setAttribute('aria-hidden', 'true');

  chatToggle.addEventListener('click', function () {
    chatWindow.hidden = false;
    chatWindow.setAttribute('aria-hidden', 'false');
    chatToggle.setAttribute('aria-expanded', 'true');
    chatToggle.style.display = 'none';
    chatInput.focus();
  });

  chatClose.addEventListener('click', function () {
    chatWindow.hidden = true;
    chatWindow.setAttribute('aria-hidden', 'true');
    chatToggle.setAttribute('aria-expanded', 'false');
    chatToggle.style.display = '';
  });

  hydrateChatThread(chatMessages);

  chatForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const message = chatInput.value.trim();
    if (!message) return;

    const userMessage = document.createElement('div');
    userMessage.className = 'user-message';
    userMessage.textContent = message;
    chatMessages.appendChild(userMessage);

    chatInput.value = '';
    chatInput.disabled = true;

    const loadingMessage = document.createElement('div');
    loadingMessage.className = 'bot-message';
    loadingMessage.textContent = 'Thinking...';
    chatMessages.appendChild(loadingMessage);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    try {
      const userId = getCurrentUserId();
      const response = await fetch('http://127.0.0.1:8018/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          message,
          user_id: userId
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        loadingMessage.textContent = errorData.detail || 'Sorry, something went wrong.';
        return;
      }

      const data = await response.json();
      loadingMessage.textContent = data.reply || 'I received an empty response.';
    } catch (error) {
      loadingMessage.textContent = 'Could not connect to the AI Tutor. Please check that the backend is running.';
      console.error('Chatbot error:', error);
    } finally {
      chatInput.disabled = false;
      chatInput.focus();
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }
  });
}

const aiChatForm = document.getElementById('ai-chat-form');
const aiChatInput = document.getElementById('ai-chat-input');
const aiChatMessages = document.getElementById('ai-chat-messages');


let activePdfText = '';

const tutorPdfInput = document.getElementById('tutor-pdf');
const tutorPdfUploadButton = document.getElementById('upload-tutor-pdf');
const tutorPdfStatus = document.getElementById('tutor-pdf-status');
const tutorPdfRemoveButton = document.getElementById('remove-tutor-pdf');

if (tutorPdfInput && tutorPdfUploadButton && tutorPdfStatus) {
  tutorPdfUploadButton.addEventListener('click', async () => {
    const file = tutorPdfInput.files[0];

    if (!file) {
      tutorPdfStatus.textContent = 'Choose a PDF first.';
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    tutorPdfUploadButton.disabled = true;
    tutorPdfStatus.textContent = 'Reading PDF...';

    try {
      const response = await fetch(
        'http://127.0.0.1:8018/api/tutor/upload-pdf',
        { method: 'POST', body: formData }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'PDF upload failed.');
      }

      activePdfText = data.text;
      tutorPdfStatus.textContent =
        `Ready: ${data.filename}` +
        (data.truncated ? ' (first 30,000 characters)' : '');

      if (tutorPdfRemoveButton) {
        tutorPdfRemoveButton.hidden = false;
      }
    } catch (error) {
      activePdfText = '';
      tutorPdfStatus.textContent = error.message;
    } finally {
      tutorPdfUploadButton.disabled = false;
    }
  });
}

if (tutorPdfRemoveButton) {
  tutorPdfRemoveButton.addEventListener('click', () => {
    activePdfText = '';
    if (tutorPdfInput) tutorPdfInput.value = '';
    if (tutorPdfStatus) tutorPdfStatus.textContent = 'PDF removed.';
    tutorPdfRemoveButton.hidden = true;
  });
}


if (aiChatForm && aiChatInput && aiChatMessages) {
  hydrateChatThread(aiChatMessages);

  aiChatForm.addEventListener('submit', async (event) => {
    event.preventDefault();

    const message = aiChatInput.value.trim();
    if (!message) return;

    const userMessage = document.createElement('div');
    userMessage.className = 'user-message';
    userMessage.textContent = message;
    aiChatMessages.appendChild(userMessage);

    aiChatInput.value = '';
    aiChatInput.disabled = true;

    const loadingMessage = document.createElement('div');
    loadingMessage.className = 'bot-message';
    loadingMessage.textContent = 'Thinking...';
    aiChatMessages.appendChild(loadingMessage);
    aiChatMessages.scrollTop = aiChatMessages.scrollHeight;

    try {
      const response = await fetch('http://127.0.0.1:8018/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
       body: JSON.stringify({
  message,
  user_id: getCurrentUserId(),
  document_context: activePdfText || null
})
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        loadingMessage.textContent = errorData.detail || 'Sorry, something went wrong.';
        return;
      }

      const data = await response.json();
      loadingMessage.textContent = data.reply || 'I received an empty response.';
    } catch (error) {
      loadingMessage.textContent = 'The AI Tutor is temporarily unavailable. Please try again in a moment.';
      console.error('Dedicated tutor chat error:', error);
    } finally {
      aiChatInput.disabled = false;
      aiChatInput.focus();
      aiChatMessages.scrollTop = aiChatMessages.scrollHeight;
    }
  });
}
