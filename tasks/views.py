import json
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Task, Milestone
from .forms import TaskForm, MilestoneForm


# ---------------------------------------------------------------
# Permission helpers — kept in one place so every view stays consistent
# ---------------------------------------------------------------

def _is_manager(user):
    """True if this user's profile role is 'manager'."""
    return hasattr(user, 'profile') and user.profile.role == 'manager'


def _visible_team_users(user):
    """
    Returns the queryset of users whose tasks this person is allowed to see.
    - Admin (superuser): everyone
    - Manager: themself + employees assigned to them
    - Employee: just themself
    """
    if user.is_superuser:
        return User.objects.all()
    if _is_manager(user):
        return User.objects.filter(Q(id=user.id) | Q(profile__manager=user)).distinct()
    return User.objects.filter(id=user.id)


def _can_manage_task(user, task):
    """True if this user may create/edit/delete the given task."""
    if user.is_superuser:
        return True
    if _is_manager(user) and task.assigned_to and hasattr(task.assigned_to, 'profile'):
        return task.assigned_to.profile.manager_id == user.id
    return False


# ---------------------------------------------------------------
# Page views
# ---------------------------------------------------------------

@login_required
def dashboard(request):
    user = request.user
    team_users = _visible_team_users(user)
    my_tasks = Task.objects.filter(assigned_to__in=team_users)

    total = my_tasks.count()
    done = my_tasks.filter(status='Done').count()
    percent_complete = round((done / total) * 100) if total else 0

    member_stats = []
    for u in team_users:
        user_total = u.tasks.count()
        user_done = u.tasks.filter(status='Done').count()
        member_stats.append({
            'user': u,
            'percent': round((user_done / user_total) * 100) if user_total else 0,
            'total': user_total,
            'done': user_done,
        })

    context = {
        'milestones': Milestone.objects.all(),
        'percent_complete': percent_complete,
        'total_tasks': total,
        'done_tasks': done,
        'member_stats': member_stats,
        'can_manage': user.is_superuser or _is_manager(user),
    }
    return render(request, 'tasks/dashboard.html', context)


@login_required
def kanban_board(request):
    today = timezone.now().date()
    team_users = _visible_team_users(request.user)
    tasks = Task.objects.select_related('assigned_to', 'milestone').filter(assigned_to__in=team_users)

    board = {
        'Backlog': tasks.filter(status='Backlog'),
        'In Progress': tasks.filter(status='In Progress'),
        'Review': tasks.filter(status='Review'),
        'Done': tasks.filter(status='Done'),
    }
    can_manage = request.user.is_superuser or _is_manager(request.user)

    context = {
        'board': board,
        'today': today,
        'can_manage': can_manage,
        # Only managers/admin need the assignee dropdown in the quick-add modal
        'team_users': team_users if can_manage else User.objects.none(),
    }
    return render(request, 'tasks/kanban.html', context)


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    context = {
        'task': task,
        'can_manage': _can_manage_task(request.user, task),
        'can_update_status': (
            request.user.is_superuser
            or _can_manage_task(request.user, task)
            or task.assigned_to_id == request.user.id
        ),
    }
    return render(request, 'tasks/task_detail.html', context)


@login_required
def task_form_view(request, pk=None):
    task = get_object_or_404(Task, pk=pk) if pk else None

    # Creating a new task: only managers/admin may do this
    if task is None:
        if not (request.user.is_superuser or _is_manager(request.user)):
            return HttpResponseForbidden("You don't have permission to create tasks.")
    # Editing an existing task: must be admin, or the manager of the assignee
    else:
        if not _can_manage_task(request.user, task):
            return HttpResponseForbidden("You don't have permission to edit this task.")

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('tasks:kanban')
    else:
        form = TaskForm(instance=task, user=request.user)

    return render(request, 'tasks/task_form.html', {'form': form, 'task': task})


@login_required
def milestone_form_view(request):
    if not (request.user.is_superuser or _is_manager(request.user)):
        return HttpResponseForbidden("You don't have permission to create milestones.")

    if request.method == 'POST':
        form = MilestoneForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('tasks:dashboard')
    else:
        form = MilestoneForm()
    return render(request, 'tasks/milestone_form.html', {'form': form})


@login_required
@require_POST
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if not _can_manage_task(request.user, task):
        return HttpResponseForbidden("You don't have permission to delete this task.")
    task.delete()
    return redirect('tasks:kanban')


# ---------------------------------------------------------------
# API endpoints (Fetch-driven, JSON in/out)
# ---------------------------------------------------------------

@login_required
@require_POST
def update_task_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    if request.content_type == 'application/json':
        data = json.loads(request.body)
        new_status = data.get('status')
    else:
        new_status = request.POST.get('status')

    # Admin, the assignee's manager, or the assignee themself may move the card
    allowed = (
        request.user.is_superuser
        or _can_manage_task(request.user, task)
        or task.assigned_to_id == request.user.id
    )
    if not allowed:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    data = json.loads(request.body)
    new_status = data.get('status')
    if new_status not in dict(Task.STATUS_CHOICES):
        return JsonResponse({'error': 'Invalid status'}, status=400)

    task.status = new_status
    task.save(update_fields=['status', 'updated_at'])
    return JsonResponse({'success': True, 'task_id': task.id, 'status': task.status})


@login_required
@require_POST
def quick_create_task(request):
    # Only managers/admin can quick-create tasks
    if not (request.user.is_superuser or _is_manager(request.user)):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    data = json.loads(request.body)
    title = data.get('title', '').strip()
    priority = data.get('priority', 'Medium')
    assigned_to_id = data.get('assigned_to')

    if not title:
        return JsonResponse({'error': 'Title is required'}, status=400)

    # Restrict assignment to people this manager/admin can actually see
    team_users = _visible_team_users(request.user)
    if assigned_to_id:
        assigned_to = team_users.filter(id=assigned_to_id).first()
        if not assigned_to:
            return JsonResponse({'error': 'Invalid assignee'}, status=400)
    else:
        assigned_to = request.user

    task = Task.objects.create(
        title=title, priority=priority, status='Backlog', assigned_to=assigned_to
    )
    return JsonResponse({
        'success': True,
        'id': task.id,
        'title': task.title,
        'priority': task.priority,
        'assigned_to': task.assigned_to.username,
    })