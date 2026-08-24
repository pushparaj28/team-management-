from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('team/', views.team_list, name='team_list'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('team/delete/<int:user_id>/', views.delete_member, name='delete_member'),
    path('team/edit/<int:user_id>/', views.edit_member, name='edit_member'),
    path('my-team/', views.manager_dashboard, name='manager_dashboard'),
    path('add-to-team/<int:profile_id>/', views.add_employee_to_team, name='add_employee_to_team'),
]