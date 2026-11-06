const notesForm = document.getElementById('notesForm');
const notesList = document.getElementById('notesList');

async function renderNotes() {
  const userId = getCurrentUserId();
  try {
    const data = await apiFetch(`${API_BASE}/api/notes/${encodeURIComponent(userId)}`);
    const notes = data.notes || [];
    if (!notes.length) {
      notesList.innerHTML = '<div class="empty-state">No notes saved yet.</div>';
      return;
    }

    notesList.innerHTML = notes.map((note) => `
      <div class="info-card">
        <div class="info-header">
          <strong>${note.title}</strong>
          <span class="mini-badge light">${note.category}</span>
        </div>
        <p>${note.content}</p>
        <div class="inline-actions">
          <button class="btn btn-secondary small-btn" data-note-id="${note.note_id}" data-action="edit">Edit</button>
          <button class="btn btn-secondary small-btn" data-note-id="${note.note_id}" data-action="delete">Delete</button>
        </div>
      </div>
    `).join('');

    notesList.querySelectorAll('[data-action]').forEach((button) => {
      button.addEventListener('click', async () => {
        const noteId = button.dataset.noteId;
        const note = notes.find((item) => item.note_id === noteId);
        if (!note) return;
        if (button.dataset.action === 'delete') {
          try {
            await apiFetch(`${API_BASE}/api/notes/${encodeURIComponent(userId)}/${encodeURIComponent(noteId)}`, { method: 'DELETE' });
            await renderNotes();
          } catch (error) {
            alert(error.message || 'Unable to delete note.');
          }
          return;
        }

        document.getElementById('notesTitle').value = note.title;
        document.getElementById('notesCategory').value = note.category;
        document.getElementById('notesContent').value = note.content;
        notesForm.dataset.noteId = noteId;
        notesForm.querySelector('button[type="submit"]').textContent = 'Update note';
      });
    });
  } catch (error) {
    notesList.innerHTML = `<div class="empty-state">${error.message || 'Unable to load notes.'}</div>`;
  }
}

if (notesForm) {
  notesForm.addEventListener('submit', async (event) => {
    event.preventDefault();
    const userId = getCurrentUserId();
    const title = document.getElementById('notesTitle').value.trim();
    const category = document.getElementById('notesCategory').value;
    const content = document.getElementById('notesContent').value.trim();

    if (!title || !content) return;

    try {
      const noteId = notesForm.dataset.noteId || `note-${Date.now()}`;
      const method = notesForm.dataset.noteId ? 'PUT' : 'POST';
      const url = notesForm.dataset.noteId
        ? `${API_BASE}/api/notes/${encodeURIComponent(userId)}/${encodeURIComponent(noteId)}`
        : `${API_BASE}/api/notes/${encodeURIComponent(userId)}`;

      await apiFetch(url, {
        method,
        body: JSON.stringify({ note_id: noteId, title, category, content }),
      });

      notesForm.reset();
      notesForm.dataset.noteId = '';
      notesForm.querySelector('button[type="submit"]').textContent = 'Save note';
      await renderNotes();
    } catch (error) {
      alert(error.message || 'Unable to save note.');
    }
  });
}

renderNotes();
