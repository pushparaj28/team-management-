from django.contrib import admin
from .models import UserProfile

# Admin panel me hamara model kaisa dikhega, uski setting
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'phone_number', 'is_active_team_member')
    list_filter = ('role', 'is_active_team_member')
    search_fields = ('user__username', 'phone_number')