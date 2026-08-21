from django.contrib import admin
from .models import Milestone, Task


@admin.register(Milestone)
class MilestoneAdmin(admin.ModelAdmin):
    list_display = ('title', 'target_date', 'status')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'assigned_to', 'priority', 'status', 'due_date')
    list_filter = ('status', 'priority')