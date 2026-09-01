from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('employee', 'Employee'),
    )
    
    DEPARTMENT_CHOICES = [
        ('IT', 'IT / Development'),
        ('Design', 'UI/UX Design'),
        ('Marketing', 'Marketing'),
        ('HR', 'Human Resources'),
        ('Sales', 'Sales'),
        ('Administration', 'Administration'),
    ]
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    theme_preference = models.CharField(max_length=10, choices=[('light', 'Light'), ('dark', 'Dark')], default='light')
    email_notifications = models.BooleanField(default=True) 
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='team_employees')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    department = models.CharField(max_length=50, choices=DEPARTMENT_CHOICES, default='IT')
    is_active_team_member = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    profile_pic = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True) # Duplicate phone field hatakar ek kiya
    
    # Personal Info
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    blood_group = models.CharField(max_length=5, blank=True, null=True)
    nationality = models.CharField(max_length=50, default='Indian')
    
    # Work Info
    employee_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    joining_date = models.DateField(null=True, blank=True)
    
    # Address Info (Pincode API ke liye)
    country = models.CharField(max_length=100, default='India')
    city = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    address_line = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('info', 'Information'),
        ('success', 'Success'),
        ('warning', 'Warning'),
        ('task', 'Task Update'),
        ('attendance', 'Attendance Alert'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    title = models.CharField(max_length=150)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')
    link = models.CharField(max_length=255, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.title} ({'Read' if self.is_read else 'Unread'})"