function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

function addColleague(taskId) {
  const select = document.getElementById('colleagueSelect');
  const userId = select ? select.value : null;
  if (!userId) { alert('Choose a colleague first'); return; }

  fetch(`/tasks/api/task/${taskId}/team/add/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
    body: JSON.stringify({ user_id: userId }),
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) { alert(data.error); return; }
    location.reload();
  })
  .catch(() => alert('Could not add colleague.'));
}

function removeMember(taskId, membershipId) {
  if (!confirm('Remove this person from the task?')) return;
  fetch(`/tasks/api/task/${taskId}/team/${membershipId}/remove/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') },
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) { alert(data.error); return; }
    document.getElementById(`member-row-${membershipId}`).remove();
  })
  .catch(() => alert('Could not remove member.'));
}