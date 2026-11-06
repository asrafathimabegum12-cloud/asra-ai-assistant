const DEFAULT_QUIZ_OPTIONS = ['A', 'B', 'C', 'D'];
const quizButton = document.getElementById('loadQuizBtn');

async function loadTechnicalQuiz() {
  const userId = getCurrentUserId();
  const subject = document.getElementById('quizSubjectSelect').value;
  const container = document.getElementById('quizQuestionBlock');
  const resultBlock = document.getElementById('quizResultBlock');

  container.classList.remove('hidden');
  resultBlock.classList.add('hidden');
  container.innerHTML = '<div class="empty-state">Loading quiz...</div>';

  try {
    const data = await apiFetch(`${API_BASE}/api/technical-quiz/questions?subject=${encodeURIComponent(subject)}`);
    const questions = data.questions || [];
    if (!questions.length) {
      container.innerHTML = '<div class="empty-state">No questions available for this subject.</div>';
      return;
    }

    let currentIndex = 0;
    const selectedAnswers = {};

    function renderQuestion() {
      const question = questions[currentIndex];
      if (!question) return;
      const answerButtons = question.options.map((option, index) => `
        <label class="option-pill ${selectedAnswers[currentIndex] === DEFAULT_QUIZ_OPTIONS[index] ? 'selected' : ''}">
          <input type="radio" name="q-${currentIndex}" value="${DEFAULT_QUIZ_OPTIONS[index]}" ${selectedAnswers[currentIndex] === DEFAULT_QUIZ_OPTIONS[index] ? 'checked' : ''} />
          <span>${DEFAULT_QUIZ_OPTIONS[index]}. ${option}</span>
        </label>
      `).join('');

      container.innerHTML = `
        <div class="quiz-card">
          <div class="question-topline">
            <strong>${subject}</strong>
            <span>Q${currentIndex + 1}/${questions.length}</span>
          </div>
          <h4>${question.question}</h4>
          <div class="option-list">${answerButtons}</div>
          <div class="quiz-actions-inline">
            <button class="btn btn-secondary" type="button" ${currentIndex === 0 ? 'disabled' : ''} data-action="prev">Previous</button>
            <button class="btn btn-primary" type="button" ${currentIndex === questions.length - 1 ? 'hidden' : ''} data-action="next">Next</button>
            <button class="btn btn-primary" type="button" ${currentIndex !== questions.length - 1 ? 'hidden' : ''} data-action="submit">Submit</button>
          </div>
        </div>
      `;

      container.querySelectorAll('input[type="radio"]').forEach((input) => {
        input.addEventListener('change', (event) => {
          selectedAnswers[currentIndex] = event.target.value;
          renderQuestion();
        });
      });

      container.querySelectorAll('[data-action]').forEach((button) => {
        button.addEventListener('click', async () => {
          const action = button.dataset.action;
          if (action === 'prev') currentIndex = Math.max(0, currentIndex - 1);
          if (action === 'next') currentIndex = Math.min(questions.length - 1, currentIndex + 1);
          if (action === 'submit') {
            const answers = questions.map((_, idx) => selectedAnswers[idx] || '');
            if (answers.some((answer) => !answer)) {
              resultBlock.innerHTML = '<div class="empty-state">Please answer every question before submitting.</div>';
              resultBlock.classList.remove('hidden');
              return;
            }

            try {
              const response = await apiFetch(`${API_BASE}/api/technical-quiz/submit`, {
                method: 'POST',
                body: JSON.stringify({ user_id: userId, subject, answers }),
              });

              resultBlock.classList.remove('hidden');
              resultBlock.innerHTML = `
                <div class="score-box">
                  <strong>${response.percentage}%</strong>
                  <span>${response.score}/${response.total_questions} correct</span>
                </div>
                ${(response.review || []).map((item) => `
                  <div class="review-item ${item.is_correct ? 'correct' : 'incorrect'}">
                    <strong>${item.question}</strong>
                    <div>Your answer: ${item.selected_value || item.selected_answer || 'No answer'}</div>
                    <div>${item.is_correct ? 'Correct.' : `Correct answer: ${item.correct_answer}`}</div>
                    <small>${item.explanation || ''}</small>
                  </div>
                `).join('')}
              `;
            } catch (error) {
              resultBlock.classList.remove('hidden');
              resultBlock.innerHTML = `<div class="empty-state">${error.message || 'Quiz submission failed.'}</div>`;
            }
            return;
          }
          renderQuestion();
        });
      });
    }

    renderQuestion();
  } catch (error) {
    container.innerHTML = `<div class="empty-state">${error.message || 'Unable to load questions.'}</div>`;
  }
}

if (quizButton) {
  quizButton.addEventListener('click', loadTechnicalQuiz);
}
