from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('overview/', views.overview, name='overview'),
    path('api/overview-data/', views.overview_data_api, name='overview_data_api'),
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
    path('calendar/event/new/', views.event_create, name='event_create'),
    path('list/', views.task_list_view, name='task_list'),
    path('api/task/<int:pk>/detail/', views.task_detail_api, name='task_detail_api'),
    path('api/task/<int:pk>/team/add/', views.task_team_add, name='task_team_add'),
    path('api/task/<int:pk>/team/<int:membership_id>/remove/', views.task_team_remove, name='task_team_remove'),
]