from django import forms
from .models import Task, Milestone


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'milestone', 'assigned_to', 'priority', 'status', 'due_date']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'border rounded px-3 py-2 w-full'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'border rounded px-3 py-2 w-full'}),
            'title': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'milestone': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'assigned_to': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'priority': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'status': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
        }


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['title', 'target_date', 'status']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'border rounded px-3 py-2 w-full'}),
            'title': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'status': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
        }