function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}
function showToast(message, isError = false) {
  const toast = document.createElement('div');
  toast.textContent = message;
  toast.className = `px-4 py-2 rounded-lg shadow-lg text-white text-sm ${isError ? 'bg-rose-600' : 'bg-emerald-600'}`;
  document.getElementById('toast-region').appendChild(toast);
  setTimeout(() => toast.remove(), 2500);
}

function badgeClass(type, value) {
  const map = {
    status: { 'Done': 'bg-emerald-100 text-emerald-700', 'In Progress': 'bg-blue-100 text-blue-700', 'Review': 'bg-amber-100 text-amber-700' },
    priority: { 'High': 'bg-rose-100 text-rose-700', 'Medium': 'bg-amber-100 text-amber-700', 'Low': 'bg-emerald-100 text-emerald-700' }
  };
  return (map[type] && map[type][value]) || 'bg-gray-100 text-gray-600';
}

function openTaskDrawer(taskId) {
  document.getElementById('taskDrawerOverlay').classList.remove('hidden');
  document.getElementById('taskDrawer').classList.remove('hidden');
  document.getElementById('taskDrawerBody').innerHTML = '<p class="text-sm text-gray-400 text-center py-10">Loading...</p>';

  fetch(`/tasks/api/task/${taskId}/detail/`)
    .then(res => res.json())
    .then(data => {
      if (data.error) { showToast(data.error, true); closeTaskDrawer(); return; }
      renderDrawer(taskId, data);
    })
    .catch(() => showToast('Could not load task details', true));
}

function closeTaskDrawer() {
  document.getElementById('taskDrawerOverlay').classList.add('hidden');
  document.getElementById('taskDrawer').classList.add('hidden');
}

function initials(name) { return name ? name.charAt(0).toUpperCase() : '?'; }
function avatarColor(name) {
  const palette = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#0ea5e9', '#ef4444', '#14b8a6'];
  let sum = 0;
  for (const c of (name || '')) sum += c.charCodeAt(0);
  return palette[sum % palette.length];
}
function avatarHtml(name, size = 9) {
  return `<span class="w-${size} h-${size} rounded-full text-white text-xs flex items-center justify-center font-semibold flex-shrink-0" style="background-color:${avatarColor(name)}">${initials(name)}</span>`;
}

function renderDrawer(taskId, t) {
  let html = `
    <p class="text-xs font-bold text-gray-400 mb-1">T-${String(taskId).padStart(3, '0')}</p>
    <div class="flex items-center justify-between mb-2">
      <h2 class="text-xl font-bold text-gray-800">${t.title}</h2>
    </div>
    <div class="flex gap-2 mb-4">
      <span class="text-xs font-semibold px-2 py-1 rounded-full ${badgeClass('status', t.status)}">${t.status}</span>
      <span class="text-xs font-semibold px-2 py-1 rounded-full ${badgeClass('priority', t.priority)}">${t.priority}</span>
    </div>

    <div class="grid grid-cols-2 gap-4 text-sm mb-5 pb-5 border-b border-gray-100">
      <div>
        <p class="text-[10px] font-bold text-gray-400 uppercase mb-1">Assigned To</p>
        <div class="flex items-center gap-2">${avatarHtml(t.assigned_to, 8)}<span class="font-semibold text-gray-800">${t.assigned_to}</span></div>
      </div>
      <div>
        <p class="text-[10px] font-bold text-gray-400 uppercase mb-1">Created By</p>
        <div class="flex items-center gap-2">${avatarHtml(t.created_by, 8)}<span class="font-semibold text-gray-800">${t.created_by}</span></div>
      </div>
      <div><p class="text-[10px] font-bold text-gray-400 uppercase">Department</p><p class="font-semibold text-gray-800">${t.department || '—'}</p></div>
      <div><p class="text-[10px] font-bold text-gray-400 uppercase">Due Date</p><p class="font-semibold text-gray-800">${t.due_date || '—'}</p></div>
      <div><p class="text-[10px] font-bold text-gray-400 uppercase">Milestone</p><p class="font-semibold text-gray-800">${t.milestone || '—'}</p></div>
      <div><p class="text-[10px] font-bold text-gray-400 uppercase">Manager</p><p class="font-semibold text-gray-800">${t.manager ? t.manager.username : '—'}</p></div>
    </div>

    <div class="mb-5 pb-5 border-b border-gray-100">
      <p class="text-sm font-semibold text-gray-700 mb-2">Description</p>
      <div class="bg-gray-50 rounded-lg p-3 text-sm text-gray-600">${t.description || 'No description provided.'}</div>
    </div>`;

  if (t.attachment_url || t.reference_url) {
    html += `<div class="mb-5 pb-5 border-b border-gray-100">
      <p class="text-sm font-semibold text-gray-700 mb-2">Attachments</p>`;
    if (t.attachment_url) {
      html += `<div class="flex items-center gap-3 bg-gray-50 border border-gray-100 rounded-xl p-3 mb-2">
        <div class="w-9 h-9 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0"><i class="fas fa-file-alt text-indigo-500"></i></div>
        <div class="min-w-0 flex-1"><p class="text-sm font-medium text-gray-800 truncate">${t.attachment_name}</p></div>
        <a href="${t.attachment_url}" target="_blank" class="text-indigo-500 hover:text-indigo-700"><i class="fas fa-download"></i></a>
      </div>`;
    }
    if (t.reference_url) {
      html += `<div class="flex items-center gap-3 bg-gray-50 border border-gray-100 rounded-xl p-3">
        <div class="w-9 h-9 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0"><i class="fas fa-link text-indigo-500"></i></div>
        <div class="min-w-0 flex-1"><p class="text-sm font-medium text-gray-800 truncate">${t.reference_url}</p></div>
        <a href="${t.reference_url}" target="_blank" class="text-indigo-500 hover:text-indigo-700"><i class="fas fa-arrow-up-right-from-square"></i></a>
      </div>`;
    }
    html += `</div>`;
  }

  html += `<div class="mb-5 pb-5 border-b border-gray-100">
    <div class="flex justify-between items-center mb-2">
      <p class="text-sm font-semibold text-gray-700">Team Members (${t.team_members.length + 1})</p>
    </div>
    <div class="flex items-center justify-between py-1.5">
      <div class="flex items-center gap-2">${avatarHtml(t.assigned_to, 8)}<span class="text-sm text-gray-700">${t.assigned_to}</span></div>
      <span class="text-[10px] font-bold bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">Primary</span>
    </div>`;

  t.team_members.forEach(m => {
    html += `<div class="flex items-center justify-between py-1.5">
      <div class="flex items-center gap-2">${avatarHtml(m.username, 8)}<span class="text-sm text-gray-700">${m.username}</span></div>
      ${t.can_manage ? `<button onclick="removeTeamMember(${taskId}, ${m.membership_id})" class="text-gray-400 hover:text-rose-600 text-xs"><i class="fas fa-times"></i></button>` : ''}
    </div>`;
  });

  if (t.colleagues && t.colleagues.length) {
    html += `<p class="text-[11px] text-gray-400 mt-2 mb-1">Suggested — same manager as ${t.assigned_to}:</p>`;
  }

  if (t.can_manage) {
    html += `<div class="flex gap-2 mt-3">
      <select id="addMemberSelect_${taskId}" class="border border-gray-200 rounded-lg px-2 py-1.5 text-xs flex-1 bg-white">
        <option value="">Choose colleague...</option>
        ${(t.colleagues || []).map(c => `<option value="${c['user__id']}">${c['user__username']}</option>`).join('')}
      </select>
      <button onclick="addTeamMember(${taskId})" class="text-xs font-semibold bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1.5 rounded-lg transition">
        <i class="fas fa-plus mr-1"></i>Add
      </button>
    </div>`;
  }
  html += `</div>
    <p class="text-[10px] text-gray-400">Created ${t.created_at} · Updated ${t.updated_at}</p>`;

  document.getElementById('taskDrawerBody').innerHTML = html;
}

function addTeamMember(taskId) {
  const select = document.getElementById(`addMemberSelect_${taskId}`);
  const userId = select ? select.value : null;
  if (!userId) { showToast('Choose a colleague first', true); return; }
  fetch(`/tasks/api/task/${taskId}/team/add/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
    body: JSON.stringify({ user_id: userId }),
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) { showToast(data.error, true); return; }
    showToast('Team member added');
    openTaskDrawer(taskId);
  });
}

function removeTeamMember(taskId, membershipId) {
  if (!confirm('Remove this person from the task?')) return;
  fetch(`/tasks/api/task/${taskId}/team/${membershipId}/remove/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': getCookie('csrftoken') },
  })
  .then(res => res.json())
  .then(data => {
    if (data.error) { showToast(data.error, true); return; }
    showToast('Team member removed');
    openTaskDrawer(taskId);
  });
}