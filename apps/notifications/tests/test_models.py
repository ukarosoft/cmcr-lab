"""Tests del modelo Notification."""
import pytest

from apps.notifications.models import Notification
from apps.notifications.tests.factories import NotificationFactory
from apps.lab_inventory.tests.factories import OrganizationFactory, UserFactory

pytestmark = pytest.mark.django_db


class TestNotification:
    def test_creation(self):
        n = NotificationFactory(mensaje='Hola')
        assert n.pk is not None
        assert n.mensaje == 'Hola'
        assert n.leida is False

    def test_for_tenant_isolation(self):
        org_a = OrganizationFactory()
        org_b = OrganizationFactory()
        NotificationFactory.create_batch(3, organization=org_a)
        NotificationFactory.create_batch(2, organization=org_b)

        assert Notification.objects.for_tenant(org_a).count() == 3
        assert Notification.objects.for_tenant(org_b).count() == 2

    def test_str_truncates_long_message(self):
        n = NotificationFactory(mensaje='a' * 100, tipo='warning')
        assert 'warning:' in str(n)
        assert len(str(n).split(':', 1)[1].strip()) <= 50

    def test_ordered_by_created_desc(self):
        org = OrganizationFactory()
        NotificationFactory(organization=org, mensaje='primera')
        NotificationFactory(organization=org, mensaje='segunda')
        msgs = list(
            Notification.objects.for_tenant(org).values_list('mensaje', flat=True)
        )
        assert msgs == ['segunda', 'primera']
