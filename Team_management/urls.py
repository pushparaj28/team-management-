from django.contrib import admin
#from django.templatetags import static

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from django.views.generic import RedirectView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('tasks/', include('tasks.urls')),
    path('', RedirectView.as_view(pattern_name='accounts:login'), name='home'),
    # Ye ek nayi line add kar dijiye 
     path('resource/', include('resource.urls')),

     
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )