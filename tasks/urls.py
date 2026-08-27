from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('overview/', views.overview, name='overview'),
    path('', views.dashboard, name='dashboard'),
    path('kanban/', views.kanban_board, name='kanban'),
    path('task/<int:pk>/', views.task_detail, name='task_detail'),
    path('task/new/', views.task_form_view, name='task_create'),
    path('task/<int:pk>/edit/', views.task_form_view, name='task_edit'),
    path('task/<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('milestone/new/', views.milestone_form_view, name='milestone_create'),
    path('api/task/<int:pk>/update-status/', views.update_task_status, name='update_task_status'),
    path('api/task/quick-create/', views.quick_create_task, name='quick_create_task'),
    path('task/<int:pk>/comment/', views.add_task_comment, name='add_task_comment'),
    path('leaves/', views.leave_list, name='leave_list'),
    path('leaves/new/', views.leave_request_create, name='leave_request_create'),
    path('leaves/<int:pk>/review/', views.leave_review, name='leave_review'),
    path('calendar/', views.calendar_view, name='calendar'),
]