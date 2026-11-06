const plannerForm = document.getElementById('studyPlannerForm');
const studyTaskList = document.getElementById('studyTaskList');
const plannerProgressFill = document.getElementById('plannerProgressFill');
const plannerCompletionText = document.getElementById('plannerCompletionText');

async function renderStudyPlanner() {
  const userId = getCurrentUserId();
  try {
    const data = await apiFetch(`${API_BASE}/api/study-planner/${encodeURIComponent(userId)}`);
    const tasks = data.tasks || [];
    const percent = data.completion_percent || 0;
    plannerProgressFill.style.width = `${percent}%`;
    plannerCompletionText.textContent = `${percent}% complete (${data.completed_count || 0}/${data.total_tasks || 0})`;

    if (!tasks.length) {
      studyTaskList.innerHTML = '<div class="empty-state">No tasks yet. Add your first study session.</div>';
      return;
    }

    studyTaskList.innerHTML = tasks.map((task) => `
      <div class="task-item ${task.completed ? 'done' : ''}">
        <label class="task-check">
          <input type="checkbox" data-task-id="${task.task_id}" ${task.completed ? 'checked' : ''} />
          <span>${task.title}</span>
        </label>
        <div class="task-meta">
          <span class="priority-pill ${(task.priority || 'medium').toLowerCase()}">${task.priority || 'Medium'}</span>
          ${task.deadline ? `<small>${task.deadline}</small>` : ''}
          <button type="button" class="delete-task" data-task-id="${task.task_id}">Delete</button>
        </div>
      </div>
    `).join('');

    studyTaskList.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
      checkbox.addEventListener('change', async (event) => {
        const taskId = event.target.dataset.taskId;
        const completed = event.target.checked;
        try {
          await apiFetch(`${API_BASE}/api/study-planner/${encodeURIComponent(userId)}/${encodeURIComponent(taskId)}`, {
            method: 'PATCH',
            body: JSON.stringify({ completed }),
          });
          await renderStudyPlanner();
        } catch (error) {
          console.error(error);
          alert(error.message || 'Unable to update task.');
        }
      });
    });

    studyTaskList.querySelectorAll('.delete-task').forEach((button) => {
      button.addEventListener('click', async () => {
        try {
          await apiFetch(`${API_BASE}/api/study-planner/${encodeURIComponent(userId)}/${encodeURIComponent(button.dataset.taskId)}`, {
            method: 'DELETE',
          });
          await renderStudyPlanner();
        } catch (error) {
          console.error(error);
          alert(error.message || 'Unable to delete task.');
        }
      });
    });
  } catch (error) {
    studyTaskList.innerHTML = `<div class="empty-state">${error.message || 'Unable to load planner.'}</div>`;
  }
}

if (plannerForm) {
  plannerForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const userId = getCurrentUserId();
    const title = document.getElementById('studyTaskTitle').value.trim();
    const deadline = document.getElementById('studyTaskDeadline').value;
    const priority = document.getElementById('studyTaskPriority').value;

    if (!title) return;

    try {
      await apiFetch(`${API_BASE}/api/study-planner/${encodeURIComponent(userId)}`, {
        method: 'POST',
        body: JSON.stringify({
          task_id: `task-${Date.now()}`,
          title,
          deadline,
          priority,
          completed: false,
        }),
      });
      plannerForm.reset();
      document.getElementById('studyTaskPriority').value = 'Medium';
      await renderStudyPlanner();
    } catch (error) {
      alert(error.message || 'Unable to save study task.');
    }
  });
}

renderStudyPlanner();
