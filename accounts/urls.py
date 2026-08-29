from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_user, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    
    # 🟢 Sirf ek My Team URL (Purana wala hata diya gaya hai)
    
    path('my-team/add/<int:profile_id>/', views.add_employee_to_team, name='add_employee_to_team'),
    
    path('switch-role/<str:role>/', views.switch_role, name='switch_role'),
    path('managers/', views.managers_list, name='managers_list'),
    path('make-manager/<int:user_id>/', views.make_manager, name='make_manager'),
    path('toggle-status/<int:user_id>/', views.toggle_user_status, name='toggle_user_status'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('edit-manager/<int:user_id>/', views.edit_manager, name='edit_manager'),

    path('employees/', views.employees_list, name='employees_list'),
    path('edit-employee/<int:user_id>/', views.edit_employee, name='edit_employee'),
    path('add-user/', views.add_user, name='add_user'),

    # 🟢 Naya URL Manager ke personal team page ke liye
    path('my-squad/', views.manager_roster_view, name='manager_roster'),
    path('my-squad/add/', views.add_to_squad, name='add_to_squad'),
    path('my-squad/remove/<int:emp_id>/', views.remove_from_squad, name='remove_from_squad'),
]