from django.db import models
from apps.core.models import TenantModel


class Notification(TenantModel):
    """Notificación interna para un usuario."""
    TIPOS = [
        ('info',    'Información'),
        ('success', 'Éxito'),
        ('warning', 'Advertencia'),
        ('error',   'Error'),
    ]

    user      = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='notifications')
    mensaje   = models.TextField()
    tipo      = models.CharField(max_length=10, choices=TIPOS, default='info')
    leida     = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'leida']),
            models.Index(fields=['organization', '-created_at']),
        ]

    def __str__(self):
        return f'{self.tipo}: {self.mensaje[:50]}'
