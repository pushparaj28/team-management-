from django import forms
from .models import Task, Milestone
from django.contrib.auth.models import User # Ye zaroori hai filtering ke liye

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

    # 🟢 JAADU: Form ko batane ke liye ki "Kaun sa user form khol raha hai"
    def __init__(self, *args, **kwargs):
        # Views se hum 'user' bhejege, usko yahan catch kar liya
        user = kwargs.pop('user', None) 
        super(TaskForm, self).__init__(*args, **kwargs)
        
        if user:
            # Agar user ADMIN (Superuser) nahi hai, aur role MANAGER hai...
            if not user.is_superuser and hasattr(user, 'profile') and user.profile.role == 'manager':
                # Toh 'Assign To' dropdown me sirf uski team ke members dikhao
                self.fields['assigned_to'].queryset = self.fields['assigned_to'].queryset.filter(profile__manager=user)


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['title', 'target_date', 'status']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'border rounded px-3 py-2 w-full'}),
            'title': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'status': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
        }