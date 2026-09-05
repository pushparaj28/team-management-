from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import Notification

class Milestone(models.Model):
    STATUS_CHOICES = [
        ('Upcoming', 'Upcoming'),
        ('Active', 'Active'),
        ('Completed', 'Completed'),
    ]
    title = models.CharField(max_length=200)
    target_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Upcoming')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Task(models.Model):
    PRIORITY_CHOICES = [('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')]
    STATUS_CHOICES = [
        ('Backlog', 'Backlog'),
        ('In Progress', 'In Progress'),
        ('Review', 'Review'),
        ('Done', 'Done'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    milestone = models.ForeignKey(Milestone, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='Medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Backlog')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    attachment = models.FileField(upload_to='task_attachments/', null=True, blank=True)
    reference_url = models.URLField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tasks')
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

class TaskComment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.author.username}: {self.message[:30]}"

class LeaveRequest(models.Model):
    STATUS_CHOICES = [('Pending', 'Pending'), ('Approved', 'Approved'), ('Rejected', 'Rejected')]
    employee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='leave_requests')
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_leaves')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class Event(models.Model):
    """
    Admin-created company-wide events/announcements/meetings.
    Always visible to every authenticated user on the calendar —
    there's no audience-scoping field because only Admins can create
    these, and the requirement is that they broadcast to everyone.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    date = models.DateField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return self.title


@receiver(post_save, sender=Task)
def notify_employee_on_task_event(sender, instance, created, **kwargs):
    # 🟢 1. Check karein ki task kis employee ko assign kiya gaya hai
    employee = getattr(instance, 'assigned_to', None)
    if not employee:
        return

    # Task assign karne wala manager (agar model me field hai, nahi toh None)
    manager = getattr(instance, 'created_by', None)

    if created:
        title = "New Task Assigned"
        msg = f"A new task '{instance.title}' has been assigned to you."
    else:
        title = "Task Updated"
        msg = f"Your task '{instance.title}' was modified."

    # 🟢 2. Target employee ke liye notification create karein
    Notification.objects.create(
        user=employee,                      # 👈 Notification assigned employee ke account me jayegi
        sender=manager,                     # 👈 Assign karne wala manager
        title=title,
        message=msg,
        notification_type='task',
        link='/tasks/kanban/'            # Click karne par employee seedha task page par jayega
    )


class TaskTeamMember(models.Model):
    """
    Additional people working on a task beyond the primary assignee
    (Task.assigned_to). Kept as a separate small model rather than
    turning assigned_to into a ManyToMany, so every existing query,
    form, and permission check built around a single assignee keeps
    working unchanged.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='team_members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_team_memberships')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('task', 'user')

    def __str__(self):
        return f"{self.user.username} on {self.task.title}"