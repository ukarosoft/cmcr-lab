from django.conf import settings
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls', namespace='core')),
    path('inventario/', include('apps.lab_inventory.urls', namespace='lab_inventory')),
    path('notificaciones/', include('apps.notifications.urls', namespace='notifications')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns.insert(0, path('__debug__/', include(debug_toolbar.urls)))
