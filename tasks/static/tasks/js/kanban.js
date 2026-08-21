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

  event.currentTarget.appendChild(card);

  fetch(`/tasks/api/task/${taskId}/update-status/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCookie('csrftoken'),
    },
    body: JSON.stringify({ status: newStatus }),
  })
  .then(res => { if (!res.ok) throw new Error('Update failed'); return res.json(); })
  .catch(() => {
    previousParent.appendChild(card);
    alert('Could not update task status. Please try again.');
  });
}
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}
document.getElementById('searchInput')?.addEventListener('input', filterTasks);
document.getElementById('priorityFilter')?.addEventListener('change', filterTasks);
function filterTasks() {
  const search = document.getElementById('searchInput').value.toLowerCase();
  const priority = document.getElementById('priorityFilter').value;
  document.querySelectorAll('.task-card').forEach(card => {
    const matchesSearch = card.dataset.title.includes(search);
    const matchesPriority = !priority || card.dataset.priority === priority;
    card.style.display = (matchesSearch && matchesPriority) ? '' : 'none';
  });
}