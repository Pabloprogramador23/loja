from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('saas/', include('core.saas_urls')),
    path('auth/', include('accounts.urls')),
    path('', include('core.urls')),
    path('', include('accounts.urls')),
]

from django.conf import settings
from django.urls import re_path
from django.views.static import serve

# Serve media files in all environments (Caddy/Nginx handles caching in prod)
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
