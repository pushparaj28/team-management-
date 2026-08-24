import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q

from .models import Task, Milestone
from .forms import TaskForm, MilestoneForm

@login_required
def dashboard(request):
    user = request.user
    
    # 1. ADMIN LOGIC (Sabka Baap)
    if user.is_superuser:
        my_tasks = Task.objects.all()
        team_users = User.objects.filter(tasks__isnull=False).distinct()
        
    # 2. 🟢 MANAGER LOGIC: Khud ke aur apne employees ke stats dekhna
    elif hasattr(user, 'profile') and user.profile.role == 'manager':
        my_tasks = Task.objects.filter(
            Q(assigned_to=user) | Q(assigned_to__profile__manager=user)
        ).distinct()
        team_users = User.objects.filter(
            Q(id=user.id) | Q(profile__manager=user)
        ).distinct()
        
    # 3. EMPLOYEE LOGIC
    else:
        my_tasks = Task.objects.filter(assigned_to=user)
        team_users = User.objects.filter(id=user.id) # Sirf yahi user aayega

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
        'tasks': my_tasks, 
        'milestones': Milestone.objects.all(),
        'percent_complete': percent_complete,
        'total_tasks': total,
        'done_tasks': done,
        'member_stats': member_stats,
    }
    
    return render(request, 'tasks/dashboard.html', context)


@login_required
def kanban_board(request):
    user = request.user
    
    if user.is_superuser:
        tasks = Task.objects.select_related('assigned_to').all()
        
    elif hasattr(user, 'profile') and user.profile.role == 'manager':
        tasks = Task.objects.filter(
            Q(assigned_to=user) | Q(assigned_to__profile__manager=user)
        ).select_related('assigned_to').distinct()
        
    else:
        tasks = Task.objects.filter(assigned_to=user).select_related('assigned_to')

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
        # 🟢 JAADU: form ko 'user' pass karna taaki Manager ki team filter ho sake
        form = TaskForm(request.POST, instance=task, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('tasks:kanban')
    else:
        # 🟢 JAADU: GET request me bhi form ko 'user' dena
        form = TaskForm(instance=task, user=request.user)
        
    return render(request, 'tasks/task_form.html', {'form': form, 'task': task})


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
def task_delete(request, pk):
    # 🟢 SECURITY: Agar user Admin nahi hai aur Manager bhi nahi hai, toh bhaga do
    if not request.user.is_superuser:
        if not hasattr(request.user, 'profile') or request.user.profile.role != 'manager':
            return redirect('tasks:kanban') 

    task = get_object_or_404(Task, pk=pk)
    task.delete()
    return redirect('tasks:kanban')


@login_required
@require_POST
def update_task_status(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            new_status = data.get('status')
            if new_status in dict(Task.STATUS_CHOICES):
                task.status = new_status
                task.save(update_fields=['status', 'updated_at'])
                return JsonResponse({'success': True, 'task_id': task.id, 'status': task.status})
            return JsonResponse({'error': 'Invalid status'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid request format'}, status=400)
            
    else:
        new_status = request.POST.get('status')
        if new_status and new_status in dict(Task.STATUS_CHOICES):
            task.status = new_status
            task.save(update_fields=['status', 'updated_at'])
            
        return redirect('tasks:kanban')