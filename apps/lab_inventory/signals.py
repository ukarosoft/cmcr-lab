"""Signals para notificaciones automáticas de lab_inventory."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.core.models import User
from apps.notifications.models import Notification
from .models import StockMovement, ProductionOrder


@receiver(post_save, sender=StockMovement)
def check_low_stock(sender, instance, created, **kwargs):
    """Notifica admin/manager cuando un insumo o reactivo baja de su stock mínimo."""
    if not created:
        return

    item = instance.supply or instance.reagent
    if not item or not hasattr(item, 'stock_status'):
        return

    if item.stock_status != 'low':
        return

    # Evitar spam: no notificar si ya hay una notificación reciente (últimas 24h)
    from django.utils import timezone
    from datetime import timedelta
    recent_cutoff = timezone.now() - timedelta(hours=24)
    recent = Notification.objects.for_tenant(instance.organization).filter(
        mensaje__contains=item.name,
        tipo='warning',
        created_at__gte=recent_cutoff,
    ).exists()
    if recent:
        return

    if hasattr(item, 'unit'):
        unit_abbr = item.unit.abbreviation
    else:
        unit_abbr = item.yield_unit.abbreviation

    users = User.objects.filter(
        organization=instance.organization,
        role__in=['admin', 'manager'],
        is_active=True,
    )
    for user in users:
        Notification.objects.create(
            organization=instance.organization,
            user=user,
            mensaje=f'Stock bajo de {item.name}: {item.current_stock} {unit_abbr}',
            tipo='warning',
        )


@receiver(post_save, sender=ProductionOrder)
def notify_order_status_change(sender, instance, **kwargs):
    """Notifica admin/manager cuando una OP se completa o cancela."""
    if instance.status not in ('completed', 'cancelled'):
        return

    tipo = 'success' if instance.status == 'completed' else 'warning'
    estado = 'completada' if instance.status == 'completed' else 'cancelada'
    msg = f'OP-{instance.batch_number} ({instance.reagent.name}) {estado}'

    users = User.objects.filter(
        organization=instance.organization,
        role__in=['admin', 'manager'],
        is_active=True,
    )
    for user in users:
        Notification.objects.create(
            organization=instance.organization,
            user=user,
            mensaje=msg,
            tipo=tipo,
        )
