function getCurrentUserId() {
  let userId = localStorage.getItem('user_id');
  if (!userId) {
    userId = `guest-${crypto.randomUUID()}`;
    localStorage.setItem('user_id', userId);
  }
  return userId;
}

async function apiFetch(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = data.detail;
    const message = Array.isArray(detail)
      ? detail.map((item) => item.msg || item).join(' ')
      : (detail || data.message || 'Request failed.');
    throw new Error(message);
  }
  return data;
}

const API_BASE = 'http://127.0.0.1:8018';
