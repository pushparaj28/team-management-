import json
import calendar as cal_module
from datetime import timedelta, datetime
from math import ceil
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import LeaveRequest, Event
from .forms import LeaveRequestForm

from accounts.models import UserProfile
from .models import Task, Milestone, TaskComment
from .forms import TaskForm, MilestoneForm, EventForm


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
# Leave permission helpers
# ---------------------------------------------------------------

def _leave_submitter_role(leave):
    """Role of the person who submitted this leave request."""
    employee = leave.employee
    if hasattr(employee, 'profile'):
        return employee.profile.role
    return 'employee'


def _visible_leaves(user):
    """
    Returns the queryset of leave requests this user is allowed to see.
    - Admin: all Manager-submitted leaves (full history) +
             Employee-submitted leaves that have already been decided
             by their manager (Approved/Rejected) — pending employee
             leaves stay with the manager until a decision is made.
    - Manager: leave requests from employees assigned to them, plus
               their own leave request (read-only status).
    - Employee: only their own leave request.
    """
    if user.is_superuser:
        manager_leaves = LeaveRequest.objects.filter(employee__profile__role='manager')
        decided_employee_leaves = LeaveRequest.objects.filter(
            employee__profile__role='employee'
        ).exclude(status='Pending')
        return (manager_leaves | decided_employee_leaves).select_related('employee', 'employee__profile', 'reviewed_by').distinct()

    if _is_manager(user):
        team_leaves = LeaveRequest.objects.filter(
            employee__profile__manager=user, employee__profile__role='employee'
        )
        own_leave = LeaveRequest.objects.filter(employee=user)
        return (team_leaves | own_leave).select_related('employee', 'employee__profile', 'reviewed_by').distinct()

    # Employee: only ever their own
    return LeaveRequest.objects.filter(employee=user).select_related('employee', 'reviewed_by')


def _can_review_leave(user, leave):
    """
    True if this user may approve/reject the given leave request.
    - Manager-submitted leave -> only Admin (superuser) may decide.
    - Employee-submitted leave -> only that employee's assigned
      manager may decide. Admin never decides employee leave directly.
    """
    submitter_role = _leave_submitter_role(leave)

    if submitter_role == 'manager':
        return user.is_superuser

    # submitter is an employee
    employee = leave.employee
    if not hasattr(employee, 'profile'):
        return False
    return employee.profile.manager_id == user.id


# ---------------------------------------------------------------
# Page views
# ---------------------------------------------------------------

@login_required
def overview(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden("Overview is only available to admins.")

    today = timezone.localdate()

    # ---------------- Filters ----------------
    range_param = request.GET.get('range', '7')       # '7' | '30' | '90' | 'custom'
    department = request.GET.get('department', '')     # '' = all departments

    if range_param == 'custom':
        try:
            start_date = datetime.strptime(request.GET.get('start', ''), '%Y-%m-%d').date()
        except ValueError:
            start_date = today - timedelta(days=6)
        try:
            end_date = datetime.strptime(request.GET.get('end', ''), '%Y-%m-%d').date()
        except ValueError:
            end_date = today
        if end_date < start_date:
            start_date, end_date = end_date, start_date
    else:
        days = int(range_param) if range_param in ('7', '30', '90') else 7
        start_date = today - timedelta(days=days - 1)
        end_date = today

    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    assignee_filter = request.GET.get('assignee', '')
    milestone_filter = request.GET.get('milestone', '')

    tasks_qs = Task.objects.select_related('assigned_to', 'milestone').all()
    if department:
        tasks_qs = tasks_qs.filter(assigned_to__profile__department=department)
    if status_filter:
        tasks_qs = tasks_qs.filter(status=status_filter)
    if priority_filter:
        tasks_qs = tasks_qs.filter(priority=priority_filter)
    if assignee_filter:
        tasks_qs = tasks_qs.filter(assigned_to_id=assignee_filter)
    if milestone_filter:
        tasks_qs = tasks_qs.filter(milestone_id=milestone_filter)

    # ---------------- KPI cards ----------------
    total_users = User.objects.count()
    active_projects = Milestone.objects.filter(status='Active').count()
    tasks_in_progress = tasks_qs.filter(status='In Progress').count()
    tasks_completed = tasks_qs.filter(status='Done').count()
    overdue_tasks = tasks_qs.filter(due_date__lt=today).exclude(status='Done').count()

    # ---------------- Trend chart, bucketed so wide ranges stay readable ----------------
    total_days = (end_date - start_date).days + 1
    max_points = 14
    if total_days <= max_points:
        buckets = [(start_date + timedelta(days=i), start_date + timedelta(days=i)) for i in range(total_days)]
    else:
        bucket_size = ceil(total_days / max_points)
        buckets, cur = [], start_date
        while cur <= end_date:
            b_end = min(cur + timedelta(days=bucket_size - 1), end_date)
            buckets.append((cur, b_end))
            cur = b_end + timedelta(days=1)

    chart_labels, completed_series, in_progress_series, overdue_series = [], [], [], []
    for b_start, b_end in buckets:
        chart_labels.append(
            b_start.strftime('%d %b') if b_start == b_end
            else f"{b_start.strftime('%d %b')}\u2013{b_end.strftime('%d %b')}"
        )
        completed_series.append(tasks_qs.filter(status='Done', updated_at__date__gte=b_start, updated_at__date__lte=b_end).count())
        in_progress_series.append(tasks_qs.filter(status='In Progress', updated_at__date__gte=b_start, updated_at__date__lte=b_end).count())
        overdue_series.append(tasks_qs.filter(due_date__gte=b_start, due_date__lte=b_end).exclude(status='Done').count())

    # ---------------- Project status donut ----------------
    milestone_counts = {
        'Completed': Milestone.objects.filter(status='Completed').count(),
        'Active': Milestone.objects.filter(status='Active').count(),
        'Upcoming': Milestone.objects.filter(status='Upcoming').count(),
    }

    # ---------------- Team distribution donut (always the full picture, not date/dept scoped) ----------------
    dept_counts = {}
    for code, label in UserProfile.DEPARTMENT_CHOICES:
        count = UserProfile.objects.filter(department=code).count()
        if count:
            dept_counts[label] = count

    # ---------------- Recent activity, scoped to the selected range ----------------
    activity = []
    for c in TaskComment.objects.select_related('author', 'task').filter(
        created_at__date__gte=start_date, created_at__date__lte=end_date
    ).order_by('-created_at')[:5]:
        activity.append({'text': f'{c.author.username} commented on "{c.task.title}"', 'time': c.created_at})
    for t in tasks_qs.select_related('assigned_to').filter(
        created_at__date__gte=start_date, created_at__date__lte=end_date
    ).order_by('-created_at')[:5]:
        activity.append({'text': f'Task "{t.title}" created', 'time': t.created_at})
    activity.sort(key=lambda x: x['time'], reverse=True)
    activity = activity[:6]

    upcoming = tasks_qs.filter(due_date__gte=today).exclude(status='Done').order_by('due_date')[:6]

    context = {
        'total_users': total_users,
        'active_projects': active_projects,
        'tasks_in_progress': tasks_in_progress,
        'tasks_completed': tasks_completed,
        'overdue_tasks': overdue_tasks,
        'chart_labels': chart_labels,
        'completed_series': completed_series,
        'in_progress_series': in_progress_series,
        'overdue_series': overdue_series,
        'milestone_counts': milestone_counts,
        'dept_counts': dept_counts,
        'activity': activity,
        'upcoming': upcoming,
        'today': today,
        'selected_range': range_param,
        'selected_department': department,
        'department_choices': UserProfile.DEPARTMENT_CHOICES,
        'start_date': start_date,
        'end_date': end_date,
        'selected_status': status_filter,
        'selected_priority': priority_filter,
        'selected_assignee': assignee_filter,
        'selected_milestone': milestone_filter,
        'status_choices': Task.STATUS_CHOICES,
        'priority_choices': Task.PRIORITY_CHOICES,
        'assignee_choices': User.objects.filter(tasks__isnull=False).distinct().order_by('username'),
        'milestone_choices': Milestone.objects.all().order_by('title'),
    }
    from django.template.response import TemplateResponse
    return TemplateResponse(request, 'tasks/overview.html', context)


@login_required
def overview_data_api(request):
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    # Re-run overview() logic but return JSON instead of a template.
    # We call the view function internally and pull the exact same
    # context so filters can never drift out of sync between the
    # full-page load and the AJAX refresh.
    from django.template.response import TemplateResponse
    response = overview(request)
    if isinstance(response, JsonResponse):
        return response
    context = response.context_data if hasattr(response, 'context_data') else None
    if context is None:
        return JsonResponse({'error': 'Could not build overview data'}, status=500)

    return JsonResponse({
        'total_users': context['total_users'],
        'active_projects': context['active_projects'],
        'tasks_in_progress': context['tasks_in_progress'],
        'tasks_completed': context['tasks_completed'],
        'overdue_tasks': context['overdue_tasks'],
        'chart_labels': context['chart_labels'],
        'completed_series': context['completed_series'],
        'in_progress_series': context['in_progress_series'],
        'overdue_series': context['overdue_series'],
        'milestone_counts': context['milestone_counts'],
    })

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

    today = timezone.localdate()
    overdue_count = my_tasks.filter(due_date__lt=today).exclude(status='Done').count()
    upcoming_tasks = my_tasks.filter(due_date__gte=today).exclude(status='Done').order_by('due_date')[:4]

    # Role-based extra KPI: dynamic counts, never hardcoded
    total_managers = None
    total_employees = None
    if user.is_superuser:
        total_managers = UserProfile.objects.filter(role='manager').count()
        total_employees = UserProfile.objects.filter(role='employee').count()
    elif _is_manager(user):
        total_employees = UserProfile.objects.filter(manager=user, role='employee').count()

    context = {
        'milestones': Milestone.objects.all(),
        'percent_complete': percent_complete,
        'total_tasks': total,
        'done_tasks': done,
        'overdue_count': overdue_count,
        'upcoming_tasks': upcoming_tasks,
        'member_stats': member_stats,
        'can_manage': user.is_superuser or _is_manager(user),
        'today': today,
        'total_managers': total_managers,
        'total_employees': total_employees,
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

    if request.user.is_superuser:
        comment_placeholder = "Add an admin note about this task..."
    elif _is_manager(request.user):
        comment_placeholder = "Add an update or comment about this task..."
    else:
        comment_placeholder = "Ask your manager about this task..."

    context = {
        'task': task,
        'comments': task.comments.select_related('author'),
        'can_manage': _can_manage_task(request.user, task),
        'can_update_status': (
            request.user.is_superuser
            or _can_manage_task(request.user, task)
            or task.assigned_to_id == request.user.id
        ),
        'comment_placeholder': comment_placeholder,
    }
    return render(request, 'tasks/task_detail.html', context)


@login_required
@require_POST
def add_task_comment(request, pk):
    task = get_object_or_404(Task, pk=pk)
    # Only the assignee, their manager, or admin can post on this task
    allowed = (
        request.user.is_superuser
        or _can_manage_task(request.user, task)
        or task.assigned_to_id == request.user.id
    )
    if not allowed:
        return HttpResponseForbidden("You don't have permission to comment on this task.")

    message = request.POST.get('message', '').strip()
    if message:
        TaskComment.objects.create(task=task, author=request.user, message=message)
    return redirect('tasks:task_detail', pk=task.pk)


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
        form = TaskForm(request.POST, request.FILES, instance=task, user=request.user)
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

@login_required
def leave_list(request):
    user = request.user
    leaves = _visible_leaves(user)

    context = {
        'is_admin': user.is_superuser,
        'is_manager': _is_manager(user),
    }

    if user.is_superuser:
        # Admin sees two clearly separated sections — never mixed
        context['manager_leaves'] = leaves.filter(employee__profile__role='manager').order_by('-created_at')
        context['employee_leaves'] = leaves.filter(employee__profile__role='employee').order_by('-created_at')
    elif _is_manager(user):
        context['team_leaves'] = leaves.filter(employee__profile__role='employee').order_by('-created_at')
        context['own_leave'] = leaves.filter(employee=user).order_by('-created_at')
    else:
        context['leaves'] = leaves.order_by('-created_at')

    return render(request, 'tasks/leaves.html', context)


@login_required
def leave_request_create(request):
    # Unchanged — employees, managers, and admins can all apply for
    # their own leave; the workflow difference happens at review time.
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.employee = request.user
            leave.save()
            return redirect('tasks:leave_list')
    else:
        form = LeaveRequestForm()
    return render(request, 'tasks/leave_form.html', {'form': form})


@login_required
@require_POST
def leave_review(request, pk):
    leave = get_object_or_404(LeaveRequest, pk=pk)

    # Backend-enforced — not just a hidden button. A crafted POST from
    # an unauthorized user (wrong manager, another employee, etc.)
    # is rejected here regardless of what the UI shows them.
    if not _can_review_leave(request.user, leave):
        return HttpResponseForbidden("You don't have permission to review this leave request.")

    decision = request.POST.get('decision')
    if decision in ('Approved', 'Rejected'):
        leave.status = decision
        leave.reviewed_by = request.user
        leave.save()

    return redirect('tasks:leave_list')

@login_required
def calendar_view(request):
    today = timezone.localdate()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    # Backend-enforced role scoping — the same visibility rule your
    # Kanban/Dashboard/Leaves already use. Admin -> everyone,
    # Manager -> self + their employees, Employee -> just themself.
    team_users = _visible_team_users(request.user)

    tasks = Task.objects.filter(assigned_to__in=team_users, due_date__year=year, due_date__month=month)
    leaves = LeaveRequest.objects.filter(
        employee__in=team_users, status='Approved'
    ).filter(Q(start_date__year=year, start_date__month=month) | Q(end_date__year=year, end_date__month=month))

    # Milestones are org-wide project data (no owner field on the
    # model), so they stay visible to every authenticated user
    # regardless of role — same as before this change.
    milestones = Milestone.objects.filter(target_date__year=year, target_date__month=month)

    # Company-wide events are visible to everyone by design — only
    # Admins can create them (enforced in event_create below), so
    # there's no audience filter needed here.
    events = Event.objects.filter(date__year=year, date__month=month)

    events_by_day = {}
    for t in tasks:
        events_by_day.setdefault(t.due_date.day, []).append({
            'type': 'task', 'label': t.title, 'sub': t.assigned_to.username if t.assigned_to else 'Unassigned'
        })
    for m in milestones:
        events_by_day.setdefault(m.target_date.day, []).append({
            'type': 'milestone', 'label': m.title, 'sub': m.status
        })
    for l in leaves:
        d = l.start_date if l.start_date.month == month else l.end_date
        events_by_day.setdefault(d.day, []).append({
            'type': 'leave', 'label': f"{l.employee.username} — leave", 'sub': l.status
        })
    for e in events:
        events_by_day.setdefault(e.date.day, []).append({
            'type': 'event', 'label': e.title, 'sub': f"by {e.created_by.username}"
        })

    cal = cal_module.Calendar(firstweekday=0)
    month_days = cal.monthdayscalendar(year, month)

    prev_month, prev_year = (12, year - 1) if month == 1 else (month - 1, year)
    next_month, next_year = (1, year + 1) if month == 12 else (month + 1, year)

    context = {
        'month_days': month_days,
        'events_by_day': events_by_day,
        'month_name': cal_module.month_name[month],
        'year': year, 'month': month, 'today': today,
        'prev_month': prev_month, 'prev_year': prev_year,
        'next_month': next_month, 'next_year': next_year,
        'can_create_event': request.user.is_superuser,
    }
    return render(request, 'tasks/calendar.html', context)


@login_required
def event_create(request):
    # Backend-enforced, not just a hidden button — a non-admin who
    # manually POSTs here is rejected regardless of what the UI shows.
    if not request.user.is_superuser:
        return HttpResponseForbidden("Only admins can create company-wide events.")

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            return redirect('tasks:calendar')
    else:
        form = EventForm()
    return render(request, 'tasks/event_form.html', {'form': form})