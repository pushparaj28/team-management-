from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    # Team roles define kar rahe hain
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    )

    # Django ke default User model ke sath jod rahe hain
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Hamari custom fields
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_active_team_member = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"