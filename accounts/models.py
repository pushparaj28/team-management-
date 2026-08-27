from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    theme_preference = models.CharField(max_length=10, choices=[('light', 'Light'), ('dark', 'Dark')], default='light')
    email_notifications = models.BooleanField(default=True)     
    phone = models.CharField(max_length=20, blank=True, null=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='team_employees')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_active_team_member = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    DEPARTMENT_CHOICES = [
        ('IT', 'IT / Development'),
        ('Design', 'UI/UX Design'),
        ('Marketing', 'Marketing'),
        ('HR', 'Human Resources'),
        ('Sales', 'Sales'),
    ]
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='IT')

    def __str__(self):
        return f"{self.user.username} - {self.role}"