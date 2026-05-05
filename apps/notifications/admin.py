from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Administración de notificaciones."""
    list_display = ['user', 'tipo', 'mensaje', 'leida', 'created_at']
    list_filter = ['tipo', 'leida', 'organization']
    search_fields = ['user__username', 'mensaje']
    readonly_fields = ['created_at']
