import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Task, Milestone
from .forms import TaskForm, MilestoneForm


@login_required
def dashboard(request):
    total = Task.objects.count()
    done = Task.objects.filter(status='Done').count()
    percent_complete = round((done / total) * 100) if total else 0

    member_stats = []
    for user in User.objects.filter(tasks__isnull=False).distinct():
        user_total = user.tasks.count()
        user_done = user.tasks.filter(status='Done').count()
        member_stats.append({
            'user': user,
            'percent': round((user_done / user_total) * 100) if user_total else 0,
            'total': user_total,
        })

    context = {
        'milestones': Milestone.objects.all(),
        'percent_complete': percent_complete,
        'member_stats': member_stats,
    }
    return render(request, 'tasks/dashboard.html', context)


@login_required
def kanban_board(request):
    tasks = Task.objects.select_related('assigned_to', 'milestone').all()
    board = {
        'Backlog': tasks.filter(status='Backlog'),
        'In Progress': tasks.filter(status='In Progress'),
        'Review': tasks.filter(status='Review'),
        'Done': tasks.filter(status='Done'),
    }
    return render(request, 'tasks/kanban.html', {'board': board})


@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    return render(request, 'tasks/task_detail.html', {'task': task})


@login_required
def task_form_view(request, pk=None):
    task = get_object_or_404(Task, pk=pk) if pk else None
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            return redirect('tasks:kanban')
    else:
        form = TaskForm(instance=task)
    return render(request, 'tasks/task_form.html', {'form': form})


@login_required
def milestone_form_view(request):
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
def update_task_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    data = json.loads(request.body)
    new_status = data.get('status')
    if new_status not in dict(Task.STATUS_CHOICES):
        return JsonResponse({'error': 'Invalid status'}, status=400)
    task.status = new_status
    task.save(update_fields=['status', 'updated_at'])
    return JsonResponse({'success': True, 'task_id': task.id, 'status': task.status})