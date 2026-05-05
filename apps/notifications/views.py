from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
@require_POST
def marcar_leida(request, pk):
    """Marca una notificación como leída (endpoint HTMX)."""
    notificacion = get_object_or_404(
        Notification,
        pk=pk,
        user=request.user,
    )
    notificacion.leida = True
    notificacion.save(update_fields=['leida'])
    return JsonResponse({'status': 'ok'})


@login_required
@require_POST
def marcar_todas_leidas(request):
    """Marca todas las notificaciones del usuario como leídas."""
    Notification.objects.filter(
        user=request.user,
        leida=False,
    ).update(leida=True)
    return JsonResponse({'status': 'ok'})
