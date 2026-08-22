from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView  # Ye naya import add karna hai

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    
    # Jab koi khali URL (root) dale, toh usko accounts:login par bhej do
    path('', RedirectView.as_view(pattern_name='accounts:login'), name='home'),
    # Ye ek nayi line add kar dijiye 👇
    path('tasks/', include('tasks.urls')),
]