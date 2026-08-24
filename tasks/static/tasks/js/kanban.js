function dragTask(event) {
  event.dataTransfer.setData('taskId', event.currentTarget.dataset.taskId);
}

function allowDrop(event) {
  event.preventDefault();
}

function dropTask(event) {
  event.preventDefault();

  const taskId = event.dataTransfer.getData('taskId');
  const card = document.querySelector(`[data-task-id="${taskId}"]`);
  const targetColumn = event.currentTarget.closest('.kanban-column');
  const newStatus = targetColumn.dataset.status;
  const previousParent = card.parentElement;

  // Move card immediately in the UI
  event.currentTarget.appendChild(card);

  fetch(`/tasks/api/task/${taskId}/update-status/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({ status: newStatus }),
  })
    .then(res => {
      if (!res.ok) {
        throw new Error('Update failed');
      }

      return res.json();
    })
    .then(() => {
      // Quiet success confirmation
      showToast('Task status updated');
    })
    .catch(() => {
      // Move card back if server update failed
      previousParent.appendChild(card);

      showToast('Could not update task status', true);
    });
}


// Toast notification
function showToast(message, isError = false) {
  const toast = document.createElement('div');

  toast.textContent = message;

  toast.className = `fixed bottom-4 right-4 px-4 py-2 rounded-lg shadow-lg text-white text-sm z-50 ${
    isError ? 'bg-rose-600' : 'bg-emerald-600'
  }`;

  document.body.appendChild(toast);

  setTimeout(() => toast.remove(), 2500);
}


function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);

  if (parts.length === 2) {
    return parts.pop().split(';').shift();
  }
}


// Search and priority filters
document.getElementById('searchInput')?.addEventListener('input', filterTasks);
document.getElementById('priorityFilter')?.addEventListener('change', filterTasks);

function filterTasks() {
  const search = document.getElementById('searchInput').value.toLowerCase();
  const priority = document.getElementById('priorityFilter').value;

  document.querySelectorAll('.task-card').forEach(card => {
    const matchesSearch = card.dataset.title.includes(search);
    const matchesPriority =
      !priority || card.dataset.priority === priority;

    card.style.display =
      (matchesSearch && matchesPriority) ? '' : 'none';
  });
}

function openQuickAdd() { document.getElementById('quickAddModal').classList.remove('hidden'); }
function closeQuickAdd() { document.getElementById('quickAddModal').classList.add('hidden'); }

function submitQuickAdd() {
  const title = document.getElementById('quickTaskTitle').value.trim();
  const priority = document.getElementById('quickTaskPriority').value;
  if (!title) return;

  fetch('/tasks/api/task/quick-create/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
    body: JSON.stringify({ title, priority }),
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) { showToast(data.error, true); return; }
    location.reload(); // simplest reliable way to show the new card in the right column
  })
  .catch(() => showToast('Could not create task', true));
}