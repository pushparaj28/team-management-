from django import forms
from .models import Task, Milestone, LeaveRequest
from django.contrib.auth.models import User
from django.utils import timezone 

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'milestone', 'assigned_to', 'priority', 'status', 'due_date', 'attachment', 'reference_url']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'border rounded px-3 py-2 w-full'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'border rounded px-3 py-2 w-full'}),
            'title': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'milestone': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'assigned_to': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'priority': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'status': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'border rounded px-3 py-2 w-full text-sm'}),
            'reference_url': forms.URLInput(attrs={'class': 'border rounded px-3 py-2 w-full', 'placeholder': 'https://...'}),
        }

    # 🟢 JAADU: Form ko batane ke liye ki "Kaun sa user form khol raha hai"
    def __init__(self, *args, **kwargs):
        # Views se hum 'user' bhejege, usko yahan catch kar liya
        user = kwargs.pop('user', None) 
        super(TaskForm, self).__init__(*args, **kwargs)

        # Frontend restriction: date picker won't show past dates
        self.fields['due_date'].widget.attrs['min'] = timezone.localdate().isoformat()

        if user:
            # Agar user ADMIN (Superuser) nahi hai, aur role MANAGER hai...
            if not user.is_superuser and hasattr(user, 'profile') and user.profile.role == 'manager':
                # Toh 'Assign To' dropdown me sirf uski team ke members dikhao
                self.fields['assigned_to'].queryset = self.fields['assigned_to'].queryset.filter(profile__manager=user)

    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date:
            today = timezone.localdate()
            if due_date < today:
                # Allow saving unchanged if this task already had this
                # past date before the edit — don't break existing valid tasks.
                already_had_this_date = (
                    self.instance
                    and self.instance.pk
                    and self.instance.due_date == due_date
                )
                if not already_had_this_date:
                    raise forms.ValidationError("Due date cannot be in the past.")
        return due_date


class MilestoneForm(forms.ModelForm):
    class Meta:
        model = Milestone
        fields = ['title', 'target_date', 'status']
        widgets = {
            'target_date': forms.DateInput(attrs={'type': 'date', 'class': 'border rounded px-3 py-2 w-full'}),
            'title': forms.TextInput(attrs={'class': 'border rounded px-3 py-2 w-full'}),
            'status': forms.Select(attrs={'class': 'border rounded px-3 py-2 w-full'}),
        }

class LeaveRequestForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ['start_date', 'end_date', 'reason']
        widgets = {
            'start_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'border rounded px-3 py-2 w-full',
                }
            ),
            'end_date': forms.DateInput(
                attrs={
                    'type': 'date',
                    'class': 'border rounded px-3 py-2 w-full',
                }
            ),
            'reason': forms.Textarea(
                attrs={
                    'rows': 3,
                    'class': 'border rounded px-3 py-2 w-full',
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        today = timezone.localdate().isoformat()

        self.fields['start_date'].widget.attrs['min'] = today
        self.fields['end_date'].widget.attrs['min'] = today

    def clean(self):
        cleaned_data = super().clean()

        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        today = timezone.localdate()

        if start_date and start_date < today:
            self.add_error(
                'start_date',
                'Leave start date cannot be in the past.'
            )

        if end_date and end_date < today:
            self.add_error(
                'end_date',
                'Leave end date cannot be in the past.'
            )

        if start_date and end_date and end_date < start_date:
            self.add_error(
                'end_date',
                'End date cannot be before the start date.'
            )

        return cleaned_data 